import bottlenose
from lxml import objectify
from amazonconfig import AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID
import urllib2
from time import sleep
import pprint

# allow us to print lxml.objectify objects in a nice way
# can pull this out in prod
objectify.enable_recursive_str()


def debug_print_lxml(to_print):
    with open('debug.txt','w') as f:
        f.write(str(to_print))

def get_amazon_api():
    amazon_api = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID, MaxQPS=0.9)
    return amazon


def clean_response(response):
    ''' takes a response string
    returns that string without the 'http://webservices.amazon.com/AWSECommerceService/2011-08-01' text

    helps for using tags later on

    '''
    cleaned = response.replace('http://webservices.amazon.com/AWSECommerceService/2011-08-01','')
    return cleaned


def get_parent_ASIN(ASIN, amazon_api=None):
    ''' input: Amazon ASIN and optional amazon object
       output: the ASIN of the parent or the AuthorityTitle for a book
               if the object doesn't have a parent (or is the parent), the same ASIN is returned
    '''
    if amazon_api is None:  
        amazon_api = get_amazon_api()

    # different product types handle related items differently, so we need to
    # know how to handle this product
    product_group = get_product_group(ASIN=ASIN, amazon_api=amazon_api)

    parent_ASIN = ''

    if product_group == 'Book':
        response = clean_response(amazon_api.ItemLookup(ItemId=ASIN, ResponseGroup="RelatedItems,ItemAttributes", Condition='All', RelationshipType='AuthorityTitle'))
        item = objectify.fromstring(response)

        if item.Items.Item.RelatedItems.RelatedItem.Item.ItemAttributes.ProductGroup == 'Authority Non Buyable':
            parent_ASIN = item.Items.Item.RelatedItems.RelatedItem.Item.ASIN
        else:
            parent_ASIN = ASIN
    else:
        response = clean_response(amazon_api.ItemLookup(ItemId=ASIN, ResponseGroup="Variations", Condition='All' ))
        item = objectify.fromstring(response)

        try:
            parent_ASIN = item.Items.Item.ParentASIN
        except:
            parent_ASIN = ASIN

    parent_ASIN = str(parent_ASIN)

    return parent_ASIN


def get_book_variations_from_page(ASIN, amazon_api=None, page_number=1):
    ''' takes an ASIN and a page number
        returns a list of all variation ASINs on that page
    '''
    if amazon_api is None:  
        amazon_api = get_amazon_api()

    print 'getting variations on page ' + str(page_number)
    response = clean_response(amazon_api.ItemLookup(ItemId=ASIN,
                                                ResponseGroup="RelatedItems",
                                                Condition='All',
                                                RelationshipType='AuthorityTitle',
                                                RelatedItemPage=page_number ))
    root = objectify.fromstring(response)
    relatedItems = root.Items.Item.RelatedItems
    variations_on_page = []

    for x in relatedItems.iterchildren(tag='RelatedItem'):
        # make sure ASINs are 10 digits
        variationASIN = str(x.Item.ASIN).zfill(10)
        variations_on_page.append(variationASIN)

    return variations_on_page


def get_item_variations_from_parent(ASIN, amazon_api=None):
    ''' take an amazon "parent" ASIN
        returns a list of item variation ASINs
    '''
    if amazon_api is None:  
        amazon_api = get_amazon_api()

    # different product types handle related items differently, so we need to
    # know how to handle this product
    product_group = get_product_group(ASIN=ASIN, amazon_api=amazon_api)    

    if product_group == 'Book':
        response = clean_response(amazon_api.ItemLookup(ItemId=ASIN,
                                                    ResponseGroup="RelatedItems",
                                                    Condition='All',
                                                    RelationshipType='AuthorityTitle'))
        root = objectify.fromstring(response)
        relatedItems = root.Items.Item.RelatedItems
        numberOfPages = relatedItems.RelatedItemPageCount
        variationASINs= []
        for i in range(1,numberOfPages+1):
            variationASINs.extend(get_book_variations_from_page(ASIN=ASIN, page_number=i))

    else:
        amazon_api = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
        response = clean_response(amazon_api.ItemLookup(ItemId=ASIN,
                                                    ResponseGroup="Variations",
                                                    Condition='All' ))
        root = objectify.fromstring(response)

        variationASINs = []
        # if root.Items.Item.Variations doesn't exist,
        # there are no variations, so just the one version
        # which we add to the array and return. I don't love
        # the try-except block but it's working.

        try:
            variations = root.Items.Item.Variations
            # I don't think non-book variations will have more than one page.
            # Grabbed one shoe example (B00PVY92GS) that has 50+ variations retured
            for v in variations.iterchildren(tag='Item'):
                varASIN = str(v.ASIN).zfill(10)
                variationASINs.append(varASIN)
        except:
            variationASINs = [ASIN]

    return variationASINs


def get_product_group(ASIN, amazon_api=None):
    ''' takes an ASIN
       returns the product group (Book, UnboxVideo, Kitchen, etc)
    '''
    if amazon_api is None:  
        amazon_api = get_amazon_api()

    response = clean_response(amazon_api.ItemLookup(ItemId=ASIN, ResponseGroup="ItemAttributes", Condition='All' ))
    item = objectify.fromstring(response)

    try:
        product_group = item.Items.Item.ItemAttributes.ProductGroup
    except:
        product_group = 'Not Found'
    finally:
        return product_group


def get_offers(ASIN, amazon_api=None):
    ''' take an ASIN
        return a list of all best-price offers with price, condition, and prime status
    '''
    if amazon_api is None:  
        amazon_api = get_amazon_api()

    response = clean_response(amazon_api.ItemLookup(ItemId=ASIN, ResponseGroup="Offers", Condition='All' ))
    root = objectify.fromstring(response)

    offerList = root.Items.Item.Offers.iterchildren(tag='Offer')

    offers = []
    for offer in offerList:
        offers.append({"Condition":offer.OfferAttributes.Condition,
                       "PriceAmount":offer.OfferListing.Price.Amount,
                       "FormattedPrice":offer.OfferListing.Price.FormattedPrice,
                       "PrimeEligibility":offer.OfferListing.IsEligibleForPrime
                       })

    return offers


def get_images(ASIN, amazon_api=None):
    ''' take an ASIN
        return a dict with the Small, Medium, and Large image URLS and dimensions
    '''
    if amazon_api is None:  
        amazon_api = get_amazon_api()

    try:
        response = clean_response(amazon_api.ItemLookup(ItemId=ASIN, ResponseGroup="Images", Condition='All' ))
    except Error, err:
        print err

    root = objectify.fromstring(response)

    item = root.Items.Item

    images = {"SmallImage": {"URL": item.SmallImage.URL,
                             "Height": item.SmallImage.Height,
                             "Width": item.SmallImage.Width
                             },
              "MediumImage": {"URL": item.MediumImage.URL,
                             "Height": item.MediumImage.Height,
                             "Width": item.MediumImage.Width
                             },
              "LargeImage": {"URL": item.LargeImage.URL,
                             "Height": item.LargeImage.Height,
                             "Width": item.LargeImage.Width
                             }
             }

    return images


def check_for_valid_ASIN(ASIN, amazon_api=None):
    
    if amazon_api is None:
        amazon_api = get_amazon_api()

    response = clean_response(amazon_api.ItemLookup(ItemId=ASIN, ResponseGroup="ItemAttributes"))
    root = objectify.fromstring(response)

    # if there are errors, check for the invalid param one

    if hasattr(root.Items.Request,'Errors') and root.Items.Request.Errors.Error.Code == 'AWS.InvalidParameterValue':
        return False
    else:
        return True


def get_item_attributes(ASIN, amazon_api=None):

    if amazon_api is None:
        amazon_api = get_amazon_api()

    response = clean_response(amazon_api.ItemLookup(ItemId=ASIN, ResponseGroup="ItemAttributes"))
    root = objectify.fromstring(response)

    item = root.Items.Item

    URL = ''
    listPriceAmount = ''
    listPriceFormatted = ''
    title = ''
    product_group = ''

    if hasattr(item, 'DetailPageURL'):
        URL = str(item.DetailPageURL)
    if hasattr(item.ItemAttributes, 'ListPrice'):
        listPriceAmount = str(item.ItemAttributes.ListPrice.Amount)
        listPriceFormatted = str(item.ItemAttributes.ListPrice.FormattedPrice)
    if hasattr(item.ItemAttributes, 'Title'):
        title = str(item.ItemAttributes.Title)
    if hasattr(item.ItemAttributes, 'ProductGroup'):
        product_group = str(item.ItemAttributes.ProductGroup)

    item_attributes = {"URL": URL,
                       "listPriceAmount": listPriceAmount,
                       "listPriceFormatted": listPriceFormatted,
                       "title": title,
                       "product_group": product_group
                       }

    return item_attributes


def get_all_item_info(ASIN, amazon_api=None):

    if amazon_api is None:
        amazon_api = get_amazon_api()

    assert check_for_valid_ASIN(ASIN=ASIN, amazon_api=amazon_api) == True, "This is an invalid ASIN!"
    
    # get parent ASIN if applicable
    # if there isn't a parent, this will return the same ASIN
    parent_ASIN = get_parent_ASIN(ASIN=ASIN, amazon_api=amazon_api)
    print 'parent ASIN is ' + parent_ASIN
    parent_attribs = get_item_attributes(ASIN=parent_ASIN, amazon_api=amazon_api)
    # get variation ASINs
    variations = get_item_variations_from_parent(ASIN=parent_ASIN, amazon_api=amazon_api)
    print 'There are %s variations.' % str(len(variations))

    # for each variation:
    all_item_info = {"parent_ASIN": parent_ASIN,
                     "parent_attribs": parent_attribs,
                     "items": []
                     }

    for v in variations:
        print 'starting  ' + str(v)
        images = get_images(ASIN=v, amazon_api=amazon_api)
        print '    There are %s images.' % str(len(images))
        attributes = get_item_attributes(ASIN=v, amazon_api=amazon_api)
        offers = get_offers(ASIN=v, amazon_api=amazon_api)
        print '    There are %s offers.' % str(len(offers))
        all_item_info["items"].append({"ASIN": ASIN,
                              "images": images,
                              "attributes": attributes,
                              "offers": offers
                              })
        print 'done'

    return all_item_info



def main():

    amazon_api = get_amazon_api()
    ASIN = 'B00L5HCVSG'
    iteminfo = get_all_item_info(ASIN=ASIN, amazon_api=amazon_api)

    with open('item_info.txt','w') as f:
        f.write(str(iteminfo))


if __name__ == '__main__':
    main()

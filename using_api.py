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


def clean_response(response):
    ''' takes a response string
    returns that string without the 'http://webservices.amazon.com/AWSECommerceService/2011-08-01' text

    helps for using tags later on

    '''
    cleaned = response.replace('http://webservices.amazon.com/AWSECommerceService/2011-08-01','')
    return cleaned


def get_parent_ASIN(ASIN, product_group='Book' ):
    ''' input: Amazon ASIN and product group
       output: the ASIN of the parent or the AuthorityTitle for a book
               if the object doesn't have a parent (or is the parent), the same ASIN is returned
    '''

    parent_ASIN = ''

    if product_group == 'Book':
        amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
        response = clean_response(amazon.ItemLookup(ItemId=ASIN, ResponseGroup="RelatedItems,ItemAttributes", Condition='All', RelationshipType='AuthorityTitle'))
        item = objectify.fromstring(response)

        if item.Items.Item.RelatedItems.RelatedItem.Item.ItemAttributes.ProductGroup == 'Authority Non Buyable':
            parent_ASIN = item.Items.Item.RelatedItems.RelatedItem.Item.ASIN
        else:
            parent_ASIN = ASIN
    else:
        amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
        response = clean_response(amazon.ItemLookup(ItemId=ASIN, ResponseGroup="Variations", Condition='All' ))
        item = objectify.fromstring(response)

        try:
            parent_ASIN = item.Items.Item.ParentASIN
        except:
            parent_ASIN = ASIN

    return parent_ASIN


def get_book_variations_from_page(ASIN, page_number=1):
    ''' takes an ASIN and a page number
        returns a list of all variation ASINs on that page
    '''
    print 'getting variations on page ' + str(page_number)
    amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
    response = clean_response(amazon.ItemLookup(ItemId=ASIN,
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


def get_item_variations_from_parent(ASIN, product_group='Book'):
    ''' take an amazon "parent" ASIN
        returns a list of item variation ASINs
    '''

    amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)

    if product_group == 'Book':
        response = clean_response(amazon.ItemLookup(ItemId=ASIN,
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
        amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
        response = clean_response(amazon.ItemLookup(ItemId=ASIN,
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


def get_product_group(ASIN):
    ''' takes an ASIN
       returns the product group (Book, UnboxVideo, Kitchen, etc)
    '''

    amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
    response = clean_response(amazon.ItemLookup(ItemId=ASIN, ResponseGroup="ItemAttributes", Condition='All' ))
    item = objectify.fromstring(response)

    try:
        product_group = item.Items.Item.ItemAttributes.ProductGroup
    except:
        product_group = 'Not Found'
    finally:
        return product_group


def get_offers(ASIN):
    ''' take an ASIN
        return a list of all best-price offers with price, condition, and prime status
    '''

    amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
    response = clean_response(amazon.ItemLookup(ItemId=ASIN, ResponseGroup="Offers", Condition='All' ))
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


def get_images(ASIN):
    ''' take an ASIN
        return a dict with the Small, Medium, and Large image URLS and dimensions
    '''
    amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
    try:
        response = clean_response(amazon.ItemLookup(ItemId=ASIN, ResponseGroup="Images", Condition='All' ))
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


def check_for_valid_ASIN(ASIN):
    amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
    response = clean_response(amazon.ItemLookup(ItemId=ASIN, ResponseGroup="ItemAttributes"))
    root = objectify.fromstring(response)

    # if there are errors, check for the invalid param one

    if hasattr(root.Items.Request,'Errors') and root.Items.Request.Errors.Error.Code == 'AWS.InvalidParameterValue':
        return False
    else:
        return True


def get_item_attributes(ASIN):
    amazon = bottlenose.Amazon(AMAZON_KEY_ID, AMAZON_SECRET_KEY, AMAZON_AFFILIATE_ID)
    response = clean_response(amazon.ItemLookup(ItemId=ASIN, ResponseGroup="ItemAttributes"))
    root = objectify.fromstring(response)

    item = root.Items.Item

    URL = item.DetailPageURL
    listPriceAmount = item.ItemAttributes.ListPrice.Amount
    listPriceFormatted = item.ItemAttributes.ListPrice.FormattedPrice
    title = item.ItemAttributes.Title

    item_attributes = {"URL": URL,
                       "listPriceAmount": listPriceAmount,
                       "listPriceFormatted": listPriceFormatted,
                       "title": title
                       }

    return item_attributes


def get_all_item_info(ASIN):

    assert check_for_valid_ASIN(ASIN) == True, "This is an invalid ASIN!"
    print 'it\'s a valid ASIN'
    # different product types handle related items differently, so we need to
    # know how to handle this product
    print 'getting product_group'
    product_group = get_product_group(ASIN)
    print 'done getting product_group'

    # get parent ASIN if applicable
    # if there isn't a parent, this will return the same ASIN
    print 'getting parent_ASIN'
    parent_ASIN = get_parent_ASIN(ASIN=ASIN, product_group=product_group)
    print 'done getting parent_ASIN'

    print 'getting parent attribs'
    parent_attribs = get_item_attributes(parent_ASIN)
    print 'done getting parent attribs'


    # get variation ASINs
    print 'getting variations'
    variations = get_item_variations_from_parent(ASIN=parent_ASIN, product_group=product_group)
    print 'done getting variations'

    # for each variation:
    all_item_info = []
    for v in variations:
        print 'starting  ' + str(v)
        print 'about to get images'
        images = get_images(v)
        print 'done getting images'
        print 'about to get attributes'
        attributes = get_item_attributes(v)
        print 'done getting attributes'
        print 'about to get offers'
        offers = get_offers(v)
        print 'done getting offers'
        all_item_info.append({"ASIN": ASIN,
                              "parent": {"parent_ASIN": parent_ASIN,
                                         "parent_attribs": parent_attribs
                                         },
                              "images": images,
                              "attributes": attributes
                              "offers": offers
                              })
        print 'done with ' + str(v)
        print 'Waiting...'
        sleep(2.2)
        print 'Done waiting...'

    return all_item_info



def main():

    ASIN = 'B00006JSUB'
    item = get_all_item_info(ASIN)


if __name__ == '__main__':
    main()

from app import db
from app.models import Wishlist, Item, ParentItem, Image, Variation
from app.amazon_api import get_parent_ASIN, get_item_attributes, get_amazon_api, get_images, get_item_variations_from_parent
from app.wishlist import get_items_from_wishlist, get_wishlist_name
from datetime import datetime


def add_wishlist_items_to_db(wishlist, wishlist_items):
    for i in wishlist_items:
        print 'on item ' + i['ASIN']
        # add item to database if it doesn't exist
        item_to_add = Item.query.filter_by(ASIN=i['ASIN']).first()
        
        if item_to_add is None:
            print i['ASIN'] + "doesn't exist, creating it"
            item_to_add = Item(ASIN=i['ASIN'])

        # check to see if it's already in that wishlist, if not, add it
        if not(item_to_add in wishlist.items):
            print 'not already in the wishlist... adding'
            item_to_add.wishlists.append(wishlist)
            db.session.add(item_to_add)
            db.session.commit()
        else:
            print 'already in the wishlist'

        print 'done with ' + i['ASIN']


def get_image_sizes(item_image):
    """ Amazon API isn't reliable about sending the same fields back every ThumbnailImage
        This takes an item_image dict and returns what it can get as another dict.
    """

    smallImage = item_image.get('SmallImage')
    mediumImage = item_image.get('MediumImage')
    largeImage = item_image.get('LargeImage')

    if smallImage:
        smallURL = smallImage.get('URL')
        smallHeight = smallImage.get('Height')
        smallWidth = smallImage.get('Width')
    else:
        smallURL = ''
        smallHeight = ''
        smallWidth = ''

    if mediumImage:
        mediumURL = mediumImage.get('URL')
        mediumHeight = mediumImage.get('Height')
        mediumWidth = mediumImage.get('Width')
    else:
        mediumURL = ''
        mediumHeight = ''
        mediumWidth = ''

    if largeImage:
        largeURL = largeImage.get('URL')
        largeHeight = largeImage.get('Height')
        largeWidth = largeImage.get('Width')
    else:
        largeURL = ''
        largeHeight = ''
        largeWidth = ''

    image_sizes = {'smallURL'     : smallURL,
                   'smallHeight'  : smallHeight,
                   'smallWidth'   : smallWidth,
                   'mediumURL'    : mediumURL,
                   'mediumHeight' : mediumHeight,
                   'mediumWidth'  : mediumWidth,
                   'largeURL'     : largeURL,
                   'largeHeight'  : largeHeight,
                   'largeWidth'   : largeWidth}

    return image_sizes


def add_variations_to_db(parentASIN, variations):
    ''' take a parent ASIN and a list of variation ASINs, add to database
    '''

    for ASIN in variations:
        # check to see if variation exists
        v = Variation.query.filter_by(parent_ASIN=parentASIN).filter_by(ASIN=ASIN).first()
        if v is None:
            new_variation = Variation(parent_ASIN=parentASIN, 
                                      ASIN=v)
            db.session.add(new_variation)
            db.session.commit()


def get_variations(parent_ASIN, amazon_api=None):
    ''' take an ASIN and amazon API object, get all ASINs for all variations for that items
        if nothing is found, return an array with just that ASIN
    '''
    if amazon_api is None:
        amazon_api = get_amazon()

    parentASIN = get_parent_ASIN(ASIN=parent_ASIN, amazon_api=amazon_api)
    if parentASIN:
        variations = get_item_variations_from_parent(parentASIN=parentASIN, amazon_api=amazon_api)
        return variations
    else:
        return [parentASIN]


def refresh_item_data(item, amazon_api=None):
    ''' Take an Item object and update the data in the database
        Returns True if everything goes well
        Returns False if this isn't an item we can get through the API

        TODO - literally any error handling
    '''


    if amazon_api is None:
        amazon_api = get_amazon()


    print 'on ' + i.ASIN
    
    ASIN = i.ASIN
    
    # get other item attribs
    print 'getting attributes'
    item_attributes = get_item_attributes(ASIN, amazon_api=amazon_api)

    if item_attributes == {}:
        return False

    # using .get() here because it will default to None is the key is
    # not in the dict, and the API is not reliable about sending everything back
    i.list_price_amount = item_attributes.get('listPriceAmount')
    i.list_price_formatted = item_attributes.get('listPriceFormatted')
    i.product_group = item_attributes.get('product_group')
    i.name = item_attributes.get('title')
    i.URL = item_attributes.get('URL')
    i.date_last_checked = datetime.date(datetime.today())

    db.session.add(i)
    db.session.commit()
    print 'got attribs for  ' + ASIN

    # get the main image for the item
    ## TODO: there are multiple images for each prod, it would be nice to get them all.
    item_image = get_images(ASIN=ASIN, amazon_api=amazon_api)

    # if we got images back, remove the old ones
    # if item_image is not None:
    #     current_images = i.images.all()
    #     for image in current_images:
    #         db.delete(image)
    #         db.commit()

    image_sizes = get_image_sizes(item_image)
    new_item_image = Image(smallURL        = str(image_sizes['smallURL']),
                           smallHeight     = int(image_sizes['smallHeight'] or 0),
                           smallWidth      = int(image_sizes['smallWidth'] or 0),
                           mediumURL       = str(image_sizes['mediumURL']),
                           mediumHeight    = int(image_sizes['mediumHeight']  or 0),
                           mediumWidth     = int(image_sizes['mediumWidth'] or 0),
                           largeURL        = str(image_sizes['largeURL']),
                           largeHeight     = int(image_sizes['largeHeight'] or 0),
                           largeWidth      = int(image_sizes['largeWidth'] or 0),
                           item_id         = i.id)
    db.session.add(new_item_image)

    return True



def main():

    amazon_api = get_amazon_api()

    # pull all existing wishlists
    wishlists = Wishlist.query.all()

    for w in wishlists:
        # get all of the items from the withlist
        # make sure we have an updated name for the wishlist
        wishlist_name = get_wishlist_name(w.amazonWishlistID)
        if wishlist_name is not None:
            w.name = wishlist_name
            db.session.add(w)
            db.session.commit()
        wishlist_items = get_items_from_wishlist(w.amazonWishlistID)
        # add all of the wishlist items to the database
        add_wishlist_items_to_db(wishlist=w, wishlist_items=wishlist_items)

    # now that all of the base items are in the wishlist, get all of the parent items
    all_items = Item.query.all()
    for i in all_items:
        print 'getting parent'
        item_parent_ASIN = get_parent_ASIN(ASIN=i.ASIN, amazon_api=amazon_api)
        print 'got parent'
        # if this parent doesn't exist, create it
        parent = ParentItem.query.filter_by(parent_ASIN=item_parent_ASIN).first()
        if parent is None:
            print "parent doesn't exist, creating"
            parent = ParentItem(parent_ASIN=item_parent_ASIN)
            db.session.add(parent)
            db.session.commit()
        # add the parent to the item
        i.parent_item = parent
        db.session.add(i)
        db.session.commit()     

    # from that list of parents, get all variations
    all_parents = ParentItem.query.all()
    for p in all_parents:
        # get a list of all ASINS under that parent
        print 'getting variations for {0}'.format(p.parent_ASIN)
        variations = get_variations(parent_ASIN=p.parent_ASIN, amazon_api=amazon_api)
        print 'Found {0} variations for {1}'.format(len(variations), p.parent_ASIN)
        for v in variations:
            print 'Checking for existence of variation {0}'.format(v)
            var = Item.query.filter_by(ASIN=v).all()
            if len(var) == 0:
                print 'Don''t have this one, adding.'
                # if we don't have these variations already, add them to the database
                # with the correct parent
                new_variation = Item(ASIN=v, parent_item=p)
                db.session.add(new_variation)
                db.session.commit()
            else:
                print 'Have it.'


    
    ## Next step is to get the item data for everything in the database

    # get all of the items again
    all_items = Item.query.all()
    for i in all_items: 
        refresh_item_data(item=i, amazon_api=amazon_api)


    





if __name__ == '__main__':

    main()









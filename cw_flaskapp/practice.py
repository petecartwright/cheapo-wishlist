from app import db
from app.models import Wishlist, Item, ParentItem, Image
from app.amazon_api import get_parent_ASIN, get_item_attributes, get_amazon_api, get_images
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
            item_to_add.name = i['ASIN'] + ' : Temp Name'

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

    image_sizes = {'smallURL'        : smallURL,
                   'smallHeight'     : smallHeight,
                   'smallWidth'      : smallWidth,
                   'mediumURL'       : mediumURL,
                   'mediumHeight'    : mediumHeight,
                   'mediumWidth'     : mediumWidth,
                   'largeURL'        : largeURL,
                   'largeHeight'     : largeHeight,
                   'largeWidth'      : largeWidth}

    return image_sizes


def add_variations_to_db(variations):
    for variation in variations:
        # check to see if variation exists
        v = Variation.query.filter_by(parent_ASIN=parent_ASIN).filter_by(ASIN=ASIN).first()
        if v is None:
            new_variation = Variation(parent_ASIN=parent_ASIN, 
                                      ASIN=ASIN)
            db.session.add(new_variation)
            db.session.commit()


def refresh_all_item_data(items, amazon_api=None):
    
    if amazon_api is None:
        amazon_api = get_amazon()

    print 'starting items'
    for i in items:
        print 'on ' + i.ASIN
        # get parent ASIN
        ASIN = i.ASIN
        print 'getting parent'
        item_parent_ASIN = get_parent_ASIN(ASIN=ASIN, amazon_api=amazon_api)
        print 'got parent'

        # if this parent doesn't exist, create it
        parent = ParentItem.query.filter_by(parent_ASIN=item_parent_ASIN).first()
        if parent is None:
            print "parent doesn't exist, creating"
            parent = ParentItem(parent_ASIN=item_parent_ASIN)
            db.session.add(parent)
            db.session.commit()
            
        i.parent_item = parent

        # get other item attribs
        print 'getting attribs'
        item_attributes = get_item_attributes(ASIN, amazon_api=amazon_api)

        if item_attributes is not None:
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

        # get images
        item_images = get_images(ASIN=ASIN, amazon_api=amazon_api)

        # if we got images back, remove the old ones
        if item_images is not None:
            current_images = i.images
            for image in images:
                db.delete(i)
                db.commit()

        for item_image in item_images:
            # I wish I could trust the Amazon API to give me good data. 
            # but I can't.
            image_sizes = get_image_sizes(item_image)
            new_item_image = Image(# thumbnailURL    = item_image["ThumbnailImage"]["URL"],
                                   # thumbnailHeight = item_image["ThumbnailImage"]["Height"],
                                   # thumbnailWidth  = ite m_image["ThumbnailImage"]["Width"],
                                   smallURL        = image_sizes['smallURL'],
                                   smallHeight     = image_sizes['smallHeight'],
                                   smallWidth      = image_sizes['smallWidth'],
                                   mediumURL       = image_sizes['mediumURL'],
                                   mediumHeight    = image_sizes['mediumHeight'],
                                   mediumWidth     = image_sizes['mediumWidth'],
                                   largeURL        = image_sizes['largeURL'],
                                   largeHeight     = image_sizes['largeHeight'],
                                   largeWidth      = image_sizes['largeWidth'],
                                   item_id         = i.id)

        variations = get_variations(ASIN=ASIN, amazon_api=amazon_api)

        add_variations_to_db(variations)

        



def main():

    amazon_api = get_amazon_api()

    # pull all existing wishlists
    wishlists = Wishlist.query.all()

    # for each wishlist, get the name and all items
    # and push that to the database
    for w in wishlists:
        # make sure we have an updated name for the wishlist
        wishlist_name = get_wishlist_name(w.amazonWishlistID)
        if wishlist_name is not None:
            w.name = wishlist_name
            db.session.add(w)
            db.session.commit()
        print 'getting wishlist items'
        wishlist_items = get_items_from_wishlist(w.amazonWishlistID)
        print 'got wishlist items'
        add_wishlist_items_to_db(wishlist=w, wishlist_items=wishlist_items)

    items = Item.query.all()

    refresh_all_item_data(items=items, amazon_api=amazon_api)


    





if __name__ == '__main__':

    main()









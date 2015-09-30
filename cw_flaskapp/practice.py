from app import db
from app.models import Wishlist, Item, ParentItem, Image
from amazon_api import get_parent_ASIN, get_item_attributes, get_amazon, get_images
from wishlist import get_items_from_wishlist, get_wishlist_name
from datetime import datetime


def add_wishlist_items_to_db(wishlist_items):
    for i in wishlist_items:
        print 'on item ' + i['ASIN']
        # add item to database if it doesn't exist
        item_to_add = Item.query.filter_by(ASIN=i['ASIN']).first()
        if item_to_add is None:
            print "doesn't exist, creating it"
            item_to_add = Item(ASIN=i['ASIN'])
            item_to_add.name = i['ASIN'] + 'sadfkasdmfasd'

        # check to see if it's already in that wishlist, if not, add it
        if not(item_to_add in w.items):
            print 'not already in the wishlist... adding'
            item_to_add.wishlists.append(w)
            db.session.add(item_to_add)
            db.session.commit()
        else:
            print 'already in the wishlist'

        print 'done with ' + i['ASIN']



def main():

    items = Item.query.all()
    amazon = get_amazon()

    wishlists = Wishlist.query.all()

    for w in wishlists:
        name = get_wishlist_name(w.amazonWishlistID)
        print 'getting wishlist items'
        wishlist_items = get_items_from_wishlist(w.amazonWishlistID)
        print 'got wishlist items'
        add_wishlist_items_to_db(wishlist_items=wishlist_items)

    # get_item_info(items=items, amazon=amazon)



    print 'starting items'
    for i in items:
        print 'on ' + i.ASIN
        # get parent ASIN
        ASIN = i.ASIN
        print 'getting parent'
        item_parent_ASIN = get_parent_ASIN(ASIN=ASIN, amazon=amazon)
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
        item_attributes = get_item_attributes(ASIN, amazon=amazon)


        ## TODO PC - make these return None on error?
        if item_attributes is not None:
            i.list_price_amount = item_attributes['listPriceAmount']
            i.list_price_formatted = item_attributes['listPriceFormatted']
            i.product_group = item_attributes['product_group']
            i.name = item_attributes['title']
            i.URL = item_attributes['URL']
            i.date_last_checked = datetime.date.today().strftime('%Y-%m-%d')    # today's date as YYYY-MM-DD

            db.session.add(i)
            db.session.commit()
            print 'got attribs for  ' + ASIN

        # get images
        ## TODO PC - make these return None on error?
        item_images = get_images(ASIN=ASIN, amazon=amazon)

        # if we got images back, remove the old ones
        if item_images is not None:
            current_images = i.images
            for image in images:
                db.delete(i)
                db.commit()

        for item_image in item_images:
            new_item_image = Image(# thumbnailURL    = item_image["ThumbnailImage"]["URL"],
                                   # thumbnailHeight = item_image["ThumbnailImage"]["Height"],
                                   # thumbnailWidth  = item_image["ThumbnailImage"]["Width"],
                                   smallURL        = item_image["SmallImage"]["URL"],
                                   smallHeight     = item_image["SmallImage"]["Height"],
                                   smallWidth      = item_image["SmallImage"]["Width"],
                                   mediumURL       = item_image["MediumImage"]["URL"],
                                   mediumHeight    = item_image["MediumImage"]["Height"],
                                   mediumWidth     = item_image["MediumImage"]["Width"],
                                   largeURL        = item_image["LargeImage"]["URL"],
                                   largeHeight     = item_image["LargeImage"]["Height"],
                                   largeWidth      = item_image["LargeImage"]["Width"],
                                   item_id         = i.id)

        # get variations
        ## TODO PC - make these return None on error?
        variations = get_images(ASIN=ASIN, amazon=amazon)

        for variation in variations:
            # check to see if variation exists
            v = Variation.query.filter_by(parent_ASIN=parent_ASIN).filter_by(ASIN=ASIN).first()
            if v is None:
                new_variation = Variation(parent_ASIN=parent_ASIN, 
                                          ASIN=ASIN)
                db.session.add(new_variation)
                db.session.commit()





if __name__ == '__main__':

    main()









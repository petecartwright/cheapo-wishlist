from app import db
from app.models import Item, ParentItem, Image, Offer, LastRefreshed, Variation
from app.amazon_api import get_parent_ASIN, get_item_attributes, get_amazon_api, get_images, get_item_variations_from_parent, get_offers
from app.wishlist import get_items_from_wishlist
from datetime import datetime

import logging

FORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(filename='amazon_log.txt', level=logging.DEBUG, format=FORMAT)

logger = logging.getLogger(__name__)

WISHLIST_ID = '1ZF0FXNHUY7IG'


def get_buybox_price(item):
    ''' take an Item object, return the buybox price and offer if one exists.
        Returns None if not
    '''

    buybox_price = None

    for offer in item.offers.all():
        if offer.offer_source == 'Buybox':
            buybox_price = offer.offer_price_amount

    return buybox_price


def find_best_offer_per_wishlist_item():
    ''' look at all of the items and offers in the wishlist, then flag one offer per item as the best
    '''

    all_wishlist_items = Item.query.filter(Item.is_on_wishlist==True).filter(Item.live_data==False).all()

    for item in all_wishlist_items:

        # get the list price for the variant we had in the wishlist
        # get the buybox for this item
        best_offer_price = 999999999      # assuming all of our prices will be lower than a billion dollars
        best_offer = None

        # get all variants, including that item
        all_items_under_parent = item.parent_item.items.all()

        for x in all_items_under_parent:
            for o in x.offers.all():
                # reset the best offer tracking from last time
                o.best_offer = False
                if o.offer_price_amount < best_offer_price:
                    best_offer = o
                    best_offer_price = o.offer_price_amount

        if best_offer:
            # mark the best offer
            print('Best Offer for {0} is {1}'.format(item.name, best_offer))
            best_offer.best_offer = True
            best_offer.wishlist_item_id = item.id
            db.session.add(best_offer)
            db.session.commit()
        else:
            print('No best offer for {0}'.format(item.name))


def add_wishlist_items_to_db(wishlist_items):
    for i in wishlist_items:
        print 'on item ' + i['ASIN']
        # check to see if we already have it, if not, add it to the database
        item_to_add = Item.query.filter_by(ASIN=i['ASIN']).filter(Item.live_data==False).first()

        if item_to_add is None:
            print "{0} doesn't exist, creating it".format(i['ASIN'])
            item_to_add = Item(ASIN=i['ASIN'])
            item_to_add.is_on_wishlist = True
            db.session.add(item_to_add)
            db.session.commit()


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

    image_sizes = {'smallURL': smallURL,
                   'smallHeight': smallHeight,
                   'smallWidth': smallWidth,
                   'mediumURL': mediumURL,
                   'mediumHeight': mediumHeight,
                   'mediumWidth': mediumWidth,
                   'largeURL': largeURL,
                   'largeHeight': largeHeight,
                   'largeWidth': largeWidth}

    return image_sizes


def get_variations(parent_ASIN, amazon_api=None):
    ''' take an ASIN and amazon API object, get all ASINs for all variations for that items
        if nothing is found, return an array with just that ASIN
    '''
    if amazon_api is None:
        amazon_api = get_amazon_api()

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
        amazon_api = get_amazon_api()

    print 'on ' + item.ASIN

    ASIN = item.ASIN

    # get other item attribs
    print 'getting attributes'
    item_attributes = get_item_attributes(ASIN, amazon_api=amazon_api)

    if item_attributes == {}:
        return False

    # using .get() here because it will default to None is the key is
    # not in the dict, and the API is not reliable about sending everything back
    item.list_price_amount = item_attributes.get('listPriceAmount')
    item.list_price_formatted = item_attributes.get('listPriceFormatted')
    item.product_group = item_attributes.get('product_group')
    item.name = item_attributes.get('title')
    item.URL = item_attributes.get('URL')
    item.date_last_checked = datetime.date(datetime.today())

    db.session.add(item)
    db.session.commit()
    print 'got attribs for  ' + ASIN

    # only get images if it's the wishlist item
    if item.is_on_wishlist:
        # get the main image for the item
        ## TODO: there are multiple images for each prod, it would be nice to get them all.
        item_image = get_images(ASIN=ASIN, amazon_api=amazon_api)
        image_sizes = get_image_sizes(item_image)
        new_item_image = Image(smallURL=str(image_sizes['smallURL']),
                               smallHeight=int(image_sizes['smallHeight'] or 0),
                               smallWidth=int(image_sizes['smallWidth'] or 0),
                               mediumURL=str(image_sizes['mediumURL']),
                               mediumHeight=int(image_sizes['mediumHeight'] or 0),
                               mediumWidth=int(image_sizes['mediumWidth'] or 0),
                               largeURL=str(image_sizes['largeURL']),
                               largeHeight=int(image_sizes['largeHeight'] or 0),
                               largeWidth=int(image_sizes['largeWidth'] or 0),
                               item_id=item.id)
        db.session.add(new_item_image)

    return True


def update_last_refreshed():
    ''' Remove the last_refreshed date and replace it with now
    '''
    deleted_last_refreshed = LastRefreshed.query.delete()
    last = LastRefreshed()
    last.last_refreshed = datetime.now()
    db.session.add(last)
    db.session.commit()
    return deleted_last_refreshed


def remove_old_data():
    ''' Delete everything from the database that's flagged as live_data == True '''
    deleted_items = Item.query.filter(Item.live_data==True).delete()
    logger.debug('deleted {0} items'.format(str(deleted_items)))
    deleted_images = Image.query.filter(Image.live_data==True).delete()
    logger.debug('deleted {0} images'.format(str(deleted_images)))
    deleted_offers = Offer.query.filter(Offer.live_data==True).delete()
    logger.debug('deleted {0} offers'.format(str(deleted_images)))
    delete_parents = ParentItem.query.filter(ParentItem.live_data==True).delete()
    logger.debug('deleted {0} parents'.format(str(deleted_images)))
    db.session.commit()


def set_live_data_flag():

    updated_items = Item.query.filter().update(dict(live_data=True))
    updated_parents = ParentItem.query.filter().update(dict(live_data=True))
    updated_offers = Offer.query.filter().update(dict(live_data=True))
    updated_images = Image.query.filter().update(dict(live_data=True))
    db.session.commit()


def main():

    amazon_api = get_amazon_api()

    # scan the wishlist on Amazon's site
    wishlist_items = get_items_from_wishlist(WISHLIST_ID)
    # add all of the wishlist items to the database
    add_wishlist_items_to_db(wishlist_items=wishlist_items)

    # we're using a live_data flag to indicate which are live on the site and which aren't
    # everything we're updating won't have a live data flag until the end, where we delete
    # everything with the live_data flag and then update the new stuff

    # now that all of the base items are in the wishlist, get all of the parent items
    all_items = Item.query.filter(Item.live_data==False).all()
    for i in all_items:
        print 'getting parent for {0}'.format(i.ASIN)
        item_parent_ASIN = get_parent_ASIN(ASIN=i.ASIN, amazon_api=amazon_api)
        print 'got parent'
        # if this parent doesn't exist, create it
        parent = ParentItem.query.filter_by(parent_ASIN=item_parent_ASIN, live_data=False).first()
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
    all_parents = ParentItem.query.filter(Item.live_data==False).all()
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

    # get attributes (name, price, URL, etc) for all items
    # all all offers for each item
    all_items = Item.query.filter(Item.live_data==False).all()
    for i in all_items:
        print 'in the item refresh'
        refresh_item_data(item=i, amazon_api=amazon_api)
        # cant' get info on some - looks like maybe weapons?
        if i.name is not None:
            # get all of the available offers
            # first remove existing offers from database
            item_offers = i.offers.all()
            for x in item_offers:
                print 'trying to remove old offers'
                db.session.delete(x)
                db.session.commit()
            # can't get offers for Kindle Books
            if i.product_group == 'eBooks':
                print "can't get offers for Kindle books"
            else:
                print 'getting offers for {0}'.format(i.ASIN)
                offers = get_offers(item=i, amazon_api=amazon_api)
                for o in offers:
                    new_offer = Offer()
                    new_offer.condition = str(o['condition'])
                    new_offer.offer_source = str(o['offer_source'])
                    new_offer.offer_price_amount = int(o['offer_price_amount'])
                    new_offer.offer_price_formatted = str(o['offer_price_formatted'])
                    new_offer.prime_eligible = o['prime_eligible']
                    new_offer.availability = str(o['availability'])
                    new_offer.item_id = o['item_id']
                    new_offer.item = i
                    db.session.add(new_offer)
                    db.session.commit()

    # now let's see what the best deals are!
    find_best_offer_per_wishlist_item()

    update_last_refreshed()

    remove_old_data()

    set_live_data_flag()

    print 'Finished run at {0}'.format(datetime.now().strftime('%H:%M %Y-%m-%d'))
    logging.info('Finished run at {0}'.format(datetime.now().strftime('%H:%M %Y-%m-%d')))


if __name__ == '__main__':

    main()

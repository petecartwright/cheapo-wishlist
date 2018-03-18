from flask_mail import Message

from app import db, mail, app
from app.models import Item, ParentItem, Image, Offer, LastRefreshed
from amazon_api import get_parent_ASIN, get_item_attributes, get_amazon_api, get_images, get_item_variations_from_parent, get_offers
from wishlist import get_items_from_wishlist, get_items_from_local_file
from datetime import datetime

from config import get_logger

import os
import logging

logger = get_logger('refresh_data')

WISHLIST_ID = '1ZF0FXNHUY7IG'
MAILTO = 'pete@petecartwright.com'

DEBUG = True

def get_buybox_price(item):
    ''' take an Item object, return the buybox price
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
    logger.info('Getting the best offers for each item on the wishlist')
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
            logger.info('   Best Offer for {0} is {1}'.format(item.name, best_offer))
            best_offer.best_offer = True
            best_offer.wishlist_item_id = item.id
            db.session.add(best_offer)
            db.session.commit()
        else:
            logger.info('No best offer for {0}'.format(item.name))


def add_wishlist_items_to_db(wishlist_items):
    for i in wishlist_items:
        logger.info('Checking to see if {0} is in our db already'.format(i['ASIN']))
        # check to see if we already have it, if not, add it to the database
        item_to_add = Item.query.filter_by(ASIN=i['ASIN']).filter(Item.live_data==False).first()

        if item_to_add is None:
            logger.info('   Don''t have it, adding now')
            item_to_add = Item(ASIN=i['ASIN'])
            item_to_add.is_on_wishlist = True
            db.session.add(item_to_add)
            db.session.commit()
        else:
            logger.info('   Yep, we had it')


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

    if parent_ASIN:
        variations = get_item_variations_from_parent(parentASIN=parent_ASIN, amazon_api=amazon_api)
        return variations
    else:
        return [parent_ASIN]


def refresh_item_data(item, amazon_api=None):
    ''' Take an Item object and update the data in the database
        Returns True if everything goes well
        Returns False if this isn't an item we can get through the API

        TODO - literally any error handling
    '''

    if amazon_api is None:
        amazon_api = get_amazon_api()

    ASIN = item.ASIN
    
    logger.info('refreshing data for item {0}'.format(ASIN))

    # get other item attribs
    logger.info('   getting attributes')
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
    item.is_cookbook = item_attributes.get('is_cookbook') 

    db.session.add(item)
    db.session.commit()
    logger.info('   got attributes')
    
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
    logger.debug('deleted {0} offers'.format(str(deleted_offers)))

    delete_parents = ParentItem.query.filter(ParentItem.live_data==True).delete()
    logger.debug('deleted {0} parents'.format(str(delete_parents)))
    
    db.session.commit()


def set_live_data_flag():

    updated_items = Item.query.filter().update(dict(live_data=True))
    logger.debug('set {0} items to Live'.format(str(updated_items)))

    updated_parents = ParentItem.query.filter().update(dict(live_data=True))
    logger.debug('set {0} parents to Live'.format(str(updated_parents)))

    updated_offers = Offer.query.filter().update(dict(live_data=True))
    logger.debug('set {0} offers to Live'.format(str(updated_offers)))

    updated_images = Image.query.filter().update(dict(live_data=True))
    logger.debug('set {0} images to Live'.format(str(updated_images)))

    db.session.commit()


def send_completion_message():
    msg = Message("WSIBPT has refreshed", sender="pete.cartwright@gmail.com", recipients=[MAILTO])
    with app.app_context():
        mail.send(msg)


def get_current_wishlist_items():
    ''' We call this if we don't get anything back from our web scraping
        Returns a dict with all current wishlist items, with ASIN and date added,
            just like the real wishlist would
    '''
    all_items = Item.query.filter(Item.is_on_wishlist==True).with_entities(Item.ASIN, Item.date_last_checked).all()

    items_to_return = [{"ASIN": x[0], "date_last_checked": x[1]} for x in all_items]
    
    return items_to_return


def main():

    amazon_api = get_amazon_api()

    todays_date = datetime.date.today()

    if DEBUG:
        logger.info('loading items from local file')
        wishlist_items = get_items_from_local_file()
    else:
        # scan the wishlist on Amazon's site
        logger.info('loading items from amazon')
        wishlist_items = get_items_from_wishlist(WISHLIST_ID)

    # if we didn't get anything back, refresh the prices for what we do have
    if len(wishlist_items) == 0:
        wishlist_items = get_current_wishlist_items()
        logger.info('Nothing returned from the last wishlist check - using old data.')
    else:
        # add all of the wishlist items to the database
        add_wishlist_items_to_db(wishlist_items=wishlist_items)

    # we're using a live_data flag to indicate which are live on the site and which aren't
    # everything we're updating won't have a live data flag until the end, where we delete
    # everything with the live_data flag and then update the new stuff

    # now that all of the base items are in the wishlist, get all of the parent items

    all_items = Item.query.filter(Item.live_data == False) \
                          .filter(Item.date_last_checked != todays_date) \
                          .all()

    if DEBUG:
        all_items = all_items[:5]
        logger.info('in DEBUG, limiting all_items to 5')

    for i in all_items:
        logger.info('getting parent for {0}'.format(i.ASIN))
        item_parent_ASIN = get_parent_ASIN(ASIN=i.ASIN, amazon_api=amazon_api)
        logger.info('   got parent')
        # if this parent doesn't exist, create it
        parent = ParentItem.query.filter_by(parent_ASIN=item_parent_ASIN, live_data=False).first()
        if parent is None:
            logger.info("parent doesn't exist, creating")
            parent = ParentItem(parent_ASIN=item_parent_ASIN)
            db.session.add(parent)
            db.session.commit()
        # add the parent to the item
        i.parent_item = parent
        db.session.add(i)
        db.session.commit()

    # from that list of parents, get all variations
    all_parents = ParentItem.query.filter(Item.live_data==False) \
                                  .filter(Item.date_last_checked != todays_date) \
                                  .all()
    for p in all_parents:
        # get a list of all ASINS under that parent
        logger.info('getting variations for {0}'.format(p.parent_ASIN))
        variations = get_variations(parent_ASIN=p.parent_ASIN, amazon_api=amazon_api)
        logger.info('Found {0} variations for {1}'.format(len(variations), p.parent_ASIN))
        for v in variations:
            logger.info('   Checking for existence of variation {0}'.format(v))
            var = Item.query.filter_by(ASIN=v).all()
            if len(var) == 0:
                logger.info("       Don't have this one, adding.")
                # if we don't have these variations already, add them to the database
                # with the correct parent
                new_variation = Item(ASIN=v, parent_item=p)
                db.session.add(new_variation)
                db.session.commit()
            else:
                logger.info("       Have it.")

    ## Next step is to get the item data for everything in the database

    # get attributes (name, price, URL, etc) for all items
    # all all offers for each item
    all_items = Item.query.filter(Item.live_data==False) \
                          .filter(Item.date_last_checked != todays_date) \
                          .all()
    for i in all_items:
        logger.info('in the item refresh')
        refresh_item_data(item=i, amazon_api=amazon_api)
        # cant' get info on some - looks like maybe weapons?
        if i.name is not None:
            # get all of the available offers
            # first remove existing offers from database
            item_offers = i.offers.all()
            for x in item_offers:
                logger.info('   trying to remove old offers')
                db.session.delete(x)
                db.session.commit()
            # can't get offers for Kindle Books
            if i.product_group == 'eBooks':
                logger.info("   can't get offers for Kindle books")
            else:
                logger.info('   getting offers for {0}'.format(i.ASIN))
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

    logger.info('Finished run at {0}'.format(datetime.now().strftime('%H:%M %Y-%m-%d')))

    send_completion_message()

if __name__ == '__main__':

    main()

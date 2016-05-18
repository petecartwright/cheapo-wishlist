import requests
import logging

from app  import app, db
from .models import ParentItem, Item

from flask import render_template, request, url_for, redirect, g, session, flash, Markup, jsonify
import wishlist as w

FORMAT = '%(asctime)-15s %(message)s'


logging.basicConfig(filename='best_deals.txt', level=logging.DEBUG, format=FORMAT)

logger = logging.getLogger(__name__)

#########################################################################
#########################################################################
#
#   Helpers
#
#########################################################################
#########################################################################

def get_buybox_price(item):
    ''' take an Item object, return the buybox price and offer if one exists.
        Returns None if not
    '''

    buybox_price = None

    for offer in item.offers.all():
        if offer.offer_source == 'Buybox':
            buybox_price = offer.offer_price_amount

    return buybox_price



def get_best_deals():
    ''' look at all of the items and offers in the wishlist, then return a dict with the best deal per item
    '''

    logging.debug('Getting wishlist items')
    all_wishlist_items = Item.query.filter(Item.is_on_wishlist==True).all()
    logging.debug('Got wishlist items')

    best_deals_on_each_item = []

    logging.debug('Starting outer loop')    
    for item in all_wishlist_items:

        # get the list price for the variant we had in the wishlist
        # get the buybox for this item
        list_price = item.list_price_amount or 0
        best_offer_price = 999999999      # assuming all of our prices will be lower than a billion dollars
        best_offer = None
        main_item_url = item.URL
        logging.debug('     Getting Buybox Price')
        # get the buybox price for this item
        buybox_price = get_buybox_price(item)
        logging.debug('     Got Buybox Price')
        # get all variants, including that item
        logging.debug('     Getting all items under Parent')
        all_items_under_parent = item.parent_item.items.all()
        logging.debug('     Got all items under Parent')

        logging.debug('     Looking at all offers under the parent')
        for x in all_items_under_parent:
            for o in x.offers.all():
                if o.offer_price_amount < best_offer_price:
                    best_offer = o
                    best_offer_price = o.offer_price_amount
        logging.debug('     Done looking at all offers under the parent')

        # calculate savings!
        if list_price and best_offer_price:
            savings_vs_list = list_price - best_offer_price
        else:
            savings_vs_list = 0

        if buybox_price and best_offer_price:
            savings_vs_buybox = buybox_price - best_offer_price
        else:
            savings_vs_buybox = 0

        best_deal = {'wishlist_item': item,
                     'best_price_item': o.item,
                     'list_price': list_price,
                     'buybox_price': buybox_price,
                     'best_offer_price': best_offer_price,
                     'best_offer': best_offer,
                     'savings_vs_list': savings_vs_list,
                     'savings_vs_buybox': savings_vs_buybox
                     }
        best_deals_on_each_item.append(best_deal)

    logging.debug('Done with outer loop')
    return best_deals_on_each_item



#########################################################################
#########################################################################
#
#   Routes
#
#########################################################################
#########################################################################


@app.route('/')
@app.route('/index')
# @login_required
def index():

    print 'loading index'
    print 'about to get deals'
    best_deals = get_best_deals()
    ## TODO - this should be called once per day and put into the database
    ##      - BUUUUUUT  JFDI
    print 'done loading deals'

    print 'got best deals, sorting by list'
    best_by_list = sorted(best_deals, key=lambda k:k['savings_vs_list'], reverse=True)[0]
    print 'done sorting by list, sorting by buybox'
    best_by_buybox = sorted(best_deals, key=lambda k:k['savings_vs_buybox'], reverse=True)[0]
    print 'done sorting by buybox'
    cheapest_overall = sorted(best_deals, key=lambda k:k['best_offer_price'])[0]
    print 'done sorting by buybox'

    return render_template('index.html',
                           best_by_buybox=best_by_buybox,
                           best_by_list=best_by_list,
                           cheapest_overall=cheapest_overall
                           )


@app.route('/item/<item_id>')
def item(item_id):

    item = Item.query.filter_by(id=int(item_id)).first()
    variations = item.parent_item.items

    # 404 if we don't have it
    if item is None:
        return render_template('404.html')

    return render_template('item.html', 
                            item=item,
                            variations=variations)


@app.route('/item/all')
def all_items():

    best_deals = get_best_deals()

    best_deals_sorted = sorted(best_deals, key=lambda k:k['best_offer_price'])

    return render_template('all_items.html',
                            best_deals_sorted=best_deals_sorted)    



#########################################################################
#########################################################################
#
#   Error Handlers
#
#########################################################################
#########################################################################


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

import logging
import os
import datetime

from flask import render_template, jsonify

from app import app, db
from .models import Item, Offer, LastRefreshed

FORMAT = '%(asctime)-15s %(message)s'
current_folder = os.path.dirname(os.path.realpath(__file__))
logfile = os.path.join(current_folder, 'log/views.txt')
logging.basicConfig(filename=logfile, level=logging.DEBUG, format=FORMAT)

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

    all_best_deals = Offer.query.filter(Offer.best_offer == True).all()

    # get all of the WISHLIST items associated with these deals
    deals_with_info = []
    for deal in all_best_deals:
        item = Item.query.filter(Item.live_data == True).filter(Item.id == deal.wishlist_item_id).first()
        buybox_price = get_buybox_price(item) or 0
        list_price = item.list_price_amount or 0
        best_offer_price = deal.offer_price_amount

        item.buybox_price = buybox_price
        item.best_offer_price = best_offer_price
        db.session.add(item)
        db.commit()

        # calculate savings!
        if list_price and best_offer_price:
            savings_vs_list = list_price - best_offer_price
        else:
            savings_vs_list = 0

        if buybox_price and best_offer_price:
            savings_vs_buybox = buybox_price - best_offer_price
        else:
            savings_vs_buybox = 0

        best_deal = {'wishlist_item': item,         # the wishlist item this offer applies to
                     'best_price_item': deal.item,  # the actual variant the offer is associated with
                     'list_price': list_price,
                     'buybox_price': buybox_price,
                     'best_offer_price': best_offer_price,
                     'best_offer': deal,
                     'savings_vs_list': savings_vs_list,
                     'savings_vs_buybox': savings_vs_buybox
                    }
        deals_with_info.append(best_deal)

    return deals_with_info


#########################################################################
#########################################################################
#
#   Routes
#
#########################################################################
#########################################################################


# @app.route('/')
# @app.route('/index')
# def index():

#     print 'loading index'
#     print 'about to get deals'
#     best_deals = get_best_deals()

#     print 'done loading deals'
#     lastr = LastRefreshed.query.first()
#     refreshed_time = lastr.last_refreshed.strftime('%Y-%m-%d %H:%M%p')

#     if len(best_deals) == 0:
#         return render_template('index.html',
#                                best_by_buybox=None,
#                                best_by_list=None,
#                                cheapest_overall=None,
#                                refreshed_time=None
#                               )

#     print 'got best deals, sorting by list'
#     best_by_list = sorted(best_deals, key=lambda k: k['savings_vs_list'], reverse=True)[0]
#     print 'done sorting by list, sorting by buybox'
#     best_by_buybox = sorted(best_deals, key=lambda k: k['savings_vs_buybox'], reverse=True)[0]
#     print 'done sorting by buybox'
#     cheapest_overall = sorted(best_deals, key=lambda k: k['best_offer_price'])[0]
#     print 'done sorting by cheapest'

#     return render_template('index.html',
#                            best_by_buybox=best_by_buybox,
#                            best_by_list=best_by_list,
#                            cheapest_overall=cheapest_overall,
#                            refreshed_time=refreshed_time
#                           )


# @app.route('/all')
# def all_items():

#     best_deals = get_best_deals()
#     best_deals_sorted = sorted(best_deals, key=lambda k: k['savings_vs_list'], reverse=True)

#     lastr = LastRefreshed.query.first()
#     refreshed_time = lastr.last_refreshed.strftime('%Y-%m-%d %H:%M%p')


#     return render_template('all_items.html',
#                            best_deals_sorted=best_deals_sorted,
#                            refreshed_time=refreshed_time
#                           )

# @app.route('/faq')
# def faq():
#     return render_template('faq.html')

#########################################################################
#########################################################################
#
#   api
#
#########################################################################
#########################################################################

@app.route('/items/all')
def items():

    # print '{0} getting best offers'.format(datetime.datetime.now())
    best_offers = Offer.query.filter(Offer.best_offer == True ).all()
    # print '{0} got best offers'.format(datetime.datetime.now())

    output_data = {'results': []}

    for offer in best_offers:
        
        # print '{0} getting item'.format(datetime.datetime.now())
        item = offer.item
        # print '{0} got item'.format(datetime.datetime.now())

        # print '{0} building dict'.format(datetime.datetime.now())
        data_to_return = {
                'item_name':             item.name,
                'url':                   item.URL,
                'is_board_game':         item.is_board_game,
                'is_cookbook':           item.is_cookbook,
                'list_price_amount':     item.list_price_amount,
                'list_price_formatted':  item.list_price_formatted,
                'parent_id':             item.parent_id,
                'product_group':         item.product_group,
                'condition':             offer.condition,
                'offer_source':          offer.offer_source,
                'offer_price_amount':    offer.offer_price_amount,
                'offer_price_formatted': offer.offer_price_formatted,
                'prime_eligible':        offer.prime_eligible,
                'availability':          offer.availability,
                'item_id':               offer.item_id,
                'wishlist_item_id':      offer.wishlist_item_id,
                'savings_vs_list':       offer.savings_vs_list
        }
        # print '{0} built dict'.format(datetime.datetime.now())
        # print '{0} appending'.format(datetime.datetime.now())
        output_data['results'].append(data_to_return)
        # print '{0} appended'.format(datetime.datetime.now())

    return jsonify(output_data)


@app.route('/items/cheapest_vs_list')
def cheapest_vs_list():

    cheapest_offer = Offer.query.filter(Offer.cheapest_vs_list == True ).first()

    cheapest_item = cheapest_offer.item

    if cheapest_item.images.first():
        smallImageURL = cheapest_item.images.first().smallURL
        mediumImageURL = cheapest_item.images.first().mediumURL
        largeImageURL = cheapest_item.images.first().largeURL
        thumbnailImageURL = cheapest_item.images.first().thumbnailURL
    else:
        smallImageURL = ''
        mediumImageURL = ''
        largeImageURL = ''
        thumbnailImageURL = ''

    data_to_return = {
            'item_name':             cheapest_item.name,
            'url':                   cheapest_item.URL,
            'is_board_game':         cheapest_item.is_board_game,
            'is_cookbook':           cheapest_item.is_cookbook,
            'list_price_amount':     cheapest_item.list_price_amount,
            'list_price_formatted':  cheapest_item.list_price_formatted,
            'parent_id':             cheapest_item.parent_id,
            'product_group':         cheapest_item.product_group,
            'condition':             cheapest_offer.condition,
            'offer_source':          cheapest_offer.offer_source,
            'offer_price_amount':    cheapest_offer.offer_price_amount,
            'offer_price_formatted': cheapest_offer.offer_price_formatted,
            'prime_eligible':        cheapest_offer.prime_eligible,
            'availability':          cheapest_offer.availability,
            'item_id':               cheapest_offer.item_id,
            'wishlist_item_id':      cheapest_offer.wishlist_item_id,
            'savings_vs_list':       cheapest_offer.savings_vs_list,
            'smallImageURL':         smallImageURL,
            'mediumImageURL':        mediumImageURL,
            'largeImageURL':         largeImageURL,
            'thumbnailImageURL':     thumbnailImageURL
    }

    return jsonify(data_to_return)



@app.route('/items/cheapest_overall')
def cheapest_overall():

    cheapest_offer = Offer.query.filter(Offer.cheapest_overall == True ).first()

    cheapest_item = cheapest_offer.item

    if cheapest_item.images.first():
        smallImageURL = cheapest_item.images.first().smallURL
        mediumImageURL = cheapest_item.images.first().mediumURL
        largeImageURL = cheapest_item.images.first().largeURL
        thumbnailImageURL = cheapest_item.images.first().thumbnailURL
    else:
        smallImageURL = ''
        mediumImageURL = ''
        largeImageURL = ''
        thumbnailImageURL = ''

    data_to_return = {
            'item_name':             cheapest_item.name,
            'url':                   cheapest_item.URL,
            'is_board_game':         cheapest_item.is_board_game,
            'is_cookbook':           cheapest_item.is_cookbook,
            'list_price_amount':     cheapest_item.list_price_amount,
            'list_price_formatted':  cheapest_item.list_price_formatted,
            'parent_id':             cheapest_item.parent_id,
            'product_group':         cheapest_item.product_group,
            'condition':             cheapest_offer.condition,
            'offer_source':          cheapest_offer.offer_source,
            'offer_price_amount':    cheapest_offer.offer_price_amount,
            'offer_price_formatted': cheapest_offer.offer_price_formatted,
            'prime_eligible':        cheapest_offer.prime_eligible,
            'availability':          cheapest_offer.availability,
            'item_id':               cheapest_offer.item_id,
            'wishlist_item_id':      cheapest_offer.wishlist_item_id,
            'savings_vs_list':       cheapest_offer.savings_vs_list,
            'smallImageURL':         smallImageURL,
            'mediumImageURL':        mediumImageURL,
            'largeImageURL':         largeImageURL,
            'thumbnailImageURL':     thumbnailImageURL
    }

    return jsonify(data_to_return)



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
    print error
    db.session.rollback()
    return render_template('500.html'), 500

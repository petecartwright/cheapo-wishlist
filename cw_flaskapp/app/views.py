import logging
import os

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

    all_best_deals = Offer.query.filter(Offer.live_data == True).filter(Offer.best_offer == True).all()

    # get all of the WISHLIST items associated with these deals
    deals_with_info = []
    for deal in all_best_deals:
        item = Item.query.filter(Item.live_data == True).filter(Item.id == deal.wishlist_item_id).first()
        buybox_price = get_buybox_price(item) or 0
        list_price = item.list_price_amount or 0
        best_offer_price = deal.offer_price_amount

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


@app.route('/')
@app.route('/index')
def index():

    print 'loading index'
    print 'about to get deals'
    best_deals = get_best_deals()

    print 'done loading deals'
    lastr = LastRefreshed.query.first()
    refreshed_time = lastr.last_refreshed.strftime('%Y-%m-%d %H:%M%p')

    if len(best_deals) == 0:
        return render_template('index.html',
                               best_by_buybox=None,
                               best_by_list=None,
                               cheapest_overall=None,
                               refreshed_time=None
                              )

    print 'got best deals, sorting by list'
    best_by_list = sorted(best_deals, key=lambda k: k['savings_vs_list'], reverse=True)[0]
    print 'done sorting by list, sorting by buybox'
    best_by_buybox = sorted(best_deals, key=lambda k: k['savings_vs_buybox'], reverse=True)[0]
    print 'done sorting by buybox'
    cheapest_overall = sorted(best_deals, key=lambda k: k['best_offer_price'])[0]
    print 'done sorting by cheapest'

    return render_template('index.html',
                           best_by_buybox=best_by_buybox,
                           best_by_list=best_by_list,
                           cheapest_overall=cheapest_overall,
                           refreshed_time=refreshed_time
                          )


@app.route('/all')
def all_items():

    best_deals = get_best_deals()
    best_deals_sorted = sorted(best_deals, key=lambda k: k['savings_vs_list'], reverse=True)

    lastr = LastRefreshed.query.first()
    refreshed_time = lastr.last_refreshed.strftime('%Y-%m-%d %H:%M%p')


    return render_template('all_items.html',
                           best_deals_sorted=best_deals_sorted,
                           refreshed_time=refreshed_time
                          )

@app.route('/faq')
def faq():
    return render_template('faq.html')

#########################################################################
#########################################################################
#
#   api
#
#########################################################################
#########################################################################

@app.route('/items/all')
def items():

    best_deals = get_best_deals()

    output_data = {'results': []}
    
    for deal in best_deals:
        
        data_to_send = {
                'item_name': deal['best_price_item'].name,
                'url': deal['best_price_item'].URL,
                'is_board_game': deal['best_price_item'].is_board_game,
                'is_cookbook': deal['best_price_item'].is_cookbook,
                'is_on_wishlist': deal['best_price_item'].is_on_wishlist,
                'list_price_amount': deal['best_price_item'].list_price_amount,
                'list_price_formatted': deal['best_price_item'].list_price_formatted,
                'parent_id': deal['best_price_item'].parent_id,
                'product_group': deal['best_price_item'].product_group,
                'condition': deal['best_offer'].condition,
                'offer_source': deal['best_offer'].offer_source,
                'offer_price_amount': deal['best_offer'].offer_price_amount,
                'offer_price_formatted': deal['best_offer'].offer_price_formatted,
                'prime_eligible': deal['best_offer'].prime_eligible,
                'availability': deal['best_offer'].availability,
                'item_id': deal['best_offer'].item_id,
                'wishlist_item_id': deal['best_offer'].wishlist_item_id,
                'best_offer': deal['best_offer'].best_offer,
                'live_data': deal['best_offer'].live_data,
                'buybox_price': deal['buybox_price'],
                'list_price': deal['list_price'],
                'savings_vs_buybox': deal['savings_vs_buybox'],
                'savings_vs_list': deal['savings_vs_list'],
                'smallImageURL':  deal['best_price_item'].images.all()[0].smallURL,
                'mediumImageURL':  deal['best_price_item'].images.all()[0].mediumURL,
                'largeImageURL':  deal['best_price_item'].images.all()[0].largeURL,
                'thumbnailImageURL':  deal['best_price_item'].images.all()[0].thumbnailURL
        }
        
        output_data['results'].append(data_to_send)

    return jsonify(output_data)


@app.route('/items/cheapest_vs_list')
def cheapest_vs_list():

    best_deals = get_best_deals()

    cheapest_vs_list = sorted(best_deals, key=lambda k: k['savings_vs_list'], reverse=True)[0]

    data_to_return = {
            'item_name': cheapest_vs_list['best_price_item'].name,
            'url': cheapest_vs_list['best_price_item'].URL,
            'is_board_game': cheapest_vs_list['best_price_item'].is_board_game,
            'is_cookbook': cheapest_vs_list['best_price_item'].is_cookbook,
            'is_on_wishlist': cheapest_vs_list['best_price_item'].is_on_wishlist,
            'list_price_amount': cheapest_vs_list['best_price_item'].list_price_amount,
            'list_price_formatted': cheapest_vs_list['best_price_item'].list_price_formatted,
            'parent_id': cheapest_vs_list['best_price_item'].parent_id,
            'product_group': cheapest_vs_list['best_price_item'].product_group,
            'condition': cheapest_vs_list['best_offer'].condition,
            'offer_source': cheapest_vs_list['best_offer'].offer_source,
            'offer_price_amount': cheapest_vs_list['best_offer'].offer_price_amount,
            'offer_price_formatted': cheapest_vs_list['best_offer'].offer_price_formatted,
            'prime_eligible': cheapest_vs_list['best_offer'].prime_eligible,
            'availability': cheapest_vs_list['best_offer'].availability,
            'item_id': cheapest_vs_list['best_offer'].item_id,
            'wishlist_item_id': cheapest_vs_list['best_offer'].wishlist_item_id,
            'best_offer': cheapest_vs_list['best_offer'].best_offer,
            'live_data': cheapest_vs_list['best_offer'].live_data,
            'buybox_price': cheapest_vs_list['buybox_price'],
            'list_price': cheapest_vs_list['list_price'],
            'savings_vs_buybox': cheapest_vs_list['savings_vs_buybox'],
            'savings_vs_list': cheapest_vs_list['savings_vs_list'],
            'smallImageURL':  cheapest_vs_list['best_price_item'].images.all()[0].smallURL,
            'mediumImageURL':  cheapest_vs_list['best_price_item'].images.all()[0].mediumURL,
            'largeImageURL':  cheapest_vs_list['best_price_item'].images.all()[0].largeURL,
            'thumbnailImageURL':  cheapest_vs_list['best_price_item'].images.all()[0].thumbnailURL
    }

    return jsonify(data_to_return)



@app.route('/items/cheapest_overall')
def cheapest_overall():

    best_deals = get_best_deals()

    cheapest_overall = sorted(best_deals, key=lambda k: k['best_offer_price'])[0]
    
    data_to_return = {
            'item_name': cheapest_overall['best_price_item'].name,
            'url': cheapest_overall['best_price_item'].URL,
            'is_board_game': cheapest_overall['best_price_item'].is_board_game,
            'is_cookbook': cheapest_overall['best_price_item'].is_cookbook,
            'is_on_wishlist': cheapest_overall['best_price_item'].is_on_wishlist,
            'list_price_amount': cheapest_overall['best_price_item'].list_price_amount,
            'list_price_formatted': cheapest_overall['best_price_item'].list_price_formatted,
            'parent_id': cheapest_overall['best_price_item'].parent_id,
            'product_group': cheapest_overall['best_price_item'].product_group,
            'condition': cheapest_overall['best_offer'].condition,
            'offer_source': cheapest_overall['best_offer'].offer_source,
            'offer_price_amount': cheapest_overall['best_offer'].offer_price_amount,
            'offer_price_formatted': cheapest_overall['best_offer'].offer_price_formatted,
            'prime_eligible': cheapest_overall['best_offer'].prime_eligible,
            'availability': cheapest_overall['best_offer'].availability,
            'item_id': cheapest_overall['best_offer'].item_id,
            'wishlist_item_id': cheapest_overall['best_offer'].wishlist_item_id,
            'best_offer': cheapest_overall['best_offer'].best_offer,
            'live_data': cheapest_overall['best_offer'].live_data,
            'buybox_price': cheapest_overall['buybox_price'],
            'list_price': cheapest_overall['list_price'],
            'savings_vs_buybox': cheapest_overall['savings_vs_buybox'],
            'savings_vs_list': cheapest_overall['savings_vs_list'],
            'smallImageURL':  cheapest_overall['best_price_item'].images.all()[0].smallURL,
            'mediumImageURL':  cheapest_overall['best_price_item'].images.all()[0].mediumURL,
            'largeImageURL':  cheapest_overall['best_price_item'].images.all()[0].largeURL,
            'thumbnailImageURL':  cheapest_overall['best_price_item'].images.all()[0].thumbnailURL
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

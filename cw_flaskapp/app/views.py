import requests

from app  import app, db
from .models import ParentItem, Item
from flask import render_template, request, url_for, redirect, g, session, flash, Markup, jsonify
import wishlist as w


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
    return render_template('index.html')


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
    pass



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

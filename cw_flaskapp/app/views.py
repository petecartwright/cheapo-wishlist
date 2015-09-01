from app import app, db
from .models import Wishlist, User, UserSettings, ParentItem, Item

@app.route('/')
@app.route('/index')
def index():
    return 'Hello world!'

@app.route('/wishlist/<wishlist_id>')
def wishlist(wishlist_id):
    wishlist = Wishlist.query.filter_by(amazonWishlistID=wishlist_id).first()
    if wishlist == None:
        return 'No wishlist with ID ' + str(wishlist_id) +'.'
    else:
        return 'there is a wishlist with ID ' + str(wishlist_id) +'.'
        

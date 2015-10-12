from app  import app, db
from .models import Wishlist, User, UserSettings, ParentItem, Item
from flask import render_template, request, url_for, redirect
from forms import LoginForm, WishlistForm

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/wishlist/<wishlist_id>')
def wishlist(wishlist_id):
    wishlist = Wishlist.query.filter_by(amazonWishlistID=wishlist_id).first()
    if wishlist == None:
        return 'No wishlist with ID ' + str(wishlist_id) +'.'
    else:
        return 'there is a wishlist with ID ' + str(wishlist_id) +'.'
        

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()

    if request.method == 'GET':
        return render_template('login.html', 
                               form=form)

    if form.validate_on_submit():
        return 'yeah we got that login'



@app.route('/wishlist/add', methods=['GET','POST'])
# @lm.login_required
def wishlist_add():

    form = WishlistForm
    if request.method == 'GET':

        return render_template('wishlist_add.html', 
                               form=form)

    # check to see if wishlist is already in database
    wishlists = Wishlist.query(Wishlist.amazonWishlistID).all()

    wishlist_id = request['wishlist_id']

    # make sure we have a wishlist ID
    if wishlist_id is None:
        flash('No wishlist ID provided')
        redirect(url_for('wishlist_add'))

    # validate wishlist ID - there's code for this somewhere...
    ## TODO - find the code for this
    # if wishlist_id is None:
    #     flash("That's not a valid wishlist ID - check again!")
    #     redirect(url_for('wishlist_add'))

    if wishlist_id in wishlists:
        flash('This wishlist is already in our database - adding to your account')
        ##TODO - Add the wishlist to the user's account.
        ##       Need to implement user system first
        redirect(url_for('wishlist_add'))

    new_wishlist = Wishlist(amazonWishlistID=wishlist_id)

    # get wishlist name from the Amazon page
    ## TODO - find the code for this

    # add the wishlist<->user list
    ## TODO - write the code for this
    
    db.session.add(new_wishlist)
    db.session.commit()










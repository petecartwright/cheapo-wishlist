from app  import app, db, lm
from .models import Wishlist, User, UserSettings, ParentItem, Item
from flask import render_template, request, url_for, redirect, g, session, flash
from flask.ext.login import login_user, login_required, current_user
from forms import LoginForm, WishlistForm



#########################################################################
#########################################################################
#
#   Helper functions
#
#########################################################################
#########################################################################

def before_request():
    g.user = current_user

@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#########################################################################
#########################################################################
#
#   Routes
#
#########################################################################
#########################################################################


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/wishlist/<wishlist_id>')
def wishlist(wishlist_id):
    wishlist = Wishlist.query.filter_by(amazonWishlistID=wishlist_id).first()
    if wishlist == None:
        return 'No wishlist with ID ' + str(wishlist_id) +'.'
    else:
        return 'there is a wishlist with ID ' + str(wishlist_id) +'.'
        

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


@app.route('/logout')
@login_required
def logout():
    pass


@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()

    if request.method == 'GET':
        return render_template('login.html', 
                               form=form)

    if form.validate_on_submit():

        user_email = form.user_email.data
        password = form.password.data

        # see if the user is in the database
        u = User.query.filter_by(email=user_email).first()
        if not u:
            # if the user doesn't exist
            flash("this user doesn't exist!")
            return redirect(url_for('login'))
        else:
            # see if the password hashes match
            if u.verify_password(password):
                # if it does, login with flask-login
                login_user(u)
                # and add the login state to the db
                # is this overkill?
                u.logged_in = True
                db.session.add(u)
                db.session.commit()
                # redirect to next page or index
                ## TODO - the docs say this needs to be verified. How to do that?
                next = request.args.get('next')
                return redirect(next or url_for('index'))
            else:
                flash('bad password!')
                return redirect(url_for('login'))


    flash('there was a login error')
    return redirect(url_for('login'))




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




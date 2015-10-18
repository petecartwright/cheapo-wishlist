from app  import app, db, lm
from .models import Wishlist, User, UserSettings, ParentItem, Item
from flask import render_template, request, url_for, redirect, g, session, flash
from flask.ext.login import login_user, logout_user, login_required, current_user
from forms import LoginForm, WishlistForm, RegistrationForm



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


def is_invalid_wishlist(wishlist_id):

    wishlistURL = 'http://www.amazon.com/gp/registry/wishlist/' + wishlist_id
    r = requests.get(wishlistURL)
    wishlistFirstPage = BeautifulSoup(r.content, "html.parser")

    if wishlistFirstPage.text.find("The Web address you entered is not a functioning page on our site") != -1:
        return True
    else:
        return False

def user_exists(email):
    ''' take an email address
        return True if that user is already in the db
               False otherwise
    '''
    # try to get that user by email
    u = User.query.filter_by(email=email).first()
    if u:
        return True
    else:
        return False


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

    if form.validate_on_submit():
        
        wishlist_id = form.wishlist_id.data
        # make sure we have a wishlist ID
        if wishlist_id is None:
            flash('No wishlist ID provided')
            redirect(url_for('wishlist_add'))

        # make sure this is a real wishlist ID 
        if is_invalid_wishlist(wishlist_id):
            flash("That's not a valid wishlist ID - check again!")
            redirect(url_for('wishlist_add'))

        # get current user
        u = User.query.filter_by(id=current_user.id).first()
        # check to see if wishlist is already in database
        existing_wishlist = Wishlist.query.filter_by(amazonWishlistID=wishlist_id).first()
        
        if existing_wishlist:    
            u.wishlists.append(existing_wishlist)
            db.session.add(u)
            db.session.commit()
            flash('This wishlist is already in our database - adding to your account')
            redirect(url_for('wishlist_add'))

        new_wishlist = Wishlist(amazonWishlistID=wishlist_id)

        # get wishlist name from the Amazon page
        ## TODO - find the code for this
        # new_wishlist.name = get_wishlist_name(wishlist_id)

        db.session.add(new_wishlist)
        db.session.commit()

        # add the wishlist to the user
        u.wishlists.append(new_wishlist)
        db.session.add(u)
        db.session.commit()

        flash('Wishlist added!')
        return redirect(url_for('wishlist'))


################################################################################
#
#   Login/Logout/Register
#
################################################################################


@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()

    if request.method == 'GET':
        return render_template('login.html', 
                               form=form)

    if form.validate_on_submit():

        user_email = form.user_email.data
        password = form.password.data


        if user_exists(user_email):
            # if the user doesn't exist
            flash("this user doesn't exist!")
            return redirect(url_for('login'))
        else:
            # see if the user is in the database    
            u = User.query.filter_by(email=user_email).first()
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


@app.route('/logout')
@login_required
def logout():

    # mark the user in the database as logged out
    user_id = current_user.id
    u = User.query.filter_by(id=user_id).first()
    u.logged_in = False
    db.session.add(u)
    db.session.commit()
    # logout from flask-login
    logout_user()
    flash("You've been logged out!")
    return redirect(url_for('index'))


@app.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        if user_exists(email):
            flash("there's already an account with this email address!")
            return redirect(url_for('register'))
        else:
            flash("that user doesn't exist - nice!")
            return redirect(url_for('register'))


    return(render_template('register.html',
                           form=form))



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




from app  import app, db, lm, celery
from .models import Wishlist, User, UserSettings, ParentItem, Item
from flask import render_template, request, url_for, redirect, g, session, flash, Markup, jsonify   
from flask.ext.login import login_user, logout_user, login_required, current_user
from forms import LoginForm, WishlistForm, RegistrationForm
import wishlist as w
import requests
from bs4 import BeautifulSoup



#########################################################################
#########################################################################
#
#   Helper functions
#
#########################################################################
#########################################################################

@app.before_request
def before_request():
    g.user = current_user


@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


## TODO - this needs to be an endpoint

def is_usable_wishlist(wishlist_id):
    ''' Take an amazon wishlist ID, return a True if it's usable. False otherwise

        ##TODO - this should have a proper error message in it. 

    '''
    wishlistURL = 'http://www.amazon.com/gp/registry/wishlist/' + wishlist_id
    r = requests.get(wishlistURL)
    wishlistFirstPage = BeautifulSoup(r.content, "html.parser")

    if (w.is_empty_wishlist(wishlistFirstPage) or
        w.is_invalid_wishlist(wishlistFirstPage) or
        w.is_private_wishlist(wishlistFirstPage)
        ):      
        return False
    else:
        return True


def user_exists(email):
    ''' Take an email address, return True if that user is already in the db, False otherwise '''
    # try to get that user by email
    print email
    u = User.query.filter_by(email=email).first()
    if u:
        return True
    else:
        return False


#########################################################################
#########################################################################
#
#   Celery tasks and status routes!
#
#########################################################################
#########################################################################

@celery.task(bind=True)
def refresh_wishlist_on_demand_task(wishlist_id):
    return {'status': 'this is the status', 'result': 'this is the result'}


# 'liberally borrowed' from Miguel Grinberg's tutorial here:
#  http://blog.miguelgrinberg.com/post/using-celery-with-flask
@app.route('/refreshstatus/<task_id>')
def refreshstatus(task_id):
    
    task = refresh_wishlist_on_demand_task.AsyncResult(task_id)
    print task
    if not task:
        response = {'state': 'Nonexistent',
                    'status': 'No status'}

    elif task.state == 'PENDING':
        # job hasn't started
        response = {'state': task.state,
                    'status': 'Pending...',
                    'result': 'this is the result'
                    }
    elif task.state != 'FAILURE':
        response = {'state': task.state,
                    'status': task.info.get('status','')
                    }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {'state': task.state,
                    'status': str(task.info),  # this is the exception raised
                    }

    return jsonify(response)




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
@login_required
def wishlist_add():

    form = WishlistForm()
    if request.method == 'GET':
        print 'in get wishlist/add'
        return render_template('wishlist_add.html', 
                               form=form)

    if form.validate_on_submit():
        
        wishlist_id = form.wishlistID.data

        # make sure we have a wishlist ID
        if wishlist_id is None or wishlist_id.strip() == '':
            flash('No wishlist ID provided')
            return redirect(url_for('wishlist_add'))

        # make sure this is a real wishlist ID 
        if not is_usable_wishlist(wishlist_id):
            flash("That's not a valid wishlist ID - check again!")
            return redirect(url_for('wishlist_add'))

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
        new_wishlist.name = get_wishlist_name(wishlist_id)

        db.session.add(new_wishlist)
        db.session.commit()

        # add the wishlist to the user
        u.wishlists.append(new_wishlist)
        db.session.add(u)
        db.session.commit()

        flash('Wishlist added!')
        return redirect(url_for('wishlist_add'))



@app.route('/user/<user_id>')
def user(user_id):
    return render_template('user.html')


################################################################################
#
#   User Stuff - Login/Logout/Register
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

        if not user_exists(user_email):
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
            flash(Markup("there's already an account with this email address! Did you mean to <a href=\""+ url_for('login') + "\"> log in </a> ?"))
            return redirect(url_for('register'))
        # so let's create the user
        new_user = User(email=email)
        new_user.password = password
        new_user.logged_in = True
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
        
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




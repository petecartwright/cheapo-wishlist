from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object('config')


# connect to the DB
db = SQLAlchemy(app)

# give the app access to bootstrap templates/css/js/etc
bootstrap = Bootstrap(app)

# let flask-login handle all the login stuff
lm = LoginManager(app)
lm.login_view = 'login'
lm .login_message = "You need to be logged in to see that page!"

from app import views, models
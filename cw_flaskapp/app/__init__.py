from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_bootstrap import Bootstrap
from celery import Celery

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

# set up Celery to handle task queues
app.config['CELERY_BROKER_URL'] = 'redis://'
app.config['CELERY_RESULT_BACKEND'] = 'redis://'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

from app import views, models
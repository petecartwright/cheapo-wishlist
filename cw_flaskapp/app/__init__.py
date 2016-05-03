from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.config.from_object('config')

# connect to the DB
db = SQLAlchemy(app)

# give the app access to bootstrap templates/css/js/etc
bootstrap = Bootstrap(app)

from app import views, models
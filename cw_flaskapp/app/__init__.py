from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('config')
CORS(app)

db = SQLAlchemy(app)
mail = Mail(app)

from app import views, models

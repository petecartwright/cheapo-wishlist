from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired

class LoginForm(Form):
    
    user_email = StringField('email', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])


class WishlistForm(Form):
    
    wishlistID = StringField('wishlistID', validators=[DataRequired()])
    
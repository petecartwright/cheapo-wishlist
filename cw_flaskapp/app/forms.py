from flask_wtf import Form
from wtforms import StringField, BooleanField, TextField, PasswordField
from wtforms.validators import DataRequired, Length, Required, EqualTo


class LoginForm(Form):
    
    user_email = StringField('email', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])


class WishlistForm(Form):
    
    wishlistID = StringField('wishlistID', validators=[DataRequired()])
    

class RegistrationForm(Form):
    email = TextField('Email Address', [Length(min=6, max=35)])
    password = PasswordField('New Password', [
                Required(),
                EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

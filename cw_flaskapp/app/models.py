from app import db
from flask.ext.login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


userWishlists = db.Table('userWishlists', 
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('wishlist_id', db.Integer, db.ForeignKey('wishlist.id'))    
    )


class User(UserMixin, db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(80), unique=True)
    email       = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))
    logged_in   = db.Column(db.Boolean, default=False)
    wishlists   = db.relationship('Wishlist', secondary=userWishlists,
                                backref=db.backref('users', lazy='dynamic'))
    settings    = db.relationship('UserSettings', backref='user', lazy='dynamic')

    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return '<User %r>' % (self.email)


class UserSettings(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    setting1    = db.Column(db.String(40))
    setting2    = db.Column(db.String(40))
    setting3    = db.Column(db.String(40))
    setting4    = db.Column(db.String(40))
    setting5    = db.Column(db.String(40))
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<UserSettings for user %r>' % (self.user_id)


wishlistItems = db.Table('wishlistItems',
        db.Column('wishlist_id', db.Integer, db.ForeignKey('wishlist.id')),
        db.Column('item_id', db.Integer, db.ForeignKey('item.id')),
    )


class Wishlist(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    amazonWishlistID = db.Column(db.String(40), unique=True)
    name             = db.Column(db.String(40))
    items            = db.relationship('Item', secondary=wishlistItems,
                                       backref=db.backref('wishlists', lazy='dynamic'))
    def __repr__(self):
        return '<Wishlist %r>' % (self.amazonWishlistID)


class ParentItem(db.Model):
    id                      = db.Column(db.Integer, primary_key=True)
    parent_ASIN             = db.Column(db.String(40))
    items                   = db.relationship('Item', backref='parent_item', lazy='dynamic')


class Item(db.Model):
    id                      = db.Column(db.Integer, primary_key=True)
    ASIN                    = db.Column(db.String(40), unique=True)
    URL                     = db.Column(db.String(1000))
    list_price_amount       = db.Column(db.Integer)
    list_price_formatted    = db.Column(db.String(40))
    name                    = db.Column(db.String(400))
    product_group           = db.Column(db.String(40))
    date_last_checked       = db.Column(db.Date)
    images                  = db.relationship('Image', backref='item', lazy='dynamic')
    offers                  = db.relationship('Offer', backref='item', lazy='dynamic')
    parent_id               = db.Column(db.Integer, db.ForeignKey('parent_item.id'))

    def __init__(self, ASIN, parent_item=None):
        self.ASIN = ASIN
        self.parent_item = parent_item

    def __repr__(self):
        return '<Item %r>' % (self.name)


class Image(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    thumbnailURL    = db.Column(db.String(400))
    thumbnailHeight = db.Column(db.Integer)
    thumbnailWidth  = db.Column(db.Integer)
    smallURL        = db.Column(db.String(400))
    smallHeight     = db.Column(db.Integer)
    smallWidth      = db.Column(db.Integer)
    mediumURL       = db.Column(db.String(400))
    mediumHeight    = db.Column(db.Integer)
    mediumWidth     = db.Column(db.Integer)
    largeURL        = db.Column(db.String(400))
    largeHeight     = db.Column(db.Integer)
    largeWidth      = db.Column(db.Integer)
    item_id         = db.Column(db.Integer, db.ForeignKey('item.id'))

    def __repr__(self):
        return '<Image %r>' % (self.id)


class Offer(db.Model):
    id                      = db.Column(db.Integer, primary_key=True)
    condition               = db.Column(db.String(200))
    offer_price_amount      = db.Column(db.Integer)
    offer_price_formatted   = db.Column(db.String(40))
    prime_eligible          = db.Column(db.Boolean)
    item_id                 = db.Column(db.Integer, db.ForeignKey('item.id'))
    
    def __repr__(self):
        return '<Offer %r>' % (self.id)


class Variation(db.Model):
    id                      = db.Column(db.Integer, primary_key=True)
    parent_ASIN             = db.Column(db.String(40))  
    ASIN                    = db.Column(db.String(40))  

    def __repr__(self):
        return '<Variation %r>' % (self.id)


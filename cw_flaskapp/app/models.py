from app import db

userWishlists = db.Table('userWishlists', 
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('wishlist_id', db.Integer, db.ForeignKey('wishlist.id'))    
    )


class User(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(80), unique=True)
    email       = db.Column(db.String(120), unique=True)
    wishlists   = db.relationship('Wishlist', secondary=userWishlists,
                                backref=db.backref('users', lazy='dynamic'))
    settings    = db.relationship('UserSettings', backref='user', lazy='dynamic')

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % (self.username)

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
    list_price_amount       = db.Column(db.Integer)
    list_price_formatted    = db.Column(db.String(40))
    name                    = db.Column(db.String(400))
    product_group           = db.Column(db.String(40))
    images                  = db.relationship('Image', backref='item', lazy='dynamic')
    offers                  = db.relationship('Offer', backref='item', lazy='dynamic')
    parent_id               = db.Column(db.Integer, db.ForeignKey('parent_item.id'))
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
    item_id                 = db.Column(db.Integer, db.ForeignKey('item.id'))
    
    def __repr__(self):
        return '<Offer %r>' % (self.id)



class Variation(db.Model):
    id                      = db.Column(db.Integer, primary_key=True)
    parent_ASIN             = db.Column(db.String(40))  
    ASIN                    = db.Column(db.String(40))  

    def __repr__(self):
        return '<Variation %r>' % (self.id)
















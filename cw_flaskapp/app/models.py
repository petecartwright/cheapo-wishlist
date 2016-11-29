from app import db


class ParentItem(db.Model):
    id                      = db.Column(db.Integer, primary_key=True)
    parent_ASIN             = db.Column(db.String(40))
    items                   = db.relationship('Item', backref='parent_item', lazy='dynamic')
    live_data               = db.Column(db.Boolean, default=False)


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
    is_on_wishlist          = db.Column(db.Boolean, default=False)
    live_data               = db.Column(db.Boolean, default=False)

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
    live_data       = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Image %r>' % (self.id)


class Offer(db.Model):
    id                      = db.Column(db.Integer, primary_key=True)
    condition               = db.Column(db.String(200))
    offer_source            = db.Column(db.String(100))
    offer_price_amount      = db.Column(db.Integer)
    offer_price_formatted   = db.Column(db.String(40))
    prime_eligible          = db.Column(db.Boolean)
    availability            = db.Column(db.String(200))
    item_id                 = db.Column(db.Integer, db.ForeignKey('item.id'))
    wishlist_item_id        = db.Column(db.Integer)
    best_offer              = db.Column(db.Boolean, default=False)
    live_data               = db.Column(db.Boolean, default=False)

    def __repr__(self):

        return '<Offer {0} for item {1}>'.format(self.id, self.item.name)


class LastRefreshed(db.Model):
    id                      = db.Column(db.Integer, primary_key=True)
    last_refreshed          = db.Column(db.DateTime)

    def __repr__(self):
        return '<Last refreshed at {0}>'.format(str(self.last_refreshed))

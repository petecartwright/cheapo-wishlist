from app import db
from app.models import Wishlist

w = Wishlist(amazonWishlistID='U59W5QG1QZ0U', name = 'Temp')

db.session.add(w)
db.session.commit()

u1 = User(username='pete', email='pete.cartwright@gmail.com')
u1.wishlists.append(w)

db.session.add(u1)
db.session.commit()

u2 = User(username='pete2', email='pete@petecartwright.com')
u2.wishlists.append(w)

db.session.add(u2)
db.session.commit()
#! flask/bin/python

import os
import unittest

from config import basedir
from app import app, db
from app.models import User, Wishlist
from views import user_exists


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] =  False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_user_exists(self):
        u = User(username='Test User', email="test@email.com")
        db.session.add(u)
        db.session.commit()
        valid_email = u.email
        invalid_email = "this_email_isnt_in_the_db@gmail.com"
        assert user_exists(valid_email)
        assert not user_exists(valid_email)


    
    def test_user_password(self):
        u = User(username='Test User', email="test@email.com")
        u.password = 'Fake Password'
        # there should now be a password hash
        assert u.password_hash is not None


    def test_user_verify_password(self):
        ''' The correct password should return True
            Anything else should return False 
        '''
        u = User(username='Test User', email="test@email.com")
        u.password = 'Fake Password'

        assert u.verify_password('Fake Password') == True
        assert u.verify_password('Another string') == False
        assert u.verify_password('') == False


    def test_user_to_wishlist(self):
        '''
            Make sure wishlist can be added to users

        '''
        # create 2 users and 2 wishlists, add to DB
        u1 = User(username='Test User1', email="test1@email.com")
        u2 = User(username='Test User2', email="test2@email.com")
        w1 = Wishlist(amazonWishlistID='fake1', name='fakeWishlist1')
        w2 = Wishlist(amazonWishlistID='fake2', name='fakeWishlist2')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(w1)
        db.session.add(w2)
        db.session.commit()

        # user 1 will have wishlists 1 and 2
        # user 2 will have wishlist 1 only
        u1.wishlists.append(w1)
        u1.wishlists.append(w2)
        u2.wishlists.append(w1)

        # users should have the appropriate #s of wishlists
        assert len(u1.wishlists) == 2
        assert len(u2.wishlists) == 1

        # wishlists should have the appropriate number of users
        assert len(w1.users.all()) == 2
        assert len(w2.users.all()) == 1



if __name__ == '__main__':
    unittest.main()






















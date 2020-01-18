from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import User, Photo, Journey

class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        u = User(email='susan@example.com', name='Susan Tay')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_join_journey(self):
        user = User(name='John Tan', email='john@example.com')
        journey = Journey(id="Fun Tiemz")
        db.session.add(user)
        db.session.add(journey)
        db.session.commit()
        self.assertEqual(user.journeys.all(), [])
        self.assertEqual(journey.users.all(), [])

        journey.add_user(user)
        db.session.commit()
        self.assertTrue(user.is_in(journey))
        self.assertEqual(user.journeys.count(), 1)
        self.assertEqual(user.journeys.first().id, 'Fun Tiemz')
        self.assertEqual(journey.users.count(), 1)
        self.assertEqual(journey.users.first().name, 'John Tan')

        journey.remove_user(user)
        db.session.commit()
        self.assertFalse(user.is_in(journey))
        self.assertEqual(user.journeys.count(), 0)
        self.assertEqual(journey.users.count(), 0)

    def test_post_photo(self):
        # create four users
        u1 = User(name='John Tan', email='john@example.com')
        u2 = User(name='Susan Tay', email='susan@example.com')
        u3 = User(name='Mary Mee', email='mary@example.com')
        u4 = User(name='David Malan', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create and all all users to a journey
        journey = Journey(id="Fun Tiempo")
        journey.add_user(u1)
        journey.add_user(u2)
        journey.add_user(u3)
        journey.add_user(u4)
        db.session.add(journey)
        db.session.commit()

        # create four photos
        p1 = Photo(longitude=0.123, latitude=4.567, journey__id="Fun Tiempo")
        p2 = Photo(longitude=0.123, latitude=4.567, journey__id="Fun Tiempo")
        p3 = Photo(longitude=0.123, latitude=4.567, journey__id="Fun Tiempo")
        p4 = Photo(longitude=0.123, latitude=4.567, journey__id="Fun Tiempo")
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # test relationships
        self.assertEqual(journey.photos, [p1, p2, p3, p4])
        self.assertEqual(u1.journeys.first(), journey)
        self.assertEqual(u2.journeys.first().photos, [p1, p2, p3, p4])

if __name__ == '__main__':
    unittest.main(verbosity=2)
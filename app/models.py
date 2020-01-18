from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt
from app import app

user_journey = db.Table('user_journey', 
    db.Column('user_name', db.String(64), db.ForeignKey('user.name'), primary_key=True),
    db.Column('journey_id', db.String(120), db.ForeignKey('journey.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    name = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    journeys = db.relationship(
            "Journey",
            secondary=user_journey,
            primaryjoin=(user_journey.c.user_name == name),
            lazy='dynamic',
            backref=db.backref("users", lazy='dynamic'))

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def get_as_dict(user):
        return {
            "email": user.email,
            "password": user.name,
            "journeys": [Journey.get_as_dict(i)['id'] for i in user.journeys]
        }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_in(self, journey):
        return self.journeys.filter(
            user_journey.c.journey_id == journey.id).count() > 0

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({
            'reset_password' : self.id,
            'exp' : time() + expires_in
        }, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Photo(db.Model):
    __tablename__ = 'photo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(250), index=True)
    longitude = db.Column(db.Float, index=True) 
    latitude = db.Column(db.Float, index=True)
    taken_on = db.Column(db.String(20), default=datetime.utcnow().isoformat())
    journey__id = db.Column(db.String(120), db.ForeignKey('journey.id'))
    journey = db.relationship("Journey", back_populates="photos")

    def get_as_dict(photo):
        return {
            "id": photo.id,
            "url": photo.url,
            "journey_id": photo.journey__id,
            "longitude": photo.longitude,
            "latitude": photo.latitude,
            "taken_on": photo.taken_on
        }        
    def get_id(self):
        return self.id

    def set_url(self):
        self.url = "{}{}.jpg".format(app.config["BUCKET_URL"], self.id)
        return

class Journey(db.Model):
    __tablename__ = 'journey'
    id = db.Column(db.String(120), unique=True, primary_key=True)
    photos = db.relationship("Photo",
            back_populates="journey")

    def get_as_dict(journey):
        return {
            "id": journey.id,
            "photos": [Photo.get_as_dict(i) for i in journey.photos]
        }
    
    def add_user(self, user):
        self.users.append(user)

    def remove_user(self, user):
        self.users.remove(user)
    
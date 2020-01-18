import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my-very-special-password'

    # (SQLALCHEMY) DATABASE CONFIGURATIONS
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # EMAIL CONFIGURATIONS
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['wallacelim97@gmail.com']

    #USER INTERFACE CONFIGURATIONS
    POSTS_PER_PAGE = 25

    #AWS BUCKET CONFIGURATIONS
    BUCKET_NAME = "trippy-hnr"
    BUCKET_URL = "https://trippy-hnr.s3-ap-southeast-1.amazonaws.com/"

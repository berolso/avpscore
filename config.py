import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL','postgresql:///avp')

SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS')
# SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO')
SQLALCHEMY_ECHO = False
DEBUG_TB_INTERCEPT_REDIRECTS = os.environ.get('DEBUG_TB_INTERCEPT_REDIRECTS')


SECRET_KEY = os.environ.get('SECRET_KEY')
# SENDGRID_API_KEY=os.environ.get('SENDGRID_API_KEY')


PHONE_LIST = os.environ.get('PHONE_LIST')

TEST_NUM = os.environ.get('TEST_NUM')

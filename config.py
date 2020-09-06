import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

SQLALCHEMY_DATABASE_URI = 'postgresql:///avp'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False
DEBUG_TB_INTERCEPT_REDIRECTS = False


SECRET_KEY = os.environ.get('SECRET_KEY')
SENDGRID_API_KEY=os.environ.get('SENDGRID_API_KEY')

API_AUTH_KV  = os.environ.get('API_AUTH_KV')

PHONE_LIST = os.environ.get('PHONE_LIST')

TEST_NUM = os.environ.get('TEST_NUM')

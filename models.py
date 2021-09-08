from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import exists
from sqlalchemy.exc import IntegrityError
import requests
from flask_bcrypt import Bcrypt
from wtforms.validators import Email, NumberRange
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os
# from telegram_api import Telegram_Bot
from helpers import Helper


db = SQLAlchemy()
bcrypt = Bcrypt()

def connect_db(app):
  """Connect to db"""
  db.app = app
  db.init_app(app)

class Match(db.Model):
  """Format and store data from AVP API request."""

  __tablename__ = 'matches'

  match_id = db.Column(db.Integer, primary_key=True, autoincrement=False, unique=True)
  stats = db.Column(db.Text, nullable=True)
  competition_id = db.Column(db.Integer,nullable=True)
  competition_name = db.Column(db.String,nullable=True)
  competition_code = db.Column(db.String, nullable=True)
  match_no = db.Column(db.String, nullable=True)
  bracket = db.Column(db.String, nullable=True)
  team_a = db.Column(db.Text, nullable=True)
  team_b = db.Column(db.Text, nullable=True)
  sets = db.Column(db.Text, nullable=True)
  winner = db.Column(db.Integer, nullable=True)
  match_state = db.Column(db.String, nullable=True)

  match_sent = db.relationship('SendStatus', backref='send_status')

  @classmethod
  def get_all(cls):
    """get all matches currently in tournament. ordered by matchId"""
    return cls.query.order_by(cls.match_id).all()

  @classmethod
  def clear_matches(cls):
    """clear Matches table"""
    try:
      deleted = db.session.query(cls).delete()
      db.session.commit()
    except:
      db.session.rollback()

  @classmethod
  def format_response_merge(cls, obj):
    '''parse xml file sent from avp api'''
    for match in obj:
      # create new match for matches table 
      match_dict = Helper.parse_avp_match(match)

      # new match by dictionary unpacking(**) match_dict
      new_match = cls(**match_dict)
      
      # add or replace data
      db.session.merge(new_match)


  def __repr__(self):
    return f'< match | {self.match_id} |  | {self.team_a} | {self.team_b} | {self.winner} | {self.match_sent} >'


class SendStatus(db.Model):
  """Persistant holding table to store message delivery status"""

  __tablename__ = 'send_status'
  
  match = db.Column(db.Integer,db.ForeignKey("matches.match_id"),primary_key=True)
  has_sent = db.Column(db.Boolean,nullable=True,default=False)

  @classmethod
  def get_all(cls):
    """get all matches currently in send status table. ordered by matchId"""
    return cls.query.order_by(cls.match).all()

  @classmethod
  def clear_send_status_table(cls):
    """clear send_status table"""
    try:
      deleted = db.session.query(cls).delete()
      print('******** clear send status *********')
      print(cls)
      print(deleted)
      print('*****************')
      db.session.commit()
    except:
      db.session.rollback()

  @classmethod
  def find_and_add_matches(cls):
    """check to see if any matches have not been sent, match_state is not Finished or Canceled."""
    # filter for A)not yet in send_status table. with foreign key & B)match_state not equal to 'F' for final or 'C' for canceled after match has completed. makes sure match result is still pending. 'U' is for a scheduled match that hasn't begun. 'P' is for warmup
    new_adds = Match.query.filter((Match.match_sent == None)&
    (Match.match_state != 'F')&
    (Match.match_state != 'C')).all()
    # loop to add data to for_send
    for i in new_adds:
      id = i.match_id
      try:
        new_for_send = cls(match=id)
        db.session.add(new_for_send)
      except:
        continue

  @classmethod
  def finished_matches(cls):
    """find matches that have not been sent and have a winner. Format result message and add to delivery queue. update status to sent."""
    # join query both tables to filter for A) message has not been sent B) winner has been decided either team A or team B. result string format is different for A or B winner.
    finished_matches = db.session.query(Match).join(cls).filter((cls.has_sent == False)&(Match.winner != None)).all()

    return finished_matches

  @classmethod
  def mark_as_sent(cls,match_id):
    # change status
    x = cls.query.get(match_id)
    x.has_sent = True

  def __repr__(self):
    return f'< send | {self.match} | {self.has_sent} >'


class User(db.Model):
  """Persistant holding table to store user information"""

  __tablename__ = 'users'
  
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  first_name = db.Column(db.String(30), nullable=False, info={'label':'First Name'})
  last_name = db.Column(db.String(30), nullable=False,info={'label':'Last Name'})
  phone = db.Column(db.String, nullable=False, unique=True, info={'label':'Phone Number (must begin with 1)'})
  # phone = db.Column(db.BigInteger, nullable=False, unique=True, info={'validators': NumberRange(min=10000000000,max=19999999999,message='must be valid 10 digit phone number beginning with 1 (15555555555)'),'label':'Phone Number (must begin with 1)'})
  email = db.Column(db.String, nullable=False, unique=True, info={'validators': Email()})
  password = db.Column(db.String, nullable=False)

  @property
  def full_name(self):
    """Return full name of user."""
    return f"{self.first_name} {self.last_name}"

  @classmethod
  def register(cls, phone, pwd, email, first_name, last_name):
    """Register user w/hashed password & return user."""

    hashed = bcrypt.generate_password_hash(pwd)
    # turn bytestring into normal (unicode utf8) string
    hashed_utf8 = hashed.decode("utf8")

    # return instance of user w/username and hashed pwd
    user = cls(phone=phone, password=hashed_utf8,email=email,first_name=first_name,last_name=last_name)

    return user

  @classmethod
  def authenticate(cls, phone, pwd):
    """Validate that user exists & password is correct.

    Return user if valid; else return False.
    """

    u = User.query.filter_by(phone=phone).first()

    if u and bcrypt.check_password_hash(u.password, pwd):
        # return user instance
        return u
    else:
        return False

  def get_reset_token(self, expires_sec=1800):
    s = Serializer('AVP_API', expires_sec)
    return s.dumps({'user_id': self.id}).decode('utf-8')

  @staticmethod
  def verify_reset_token(token):
    s = Serializer('AVP_API')
    try:
      user_id = s.loads(token)['user_id']
    except:
      return None
    return User.query.get(user_id)

  def __repr__(self):
    return f'< user | {self.phone} | {self.email} >'


class EventTracker(db.Model):
  """Format and store data from AVP API request."""

  __tablename__ = 'event_tracker'

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  event_id = db.Column(db.Integer, unique=True)
  status = db.Column(db.String, nullable=True)

  @classmethod
  def instantiate(cls, event_id, status):
    """instantiate event tracker"""
    try:
      event_tracker = cls(event_id=event_id, status=status)
      db.session.add(event_tracker)
      db.session.commit()
    except:
      print('EventTracker already exists')
      db.session.rollback()

  @classmethod
  def get_event(cls):
    """get current event from database"""
    return cls.query.first()

  def set_event_status(self,obj):
    """check tournament status set current status"""
    # U - scheduled
    # C - warming up
    # P - playing
    # F - finished
    length = len(obj)
    finished_count = ([match['MatchState'] for match in obj]).count('F')
    in_progress = ([match['MatchState'] for match in obj]).count('P')
    warm_up = ([match['MatchState'] for match in obj]).count('C')
    scheduled = ([match['MatchState'] for match in obj]).count('U')

    if not obj:
      # importing from polling causes a circular imports error
      # run_poll.remove_job('in_progress')
      # print('-------- job just removed --------')
      self.status = 'not yet scheduled'
      return 1

    # set status to finished and increment event_id
    print(self.event_id, 'total', length, 'F =', finished_count, 'P =', in_progress, 'C =', warm_up, 'U =',scheduled)

    finished_finals = [m['Bracket'] for m in obj if m['Bracket'] == 'Finals' and m['MatchState'] == 'F']

    if len(finished_finals) == 2:
      self.status = 'finished'
      # clear send status table
      print('&&&&&&&&&& clear tables &&&&&&&&&&&&&&')
      SendStatus.clear_send_status_table()
      Match.clear_matches()
      self.event_id = obj[0]['EventId'] + 1

    elif (obj and length > finished_count):
      self.status = 'playing' 

    elif (obj and scheduled > 0):
      self.status = 'scheduled'
      try:
        in_progress_poll()
        print('-------- job (in_progress) just added --------')
      except:
        print('-------- job (in_progress) already running --------')

  def __repr__(self):
    return f'< current event | {self.event_id} | {self.status}>'


class TelegramUser(db.Model):
  """Database table to store telegram user information"""

  __tablename__ = 'telegram_users'
  
  telegram_id = db.Column(db.Integer, primary_key=True)
  first_name = db.Column(db.String(50), nullable=False)
  last_name = db.Column(db.String(50), nullable=False)

  @property
  def details(self):
    """Return full name of user."""
    return f"{self.first_name} {self.last_name} - {self.telegram_id}"

  @classmethod
  def get_all(cls):
    """get all telegram users' id's"""
    return cls.query.all()

  @classmethod
  def add_telegram_user(cls, telegram_id, first_name, last_name):
    """Register user w/hashed password & return user."""
    # return instance of telegram user
    user = cls(telegram_id=telegram_id,first_name=first_name,last_name=last_name)
    try:
      db.session.merge(user)
      db.session.commit()
      return 'success'
    except IntegrityError as e:
      print(e.orig.diag.message_detail)
      return 'error'

    print('usery',user)

  @classmethod
  def remove_telegram_user(cls, id):
    """Register user w/hashed password & return user."""
    print('model')
    try:
      db.session.query(cls).filter(cls.telegram_id==id).delete()
      print('deleted')
      db.session.commit()
    except IntegrityError as e:
      print(e.orig.diag.message_detail)
      return e.orig.diag.message_detail


  def __repr__(self):
    return f'< telegram_user | {self.details} >'
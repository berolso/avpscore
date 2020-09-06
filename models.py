from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import exists
import requests
from flask_bcrypt import Bcrypt
from wtforms.validators import Email, NumberRange
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os


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
  sets = db.Column(db.Text, nullable=True, )
  winner = db.Column(db.Integer, nullable=True)
  match_state = db.Column(db.String, nullable=True)

  match_sent = db.relationship('SendStatus', backref='send_status')

  @classmethod
  def format_response_merge(cls, obj):
    for i in obj:
      # unique 4 digit match id from CompId and MatchNo
      m_id = int(str(i['CompetitionId']) + str(i['MatchNo']).zfill(2))
      # stats string. (create stats relational table in future
      stats = str(i['Stats'])
      # team strings
      null_filler = 'TBD'
      try:
        team_a = f'''({i['TeamA']['Seed']}) {i['TeamA']['Captain']['FirstName']} {i['TeamA']['Captain']['LastName']} / {i['TeamA']['Player']['FirstName']} {i['TeamA']['Player']['LastName']}'''
      except:
        team_a = null_filler
      try:
        team_b = f'''({i['TeamB']['Seed']}) {i['TeamB']['Captain']['FirstName']} {i['TeamB']['Captain']['LastName']} / {i['TeamB']['Player']['FirstName']} {i['TeamB']['Player']['LastName']}'''
      except:
        team_b=null_filler
      # Sets will parse out a string for the order of who won the set
      try:
        score_w_a = ', '.join([f'''{j['A']} - {j['B']}''' for j in i['Sets']])
      except:
        score_w_a = null_filler

      try:
        score_w_b = ', '.join([f'''{j['B']} - {j['A']}''' for j in i['Sets']])
      except:
        score_w_b = null_filler

      # create local database table with live data
      new_match = cls(match_id=m_id, stats=stats,competition_id=i['CompetitionId'], competition_name=i['CompetitionName'], competition_code=i['CompetitionCode'], match_no=i['MatchNo'], bracket=i['Bracket'], team_a=team_a , team_b=team_b, sets=(score_w_a,score_w_b), winner=i['Winner'], match_state=i['MatchState'])
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
  def check_and_add_for_send(cls):
    """check for data in send_status table, add if not."""
    # filter for A)not yet in send_status table. with foreign key & B)match_state not equal to 'F' for final after match has completed. makes sure match result is still pending.
    new_adds = Match.query.filter((Match.match_sent == None)&(Match.match_state != 'F')).all()
    # loop to add data to for_send
    for i in new_adds:
      id = i.match_id
      try:
        new_for_send = cls(match=id)
        db.session.add(new_for_send)
      except:
        continue

  @classmethod
  def format_and_send_message(cls):
    """Send deliver message and update status to sent."""
    # join query both tables to filter for A) message has not been sent B) winner has been decided either team A or team B. result string format is different for A or B winner.
    has_winner = db.session.query(Match).join(cls).filter((cls.has_sent == False)&(Match.winner != None))
    # format message string for display
    for i in has_winner:
      id = i.match_id
      m = Match.query.get(id)
      score = m.sets.split('","')
      if m.winner == 1:
        string = f'{m.team_a} {score[0][2:]} def {m.team_b} in {m.bracket}'
      if m.winner == 2:
        string = f'{m.team_b} {score[1][:-2]} def {m.team_a} in {m.bracket}'
         
      # just me for testing
      # r = requests.post('https://api.twilio.com/2010-04-01/Accounts/AC103cc58558a9ad0a954cbc496b2daa19/Messages.json', auth= os.environ.get('API_AUTH_KV'), data = {'To':os.environ.get('TEST_NUM'),'From':'+12513024230','Body':string})
      
      # test phone list
      # phone_list = os.environ.get('PHONE_LIST')

      # create and fromat list of numbers to text from User table
      phone_list = [f'+{num.phone}' for num in db.session.query(User.phone).all()]

      # all phones 
      for number in phone_list:
        r = requests.post('https://api.twilio.com/2010-04-01/Accounts/AC103cc58558a9ad0a954cbc496b2daa19/Messages.json', auth=os.environ.get('API_AUTH_KV'), data = {'To':number,'From':'+12513024230','Body':string})

      # change status
      x = cls.query.get(id)
      x.has_sent = True

  def __repr__(self):
    return f'< send | {self.match} | {self.has_sent} >'


class User(db.Model):
  """Persistant holding table to store user information"""

  __tablename__ = 'users'
  
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  first_name = db.Column(db.String(30), nullable=False)
  last_name = db.Column(db.String(30), nullable=False)
  phone = db.Column(db.BigInteger, nullable=False, unique=True, info={'validators': NumberRange(min=10000000000,max=19999999999,message='must be valid 10 digit phone number beginning with 1 (15555555555)')})
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
    return cls.query.get(1)

  def set_event_status(self,obj):
    """check tournament status set current status"""
    length = len(obj)
    finished_count = ([match['MatchState'] for match in obj]).count('F')
    scheduled_count = ([match['MatchState'] for match in obj]).count('S')

    if not obj:
      # importing from polling causes a circular imports error
      # run_poll.remove_job('in_progress')
      # print('-------- job just removed --------')
      self.status = 'not yet scheduled'
      return 1

    # set status to finished and increment event_id
    if obj and length == finished_count:
      self.status = 'finished'
      self.event_id = obj[0]['EventId'] + 1
    elif (obj and length > finished_count):
      self.status = 'playing' 
    elif (obj and scheduled_count > 0):
      self.status = 'scheduled'
      try:
        in_progress_poll()
        print('-------- job (in_progress) just added --------')
      except:
        print('-------- job (in_progress) already running --------')

  def __repr__(self):
    return f'< current event | {self.event_id} | {self.status}>'

  

  
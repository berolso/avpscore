from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import exists
import requests
from classified import API_AUTH_KV, PHONE_LIST, TEST_NUM


db = SQLAlchemy()

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
      ## just me for testing
      # r = requests.post('https://api.twilio.com/2010-04-01/Accounts/AC103cc58558a9ad0a954cbc496b2daa19/Messages.json', auth= classified.API_AUTH_KV, data = {'To':classified.TEST_NUM,'From':'+12513024230','Body':string})
      
      phone_list = classified.PHONE_LIST
      # all phones 
      for number in phone_list:
        r = requests.post('https://api.twilio.com/2010-04-01/Accounts/AC103cc58558a9ad0a954cbc496b2daa19/Messages.json', auth=classified.API_AUTH_KV, data = {'To':number,'From':'+12513024230','Body':string})

      # change status
      x = cls.query.get(id)
      x.has_sent = True

  def __repr__(self):
    return f'< send | {self.match} | {self.has_sent} >'

def connect_db(app):
    """Connect to db"""

    db.app = app
    db.init_app(app)  

  
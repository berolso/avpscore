from flask import Flask, redirect, render_template
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, Match, SendStatus
from polling import run_poll_avp, ThreadClass
import threading
import time

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///avp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.config['SECRET_KEY'] = "AVP SCORES"

connect_db(app)
db.create_all()

debug = DebugToolbarExtension(app)


@app.route("/1")
def test_runtime_1():
  """Homepage."""
  
  test = Match.query.order_by('match_id').all()

  # SendStatus.check_and_add_for_send()
  # db.session.commit()

  global TC
  global thread
  TC = ThreadClass() 
  thread = threading.Thread(target = TC.run, args =(10, )) 
  thread.start() 
  print('******************* start *******************')
   
  print('refresh', threading.enumerate())

  return render_template("/index.html", test=test, var=id)

@app.route("/2")
def test_runtime_2():
  """Homepage."""

  test = Match.query.order_by('match_id').all()

  # SendStatus.format_and_send_message()
  # db.session.commit()
  try:
    TC.terminate()
    print('-------- Poll just terminated --------')
  except:
    print('there is nothing running')

  return render_template("/index.html",test=test)  


## debugCode
# import pdb
# pdb.set_trace()

# TC = ThreadClass() 
# thread = threading.Thread(target = TC.run, args =(10, )) 
# thread.start() 



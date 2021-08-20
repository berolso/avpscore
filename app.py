from flask import Flask, redirect, render_template, session, flash, url_for
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, Match, SendStatus, User, EventTracker, bcrypt
from forms import NewUserForm, LoginUserForm, UpdateUserForm, RequestResetForm, ResetPasswordForm, RegisterForm
from polling import run_poll_avp, poll_and_merge, weekly_poll, in_progress_poll, run_poll
import time
from werkzeug.exceptions import Unauthorized
from sqlalchemy.exc import IntegrityError
from mailer import email_password_reset, sg
from twilio import notify_admin_of_new_user
import requests
from flaskext.markdown import Markdown
import os

app = Flask(__name__)

Markdown(app)

app.config.from_pyfile('config.py')

connect_db(app)
db.create_all()

debug = DebugToolbarExtension(app)

# instantiate EventTracker
EventTracker.instantiate(os.environ.get('EVENT_NUMBER'),'')

# start weekly poll
weekly_poll()
# start poll()
in_progress_poll()


@app.errorhandler(404)
def page_not_found(e):
  '''custom 404'''
  # note that we set the 404 status explicitly
  return render_template('404.html'), 404

@app.route("/")
def homepage():
  """Homepage."""

  # show login if user is not
  if 'phone' not in session:
    return redirect('/login')
  phone = session['phone']
  return redirect(f'/users/{phone}')

@app.route("/about")
def about():
  """about page"""
  with open("./README.md", "r") as f: 
    content = f.read() 

  return render_template('/about.html', mkd_txt=content)

@app.route('/register', methods=['GET','POST'])
def register_new():
  '''display new user form(GET),register new user(POST)'''
  # display new user form
  form = NewUserForm()
  # if valid form post
  if form.validate_on_submit():
    phone = form.phone.data
    pwd = form.password.data
    eml = form.email.data
    fn = form.first_name.data
    ln = form.last_name.data

    # create new user
    user = User.register(phone,pwd,eml,fn,ln)
    db.session.add(user)
    # check for duplicate entry
    try:
      db.session.commit()
    except IntegrityError as e:
      # print(inspect.getmembers(e.orig.diag))
      # flash(e.orig.diag.message_detail,'danger')
      form.phone.errors = [e.orig.diag.message_detail]
      return render_template('/new_user.html', form=form)
    # add new user to current session
    # send notification to admin when user signs up
    try:
      response = notify_admin_of_new_user(user)
      print(response)
    except:
      print('not able to send text')

    session['phone'] = user.phone
    flash('new number added','success')
    return redirect(f'/users/{user.phone}')
  # if get or not valid post
  else:
    return render_template('new_user.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login_user():
  '''show login form or login new user'''
  # login form
  form = LoginUserForm()
  # validate post
  print(form)
  if form.validate_on_submit():
    phone = form.phone.data
    pwd = form.password.data
    print(pwd)
    # authenticate user in User class
    user = User.authenticate(phone,pwd)
    if user:
      session['phone'] = user.phone
      flash(f'logged in with {user.phone}','success')
      return redirect(f'/users/{user.phone}')
    else:
      form.phone.errors = ['Incorrect phone or Password']
  return render_template('/login.html',form=form)

@app.route('/logout')
def logout_user():
  session.pop("phone")
  flash('you have logged out','success')
  return redirect('/login')

@app.route('/users/<int:phone>')
def user_route(phone):
  '''show user page'''
  if 'phone' not in session:
    # raise Unauthorized()
    flash('you must be logged in!','danger')
    return redirect('/login')
  else:
    user = User.query.filter_by(phone=phone).first()
    return render_template('/user.html',user=user)

@app.route('/users/<int:phone>/update',methods=["GET","POST"])
def update_user(phone):
  '''update user'''
  user = User.query.filter_by(phone=phone).first()
  # verify user is logged in
  if "phone" not in session or user.phone != session['phone']:
    flash('you must be logged in to edit information!','danger')
    return redirect(f'/login')
  form = UpdateUserForm(obj=user)
  if form.validate_on_submit():
    form.populate_obj(user)

    db.session.commit()
    # update session
    user.phone = form.phone.data
    session['phone'] = user.phone
    flash(f'updated {user.phone}','success')

    return redirect(f"/users/{user.phone}")

  return render_template("/user_update.html", form=form)

@app.route("/users/<int:phone>/delete", methods=["POST"])
def remove_user(phone):
  """Remove user and redirect to login."""

  if "phone" not in session or phone != session['phone']:
    raise Unauthorized()

  user = User.query.filter_by(phone=phone).first()
  db.session.delete(user)
  db.session.commit()

  session.pop("phone")
  flash(f'{user.full_name} - {user.phone} has been removed from the system. To continue to recieve texts you will have to create an account again','danger')

  return redirect("/login")

@app.route("/status")
def status():
  """display EventTracker status"""
  jobs = run_poll.get_jobs()
  event = EventTracker.get_event()
  send_status = SendStatus.get_all()
  matches = Match.get_all()
  print(run_poll.get_jobs())


  return render_template("/status.html", jobs=jobs, event=event, send_status=send_status, matches=matches)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
  if 'phone' in session:
    session.pop("phone")
    flash('you have been logged out!','danger')
    return redirect('/login')
  form = RequestResetForm()
  if form.validate_on_submit():
    user = User.query.filter_by(email=form.email.data).first()
    response = email_password_reset(user)
    app.logger.info("Password Reset Requested by: " + user.email)
    app.logger.info("Response Status: " + str(response.status_code))
    app.logger.info(response.headers)

    flash('An email has been sent with instructions to reset your password.', 'info')
    return redirect(url_for('login_user'))
  return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
  if 'phone' in session:
    session.pop("phone")
  user = User.verify_reset_token(token)
  if user is None:
    flash('Using is an invalid or expired token. Request password reset again', 'warning')
    return redirect(url_for('reset_request'))
  form = ResetPasswordForm()
  if form.validate_on_submit():
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
    user.password = hashed_password
    db.session.commit()
    flash('Your password has been updated! You are now able to log in', 'success')
    return redirect(url_for('login_user'))
  return render_template('reset_token.html', title='Reset Password', form=form)


# @app.route("/1")
# def test_runtime_1():
#   """Homepage."""
  
#   test = Match.query.order_by('match_id').all()

#   # SendStatus.check_and_add_for_send()
#   # db.session.commit()

#   try:
#     print(run_poll.get_jobs())
#     run_poll.remove_job('in_progress')
#     print(run_poll.get_jobs())
#     print('-------- job just removed --------')
#   except:
#     print(run_poll.get_jobs())
#     in_progress_poll()
#     print(run_poll.get_jobs())
#     print('-------- job just added --------')

 
#   return render_template("/dev.html", test=test, var=id)

# @app.route("/2")
# def test_runtime_2():
#   """Homepage."""

#   test = Match.query.order_by('match_id').all()
#   run_poll.reschedule_job('in_progress', trigger='interval', seconds=1)


#   return render_template("/dev.html",test=test)  

# @app.route("/3")
# def test_runtime_3():
#   """Homepage."""

#   test = Match.query.order_by('match_id').all()
#   run_poll.reschedule_job('in_progress', trigger='interval', seconds=5)


#   return render_template("/dev.html",test=test)  


# @app.route("/text")
# def test_runtime_text():
#   """Homepage."""
#   test = Match.query.order_by('match_id').all()
#   user = 'hi'

#   print('before')
#   response = notify_admin_of_new_user(user)
#   # print(response)


#   return render_template("/dev.html",test=test)

@app.route("/test", methods=['GET','POST'])
def testform():
  """Homepage."""
  form = RegisterForm()

  if form.validate_on_submit():
    phone = form.phone.data

  return render_template('new_user.html', form=form)


## debugCode
# import pdb
# pdb.set_trace()



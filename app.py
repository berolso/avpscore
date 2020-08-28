from flask import Flask, redirect, render_template, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, Match, SendStatus, User
from forms import NewUserForm, LoginUserForm, UpdateUserForm
from polling import run_poll_avp, poll_and_merge, weekly_poll, in_progress_poll, run_poll
import time
from werkzeug.exceptions import Unauthorized
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///avp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.config['SECRET_KEY'] = "AVP SCORES"

connect_db(app)
db.create_all()

debug = DebugToolbarExtension(app)


@app.errorhandler(404)
def page_not_found(e):
  '''custom 404'''
  # note that we set the 404 status explicitly
  return render_template('404.html'), 404

@app.route("/home")
def homepage():
  """Homepage."""

  # show login if user is not
  if 'username' not in session:
    return redirect('/login')

  # if logged in show list of all comments
  feedback = Feedback.query.all()
  username = session['username']

  return render_template("/home.html", feedback=feedback, username=username)

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

    return redirect(f"/users/{user.phone}")

  return render_template("/user_update.html", form=form)

@app.route("/1")
def test_runtime_1():
  """Homepage."""
  
  test = Match.query.order_by('match_id').all()

  # SendStatus.check_and_add_for_send()
  # db.session.commit()

  try:
    print(run_poll.get_jobs())
    run_poll.remove_job('in_progress')
    print(run_poll.get_jobs())
    print('-------- job just removed --------')
  except:
    print(run_poll.get_jobs())
    in_progress_poll()
    print(run_poll.get_jobs())
    print('-------- job just added --------')

 
  return render_template("/dev.html", test=test, var=id)

@app.route("/2")
def test_runtime_2():
  """Homepage."""

  test = Match.query.order_by('match_id').all()
  run_poll.reschedule_job('in_progress', trigger='interval', seconds=1)


  return render_template("/dev.html",test=test)  

@app.route("/3")
def test_runtime_3():
  """Homepage."""

  test = Match.query.order_by('match_id').all()
  run_poll.reschedule_job('in_progress', trigger='interval', seconds=5)


  return render_template("/dev.html",test=test)  


## debugCode
# import pdb
# pdb.set_trace()



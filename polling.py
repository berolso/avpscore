import requests
import polling2
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from models import db, connect_db, Match, SendStatus, EventTracker
from telegram_api import TelegramBot

def run_poll_avp(event):
  """run poll function"""

  def response_is_200(response):
    """Check that the response returned == 200"""
    if response.status_code == 200:
      return True

  res = polling2.poll(lambda: requests.get(f'https://volleyballapi.web4data.co.uk/api/matches/byevent/{event.event_id}'), check_success=response_is_200, step=1, timeout=2)

  return res.json()
 
# APScheduler event cycle
def poll_and_merge():
  print('start poll and merge')
  event = EventTracker.get_event()
  obj = run_poll_avp(event)
  Match.format_response_merge(obj)
  SendStatus.find_and_add_matches()
  # delay results
  # time.sleep(6)
  # 
  finished = SendStatus.finished_matches()
  TelegramBot.send(finished)
  # 
  no_avp_obj = event.set_event_status(obj)
  if no_avp_obj:
    run_poll.remove_job('in_progress')
    print('-------- job just removed --------')


  db.session.commit()
  print('*********finished*************')

def heroku_caffeine():
  '''keep heroku from sleeping'''
  res = requests.get('https://avp-scores.herokuapp.com/')
  print('######## caffeine ##########',res)


# APscheduler
run_poll = BackgroundScheduler(daemon=True)
run_poll.start()

def weekly_poll():
  thursday_trigger = CronTrigger(day_of_week='thu', hour=6)
  run_poll.add_job(poll_and_merge, thursday_trigger, id='weekly')

def in_progress_poll():
  progress_trigger = IntervalTrigger(seconds=4)
  run_poll.add_job(poll_and_merge, progress_trigger, id='in_progress')

def heroku_poll():
  ping_trigger = IntervalTrigger(minutes=10)
  run_poll.add_job(heroku_caffeine, ping_trigger, id='heroku')

def start_pulse():
  pulse_trigger = IntervalTrigger(weeks=1)
  run_poll.add_job(TelegramBot.pulse, pulse_trigger, id='pulse')
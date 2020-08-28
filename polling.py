import requests
import polling2
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from models import db, connect_db, Match, SendStatus

def run_poll_avp():
  """run poll function"""

  def response_is_200(response):
    """Check that the response returned == 200"""
    if response.status_code == 200:
      return True

  res = polling2.poll(lambda: requests.get('https://volleyballapi.web4data.co.uk/api/matches/byevent/22'), check_success=response_is_200, step=1, timeout=2)

  return res.json()
 
# thread event cycle
def poll_and_merge():
  print('start poll and merge')
  obj = run_poll_avp()
  Match.format_response_merge(obj)
  SendStatus.check_and_add_for_send()
  # time.sleep(2)
  SendStatus.format_and_send_message()

  db.session.commit()
  print('*********finished*************')

# APscheduler
run_poll = BackgroundScheduler(daemon=True)
run_poll.start()

def weekly_poll():
  thursday_trigger = CronTrigger(day_of_week='thu', hour=6)
  run_poll.add_job(poll_and_merge, thursday_trigger)

def in_progress_poll():
  progress_trigger = IntervalTrigger(seconds=5)
  run_poll.add_job(poll_and_merge, progress_trigger, id='in_progress')
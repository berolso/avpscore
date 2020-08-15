import requests
import polling2
import threading
import time
import multiprocessing 

from models import db, connect_db, Match, SendStatus

def run_poll_avp():
  """run poll function"""

  def response_is_200(response):
    """Check that the response returned == 200"""
    if response.status_code == 200:
      return True

  res = polling2.poll(lambda: requests.get('https://volleyballapi.web4data.co.uk/api/matches/byevent/22'), check_success=response_is_200, step=1, timeout=.5)

  return res.json()

# thread event cycle
def poll_and_merge():
  obj = run_poll_avp()
  Match.format_response_merge(obj)
  SendStatus.check_and_add_for_send()
  time.sleep(2)
  SendStatus.format_and_send_message()

  db.session.commit()
  print('*********finished*************')

class ThreadClass: 
    
  def __init__(self): 
    self._running = True
    
  def terminate(self): 
    self._running = False
        
  def run(self, n): 
    while self._running and n > 0:
      # time.sleep(3) 
      poll_and_merge() 
      # print('T-minus', n) 
      # n -= 1
    
  # c = CountdownTask() 
  # t = Thread(target = c.run, args =(10, )) 
  # t.start() 
  
  # # Signal termination 
  # c.terminate()  
    
  # # Wait for actual termination (if needed)  
  # t.join()  

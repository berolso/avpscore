


class ThreadJob(threading.Thread):
  def __init__(self,callback,event,interval):
    '''runs the callback function after interval seconds

    :param callback:  callback function to invoke
    :param event: external event for controlling the update operation
    :param interval: time in seconds after which are required to fire the callback
    :type callback: function
    :type interval: int
    '''
    self.callback = callback
    self.event = event
    self.interval = interval
    super(ThreadJob,self).__init__()

  def run(self):
    while not self.event.wait(self.interval):
      print(f'''################################
      #
      #
      #
      ###############################''')
      self.callback()

thread event cycle 
def poll_and_merge():
  obj = run_poll_avp()
  Match.format_response_merge(obj)
  SendStatus.check_and_add_for_send()
  time.sleep(15)
  SendStatus.format_and_send_message()

  db.session.commit()
  print('*********finished*************')

begin
event = threading.Event()
k = ThreadJob(poll_and_merge,event,1)
## start infinite polling
k.start()
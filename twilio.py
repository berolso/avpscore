import requests
import os


def notify_admin_of_new_user(user):
  auth = eval(os.environ.get('API_AUTH_KV'))
  number = os.environ.get('TEST_NUM')
  message = f'new user: {user.full_name} - {user.phone} - {user.email}'

  r = requests.post('https://api.twilio.com/2010-04-01/Accounts/AC103cc58558a9ad0a954cbc496b2daa19/Messages.json', auth=auth, data = {'To':number,'From':'+12513024230','Body':message})

  print(r)
  return r

      # just me for testing
      # api_auth = os.environ.get('API_AUTH_KV')
      # twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
      # twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
      # test_num = os.environ.get('TEST_NUM')
      # twilio_num = os.environ.get('TWILIO_NUM')

      # r = requests.post('https://api.twilio.com/2010-04-01/Accounts/AC103cc58558a9ad0a954cbc496b2daa19/Messages.json', auth = api_auth, data = {'To': test_num,'From':twilio,'Body':string})

      # twilio
      # just results sent to test cell
      # r = requests.post(f'https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json', data = {'To': test_num,'From':twilio_num,'Body':string}, auth = (twilio_sid,twilio_token))

      # test phone list
      # phone_list = os.environ.get('PHONE_LIST')

      # create and fromat list of numbers to text from User table
      # phone_list = [f'+{num.phone}' for num in db.session.query(User.phone).all()]

      # all phones 
      # for number in phone_list:
      #   r = requests.post(f'https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json', data = {'To':number,'From':twilio_num,'Body':string}, auth = (twilio_sid,twilio_token))
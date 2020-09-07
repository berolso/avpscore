import requests
import os


def notify_admin_of_new_user(user):
  auth = eval(os.environ.get('API_AUTH_KV'))
  number = os.environ.get('TEST_NUM')
  message = f'new user: {user.full_name} - {user.phone} - {user.email}'

  r = requests.post('https://api.twilio.com/2010-04-01/Accounts/AC103cc58558a9ad0a954cbc496b2daa19/Messages.json', auth=auth, data = {'To':number,'From':'+12513024230','Body':message})

  print(r)
  return r
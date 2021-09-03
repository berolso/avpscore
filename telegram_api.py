import os
import telebot
from models import TelegramUser, SendStatus
from helpers import Helper

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

bot = telebot.AsyncTeleBot(TELEGRAM_TOKEN)

MY_TELEGRAM = os.environ.get('MY_TELEGRAM')

TELEGRAM_USER_LOG = os.environ.get('TELEGRAM_USER_LOG')

TELEGRAM_FEEDBACK = os.environ.get('TELEGRAM_FEEDBACK')


# PORT = int(os.environ.get('PORT', 5000))
HOST_URL = os.environ.get('HOST_URL')

@bot.message_handler(commands=['start'])
def welcome_message(message):
  bot.send_message(message.chat.id, f"""Thanks for trying the AVP score bot. 
  
I built this to follow AVP main draw tournament results in real time. 

Feel free to share with anyone on Telegram.
  
  👉 /help for all available commands""")

@bot.message_handler(commands=['help'])
def help_menu(message):
  bot.send_message(message.chat.id, f"""Here's what I can do..
  
  👉 /results - You will receive result updates.

  👉 /stop - You will no longer receive updates.

  👉 /bracket - check out live bracket.

  👉 /watch - live on peacock.

  👉 /feedback - I might not see it, but any feedback is welcome.


  """)
  

@bot.message_handler(commands=['results'])
def get_updates(message):
  id = message.chat.id
  first = message.chat.first_name
  last = message.chat.last_name
  try:
    res = TelegramUser.add_telegram_user(id,first,last)
    if res == 'success':
      bot.send_message(id, "You are signed up for score updates. 👉 /stop to stop receiving updates")
      bot.send_message(TELEGRAM_USER_LOG,f"ADDED {message.chat.first_name} {message.chat.last_name} id:{message.chat.id}")
    else:
      bot.send_message(id, "Oops, something went wron, I mean Ron.. 👉 /help")
  except:
    bot.send_message(id, "Unfortunately, we're unable to add you at this time")


@bot.message_handler(commands=['stop'])
def stop_updates(message):
  res = TelegramUser.remove_telegram_user(message.chat.id)
  try:
    bot.send_message(message.chat.id, "Score updates have been stopped")
    bot.send_message(TELEGRAM_USER_LOG,f"REMOVED {message.chat.first_name} {message.chat.last_name} id:{message.chat.id}")
  except:
    bot.send_message(message.chat.id, "woops")

@bot.message_handler(commands=['bracket'])
def bracket(message):
  bracket_btn = telebot.types.InlineKeyboardMarkup()
  bracket_btn.add(telebot.types.InlineKeyboardButton('live bracket', url='https://avp.com/brackets/'))

  bot.send_message(message.chat.id, f'👇',reply_markup=bracket_btn)

@bot.message_handler(commands=['watch'])
def watch(message):
  keyboard = telebot.types.InlineKeyboardMarkup()
  keyboard.add(telebot.types.InlineKeyboardButton('Watch live', url='www.peacocktv.com/watch/sports/highlights/'))

  bot.send_message(message.chat.id,f'👇',reply_markup=keyboard)

# feedback 
feedback_question = f"What do you think..?"
@bot.message_handler(commands=['feedback'])
def start_feedback(message):
  markup = telebot.types.ForceReply()
  bot.send_message(message.chat.id,feedback_question,reply_markup=markup)

@bot.message_handler(func = lambda message: message.reply_to_message and message.reply_to_message.text == feedback_question)
def received_feedback(message):
  bot.send_message(message.chat.id,f"Thanks {message.chat.first_name}!")

  bot.send_message(TELEGRAM_FEEDBACK, f"""{message.chat.first_name} {message.chat.last_name} id:{message.chat.id} -
  {message.text}""")

@bot.message_handler(commands=['data'])
def get_message_data(message):
  bot.send_message(message.chat.id,message)

@bot.message_handler()
def echo(message):
  bot.send_message(message.chat.id,f"OK {message.chat.first_name}.. If you need 👉/help.")
  bot.send_message(MY_TELEGRAM,f"{message.chat.first_name} {message.chat.last_name} is {message.chat.id} - they said: {message.text}")

class TelegramBot():
  """Telegram functions to handle message deliveries of avp data"""

  @staticmethod
  def send(finished):
    """receive list of finished matches"""
    # Todo: modify to get specific users 
    users = TelegramUser.get_all()
    for match in finished:
      # format message string for display
      message = Helper.format_result_message(match)
      # send message to each user
      for user in users:
        bot.send_message(user.telegram_id, message, parse_mode='MARKDOWN',disable_web_page_preview=True)
        SendStatus.mark_as_sent(match.match_id)

  @staticmethod
  def pulse():
    '''send message to telegram every hour to make sure heroku is still awake'''
    bot.send_message(TELEGRAM_USER_LOG, "i'm still alive")


# instead of webhook use constant polling.
# had issue of polling() blocking the APScheduler. played with running multiple threads but opted for webhooks to send updates as the optimal solution
# bot.polling()

# raw api endpoint
# https://api.telegram.org/bot<your-bot-token>/sendMessage?chat_id=<chat-id>&text=TestReply

# https://api.telegram.org/bot<YOURTOKEN/getWebhookInfo

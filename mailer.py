import sendgrid
from sendgrid.helpers.mail import *
from flask import render_template
import os


# blog
sg = sendgrid.SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))


def email_password_reset(user):
    token = user.get_reset_token()
    print(token)
    subject = "AVP Scores Reset Your Password"
    # from_email = Email(app.config['ADMINS'][0])
    from_email = Email("willakenz@gmail.com")
    to_email = To([user.email][0])
    html_body = render_template("reset_passwordz.html", user=user, token=token)

    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content)
    response = sg.send(mail)
    return response


# vid (https://www.youtube.com/watch?v=vutyTx7IaAI)(https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/10-Password-Reset-Email/flaskblog/routes.py)
# uses flask mail instead of sendgrid

# def send_reset_email(user):
#   token = user.get_reset_token()
#   msg = Message('Password Reset Request', sender='noreply@demo.com',recipients=[user.email])
#   msg.body = f'''To reset your password, visit the following link:
# {url_for('reset_token', token=token, _external=True)}
# If you did not make this request then simply ignore this email and no changes will be made.
# '''
#   mail.send(msg)


# for test
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import *
# import os

# message = Mail(
#     from_email='from_email@example.com',
#     to_emails='to@example.com',
#     subject='Sending with Twilio SendGrid is Fun',
#     html_content='<strong>and easy to do anywhere, even with Python</strong>')

# def send():
#     try:
#         sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
#         print('again sendgrid')
#         response = sg.send(message)
#         print(response.status_code)
#         print(response.body)
#         print(response.headers)
#     except Exception as e:
#         print(e.message)

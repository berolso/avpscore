from flask_wtf import FlaskForm
from wtforms_alchemy import model_form_factory
from models import db, User

from wtforms import StringField, IntegerField, PasswordField, TextField, SubmitField
# from wtforms.fields.html5 import URLField
from wtforms.validators import InputRequired, DataRequired, Optional,URL,NumberRange,Length, ValidationError, EqualTo


BaseModelForm = model_form_factory(FlaskForm)

class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session

class NewUserForm(ModelForm):
    class Meta:
        model = User

class LoginUserForm(ModelForm):
    class Meta:
        model = User
        only = ['phone', 'password']
        unique_validator = None

class UpdateUserForm(ModelForm):
    class Meta:
        model = User
        exclude = ['password']
        # unique_validator = None

class RequestResetForm(ModelForm):
    class Meta:
        model = User
        only = ['email']
        unique_validator = None
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')                          

# class NewUserForm(FlaskForm):
#     """Form for registering new users."""

#     username = StringField("UserName", validators=[InputRequired(), Length(max=20)])
#     password = PasswordField("Password", validators=[InputRequired()])
#     email = StringField("Email", validators=[InputRequired(), Length(max=50)])
#     first_name = StringField("First Name", validators=[InputRequired(), Length(max=30)])
#     last_name = StringField("Last Name", validators=[InputRequired(), Length(max=30)])

# class LoginUserForm(FlaskForm):
#     """Form for login users."""

#     username = StringField("UserName", validators=[InputRequired(), Length(max=20)])
#     password = PasswordField("Password", validators=[InputRequired()])

# class FeedbackForm(FlaskForm):
#     '''Form for creating feedback'''
#     title = StringField('Title', validators=[InputRequired(), Length(max=100)])
#     content = TextField('Content', validators=[InputRequired()])
    

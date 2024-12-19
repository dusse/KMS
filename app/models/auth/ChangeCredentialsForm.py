from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from wtforms.validators import ValidationError
from app.models import User

NEW_PASSWORD = 'new password'
CONFIRM_PASS = 'confirm password'
ACTION_BTN = "change"

class ChangeCredentialsForm(FlaskForm):
    new_password = PasswordField(NEW_PASSWORD, validators=[DataRequired()])
    confirm_password = PasswordField(CONFIRM_PASS, validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField(ACTION_BTN)
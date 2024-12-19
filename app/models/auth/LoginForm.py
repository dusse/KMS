from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

NAME_MSG = 'name is required'
NAME_LNGTH_MSG = 'name must contain from 2 up to 20 symbols'
PASS_MSG = "password is required"

class LoginForm(FlaskForm):
    name = StringField(
        'name',
        validators=[
            DataRequired(message=NAME_MSG),
            Length(min=2, max=20, message=NAME_LNGTH_MSG)
        ]
    )
    password = PasswordField(
        'password',
        validators=[DataRequired(message=PASS_MSG)]
    )
    submit = SubmitField('login')

from flask import current_app
from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, PasswordField, SubmitField, StringField
from wtforms import validators, ValidationError

class LoginForm(FlaskForm):
    next = HiddenField()
    reg_next = HiddenField()
    username = StringField('Username', validators=[
        validators.DataRequired('Username is required'),
    ])
    password = PasswordField('Password', validators=[
        validators.DataRequired('Password is required'),
    ])
    remember_me = BooleanField('Remember me')

    @property
    def user(self):
        if hasattr(self, '_user'): return self._user
        user_manager = current_app.user_manager
        self._user = user_manager.find_user_by_username(self.username.data)
        if self._user and user_manager.verify_password(self.password.data, self._user.password):
            return self._user

    def validate(self):
        if not super().validate():
            return False
        if self.user:
            return True
        self.password.errors.append('Incorrect username/password')
        return False


from flask import current_app
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import BooleanField, HiddenField, PasswordField, SubmitField, StringField
from wtforms import validators, ValidationError

from .validators import (validate_username_chars, validate_email_available,
        validate_password, validate_username_available, )

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

class RegisterForm(FlaskForm):
    next = HiddenField()
    reg_next = HiddenField()
    username = StringField('Username', validators=[
        validators.DataRequired('Username is required'),
        validate_username_chars,
        validate_username_available,
    ])
    email = StringField('Email', validators=[
        validators.DataRequired('Email is required'),
        validators.Email('Invalid Email'),
        validate_email_available,
    ])
    password = PasswordField('Password', validators=[
        validators.DataRequired('Password is required'),
        validate_password,
    ])

class ResendEmailForm(FlaskForm):
    email = StringField('Email', validators=[
        validators.DataRequired('Email is required'),
        validators.Email('Invalid Email'),
    ])

    @property
    def user(self):
        if hasattr(self, '_user'): return self._user
        user_manager = current_app.user_manager
        self._user = user_manager.find_user_by_email(self.email.data)
        return self._user

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[
        validators.DataRequired('Current Password is required'),
    ])
    new_password = PasswordField('New Password', validators=[
        validators.DataRequired('New Password is required'),
        validate_password,
    ])
    retype_password = PasswordField('Retype Password', validators=[
        validators.EqualTo('new_password', "New password and retype password doesn't match")
    ])

    def validate(self):
        user_manager =  current_app.user_manager
        if not super().validate():
            return False
        if current_user.is_anonymous:
            return False
        if not user_manager.verify_password(self.current_password.data, current_user.password):
            self.current_password.errors.append('Current password is incorrect')
            return False
        return True

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[
        validators.DataRequired('Email is required'),
        validators.Email('Invalid Email'),
    ])

    @property
    def user(self):
        if hasattr(self, '_user'): return self._user
        user_manager = current_app.user_manager
        self._user = user_manager.find_user_by_email(self.email.data)
        return self._user

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[
        validators.DataRequired('New Password is required'),
        validate_password,
    ])
    retype_password = PasswordField('Retype Password', validators=[
        validators.EqualTo('new_password', "New password and retype password doesn't match")
    ])

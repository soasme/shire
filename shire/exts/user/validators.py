import string

from wtforms import ValidationError
from flask import current_app

def validate_username_chars(form, field):
    username = field.data
    if len(username) < 3:
        raise ValidationError('Username must have at least 3 characters')
    valid_chars = string.ascii_letters + string.digits + '-_.'
    for char in username:
        if char not in valid_chars:
            raise ValidationError(
                'Username may only contain letters, digits, -, _, and .')

def validate_email_available(form, field):
    email = field.data
    user_manager = current_app.user_manager
    user = user_manager.find_user_by_email(email)
    if user:
        raise ValidationError('The email address is already in use. Please try another one')

def validate_password(form, field):
    password = field.data
    length = len(password)

    lowers_cnt = uppers_cnt = digits_cnt = 0
    for ch in password:
        if ch.islower(): lowers_cnt += 1
        elif ch.isupper(): uppers_cnt += 1
        elif ch.isdigit(): digits_cnt += 1

    if length < 6 or lowers_cnt == 0 or uppers_cnt == 0 or digits_cnt == 0:
        raise ValidationError('Password must have at least 6 chars, and at least one lowercase letter, one uppercase letter, and one number')

import json
from time import time
from random import choice
import string

from werkzeug.utils import import_string
from passlib.context import CryptContext
from authlib.jose import JsonWebSignature
from authlib.jose import JWS_ALGORITHMS
from flask import Blueprint, current_app, request, render_template, url_for, redirect, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_mail import Message
from flask_bcrypt import Bcrypt

from .forms import LoginForm, RegisterForm, ChangePasswordForm, ResendEmailForm

bp = Blueprint('user', __name__, template_folder='templates')

@bp.teardown_request
def auto_rollback(exc):
    if exc:
        current_app.db.session.rollback()
    current_app.db.session.remove()

@bp.route('/login/', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or '/'
    if current_user.is_authenticated:
        return redirect(next_url)
    login_form = LoginForm(request.form)
    if request.method != 'POST':
        login_form.next.data = next_url
    elif login_form.validate():
        if not login_form.user or not login_form.user.active:
            flash('You account is inactive.', 'error')
            return redirect(url_for('user.login'))
        login_user(login_form.user, login_form.remember_me.data)
        return redirect(next_url)
    else:
        flash('invalid login.', 'error')
        return redirect(url_for('user.login'))
    return render_template('login.html', login_form=login_form)

@bp.route('/logout/')
def logout():
    logout_user()
    return redirect('/')

@bp.route('/register/', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm(request.form)
    user_manager = current_app.user_manager
    if request.method == 'POST' and register_form.validate():
        user = user_manager.new_user()
        register_form.populate_obj(user)
        user.password = user_manager.hash_password(user.password)
        user_manager.db.session.add(user)
        user_manager.db.session.commit()
        flash(('Register successfully. Before login, '
               'please check your email and confirm your email address'),
               'info')
        message = user_manager.get_registration_message(user)
        try:
            user_manager.send_mail(message)
        except requests.Timeout:
            flash('There was something wrong when sending registration email. Please retry sending your registration email.', 'error')
        return redirect('/')
    return render_template('register.html', register_form=register_form)

@bp.route('/confirm/<token>/')
def confirm(token):
    user_manager = current_app.user_manager
    try:
        data = user_manager.validate_registration_token(token)
    except Exception:
        return 'Sorry, the link is invalid.'
    email = data['email']
    user = user_manager.find_user_by_email(email)
    if not user:
        return 'Sorry, this email is invalid.'
    user_manager.activate_user(user)
    flash('Your account is active now. Try signing in.', 'success')
    return redirect('/')

@bp.route('/resendemail/', methods=['GET', 'POST'])
def resendemail():
    user_manager = current_app.user_manager
    form = ResendEmailForm(request.form)
    if request.method == 'POST':
        if form.validate():
            user = form.user
            if user.active:
                flash('Your account is active now. Try signing in.', 'success')
                return redirect('/')
            message = user_manager.get_registration_message(user)
            try:
                user_manager.send_mail(message)
                flash('Registration email was sent. Please check your inbox.', 'success')
            except requests.Timeout:
                flash('There was something wrong when sending registration email. Please retry.', 'error')
            return redirect('/')
    return render_template('resendemail.html', form=form)


@bp.route('/forgotpass/')
def forgotpass():
    return 'Sorry, this feature is not yet implemented.'

@bp.route('/changepass/', methods=['GET', 'POST'])
@login_required
def changepass():
    user_manager = current_app.user_manager
    form = ChangePasswordForm(request.form)
    if request.method == 'POST':
        if form.validate():
            user_manager.change_password(current_user, form.new_password.data)
            flash('Your password has changed successfully.', 'success')
            return redirect(url_for('user.changepass'))
        else:
            flash('Your password has not changed due to an error.', 'error')
    return render_template('changepass.html', form=form)

@bp.route('/resetpass/<token>/')
def resetpass():
    return 'Sorry, this feature is not yet implemented.'

class UserManager:

    def __init__(self, app=None, db=None, mail=None):
        if app is not None:
            self.init_app(app, db, mail)

    def init_app(self, app, db, mail):
        assert db is not None

        self.app = app
        self.db = db
        self.mail = mail
        app.user_manager = self
        self.app.register_blueprint(bp, url_prefix='/user/')
        self.__user_class = app.config['USER_CLASS']
        app.login_manager = LoginManager(app)
        app.login_manager.user_loader(self.load_user)
        self.bcrypt = Bcrypt(app)

    @property
    def user_class(self):
        if hasattr(self, '_user_class'): return self._user_class
        self._user_class = import_string(self.__user_class)
        return self._user_class

    def load_user(self, id):
        return self.user_class.query.get(id)

    def new_user(self):
        return self.user_class()

    def find_user_by_username(self, username):
        return self.user_class.query.filter_by(username=username).first()

    def find_user_by_email(self, email):
        return self.user_class.query.filter_by(email=email).first()

    def hash_password(self, raw_password):
        return self.bcrypt.generate_password_hash(raw_password).decode('utf-8')

    def verify_password(self, password, hash_password):
        return self.bcrypt.check_password_hash(hash_password, password)

    def change_password(self, user, password):
        user.password = self.hash_password(password)
        self.db.session.add(user)
        self.db.session.commit()

    def send_mail(self, message):
        return self.mail.send_mail(message.sender, message.recipients, message.subject, message.html)

    def get_registration_token(self, user):
        now = int(time())
        rand = ''.join([choice(string.ascii_letters) for _ in range(10)])
        rands = f'{rand}.{now}'
        jws = JsonWebSignature(algorithms=JWS_ALGORITHMS)
        headers = {'alg': 'HS256'}
        payload = json.dumps({'email': user.email})
        secret = bytes(self.app.config['SECRET_KEY'], 'utf-8')
        return jws.serialize_compact(headers, payload, secret)

    def validate_registration_token(self, token):
        jws = JsonWebSignature(algorithms=JWS_ALGORITHMS)
        secret = bytes(self.app.config['SECRET_KEY'], 'utf-8')
        data = jws.deserialize_compact(token, secret)
        return json.loads(data['payload'])

    def activate_user(self, user):
        user.active = True
        self.db.session.add(user)
        self.db.session.commit()

    def get_registration_link(self, user, external=True):
        token = self.get_registration_token(user)
        return url_for('user.confirm', token=token, _external=external)

    def get_registration_message(self, user):
        html = '''
<p>Hi {username},</p>
<p>Welcome to {app_name}.</p>
<p>If you did not register {app_name}, please ignore this email.</p>
<hr>
<p>You will need to confirm your email.</p>
<p>Please click on this link: <a href="{link}">{link}</a>.<p>'''.format(
            app_name=self.app.config.get('SITE_NAME'),
            username=user.username,
            link=self.get_registration_link(user),
        )
        recipient = user.email
        sender = self.app.config['MAIL_DEFAULT_SENDER']
        subject = 'Confirm your registration'
        return Message(recipients=[recipient],
                subject=subject,
                sender=sender,
                html=html)

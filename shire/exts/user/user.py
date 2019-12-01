import string

from werkzeug import import_string
from passlib.context import CryptContext
from flask import Blueprint, current_app, request, render_template, url_for, redirect, flash
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_bcrypt import Bcrypt

from .forms import LoginForm, RegisterForm

bp = Blueprint('user', __name__, template_folder='templates')

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
        return 'validate failed.'
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
        flash('Register successfully. Before login, please check your email and confirm your email address', 'info')
        return redirect('/')
    return render_template('register.html', register_form=register_form)

@bp.route('/confirm/resend/')
def reconfirm():
    return 'Sorry, the registration has open.'

@bp.route('/confirm/<token>/')
def confirmuser(token):
    return 'Sorry, the registration has open.'

@bp.route('/forgotpass/')
def forgotpass():
    return 'Sorry, this feature is not yet implemented.'

@bp.route('/changepass/')
def changepass():
    return 'Sorry, this feature is not yet implemented.'

@bp.route('/resetpass/<token>/')
def resetpass():
    return 'Sorry, this feature is not yet implemented.'

class UserManager:

    def __init__(self, app=None, db=None, celery=None):
        if app is not None:
            self.init_app(app, db, celery)

    def init_app(self, app, db, celery):
        assert db is not None

        self.app = app
        self.db = db
        self.celery = celery
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

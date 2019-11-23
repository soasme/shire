from pathlib import Path

import stripe
from flask import Flask
from celery import Celery
from whitenoise import WhiteNoise
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_user import UserManager
from decouple import config

from shire.exts.sub import Subscription, checkout_session_completed
from shire.exts.mail import Mail

__DIR__ = Path(__file__) / ".."
__STATIC_DIR__ = __DIR__ / "static"

db = SQLAlchemy()
bcrypt = Bcrypt()
celery = Celery(__name__)
sub = Subscription()
mail = Mail()

def init_celery(app, celery):
    TaskBase = celery.Task
    class AppContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                try:
                    return TaskBase.__call__(self, *args, **kwargs)
                except Exception as e:
                    db.session.rollback()
                    raise e
                finally:
                    db.session.remove()
    celery.Task = AppContextTask

def create_app():
    app = Flask(__name__)
    app.config.update({
        # REQUIRED
        'SECRET_KEY': config('SECRET_KEY'),
        'SQLALCHEMY_DATABASE_URI': config('DATABASE_URL'),
        'BROKER_URL': config('REDIS_URL'),
        'CELERY_RESULT_BACKEND': config('REDIS_URL'),
        # OPTIONAL
        'SITE_NAME': config('SITE_NAME', default='MarkSthFun'),
        'SITE_DOMAIN': config('SITE_DOMAIN', default='127.0.0.1:5000'),
        'BLOG_URL': config('BLOG_URL', default='https://blog.marksth.fun'),
        'GITHUB_URL': config('GITHUB_URL', default='https://github.com/marksthfun/shire'),
        'SUPPORT_EMAIL': config('SUPPORT_EMAIL', default='support@marksth.fun'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': config('SQLALCHEMY_TRACK_MODIFICATIONS', cast=bool, default=False),
        'SIGNUP_ENABLED': config('SIGNUP_ENABLED', cast=bool, default=False),
        'STRIPE_ENABLED': config('STRIPE_ENABLED', cast=bool, default=False),
        'STRIPE_PUBLIC_KEY': config('STRIPE_PUBLIC_KEY', default=''),
        'STRIPE_SECRET_KEY': config('STRIPE_SECRET_KEY', default=''),
        'STRIPE_WEBHOOK_SECRET_KEY': config('STRIPE_WEBHOOK_SECRET_KEY', default=''),
        'STRIPE_API_VERSION': config('STRIPE_API_VERSION', default=''),
        'STRIPE_PLAN_ID': config('STRIPE_PLAN_ID', default=''),
        'SUBSCRIPTION_WEBHOOK_ENABLED': config('SUBSCRIPTION_WEBHOOK_ENABLED', cast=bool, default=True),
        'SUBSCRIPTION_WEBHOOK_URL': config('SUBSCRIPTION_WEBHOOK_URL', default='/subscription/hook/'),
        'SUBSCRIPTION_CLI_ENABLED': config('SUBSCRIPTION_CLI_ENABLED', cast=bool, default=True),
        'USER_ENABLE_EMAIL': config('USER_ENABLE_EMAIL', default=False),
        'USER_ENABLE_MULTIPLE_EMAILS': config('USER_ENABLE_MULTIPLE_EMAILS', default=False),
        'USER_ENABLE_USERNAME': config('USER_ENABLE_USERNAME', default=True),
        'USER_ENABLE_CHANGE_USERNAME': config('USER_ENABLE_CHANGE_USERNAME', default=False),
        'USER_ENABLE_CHANGE_PASSWORD': config('USER_ENABLE_CHANGE_PASSWORD', default=True),
        'USER_ENABLE_CONFIRM_EMAIL': config('USER_ENABLE_CONFIRM_EMAIL', default=False),
        'USER_ENABLE_FORGOT_PASSWORD': config('USER_ENABLE_FORGOT_PASSWORD', default=True),
        'USER_ENABLE_INVITE_USER': config('USER_ENABLE_INVITE_USER', default=False),
        'USER_ENABLE_REGISTER': config('USER_ENABLE_REGISTER', default=True),
        'USER_ENABLE_REMEMBER_ME': config('USER_ENABLE_REMEMBER_ME', default=True),
        'USER_ENABLE_AUTH0': config('USER_ENABLE_AUTH0', default=False),
        'USER_APP_NAME': config('SITE_NAME', default='MarkSthFun'),
        'USER_AUTO_LOGIN': config('USER_AUTO_LOGIN', default=True),
        'USER_EMAIL_SENDER_EMAIL': config('USER_EMAIL_SENDER_EMAIL', 'noreply@mail.marksth.fun'),
        'USER_EMAIL_SENDER_NAME': config('USER_EMAIL_SENDER_NAME', default='MarkSthFun'),
        'USER_SEND_PASSWORD_CHANGED_EMAIL': config('USER_SEND_PASSWORD_CHANGED_EMAIL', default=True),
        'USER_SEND_REGISTERED_EMAIL': config('USER_SEND_REGISTERED_EMAIL', default=True),
        'USER_SEND_USERNAME_CHANGED_EMAIL': config('USER_SEND_USERNAME_CHANGED_EMAIL', default=False),
        'USER_REQUIRE_INVITATION': config('USER_REQUIRE_INVITATION', default=False),
        'USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL': config('USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL', default=False),
        'USER_REQUIRE_RETYPE_PASSWORD': config('USER_REQUIRE_RETYPE_PASSWORD', default=False),
        'USER_LOGIN_URL': config('USER_LOGIN_URL', default='/login/'),
        'USER_LOGOUT_URL': config('USER_LOGOUT_URL', default='/logout/'),
        'USER_REGISTER_URL': config('USER_REGISTER_URL', default='/register/'),
        'USER_CHANGE_PASSWORD_URL': config('USER_CHANGE_PASSWORD_URL', default='/user/changepass/'),
        'USER_CONFIRM_EMAIL_URL': config('USER_CONFIRM_EMAIL_URL', default='/user/confirm/<token>/'),
        'USER_FORGOT_PASSWORD_URL': config('USER_FORGOT_PASSWORD_URL', default='/forgotpass/'),
        'USER_RESEND_EMAIL_CONFIRMATION_URL': config('USER_RESEND_EMAIL_CONFIRMATION_URL', default='/user/resend/'),
        'USER_RESET_PASSWORD_URL': config('USER_RESET_PASSWORD_URL', default='/user/resetpass/<token>/'),
        'USER_LOGIN_TEMPLATE': 'login.html',
        'USER_REGISTER_TEMPLATE': 'register.html',
        'USER_RESET_PASSWORD_TEMPLATE': 'reset_password.html',
        'USER_CHANGE_PASSWORD_TEMPLATE': 'change_password.html',
        # TODO: resetpass, resend, forgotpass, confirm.
        'MAILGUN_API_KEY': config('MAILGUN_API_KEY', default=''),
        'ANNUAL_FEE': config('ANNUAL_FEE', cast=int, default=12),
    })

    db.init_app(app)

    celery.conf.update(app.config)
    init_celery(app, celery)

    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
    stripe.api_version = app.config.get('STRIPE_API_VERSION')

    bcrypt.init_app(app)

    sub.init_app(app)

    mail.init_app(app)

    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=__STATIC_DIR__.resolve()
    )

    from shire.models import Category, User, Thing, ThingNote

    user_manager = UserManager(app, db, User)

    from shire import views, tasks

    app.jinja_env.globals['Category'] = Category

    app.template_filter('autoversion')(views.autoversion_filter)
    app.template_filter('from_now')(views.from_now)

    app.teardown_request(views.auto_rollback)

    app.add_url_rule('/', 'index', views.index)
    app.add_url_rule('/explore/', 'explore', views.explore)
    app.add_url_rule('/guide/', 'guide', views.guide)
    app.add_url_rule('/about/', 'about', views.about)
    app.add_url_rule('/privacy/', 'privacy', views.privacy)
    app.add_url_rule('/tos/', 'terms_of_service', views.terms_of_service)
    app.add_url_rule('/faq/', 'faq', views.faq)
    app.add_url_rule('/u/<username>/', 'profile', views.profile)
    app.add_url_rule('/u/<username>/t/<tag>/', 'tagged_things', views.filter_user_things_by_tag)
    app.add_url_rule('/u/<username>/c/<category>/', 'categorized_things',
            views.filter_user_things_by_category)
    app.add_url_rule('/t/<tag>/', 'all_tagged_things', views.filter_global_things_by_tag)
    app.add_url_rule('/mark/', 'mark', views.mark, methods=['POST'])
    app.add_url_rule('/m/<int:id>/', 'mark_page', views.mark_page)
    app.add_url_rule('/m/<int:id>/update/', 'update_mark_page', views.update_mark_page)
    app.add_url_rule('/m/<int:id>/update/', 'update_mark', views.update_mark, methods=['POST'])
    app.add_url_rule('/m/<int:id>/download/', 'download_mark', views.download_mark)
    app.add_url_rule('/m/<int:id>/delete/', 'delete_mark_page', views.delete_mark_page)
    app.add_url_rule('/m/<int:id>/delete/', 'delete_mark', views.delete_mark, methods=['POST'])
    app.add_url_rule('/account/', 'account', views.account)
    app.add_url_rule('/account/', 'update_account', views.update_account, methods=['POST'])

    celery.add_periodic_task(30.0, tasks.ping, expires=10.0)

    return app

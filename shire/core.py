from pathlib import Path

import stripe
from flask import Flask
from celery import Celery
from whitenoise import WhiteNoise
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
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

def create_celery(**kwargs):
    app = create_app()
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery


def create_app():
    from shire.core import db, bcrypt
    from shire.models import Category, User, Thing, ThingNote
    from shire import views, tasks

    app = Flask(__name__)
    app.config.update({
        # REQUIRED
        'SECRET_KEY': config('SECRET_KEY'),
        'SQLALCHEMY_DATABASE_URI': config('DATABASE_URL'),
        'BROKER_URL': config('BROKER_URL'),
        'CELERY_RESULT_BACKEND': config('CELERY_RESULT_BACKEND'),
        # OPTIONAL
        'SITE_NAME': config('SITE_NAME', default='MarkSthFun'),
        'SITE_DOMAIN': config('SITE_DOMAIN', default='127.0.0.1:5000'),
        'BLOG_URL': config('BLOG_URL', default='https://blog.marksth.fun'),
        'GITHUB_URL': config('GITHUB_URL', default='https://github.com/marksthfun/shire'),
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
        'MAILGUN_API_KEY': config('MAILGUN_API_KEY', default=''),
        'ANNUAL_FEE': config('ANNUAL_FEE', cast=int, default=12),
    })

    db.init_app(app)

    celery.conf.update(app.config)

    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
    stripe.api_version = app.config.get('STRIPE_API_VERSION')

    bcrypt.init_app(app)

    sub.init_app(app)
    checkout_session_completed.connect(tasks.provision_user_account.delay)

    mail.init_app(app)

    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=__STATIC_DIR__.resolve()
    )

    app.jinja_env.globals['Category'] = Category

    app.template_filter('autoversion')(views.autoversion_filter)
    app.template_filter('from_now')(views.from_now)

    app.before_request(views.setup_globals)
    app.teardown_request(views.auto_rollback)

    app.add_url_rule('/', 'index', views.index)
    app.add_url_rule('/logout/', 'logout', views.logout)
    app.add_url_rule('/explore/', 'explore', views.explore)
    app.add_url_rule('/guide/', 'guide', views.guide)
    app.add_url_rule('/about/', 'about', views.about)
    app.add_url_rule('/privacy/', 'privacy', views.privacy)
    app.add_url_rule('/tos/', 'terms_of_service', views.terms_of_service)
    app.add_url_rule('/faq/', 'faq', views.faq)
    app.add_url_rule('/signup/', 'signup_page', views.signup_page)
    app.add_url_rule('/signup/', 'signup', views.signup, methods=['POST'])
    app.add_url_rule('/signup/success/', 'signup_success_page', views.signup_success_page)
    app.add_url_rule('/signup/success/', 'signup_success', views.signup_success_page, methods=['POST'])
    app.add_url_rule('/signup/canceled/', 'signup_canceled_page', views.signup_canceled_page)
    app.add_url_rule('/u/<username>/', 'profile', views.profile)
    app.add_url_rule('/u/<username>/t/<tag>/', 'tagged_things', views.filter_user_things_by_tag)
    app.add_url_rule('/u/<username>/c/<category>/', 'categorized_things',
            views.filter_user_things_by_category)
    app.add_url_rule('/t/<tag>/', 'all_tagged_things', views.filter_global_things_by_tag)
    app.add_url_rule('/mark/', 'mark', views.mark, methods=['POST'])
    app.add_url_rule('/things/<int:id>/', 'thing_page', views.thing_page)
    app.add_url_rule('/things/<int:id>/update/', 'update_thing_page', views.update_thing_page)
    app.add_url_rule('/things/<int:id>/update/', 'update_thing', views.update_thing, methods=['POST'])
    app.add_url_rule('/things/<int:id>/download/', 'download_thing', views.download_thing)
    app.add_url_rule('/things/<int:id>/delete/', 'delete_thing_page', views.delete_thing_page)
    app.add_url_rule('/things/<int:id>/delete/', 'delete_thing', views.delete_thing, methods=['POST'])
    app.add_url_rule('/login/', 'login', views.login, methods=['POST'])
    app.add_url_rule('/account/', 'account', views.account)
    app.add_url_rule('/account/', 'update_account', views.update_account, methods=['POST'])
    app.add_url_rule('/v1/things/<int:id>/share/', 'share_thing', views.share_thing, methods=['POST'])

    return app

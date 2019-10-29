from pathlib import Path

import stripe
from flask import Flask
from celery import Celery
from whitenoise import WhiteNoise
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from decouple import config


__DIR__ = Path(__file__) / ".."
__STATIC_DIR__ = __DIR__ / "static"

db = SQLAlchemy()
bcrypt = Bcrypt()
celery = Celery(__name__)


def create_celery(**kwargs):
    app = create_app()
    celery.conf.update(app.config)
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery


def create_app():
    from shire.core import db, bcrypt
    from shire.models import Category, Progress, User, Thing, ThingNote
    from shire import views

    app = Flask(__name__)
    app.config.update({
        # REQUIRED
        'SECRET_KEY': config('SECRET_KEY'),
        'SQLALCHEMY_DATABASE_URI': config('DATABASE_URL'),
        # OPTIONAL
        'SITE_NAME': config('SITE_NAME', default='MarkSthFun'),
        'SITE_DOMAIN': config('SITE_DOMAIN', default='127.0.0.1:5000'),
        'BLOG_URL': config('BLOG_URL', default=''),
        'SQLALCHEMY_TRACK_MODIFICATIONS': config('SQLALCHEMY_TRACK_MODIFICATIONS', cast=bool, default=False),
        'SIGNUP_ENABLED': config('SIGNUP_ENABLED', cast=bool, default=False),
        'STRIPE_ENABLED': config('STRIPE_ENABLED', cast=bool, default=False),
        'STRIPE_PUBLIC_KEY': config('STRIPE_PUBLIC_KEY', default=''),
        'STRIPE_SECRET_KEY': config('STRIPE_SECRET_KEY', default=''),
        'STRIPE_WEBHOOK_SECRET_KEY': config('STRIPE_WEBHOOK_SECRET_KEY', default=''),
        'STRIPE_API_VERSION': config('STRIPE_API_VERSION', default=''),
        'STRIPE_PLAN_ID': config('STRIPE_PLAN_ID', default=''),
        'ANNUAL_FEE': config('ANUAL_FEE', cast=int, default=10),
    })
    db.init_app(app)
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
    stripe.api_version = app.config.get('STRIPE_API_VERSION')
    bcrypt.init_app(app)
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=__STATIC_DIR__.resolve()
    )

    app.jinja_env.globals['Category'] = Category
    app.jinja_env.globals['Progress'] = Progress

    app.template_filter('autoversion')(views.autoversion_filter)
    app.template_filter('from_now')(views.from_now)

    app.before_request(views.setup_globals)

    app.add_url_rule('/', 'index', views.index)
    app.add_url_rule('/logout/', 'logout', views.logout)
    app.add_url_rule('/recent/', 'recent', views.recent)
    app.add_url_rule('/guide/', 'guide', views.guide)
    app.add_url_rule('/about/', 'about', views.about)
    app.add_url_rule('/privacy/', 'privacy', views.privacy)
    app.add_url_rule('/tos/', 'terms_of_service', views.terms_of_service)
    app.add_url_rule('/faq/', 'faq', views.faq)
    app.add_url_rule('/signup/', 'signup_page', views.signup_page)
    app.add_url_rule('/signup/', 'signup', views.signup, methods=['POST'])
    app.add_url_rule('/signup/confirm/', 'confirm_signup', views.signup)
    app.add_url_rule('/charge/stripe/session', 'create_stripe_session', views.create_stripe_session, methods=['POST'])
    app.add_url_rule('/charge/stripe/success/', 'stripe_charge_success', views.stripe_charge_success)
    app.add_url_rule('/charge/stripe/cancel/', 'stripe_charge_cancel', views.stripe_charge_cancel)
    app.add_url_rule('/charge/stripe/webhook/', 'stripe_charge_webhook', views.stripe_charge_webhook, methods=['POST'])
    app.add_url_rule('/charge/', 'charge', views.charge, methods=['POST'])
    app.add_url_rule('/u/<username>/', 'profile', views.profile)
    app.add_url_rule('/u/<username>/t/<tag>/', 'tagged_things', views.filter_user_things_by_tag)
    app.add_url_rule('/mark/', 'mark', views.mark, methods=['POST'])
    app.add_url_rule('/things/<int:id>/', 'thing_page', views.thing_page)
    app.add_url_rule('/things/<int:id>/update/', 'update_thing_page', views.update_thing_page)
    app.add_url_rule('/things/<int:id>/update/', 'update_thing', views.update_thing, methods=['POST'])
    app.add_url_rule('/things/<int:id>/download/', 'download_thing', views.download_thing)
    app.add_url_rule('/things/<int:id>/delete/', 'delete_thing_page', views.delete_thing_page)
    app.add_url_rule('/things/<int:id>/delete/', 'delete_thing', views.delete_thing, methods=['POST'])

    app.add_url_rule('/login/', 'login', views.login, methods=['POST'])
    app.add_url_rule('/v1/things/<int:id>/share/', 'share_thing', views.share_thing, methods=['POST'])
    return app

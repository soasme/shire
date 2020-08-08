from pathlib import Path

import stripe
from flask import Flask
from celery import Celery
from whitenoise import WhiteNoise
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserManager
from flask_caching import Cache
from decouple import config

from shire.exts.mail import Mail
from shire.exts.user.user import UserManager

__DIR__ = Path(__file__) / ".."
__STATIC_DIR__ = __DIR__ / "static"

db = SQLAlchemy()
celery = Celery(__name__)
mail = Mail()
cache = Cache()
user_manager = UserManager()

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
        'SERVER_NAME': config('SITE_DOMAIN', default='127.0.0.1:5000'),
        'BLOG_URL': config('BLOG_URL', default='https://blog.marksth.fun'),
        'GITHUB_URL': config('GITHUB_URL', default='https://github.com/soasme/shire'),
        'SUPPORT_EMAIL': config('SUPPORT_EMAIL', default='support@marksth.fun'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': config('SQLALCHEMY_TRACK_MODIFICATIONS', cast=bool, default=False),
        'CACHE_TYPE': config('CACHE_TYPE', default='simple'),
        'CACHE_DEFAULT_TIMEOUT': config('CACHE_DEFAULT_TIMEOUT', cast=int, default=300),
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
        'USER_CLASS': config('USER_CLASS', 'shire.models:User'),
        'MAILGUN_API_KEY': config('MAILGUN_API_KEY', default=''),
        'MAILGUN_DOMAIN': config('MAILGUN_DOMAIN', default=''),
        'MAIL_DEFAULT_SENDER': config('MAIL_DEFAULT_SENDER', default='noreply@mg.marksth.fun'),
    })

    db.init_app(app)
    app.db = db

    celery.conf.update(app.config)
    init_celery(app, celery)

    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
    stripe.api_version = app.config.get('STRIPE_API_VERSION')

    mail.init_app(app)

    cache.init_app(app)

    user_manager.init_app(app, db, mail)

    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=__STATIC_DIR__.resolve()
    )

    from shire.models import Category, User, Thing, ThingNote

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
    app.add_url_rule('/robots.txt', 'robots', views.robots)
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

import os
import json
import enum
from time import time
from datetime import datetime
from pathlib import Path

import stripe
from whitenoise import WhiteNoise
from dotenv import find_dotenv, load_dotenv
from decouple import config
from flask import Flask, redirect, request, session, g, jsonify, current_app, url_for
from flask import render_template as render
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import JSON, Enum

from shire.core import db, bcrypt
from shire.errors import ShireError, ExistingError
from shire.models import Category, Progress, User, Thing, ThingNote

__DIR__ = Path(__file__) / ".."
__STATIC_DIR__ = __DIR__ / "static"

load_dotenv(find_dotenv())

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

app.wsgi_app = WhiteNoise(app.wsgi_app, root=__STATIC_DIR__.resolve())

db.init_app(app)

stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
stripe.api_version = app.config.get('STRIPE_API_VERSION')

bcrypt.init_app(app)

app.jinja_env.globals['Category'] = Category
app.jinja_env.globals['Progress'] = Progress

@app.template_filter('autoversion')
def autoversion_filter(filename):
  fullpath = os.path.join(__DIR__.resolve(), filename[1:])
  try:
      timestamp = str(os.path.getmtime(fullpath))
      return f"{filename}?v={timestamp}"
  except OSError:
      return filename

@app.before_request
def setup_g():
    g.user = session.get('uid') and User.query.filter_by(username=session['uid']).first()

@app.route('/')
def index():
    """Landing page"""
    error = session.pop('error.login', '')
    return render('index.html', error=error)

@app.route('/logout/')
def logout():
    """Logout"""
    session.pop('uid', None)
    return redirect('/')

@app.route('/recent/')
def recent():
    """Recent things"""
    things = Thing.get_recent_all_things()
    return render('recent.html', things=things)

@app.route('/popular/')
def popular():
    """Popular things"""
    return "Coming soon."

@app.route('/guide/')
def guide():
    """How to use it"""
    return "Coming soon."

@app.route('/about/')
def about():
    """About"""
    return render('about.html')

@app.route('/privacy/')
def privacy():
    return render('privacy.html')

@app.route('/tos/')
def terms_of_service():
    return render('tos.html')

@app.route('/faq/')
def faq():
    return "Coming soon."

@app.route('/signup/')
def signup_page():
    """Create an account"""
    if not current_app.config['SIGNUP_ENABLED']: return 'coming soon'
    error = session.pop('error.signup', '')
    return render("signup.html", error=error)

@app.route('/signup/', methods=['POST'])
def signup():
    """TODO: need to sort out the logic"""
    if not current_app.config['SIGNUP_ENABLED']: return 'coming soon'
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    if not username:
        session['error.signup'] = 'username is empty'
        return redirect(url_for('signup_page'))
    if not email:
        session['error.signup'] = 'email is empty'
        return redirect(url_for('signup_page'))
    if not password:
        session['error.signup'] = 'password is empty'
        return redirect(url_for('signup_page'))
    user = User.query.filter_by(username=username).first()
    if user and user.is_charged:
        session['error.signup'] = 'username exists'
        return redirect(url_for('signup_page'))
    if user and not user.is_charged:
        user = User.query.filter_by(username=username).first()
        user.email = email
        user.nickname = username
        user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.add(user)
        try:
            db.session.commit()
            session['nuid'] = user.id
            return redirect(url_for('confirm_signup'))
        except Exception:
            db.session.rollback()
            session['error.signup'] = 'database error'
            return redirect(url_for('signup_page'))
    try:
        user = User.new(username, email, username, password, autocommit=True)
        session['nuid'] = user.id
        return redirect(url_for('confirm_signup'))
    except ExistingError as e:
        user = User.query.filter_by(username=username).first()
        if user.is_charged:
            session['error.signup'] = 'username exists'
            return redirect(url_for('signup_page'))
        else:
            session['nuid'] = user.id
            return redirect(url_for('confirm_signup'))
    except Exception as e:
        app.logger.error("error: %s", e)
        db.session.rollback()
        return redirect('/signup/')

@app.route('/signup/confirm/')
def confirm_signup():
    """Pick a payment"""
    #uid = session.get('nuid')
    #if not uid: return redirect('/')
    return render('confirm_signup.html')

@app.route('/charge/stripe/session', methods=['POST'])
def create_stripe_session():
    """Create a stripe subscription checkout session.
    Potential user will be charged within this session.
    """
    plan_id = current_app.config['STRIPE_PLAN_ID']
    uid = session['nuid']
    user = User.query.get(uid)
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            subscription_data={"items": [{"plan": plan_id}]},
            success_url=url_for('stripe_charge_success',
                uid=session['nuid'], _external=True),
            cancel_url=url_for('stripe_charge_cancel', _external=True),
            customer_email=user.email,
            client_reference_id=user.id,
        )
        session['nsess'] = checkout_session['id']
        return jsonify({
            'code': 'ok',
            'checkoutSessionId': checkout_session['id']
        })
    except Exception as e:
        return jsonify({'code': str(e)}), 403

def handle_checkout_session(session):
    client_reference_id = session['client_reference_id']
    if not client_reference_id: return
    client_reference_id = int(client_reference_id)
    user = User.query.get(client_reference_id)
    sub = UserSubscription.query.filter_by(user_id=client_reference_id, subscription=session['subscription']).first()
    if not sub:
        sub = UserSubscription(user_id=client_reference_id,
                customer=session['customer'],
                subscription=session['subscription'])
        db.session.add(sub)
        db.session.commit()

def poll_completed_checkout_session(since):
    events = stripe.Event.list(type = 'checkout.session.completed', created = {
        'gte': int(since)
    })
    for event in events:
        handle_checkout_session(event['data']['object'])

@app.route('/charge/stripe/success/')
def stripe_charge_success():
    if 'nuid' not in session: return redirect('/')
    session.pop('nuid', None)
    poll_completed_checkout_session(int(time()) - 7200)
    return render('signup_success.html')

@app.route('/charge/stripe/cancel/')
def stripe_charge_cancel():
    return 'cancel'

@app.route('/charge/stripe/webhook/', methods=['POST'])
def stripe_charge_webhook():
    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET_KEY']
    request_data = json.loads(request.data)
    signature = request.headers.get('stripe-signature')
    if not secret_key or not signature:
        return jsonify({'code': 'unknown signature'}), 400
    try:
        event = stripe.Webhook.construct_event(
            payload=request.data, sig_header=signature, secret=webhook_secret)
        data = event['data']
        event_type = event['type']
    except Exception as e:
        app.logger.error("error: %s", e)
        return jsonify({'code': 'unable to construct event'}), 400

    data_object = data['object']
    if event_type == 'checkout.session.completed':
        items = data_object['display_items']
        customer = stripe.Customer.retrieve(data_object['customer'])
        if len(items) != 1 or not items[0].custom:
            return jsonify({'code': 'unknown items'}), 400

@app.route('/charge/', methods=['POST'])
def charge():
    """Charge"""
    return jsonify(dict(request.form))

@app.route('/signup/stripe/callback')
def finish_signup():
    """Handle stripe payment"""

@app.route('/404/')
def not_found():
    return 'Not found', 404

@app.route('/u/<username>/')
def profile(username):
    """Home page"""
    user = User.query.filter_by(username=username).first()
    if not user: return redirect('/404/')
    is_me = user.username == session.get('uid')
    things_cnt = Thing.get_user_things_cnt(user.id)
    offset = request.args.get('offset', type=int, default=0)
    limit = request.args.get('limit', type=int, default=100)
    things = Thing.get_recent_user_things(user.id, offset, limit)
    mark_error = session.pop('error.mark', '')
    return render('profile.html', username=username, user=user,
            things_cnt=things_cnt, things=things, is_me=is_me,
            mark_error=mark_error)

@app.route('/u/<username>/<q>/')
def query_user_marks(username, q):
    return q

@app.route('/mark/', methods=['POST'])
def mark():
    """Mark a new thing."""
    if not g.user:
        session['error.login'] = "You're not authorized. Please login."
        return redirect('/')
    user_id = g.user.id
    category_name = request.form.get('category')
    if not hasattr(Category, category_name):
        session['error.mark'] = "invalid category."
        return redirect(f'/u/{g.user.username}')
    category = getattr(Category, category_name)
    progress = Progress.done
    title = request.form.get('title')
    if not title:
        session['error.mark'] = "please provide a title."
        return redirect(f'/u/{g.user.username}')
    raw_tags = request.form.get('tags')
    if raw_tags:
        tags = [t.strip() for t in raw_tags.strip().split() if t.strip()]
    else:
        tags = []
    raw_shared = request.form.get('shared')
    shared = raw_shared == 'on'
    extended = {}
    time = datetime.utcnow()

    try:
        thing = Thing(user_id=user_id, category=category, title=title,
                shared=shared, tags=tags, extended=extended,
                time=time)
        db.session.add(thing)
        db.session.commit()
    except Exception as e:
        app.logger.error("error: %s", e)
        db.session.rollback()
        session['error.mark'] = 'database error. please try later.'
        return redirect(f'/u/{g.user.username}')

    return redirect(f'/u/{g.user.username}')

@app.route('/things/<int:id>/update/')
def update_thing_page(id):
    if not g.user:
        return jsonify({'code': 'not authenticated'}), 401

    thing = Thing.query.get(id)
    if not thing:
        return jsonify({'code': 'not_found'}), 404

    if thing.user_id != g.user.id:
        return jsonify({'code': 'not authorized'}), 403

    error = session.pop('error.mark', '')

    return render('update_thing.html', thing=thing, error=error)

@app.route('/things/<int:id>/update/', methods=['POST'])
def update_thing(id):
    if not g.user:
        return redirect('/')

    thing = Thing.query.get(id)
    if not thing:
        return 'not found', 404

    if thing.user_id != g.user.id:
        return 'not authorized', 403

    category_name = request.form.get('category')
    if not hasattr(Category, category_name):
        session['error.mark'] = 'invalid category'
        return redirect(request.referrer or '/')

    category = getattr(Category, category_name)

    title = request.form.get('title')
    if title and thing.title != title: thing.title = title

    raw_tags = request.form.get('tags')
    if raw_tags:
        thing.tags = [t.strip() for t in raw_tags.strip().split() if t.strip()]
    else:
        thing.tags = []

    thing.url = request.form.get('url')
    thing.shared = request.form.get('shared') == 'on'

    db.session.add(thing)

    try:
        db.session.commit()
    except Exception as e:
        app.logger.error("error: %s", e)
        db.session.rollback()
        session['error.mark'] = 'database error. please try later.'
        return redirect(request.referrer or '/')

    thing_note = ThingNote.query.get(thing.id)
    note_text = request.form.get('note')
    if not thing_note:
        thing_note = ThingNote(thing_id=thing.id, user_id=thing.user_id,
                text=note_text)
    else:
        thing_note.text = note_text

    db.session.add(thing_note)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error("error: %s", e)
        db.session.rollback()
        session['error.mark'] = 'database error. please try later.'
        return redirect(request.referrer or '/')

    session['error.mark'] = 'updated'
    return redirect(request.referrer)

@app.route('/login/', methods=['POST'])
def login():
    """Login"""
    username = request.form.get('username')
    password = request.form.get('password')
    if not username:
        session['error.login'] = 'missing username.'
        return redirect('/')
    if not password:
        session['error.login'] = 'missing password.'
        return redirect('/')
    user = User.query.filter_by(username=username).first()
    if not user:
        session['error.login'] = "user doesn't exist."
        return redirect('/')
    if not bcrypt.check_password_hash(user.password, password):
        session['error.login'] = "wrong password."
        return redirect('/')
    session['uid'] = user.username
    return redirect(f'/u/{username}/')

@app.route('/account/reset_password/')
def reset_password():
    """Lost password?"""
    return "Coming soon."

@app.route('/account/change_password/')
def change_password():
    """Change password"""
    return "Coming soon."

@app.route('/v1/things/<int:id>/share/', methods=['POST'])
def share_thing(id):
    """Share a thing"""
    if not g.user:
        return jsonify({'code': 'not authenticated'}), 401

    thing = Thing.query.get(id)
    if not thing:
        return jsonify({'code': 'not_found'}), 404

    if thing.user_id != g.user.id:
        return jsonify({'code': 'not authorized'}), 403

    thing.shared = not thing.shared
    db.session.add(thing)

    try:
        db.session.commit()
    except Exception as e:
        app.logger.error("error: %s", e)
        db.session.rollback()
        return jsonify({'code': 'db_error'}), 500

    return jsonify({'code': 'ok'}), 200

@app.route('/v1/things/<int:id>/', methods=['DELETE'])
def delete_thing(id):
    """Delete a thing
    """
    if not g.user:
        return jsonify({'code': 'not authenticated'}), 401

    thing = Thing.query.get(id)
    if not thing:
        return jsonify({'code': 'not_found'}), 404

    if thing.user_id != g.user.id:
        return jsonify({'code': 'not authorized'}), 403

    db.session.delete(thing)

    thing_note = ThingNote.query.get(id)
    if thing_note:
        db.session.delete(thing)

    try:
        db.session.commit()
    except Exception as e:
        app.logger.error("error: %s", e)
        db.session.rollback()
        return jsonify({'code', 'db_error'}), 500

    return jsonify({'code': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True)

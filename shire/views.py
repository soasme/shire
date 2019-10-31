import os
import json
from datetime import datetime

import stripe
from flask import (session, render_template, redirect,
                   current_app, jsonify, abort, request, g,
                   url_for, )

from shire.core import db, bcrypt, __DIR__
from shire.models import Thing, ThingNote, User, Category, Progress
from shire.errors import ShireError, ExistingError

def autoversion_filter(filename):
    fullpath = os.path.join(__DIR__.resolve(), filename[1:])
    try:
        timestamp = str(os.path.getmtime(fullpath))
        return f"{filename}?v={timestamp}"
    except OSError:
        return filename

def from_now(dt):
    diff = datetime.utcnow() - dt
    if diff.days > 0:
        return f'{diff.days} days ago'
    hours = diff.seconds // 3600
    if hours > 0:
        return f'{hours} hours ago'
    minutes = (diff.seconds//60)%60
    if minutes > 0:
        return f'{minutes} minutes ago'
    seconds = int(diff.total_seconds()%60)
    return f'{seconds} seconds ago'

def setup_globals():
    g.user = session.get('uid') and User.query.filter_by(username=session['uid']).first()

def index():
    error = session.pop('error.login', '')
    return render_template('index.html', error=error)

def guide(): return render_template('guide.html')
def about(): return render_template('about.html')
def privacy(): return render_template('privacy.html')
def terms_of_service(): return render_template('tos.html')
def faq(): return render_template('faq.html')

def logout():
    session.pop('uid', None)
    return redirect('/')

def explore():
    things = Thing.get_recent_all_things()
    tags = Thing.get_public_tagset(things)
    return render_template('explore.html', things=things, tags=tags)

def signup_page():
    if not current_app.config['SIGNUP_ENABLED']: return 'coming soon'
    error = session.pop('error.signup', '')
    return render_template("signup.html", error=error)

def signup():
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
        current_app.logger.error("error: %s", e)
        db.session.rollback()
        return redirect('/signup/')


def confirm_signup():
    uid = session.get('nuid')
    if not uid: return redirect('/')
    return render_template('confirm_signup.html')

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

def stripe_charge_success():
    if 'nuid' not in session: return redirect('/')
    session.pop('nuid', None)
    poll_completed_checkout_session(int(time()) - 7200)
    return render_template('signup_success.html')

def stripe_charge_cancel(): return 'cancel'

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
        current_app.logger.error("error: %s", e)
        return jsonify({'code': 'unable to construct event'}), 400

    data_object = data['object']
    if event_type == 'checkout.session.completed':
        items = data_object['display_items']
        customer = stripe.Customer.retrieve(data_object['customer'])
        if len(items) != 1 or not items[0].custom:
            return jsonify({'code': 'unknown items'}), 400

def charge():
    return jsonify(dict(request.form))

def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user: abort(404)
    if user.is_private and (not g.user or user.id != g.user.id): abort(403)
    is_me = user.username == session.get('uid')
    things_cnt = Thing.get_user_things_cnt(user.id)
    offset = request.args.get('offset', type=int, default=0)
    limit = max(100, request.args.get('limit', type=int, default=100))
    things = Thing.get_recent_user_things(user.id, offset, limit)
    tags = Thing.get_public_tagset(things)
    mark_error = session.pop('error.mark', '')
    return render_template('things.html',
            title=f'@{username}',
            things_cnt=things_cnt, things=things, is_me=is_me,
            mark_error=mark_error, tags=tags)

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

def thing_page(id):
    thing = Thing.query.get(id)
    if not thing: abort(404)
    owner = thing.user
    if not thing.is_visible_by(g.user): abort(403)
    if not thing.shared and g.user != owner: abort(403)
    return render_template('thing.html', thing=thing)

def update_thing_page(id):
    if not g.user:
        return jsonify({'code': 'not authenticated'}), 401

    thing = Thing.query.get(id)
    if not thing:
        return jsonify({'code': 'not_found'}), 404

    if thing.user_id != g.user.id:
        return jsonify({'code': 'not authorized'}), 403

    error = session.pop('error.mark', '')

    return render_template('update_thing.html', thing=thing, error=error)

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
        current_app.logger.error("error: %s", e)
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
        current_app.logger.error("error: %s", e)
        db.session.rollback()
        session['error.mark'] = 'database error. please try later.'
        return redirect(request.referrer or '/')

    return redirect(url_for('thing_page', id=thing.id))

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

def download_thing(id):
    if not g.user: return redirect('/')
    thing = Thing.query.get(id)
    if thing.user_id != g.user.id: abort(403)
    return jsonify(thing.to_simplejson())

def delete_thing_page(id):
    if not g.user: return redirect('/')
    thing = Thing.query.get(id)
    if thing.user_id != g.user.id: abort(403)
    return render_template('delete_thing.html', thing=thing)

def delete_thing(id):
    """Delete a thing
    """
    if not g.user: return redirect('/')
    thing = Thing.query.get(id)
    if not thing: abort(404)
    if thing.user_id != g.user.id: abort(403)

    db.session.delete(thing)
    thing_note = ThingNote.query.get(id)
    if thing_note:
        db.session.delete(thing)

    try:
        db.session.commit()
    except Exception as e:
        app.logger.error("error: %s", e)
        db.session.rollback()
        abort(500)

    return redirect(url_for('profile', username=g.user.username))

def filter_user_things_by_tag(username, tag):
    user = User.query.filter_by(username=username).first()
    if not user: abort(404)
    is_me = g.user == user
    if tag.startswith('.') and not is_me: abort(403)
    offset = request.args.get('offset', type=int, default=0)
    limit = max(100, request.args.get('limit', type=int, default=100))
    things = Thing.get_recent_user_tagged_things(user.id, [tag], offset, limit, include_private=is_me)
    tags = Thing.get_public_tagset(things)
    return render_template('things.html',
            title=f'@{username}',
            things_cnt=None, things=things, is_me=is_me,
            mark_error='', tags=tags)

def filter_global_things_by_tag(tag):
    offset = request.args.get('offset', type=int, default=0)
    limit = max(100, request.args.get('limit', type=int, default=100))
    things =  Thing.get_recent_tagged_things([tag], offset, limit)
    tags = Thing.get_public_tagset(things)
    return render_template('things.html',
            title=f'#{tag}',
            things_cnt=None, things=things, is_me=None,
            mark_error='', tags=tags)

def filter_user_things_by_category(username, category):
    user = User.query.filter_by(username=username).first()
    if not user: abort(404)
    is_me = g.user == user
    if not hasattr(Category, category): abort(404)
    offset = request.args.get('offset', type=int, default=0)
    limit = max(100, request.args.get('limit', type=int, default=100))
    category = getattr(Category, category)
    things = Thing.get_recent_user_categorized_things(user.id,
            category, offset, limit, include_private=is_me)
    tags = Thing.get_public_tagset(things)
    return render_template('things.html',
            title=f'@{username} ({category.name})',
            things_cnt=None, things=things, is_me=is_me,
            mark_error='', tags=tags)

def account():
    if not g.user: abort(403)
    error = session.pop('error.update_account', '')
    return render_template('profile.html', error=error)

def update_account():
    if not g.user: abort(403)
    is_private = request.form.get('is_private') == 'on'

    g.user.is_private = is_private

    try:
        db.session.add(g.user)
        db.session.commit()
        session['error.update_account'] = 'updated successfully!'
        return redirect(url_for('account'))
    except Exception as e:
        current_app.logger.error('update account error: %s', e)
        db.session.rollback()
        session['error.update_account'] = 'database error, please try later.'
        return redirect(url_for('account'))

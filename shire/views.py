import os
import json
from datetime import datetime

import stripe
from flask import (session, render_template, redirect,
                   current_app, jsonify, abort, request, g,
                   url_for, )
from flask_login import current_user, login_required

from shire.core import db, cache, __DIR__
from shire.models import Thing, ThingNote, User, Category
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

def auto_rollback(exception):
    if exception:
        db.session.rollback()
    db.session.remove()

def index():
    error = session.pop('error.login', '')
    users_total_count = User.get_total_count()
    return render_template('index.html', error=error, users_total_count=users_total_count)

def guide(): return render_template('guide.html')
def about(): return render_template('about.html')
def privacy(): return render_template('privacy.html')
def terms_of_service(): return render_template('tos.html')
def faq(): return render_template('faq.html')

def explore():
    things = Thing.get_recent_all_things()
    tags = Thing.get_public_tagset(things)
    return render_template('explore.html', things=things, tags=tags)

def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user: abort(404)
    if user.is_private and (current_user.is_anonymous or user.id != current_user.id): abort(403)
    is_me = (not current_user.is_anonymous) and user.username == current_user.username
    things_cnt = Thing.get_user_things_cnt(user.id)
    offset = request.args.get('offset', type=int, default=0)
    limit = max(20, request.args.get('limit', type=int, default=20))
    things = Thing.get_recent_user_things(user.id, offset, limit)
    tags = Thing.get_public_tagset(things)
    mark_error = session.pop('error.mark', '')
    return render_template('things.html',
            title=f'@{username}',
            things_cnt=things_cnt, things=things, is_me=is_me,
            offset=offset, limit=limit,
            mark_error=mark_error, tags=tags)

@login_required
def mark():
    """Mark a new thing."""
    user_id = current_user.id
    category_name = request.form.get('category')
    if not hasattr(Category, category_name):
        session['error.mark'] = "invalid category."
        return redirect(f'/u/{current_user.username}')
    category = getattr(Category, category_name)
    title = request.form.get('title')
    if not title:
        session['error.mark'] = "please provide a title."
        return redirect(f'/u/{current_user.username}')
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
        return redirect(f'/u/{current_user.username}')

    return redirect(f'/u/{current_user.username}')

def mark_page(id):
    thing = Thing.query.get(id)
    if not thing: abort(404)
    if not thing.is_visible_by(current_user): abort(403)
    return render_template('thing.html', thing=thing)

@login_required
def update_mark_page(id):
    thing = Thing.query.get(id)
    if not thing:
        return jsonify({'code': 'not_found'}), 404

    if thing.user_id != current_user.id:
        return jsonify({'code': 'not authorized'}), 403

    error = session.pop('error.mark', '')

    return render_template('update_mark.html', thing=thing, error=error)

@login_required
def update_mark(id):
    thing = Thing.query.get(id)
    if not thing:
        return 'not found', 404

    if thing.user_id != current_user.id:
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

    return redirect(url_for('mark_page', id=thing.id))

@login_required
def download_mark(id):
    thing = Thing.query.get(id)
    if thing.user_id != current_user.id: abort(403)
    return jsonify(thing.to_simplejson())

@login_required
def delete_mark_page(id):
    thing = Thing.query.get(id)
    if thing.user_id != current_user.id: abort(403)
    return render_template('delete_mark.html', thing=thing)

@login_required
def delete_mark(id):
    """Delete a thing
    """
    thing = Thing.query.get(id)
    if not thing: abort(404)
    if thing.user_id != current_user.id: abort(403)

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

    return redirect(url_for('profile', username=current_user.username))

def filter_user_things_by_tag(username, tag):
    user = User.query.filter_by(username=username).first()
    if not user: abort(404)
    is_me = current_user == user
    if tag.startswith('.') and not is_me: abort(403)
    offset = request.args.get('offset', type=int, default=0)
    limit = max(20, request.args.get('limit', type=int, default=20))
    things = Thing.get_recent_user_tagged_things(user.id, [tag], offset, limit, include_private=is_me)
    tags = Thing.get_public_tagset(things)
    return render_template('things.html',
            title=f'@{username}',
            things_cnt=None, things=things, is_me=is_me,
            offset=offset, limit=limit,
            mark_error='', tags=tags)

def filter_global_things_by_tag(tag):
    offset = request.args.get('offset', type=int, default=0)
    limit = max(20, request.args.get('limit', type=int, default=20))
    things =  Thing.get_recent_tagged_things([tag], offset, limit)
    tags = Thing.get_public_tagset(things)
    return render_template('things.html',
            title=f'#{tag}',
            offset=offset, limit=limit,
            things_cnt=None, things=things, is_me=None,
            mark_error='', tags=tags)

def filter_user_things_by_category(username, category):
    user = User.query.filter_by(username=username).first()
    if not user: abort(404)
    is_me = current_user == user
    if not hasattr(Category, category): abort(404)
    offset = request.args.get('offset', type=int, default=0)
    limit = max(20, request.args.get('limit', type=int, default=20))
    category = getattr(Category, category)
    things = Thing.get_recent_user_categorized_things(user.id,
            category, offset, limit, include_private=is_me)
    tags = Thing.get_public_tagset(things)
    return render_template('things.html',
            title=f'@{username} ({category.name})',
            offset=offset, limit=limit,
            things_cnt=None, things=things, is_me=is_me,
            mark_error='', tags=tags)

@login_required
def account():
    error = session.pop('error.update_account', '')
    return render_template('profile.html', error=error)

@login_required
def update_account():
    is_private = request.form.get('is_private') == 'on'

    current_user.is_private = is_private

    try:
        db.session.add(current_user)
        db.session.commit()
        session['error.update_account'] = 'updated successfully!'
        return redirect(url_for('account'))
    except Exception as e:
        current_app.logger.error('update account error: %s', e)
        db.session.rollback()
        session['error.update_account'] = 'database error, please try later.'
        return redirect(url_for('account'))

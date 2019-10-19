import enum
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from decouple import config
from flask import Flask, redirect, request, session, g, jsonify
from flask import render_template as render
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.types import JSON, Enum

load_dotenv(find_dotenv())

app = Flask(__name__)
app.config.update({
    'SITE_NAME': config('SITE_NAME', default='?'),
    'BLOG_URL': 'https://enqueuezero.com',
    'SECRET_KEY': config('SECRET_KEY'),
    'SQLALCHEMY_DATABASE_URI': config('DATABASE_URL'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': config('SQLALCHEMY_TRACK_MODIFICATIONS', cast=bool),
    'ANNUAL_FEE': config('ANUAL_FEE', cast=int, default=10),
})

db = SQLAlchemy()
db.init_app(app)

bcrypt = Bcrypt()
bcrypt.init_app(app)

class Progress(enum.Enum):
    """A progress enum indicating if user has used the thing.
    Currently, we only support done.
    """
    todo = 1
    doing = 2
    done = 3

class Category(enum.Enum):
    book = 1
    movie = 2
    tvshow = 3
    album = 4
    place = 5
    game = 6
    event = 7

    @property
    def display_name(self):
        if self.name == 'tvshow': return 'TV show'
        else: return self.name

class User(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    nickname = db.Column(db.String(128))
    email = db.Column(db.String(256), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @classmethod
    def new(self, username, email, nickname, password, autocommit=True):
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email,
                nickname=nickname, password=password_hash)
        db.session.add(user)
        if autocommit: db.session.commit()
        return user

class Charge(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    subscription_id = db.Column(db.String(128), nullable=False)
    fee = db.Column(db.Integer, nullable=False)
    plan_start = db.Column(db.DateTime)
    plan_end = db.Column(db.DateTime)

class Thing(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    category = db.Column(Enum(Category), nullable=False)
    title = db.Column(db.String(512), nullable=False)
    url = db.Column(db.String(2048), nullable=True, default='')
    extended = db.Column(JSON, nullable=False)
    shared = db.Column(db.Boolean, nullable=False, default=True)
    progress = db.Column(Enum(Progress), nullable=False, default=Progress.done)
    tags = db.Column(JSON, nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def user(self):
        return User.query.get(self.user_id)

    @property
    def note(self):
        _note = ThingNote.query.get(self.id)
        if not _note: return
        return _note

    @property
    def reference(self):
        if not self.url:
            q = (self.category.display_name.replace(' ', '+') + '+' +
                    self.title.replace(' ', '+'))
            return f'https://duckduckgo.com/?q={q}'
        return self.url

    @classmethod
    def get_recent_all_things(cls, limit=20):
        return cls.query.filter_by(shared=True).order_by(cls.time.desc()).limit(limit).all()

    @classmethod
    def get_recent_user_things(cls, user_id, offset, limit):
        return (Thing.query.filter_by(user_id=user_id)
                .order_by(cls.time.desc()).offset(offset).limit(limit).all())

    @classmethod
    def get_user_things_cnt(cls, user_id):
        return Thing.query.filter_by(user_id=user_id).count()

    def to_simplejson(self):
        return dict(id=self.id, user_id=user_id, category=self.category,
                title=self.title, extended=self.extended, shared=self.shared,
                url=self.url, progress=self.progress, tags=self.tags, time=self.time)

class ThingNote(db.Model):
    thing_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    shared = db.Column(db.Boolean, default=True)

app.jinja_env.globals['Category'] = Category
app.jinja_env.globals['Progress'] = Progress

@app.before_request
def setup_g():
    if session.get('uid'):
        g.user = User.query.filter_by(username=session['uid']).first()
    else:
        g.user = None

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
    return "Coming soon."

@app.route('/privacy/')
def privacy():
    return "Coming soon."

@app.route('/tos/')
def terms_of_service():
    return "Coming soon."

@app.route('/faq/')
def faq():
    return "Coming soon."

@app.route('/signup/')
def signup():
    """Create an account"""
    return "Coming soon."

@app.route('/signup/confirm/')
def confirm_signup():
    """Pick a payment"""

@app.route('/charge')
def charge():
    """Charge"""

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

@app.route('/v1/things', methods=['POST'])
def add_thing():
    """Mark a thing.

    | argument | type  | comment |
    | -------- | ----- | ------- |
    | category | str   | Type of the thing, choices: book, movie, album, etc |
    | title    | str   | Title of the thing |
    | extended | object | Metadata of the thing |
    | progress | enum  | Choices: todo, doing, done |
    | tags     | [str] | List of up to 100 tags |
    | time     | datetime | Creation time |
    | shared   | bool  | Whether to make it public |
    """
    pass

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

@app.route('/v1/things/all', methods=['GET'])
def get_things():
    """Return all things in user's account, filter by tag.

    | argument | type   | comment |
    | -------- | ------ | ------- |
    | type     | str    | return only this type of things |
    | tag      | [str]  | List of up to 3 tags |
    | extended | obj    | Common attributes among user's things |
    | start    | int    | offset value, default is 0 |
    | limit    | int    | number of results to result, default is 20, maximum is 200 |
    | since    | datetime | return only results created before this time |
    | until    | datetime | return only results created after this time |
    """

if __name__ == '__main__':
    app.run(debug=True)

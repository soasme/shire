import enum
import jinja2
from functools import reduce
from operator import add
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import JSON, Enum
from sqlalchemy.dialects.postgresql.json import JSONB

from shire.core import db, bcrypt

class Category(enum.Enum):
    book = 1
    movie = 2
    tvshow = 3
    album = 4
    place = 5
    game = 6
    event = 7
    paper = 8
    concept = 9
    software = 10

    @property
    def display_name(self):
        if self.name == 'tvshow': return 'TV show'
        else: return self.name

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    email = db.Column(db.String(256), nullable=True, unique=True)
    password = db.Column(db.String(128), nullable=False)
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    email_confirmed_at = db.Column(db.DateTime())
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @classmethod
    def new(cls, username, email, password):
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = cls(username=username, email=email, password=password_hash)
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except IntegrityError:
            db.session.rollback()
            raise ValueError({'email': email, 'username': username})

class UserSubscription(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    customer = db.Column(db.String(64))
    subscription = db.Column(db.String(64))
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Thing(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    category = db.Column(Enum(Category), nullable=False)
    title = db.Column(db.String(512), nullable=False)
    url = db.Column(db.String(2048), nullable=True, default='')
    extended = db.Column(JSON, nullable=False)
    shared = db.Column(db.Boolean, nullable=False, default=True)
    tags = db.Column(JSONB, nullable=False)
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
    def search_keywords(self):
        if self.category == Category.concept: return self.title.replace(' ', '+')
        return ('+'.join([self.category.display_name, self.title])).replace(' ', '+')

    @property
    def reference(self):
        if not self.url: return 'https://duckduckgo.com/?q=' + self.search_keywords
        return self.url

    @classmethod
    def get_recent_all_things(cls, limit=20):
        return cls.query.filter_by(shared=True).order_by(cls.time.desc()).limit(limit).all()

    @classmethod
    def get_recent_user_things(cls, user_id, offset, limit):
        return (Thing.query.filter_by(user_id=user_id)
                .order_by(cls.time.desc()).offset(offset).limit(limit).all())

    @classmethod
    def get_recent_user_categorized_things(cls, user_id, category, offset, limit, include_private=False):
        base_query = Thing.query.filter_by(user_id=user_id, category=category)
        if not include_private:
            base_query = base_query.filter_by(shared=True)
        return base_query.order_by(cls.time.desc()).offset(offset).limit(limit).all()

    @classmethod
    def get_recent_user_tagged_things(cls, user_id, tags, offset, limit, include_private=False):
        base_query = Thing.query.filter_by(user_id=user_id).filter(Thing.tags.contains(tags))
        if not include_private:
            base_query = base_query.filter_by(shared=True)
        return base_query.order_by(cls.time.desc()).offset(offset).limit(limit).all()

    @classmethod
    def get_recent_tagged_things(cls, tags, offset, limit):
        return Thing.query.filter_by(shared=True).filter(Thing.tags.contains(tags)).all()

    @classmethod
    def get_user_things_cnt(cls, user_id):
        return Thing.query.filter_by(user_id=user_id).count()

    def to_simplejson(self):
        return dict(id=self.id, user_id=self.user_id, category=self.category.name,
                title=self.title, extended=self.extended, shared=self.shared,
                url=self.url, tags=self.tags, time=self.time.isoformat(),
                note=(self.note and self.note.text or ''))

    def is_visible_by(self, user):
        is_anonymous = bool(hasattr(user, 'is_anonymous') and user.is_anonymous)
        if is_anonymous:
            return self.shared
        if self.user.is_private or not self.shared:
            return self.user_id == user.id or f'.@{user.username}' in self.tags
        return True

    @classmethod
    def get_public_tagset(cls, things):
        tags = [([tag for tag in t.tags if not tag.startswith('.')] or []) for t in things]
        if not tags: return set()
        return set(reduce(add, tags))

class ThingNote(db.Model):
    thing_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    shared = db.Column(db.Boolean, default=True)

    @property
    def html(self):
        if not self.text: return ''
        return '<br>'.join([jinja2.escape(s) for s in self.text.split('\n')])

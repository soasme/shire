from functools import wraps

import stripe
from flask import abort
from werkzeug import import_string
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from .core import bp

class CustomerManager:

    def __init__(self, app=None, db=None, cache=None):
        if app is not None:
            self.init_app(app, db, cache)

    def init_app(self, app, db, cache):
        self.app = app
        self.app.customer_manager = self
        self.db = db
        self.cache = cache
        self.__customer_class = app.config['CUSTOMER_CLASS']

        from .views import bp
        self.app.register_blueprint(bp, url_prefix='/customer/')

    @property
    def customer_class(self):
        if hasattr(self, '_customer_class'): return self._customer_class
        self._customer_class = import_string(self.__customer_class)
        return self._customer_class

    def new_customer(self, customer_id, email, extended, subscribed):
        """Create a customer record.
        """
        customer = self.customer_class(
            customer_id=customer_id,
            email=email,
            extended=extended,
            subscribed=subscribed,
        )
        self.db.session.add(customer)
        try:
            self.db.session.commit()
        except IntegrityError:
            self.db.session.rollback()
            return self.get_customer_by_id(customer_id)

    def update_customer(self, customer_id, email=None, extended=None, subscribed=None):
        """Update a customer record.
        """
        customer = self.customer_class.query.filter_by(customer_id=customer_id).first()
        if not customer:
            return
        if email is not None:
            customer.email = email
        if extended is not None:
            customer.extended = extended
        if subscribed is not None:
            customer.subscribed = subscribed
        self.db.session.add(customer)
        self.db.session.commit()

    def delete_customer(self, customer_id):
        """Delete a customer record.
        """
        customer = self.customer_class.query.filter_by(customer_id=customer_id).first()
        if not customer: return
        self.db.session.remove(customer)
        self.db.session.commit()

    def get_customers(self, offset=0, limit=100):
        """Get a list of customer records."""
        return self.customer_class.query.order_by(self.customer_class.id.desc()).offset(offset).limit(limit)

    def get_customer_by_id(self, customer_id):
        return self.customer_class.query.filter_by(customer_id=customer_id).first()

    def get_customer_by_email(self, email):
        return self.customer_class.query.filter_by(email=email).first()

    def verify_customer(self, customer_id):
        """Verify if customer is up-to-dated.

        This method will try retrieving a customer object and update customer record.
        """
        customer = stripe.Customer.retrieve(customer_id)
        if not customer:
            return self.delete_customer(customer_id)
        if not self.get_customer_by_id(customer_id):
            return self.new_customer(customer_id, customer['email'], customer['metadata'])
        return self.update_customer(customer_id, customer['email'], customer['metadata'])

    def require_customer(self):
        """Decorator for view function. Only accessible for customer users."""
        def deco(f):
            @wraps(f)
            def _(*args, **kwargs):
                if current_user.is_anonymous:
                    abort(403)
                email = current_user.email
                customer = self.get_customer_by_email(email)
                if not customer:
                    raise Exception('require to be a customer')
                return f(*args, **kwargs)
            return _
        return deco

    def handle_customer_created(self, customer):
        customer_id = customer['id']
        customer_ins = self.get_customer_by_id(customer_id)
        assert customer_ins is None, f'customer {customer_id} should not exist.'
        return self.new_customer(
            customer_id=customer_id,
            email=customer['email'],
            extended=customer['metadata'],
            subscribed=customer['subscriptions']['total_count'] != 0,
        )

    def handle_customer_deleted(self, customer):
        self.delete_customer(customer['id'])

    def handle_customer_updated(self, customer):
        customer_id = customer['id']

        if customer.get('deleted'):
            return self.delete_customer(customer_id)

        customer_ins = self.get_customer_by_id(customer_id)
        if not customer_ins:
            return self.new_customer(
                customer_id=customer['id'],
                email=customer['email'],
                extended=customer['metadata'],
                subscribed=customer['subscriptions']['total_count'] != 0,
            )

        return self.update_customer(
            customer_id=customer['id'],
            email=customer['email'],
            extended=customer['metadata'],
            subscribed=customer['subscriptions']['total_count'] != 0,
        )

    def handle_customer_subscription_updated(self, subscription):
        if isinstance(subscription['customer'], dict):
            customer_id = subscription['customer']['id']
        else:
            customer_id = subscription['customer']
        customer = stripe.Customer.retrieve(customer_id)
        self.handle_customer_updated(customer)

    def handle_customer_subscription_created(self, subscription):
        self.handle_customer_subscription_updated(subscription)

    def handle_customer_subscription_deleted(self, subscription):
        self.handle_customer_subscription_updated(subscription)

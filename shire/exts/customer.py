from functools import wraps

import stripe
from flask import abort
from werkzeug import import_string
from flask_login import current_user


class CustomerManager:

    def __init__(self, app=None, db=None, cache=None):
        if app is not None:
            self.init_app(app, db, cache)

    def init_app(self, app, db, cache):
        app.extensions['customer'] = self
        self.app = app
        self.db = db
        self.cache = cache
        self.__customer_class = app.config['CUSTOMER_CLASS']

    @property
    def customer_class(self):
        if hasattr(self, '_customer_class'): return self._customer_class
        self._customer_class = import_string(self._customer_class)
        return self._customer_class

    def new_customer(self, customer_id, email, extended):
        """Create a customer record.
        """
        customer = self.customer_class(
            customer_id=customer_id,
            email=email,
            extended=extended
        )
        self.db.session.add(customer)
        self.db.session.commit()

    def update_customer(self, customer_id, email, extended):
        """Update a customer record.
        """
        customer = self.customer_class.query.filter_by(customer_id=customer_id)
        if not customer: return
        customer.email = email
        customer.extended = extended
        self.db.session.add(customer)
        self.db.session.commit()

    def delete_customer(self, customer_id):
        """Delete a customer record.
        """
        customer = self.customer_class.query.filter_by(customer_id=customer_id)
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

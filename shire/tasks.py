"""
WARNING: The tasks defined in this module is supposed to be idempotent.
It should be safe to re-run these tasks at any time.
"""
import sys

import stripe
from loguru import logger
from flask import current_app, url_for

from shire.core import db, mail, celery
from shire.models import User, Customer, SubscriptionStatus, CustomerSubscription

@celery.task
def ping():
    sys.stderr.write("PING SUCCESS")
    sys.stderr.flush()
    return 'PONG'

@celery.task
def sync_stripe_session(session):
    session_id = session['id']
    customer_id = session['customer']
    assert customer_id, 'no customer id in session'

    stripe_customer = stripe.Customer.retrieve(customer_id)
    if stripe_customer.get('deleted'):
        logger.info("Session({}) customer doesn't exist anymore: {}. Ignore sync this stripe session.", session_id, customer_id)
        return

    user_email = stripe_customer['email']
    assert user_email, 'no email detected.'

    subscription_id = session['subscription']
    assert subscription_id, 'no subscription id in session'

    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
    status = getattr(SubscriptionStatus, stripe_subscription['status'])

    customer = Customer(
        id=customer_id,
        email=user_email,
        payload=stripe_customer
    )
    subscription = CustomerSubscription(
        id=subscription_id,
        customer_id=subscription_id,
        status=status,
        payload=stripe_subscription
    )
    db.session.add(customer)
    db.session.add(subscription)
    db.session.commit()
    # TODO: set a key in cache for validation.

def create_account(session):
    email = session['email']
    username = session['username']
    password = session['password']
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    user = User.query.filter(User.email==email | User.username==username).first()
    if user:
        raise ValueError('Re-creating account: (email|username)')

    user = User(username=username, email=email, password=password_hash)

    try:
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError:
        db.session.rollback()
        raise ValueError('Re-creating account: (email|username)')

@celery.task
def poll_payments(window=60*60):
    from shire.exts.sub import stripe_checkout_session_completed_poll
    stripe_checkout_session_completed_poll(window)
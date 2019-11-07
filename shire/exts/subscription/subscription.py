"""
This module handles the after-the-payment when customer successfully completes their
payment and initiates a subscription using Checkout.

See <https://stripe.com/docs/payments/checkout/fulfillment>.
"""

import stripe
from blinker import Namespace
from flask import request, abort

subscription_signals = Namespace()
checkout_session_completed = subscription_signals.signal('checkout.session.completed')

def stripe_checkout_session_completed_webhook():
    """Called by stripe server.

    It passively waits stripe events and handle them by per request.

    https://stripe.com/docs/payments/checkout/fulfillment#webhooks
    """
    payload = request.body
    signature = request.headers.get('stripe-signature')
    secret = current_app.config['STRIPE_WEBHOOK_SECRET']

    try:
        event = stripe.Webhook.construct_event(payload, signature, secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        abort(400)

    if event['type'] == 'checkout.session.completed':
        checkout_session_completed.send(event['data']['object'])

    return jsonify({'received': True})


def stripe_checkout_session_completed_poll(window=60*60):
    """Called by crontab.

    It actively poll stripe events and handle them in batch.

    https://stripe.com/docs/payments/checkout/fulfillment#polling
    """
    events = stripe.Event.list(type = 'checkout.session.completed', created = {
        'gte': int(time.time() - window),
    })
    for event in events.auto_paging_iter():
        session = event['data']['object']
        checkout_session_completed.send(event['data']['object'])

class Subscription:

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.extensions['subscription'] = app

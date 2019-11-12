"""
This module handles the after-the-payment when customer successfully completes their
payment and initiates a subscription using Checkout.

See <https://stripe.com/docs/payments/checkout/fulfillment>.

Tips:

1. The consumer of this extension should provide your own implementation when
   a checkout.session.completed event triggers.

Example::

    @checkout_session_completed.connect
    def do_something(session):
        print(session)
        send_registration_email.delay(session)
        # ...

2. The webhook can be enabled by specifying `SUBSCRIPTION_WEBHOOK_ENABLED`.
   By default, it's false.

3. The webhook url can be defined by specifying `SUBSCRIPTION_WEBHOOK_URL`.
   By default, it's /subscription/hook/. It works only when
   SUBSCRIPTION_WEBHOOK_ENABLED is true.

4. The cli can be enabled by specifying `SUBSCRIPTION_CLI_ENABLED`.
   By default, it's false.
   You can run `flask subscription poll` to sync and process recent events.

5. The extension does not guarantee the times of the event being processed.
   Please make sure there will not be side-effects when the event is processed
   multiple times.
"""

from time import time

import stripe
from blinker import Namespace
import click
from flask import request, abort
from flask.cli import AppGroup

subscription_cli = AppGroup('subscription')
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
        checkout_session_completed.send(session=event['data']['object'])

    return jsonify({'received': True})


def stripe_checkout_session_completed_poll(window=60*60):
    """Called by crontab or periodically cron-like beater.

    It actively polls stripe events and handles them in a batch.

    https://stripe.com/docs/payments/checkout/fulfillment#polling
    """
    events = stripe.Event.list(type = 'checkout.session.completed', created = {
        'gte': int(time() - window),
    })
    for event in events.auto_paging_iter():
        session = event['data']['object']
        checkout_session_completed.send(session=event['data']['object'])

@subscription_cli.command('poll')
@click.option('--window', '-w', type=int, default=60*60)
def cli_poll(window):
    """Poll recent checkout.session.complete events from Stripe."""
    stripe_checkout_session_completed_poll(window)

class Subscription:
    """Subscription extension.

    It supports handling after-the-payment events from Stripe.
    """

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.extensions['sub'] = self

        if app.config.get('SUBSCRIPTION_WEBHOOK_ENABLED'):
            webhook_url = app.config.get('SUBSCRIPTION_WEBHOOK_URL', '/subscription/hook/')
            app.add_url_rule(
                webhook_url,
                'stripe_checkout_session_completed_webhook',
                stripe_checkout_session_completed_webhook
            )

        if app.config.get('SUBSCRIPTION_CLI_ENABLED'):
            app.cli.add_command(subscription_cli)

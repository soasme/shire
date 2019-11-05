"""
This module handles the after-the-payment when customer successfully completes their
payment and initiates a subscription using Checkout.
"""

import stripe


def webhook():
    """Called by stripe server.

    It passively waits stripe events and handle them by per request.

    https://stripe.com/docs/payments/checkout/fulfillment#webhooks
    """
    pass


def poll():
    """Called by crontab.

    It actively poll stripe events and handle them in batch.

    https://stripe.com/docs/payments/checkout/fulfillment#polling
    """

class Subscription:

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.extensions['subscription'] = app


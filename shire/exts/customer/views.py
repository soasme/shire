import stripe
from flask import abort, request, current_app, jsonify, flash, redirect

from .core import bp

@bp.teardown_request
def auto_rollback(exc):
    if exc:
        current_app.db.session.rollback()
    current_app.db.session.remove()

EVENT_TYPES_WHITELIST = {
    'customer.created',
    'customer.updated',
    'customer.deleted',
    'customer.subscription.created',
    'customer.subscription.deleted',
    'customer.subscription.updated',
}

@bp.route('/success/')
def success():
    flash('Subscribed done.')
    return redirect('/')

@bp.route('/canceled/')
def canceled():
    flash('Subscription canceled.')
    return redirect('/')

@bp.route('/hook/', methods=['POST'])
def hook():
    payload = request.data
    signature = request.headers.get('stripe-signature')
    secret = current_app.config['STRIPE_WEBHOOK_SECRET_KEY']

    try:
        event = stripe.Webhook.construct_event(payload, signature, secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        abort(400)

    if event['type'] not in EVENT_TYPES_WHITELIST:
        return jsonify({'received': True})

    manager = current_app.customer_manager

    if event['type'] == 'customer.created':
        manager.handle_customer_created(event['data']['object'])

    elif event['type'] == 'customer.deleted':
        manager.handle_customer_deleted(event['data']['object'])

    elif event['type'] == 'customer.updated':
        manager.handle_customer_updated(event['data']['object'])

    elif event['type'] == 'customer.subscription.created':
        manager.handle_customer_subscription_created(event['data']['object'])

    elif event['type'] == 'customer.subscription.deleted':
        manager.handle_customer_subscription_deleted(event['data']['object'])

    elif event['type'] == 'customer.subscription.updated':
        manager.handle_customer_subscription_updated(event['data']['object'])

    return jsonify({'received': True})

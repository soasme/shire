import stripe
from flask import abort, request, current_app, jsonify

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
}

@bp.route('/hook/', methods=['POST'])
def hook():
    payload = request.data
    signature = request.headers.get('stripe-signature')
    secret = current_app.config['STRIPE_WEBHOOK_SECRET']

    try:
        event = stripe.Webhook.construct_event(payload, signature, secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        abort(400)

    if event['type'] not in EVENT_TYPES_WHITELIST:
        return jsonify({'received': True})

    manager = current_app.customer_manager

    if event['type'] == 'customer.created':
        customer = event['data']['object']
        manager.new_customer(
            customer_id=customer['id'],
            email=customer['email'],
            extended=customer['metadata'],
            subscribed=customer['subscriptions']['total_count'] != 0,
        )

    elif event['type'] == 'customer.deleted':
        customer = event['data']['object']
        manager.delete_customer(customer['id'])

    elif event['type'] == 'customer.updated':
        customer = event['data']['object']
        manager.update_customer(
            customer_id=customer['id'],
            email=customer['email'],
            extended=customer['metadata'],
            subscribed=customer['subscriptions']['total_count'] != 0,
        )

    elif event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        customer = subscription['customer']
        manager.update_customer(customer_id=customer, subscribed=True)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer = subscription['customer']
        # TODO: should retrieve a customer and validate if total_count != 0.
        manager.update_customer(customer_id=customer, subscribed=False)

    return jsonify({'received': True})

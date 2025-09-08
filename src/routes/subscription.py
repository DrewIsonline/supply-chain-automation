from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
import json

subscription_bp = Blueprint('subscription', __name__)
logger = logging.getLogger(__name__)

# In-memory storage for demo (replace with database in production)
subscriptions = {}
subscription_plans = {
    'basic': {
        'plan_id': 'basic',
        'name': 'Basic Plan',
        'price': 29.99,
        'currency': 'USD',
        'interval': 'month',
        'features': [
            'Up to 100 products',
            'Basic inventory tracking',
            'Email alerts',
            'Standard support'
        ],
        'limits': {
            'products': 100,
            'api_calls_per_month': 10000,
            'webhooks': 5
        }
    },
    'professional': {
        'plan_id': 'professional',
        'name': 'Professional Plan',
        'price': 79.99,
        'currency': 'USD',
        'interval': 'month',
        'features': [
            'Up to 1000 products',
            'Advanced inventory automation',
            'Supplier management',
            'Auto-reorder workflows',
            'Demand forecasting',
            'Priority support'
        ],
        'limits': {
            'products': 1000,
            'api_calls_per_month': 50000,
            'webhooks': 25
        }
    },
    'enterprise': {
        'plan_id': 'enterprise',
        'name': 'Enterprise Plan',
        'price': 199.99,
        'currency': 'USD',
        'interval': 'month',
        'features': [
            'Unlimited products',
            'Full supply chain automation',
            'Advanced analytics',
            'Custom integrations',
            'Dedicated support',
            'SLA guarantee'
        ],
        'limits': {
            'products': -1,  # Unlimited
            'api_calls_per_month': -1,  # Unlimited
            'webhooks': -1  # Unlimited
        }
    }
}

@subscription_bp.route('/status', methods=['GET'])
def subscription_status():
    """Get subscription system status"""
    return jsonify({
        'subscription_system': 'active',
        'total_subscriptions': len(subscriptions),
        'active_subscriptions': len([s for s in subscriptions.values() if s['status'] == 'active']),
        'available_plans': list(subscription_plans.keys())
    })

@subscription_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans"""
    return jsonify({
        'plans': list(subscription_plans.values())
    })

@subscription_bp.route('/plans/<plan_id>', methods=['GET'])
def get_plan_details(plan_id):
    """Get specific plan details"""
    if plan_id not in subscription_plans:
        return jsonify({'error': 'Plan not found'}), 404
    
    return jsonify(subscription_plans[plan_id])

@subscription_bp.route('/subscribe', methods=['POST'])
def create_subscription():
    """Create new subscription (integrate with Stripe)"""
    try:
        data = request.get_json()
        
        required_fields = ['user_id', 'plan_id', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        plan_id = data['plan_id']
        if plan_id not in subscription_plans:
            return jsonify({'error': 'Invalid plan ID'}), 400
        
        user_id = data['user_id']
        
        # Check if user already has an active subscription
        existing_sub = None
        for sub in subscriptions.values():
            if sub['user_id'] == user_id and sub['status'] == 'active':
                existing_sub = sub
                break
        
        if existing_sub:
            return jsonify({'error': 'User already has an active subscription'}), 400
        
        subscription_id = f"sub_{datetime.utcnow().timestamp()}"
        plan = subscription_plans[plan_id]
        
        # In production, integrate with Stripe here
        stripe_subscription_id = f"stripe_sub_{subscription_id}"
        
        subscription = {
            'subscription_id': subscription_id,
            'stripe_subscription_id': stripe_subscription_id,
            'user_id': user_id,
            'plan_id': plan_id,
            'plan_name': plan['name'],
            'price': plan['price'],
            'currency': plan['currency'],
            'interval': plan['interval'],
            'status': 'active',
            'created_date': datetime.utcnow().isoformat(),
            'current_period_start': datetime.utcnow().isoformat(),
            'current_period_end': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'trial_end': data.get('trial_end', ''),
            'payment_method': data['payment_method'],
            'features': plan['features'],
            'limits': plan['limits'],
            'usage': {
                'products': 0,
                'api_calls_this_month': 0,
                'webhooks': 0
            }
        }
        
        subscriptions[subscription_id] = subscription
        
        logger.info(f"Created subscription: {subscription_id} for user: {user_id}")
        
        return jsonify({
            'success': True,
            'subscription': subscription
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/subscriptions/<subscription_id>', methods=['GET'])
def get_subscription(subscription_id):
    """Get subscription details"""
    if subscription_id not in subscriptions:
        return jsonify({'error': 'Subscription not found'}), 404
    
    return jsonify(subscriptions[subscription_id])

@subscription_bp.route('/subscriptions/user/<user_id>', methods=['GET'])
def get_user_subscription(user_id):
    """Get user's active subscription"""
    user_subscription = None
    
    for subscription in subscriptions.values():
        if subscription['user_id'] == user_id and subscription['status'] == 'active':
            user_subscription = subscription
            break
    
    if not user_subscription:
        return jsonify({'error': 'No active subscription found for user'}), 404
    
    return jsonify(user_subscription)

@subscription_bp.route('/subscriptions/<subscription_id>/cancel', methods=['POST'])
def cancel_subscription(subscription_id):
    """Cancel subscription"""
    try:
        if subscription_id not in subscriptions:
            return jsonify({'error': 'Subscription not found'}), 404
        
        subscription = subscriptions[subscription_id]
        
        if subscription['status'] != 'active':
            return jsonify({'error': 'Subscription is not active'}), 400
        
        data = request.get_json() or {}
        
        # In production, cancel with Stripe
        subscription['status'] = 'cancelled'
        subscription['cancelled_date'] = datetime.utcnow().isoformat()
        subscription['cancellation_reason'] = data.get('reason', '')
        
        logger.info(f"Cancelled subscription: {subscription_id}")
        
        return jsonify({
            'success': True,
            'subscription': subscription
        })
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/subscriptions/<subscription_id>/upgrade', methods=['POST'])
def upgrade_subscription(subscription_id):
    """Upgrade subscription plan"""
    try:
        if subscription_id not in subscriptions:
            return jsonify({'error': 'Subscription not found'}), 404
        
        data = request.get_json()
        new_plan_id = data.get('new_plan_id')
        
        if not new_plan_id or new_plan_id not in subscription_plans:
            return jsonify({'error': 'Invalid new plan ID'}), 400
        
        subscription = subscriptions[subscription_id]
        old_plan = subscription_plans[subscription['plan_id']]
        new_plan = subscription_plans[new_plan_id]
        
        if new_plan['price'] <= old_plan['price']:
            return jsonify({'error': 'New plan must be higher tier'}), 400
        
        # In production, handle prorated billing with Stripe
        subscription['plan_id'] = new_plan_id
        subscription['plan_name'] = new_plan['name']
        subscription['price'] = new_plan['price']
        subscription['features'] = new_plan['features']
        subscription['limits'] = new_plan['limits']
        subscription['upgraded_date'] = datetime.utcnow().isoformat()
        
        logger.info(f"Upgraded subscription: {subscription_id} to {new_plan_id}")
        
        return jsonify({
            'success': True,
            'subscription': subscription
        })
        
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/subscriptions/<subscription_id>/usage', methods=['GET'])
def get_subscription_usage(subscription_id):
    """Get subscription usage statistics"""
    if subscription_id not in subscriptions:
        return jsonify({'error': 'Subscription not found'}), 404
    
    subscription = subscriptions[subscription_id]
    usage = subscription['usage']
    limits = subscription['limits']
    
    usage_stats = {
        'subscription_id': subscription_id,
        'current_usage': usage,
        'limits': limits,
        'usage_percentages': {},
        'warnings': []
    }
    
    # Calculate usage percentages
    for key, limit in limits.items():
        if limit > 0:  # Not unlimited
            current = usage.get(key, 0)
            percentage = (current / limit) * 100
            usage_stats['usage_percentages'][key] = round(percentage, 1)
            
            # Add warnings for high usage
            if percentage > 90:
                usage_stats['warnings'].append(f"{key} usage is at {percentage:.1f}%")
            elif percentage > 75:
                usage_stats['warnings'].append(f"{key} usage is at {percentage:.1f}%")
    
    return jsonify(usage_stats)

@subscription_bp.route('/subscriptions/<subscription_id>/usage', methods=['POST'])
def update_subscription_usage(subscription_id):
    """Update subscription usage (called by system)"""
    try:
        if subscription_id not in subscriptions:
            return jsonify({'error': 'Subscription not found'}), 404
        
        data = request.get_json()
        subscription = subscriptions[subscription_id]
        
        # Update usage counters
        if 'products' in data:
            subscription['usage']['products'] = data['products']
        
        if 'api_calls' in data:
            subscription['usage']['api_calls_this_month'] += data['api_calls']
        
        if 'webhooks' in data:
            subscription['usage']['webhooks'] = data['webhooks']
        
        # Check limits
        limits_exceeded = check_subscription_limits(subscription)
        
        return jsonify({
            'success': True,
            'usage': subscription['usage'],
            'limits_exceeded': limits_exceeded
        })
        
    except Exception as e:
        logger.error(f"Error updating subscription usage: {str(e)}")
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        # In production, verify webhook signature
        data = request.get_json()
        event_type = data.get('type')
        
        if event_type == 'invoice.payment_succeeded':
            # Handle successful payment
            subscription_id = data['data']['object']['subscription']
            handle_payment_success(subscription_id)
            
        elif event_type == 'invoice.payment_failed':
            # Handle failed payment
            subscription_id = data['data']['object']['subscription']
            handle_payment_failure(subscription_id)
            
        elif event_type == 'customer.subscription.deleted':
            # Handle subscription cancellation
            subscription_id = data['data']['object']['id']
            handle_subscription_cancellation(subscription_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/billing/invoices/<user_id>', methods=['GET'])
def get_user_invoices(user_id):
    """Get user's billing invoices"""
    # In production, fetch from Stripe
    sample_invoices = [
        {
            'invoice_id': 'inv_001',
            'amount': 79.99,
            'currency': 'USD',
            'status': 'paid',
            'date': datetime.utcnow().isoformat(),
            'period_start': (datetime.utcnow() - timedelta(days=30)).isoformat(),
            'period_end': datetime.utcnow().isoformat()
        }
    ]
    
    return jsonify({
        'invoices': sample_invoices,
        'total_count': len(sample_invoices)
    })

def check_subscription_limits(subscription):
    """Check if subscription limits are exceeded"""
    usage = subscription['usage']
    limits = subscription['limits']
    exceeded = []
    
    for key, limit in limits.items():
        if limit > 0:  # Not unlimited
            current = usage.get(key, 0)
            if current >= limit:
                exceeded.append(key)
    
    return exceeded

def handle_payment_success(stripe_subscription_id):
    """Handle successful payment"""
    # Find subscription by Stripe ID
    for subscription in subscriptions.values():
        if subscription.get('stripe_subscription_id') == stripe_subscription_id:
            subscription['status'] = 'active'
            subscription['last_payment_date'] = datetime.utcnow().isoformat()
            
            # Reset monthly usage counters
            subscription['usage']['api_calls_this_month'] = 0
            
            logger.info(f"Payment succeeded for subscription: {subscription['subscription_id']}")
            break

def handle_payment_failure(stripe_subscription_id):
    """Handle failed payment"""
    # Find subscription by Stripe ID
    for subscription in subscriptions.values():
        if subscription.get('stripe_subscription_id') == stripe_subscription_id:
            subscription['status'] = 'past_due'
            subscription['payment_failed_date'] = datetime.utcnow().isoformat()
            
            logger.warning(f"Payment failed for subscription: {subscription['subscription_id']}")
            break

def handle_subscription_cancellation(stripe_subscription_id):
    """Handle subscription cancellation from Stripe"""
    # Find subscription by Stripe ID
    for subscription in subscriptions.values():
        if subscription.get('stripe_subscription_id') == stripe_subscription_id:
            subscription['status'] = 'cancelled'
            subscription['cancelled_date'] = datetime.utcnow().isoformat()
            
            logger.info(f"Subscription cancelled via Stripe: {subscription['subscription_id']}")
            break


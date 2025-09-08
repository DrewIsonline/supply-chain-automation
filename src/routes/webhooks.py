from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import json
import hmac
import hashlib

webhooks_bp = Blueprint('webhooks', __name__)
logger = logging.getLogger(__name__)

# In-memory storage for demo (replace with database in production)
webhook_subscriptions = {}
webhook_events = []
webhook_config = {
    'secret_key': 'supply_chain_webhook_secret_2024'
}

@webhooks_bp.route('/status', methods=['GET'])
def webhook_status():
    """Get webhook system status"""
    return jsonify({
        'webhook_system': 'active',
        'total_subscriptions': len(webhook_subscriptions),
        'recent_events': len([e for e in webhook_events if 
                            (datetime.utcnow() - datetime.fromisoformat(e['timestamp'])).days < 1]),
        'supported_triggers': [
            'stockout_alert',
            'overstock_warning',
            'supplier_request',
            'reorder_generated',
            'forecast_updated'
        ]
    })

@webhooks_bp.route('/subscribe', methods=['POST'])
def subscribe_webhook():
    """Subscribe to webhook events (for Zapier integration)"""
    try:
        data = request.get_json()
        
        required_fields = ['trigger_event', 'webhook_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        subscription_id = f"sub_{datetime.utcnow().timestamp()}"
        
        webhook_subscriptions[subscription_id] = {
            'subscription_id': subscription_id,
            'trigger_event': data['trigger_event'],
            'webhook_url': data['webhook_url'],
            'filters': data.get('filters', {}),
            'status': 'active',
            'created_date': datetime.utcnow().isoformat(),
            'last_triggered': None,
            'total_triggers': 0,
            'user_id': data.get('user_id', 'anonymous'),
            'description': data.get('description', '')
        }
        
        logger.info(f"Created webhook subscription: {subscription_id}")
        
        return jsonify({
            'success': True,
            'subscription': webhook_subscriptions[subscription_id]
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating webhook subscription: {str(e)}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    """Get all webhook subscriptions"""
    return jsonify({
        'subscriptions': list(webhook_subscriptions.values()),
        'total_count': len(webhook_subscriptions)
    })

@webhooks_bp.route('/subscriptions/<subscription_id>', methods=['DELETE'])
def unsubscribe_webhook(subscription_id):
    """Unsubscribe from webhook events"""
    try:
        if subscription_id not in webhook_subscriptions:
            return jsonify({'error': 'Subscription not found'}), 404
        
        del webhook_subscriptions[subscription_id]
        
        logger.info(f"Deleted webhook subscription: {subscription_id}")
        
        return jsonify({
            'success': True,
            'message': 'Subscription deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting webhook subscription: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Zapier-specific webhook endpoints
@webhooks_bp.route('/stockout', methods=['POST'])
def stockout_webhook():
    """Webhook endpoint for stockout alerts (Zapier trigger)"""
    try:
        # This endpoint is called by the inventory bot when stockout occurs
        data = request.get_json()
        
        event = {
            'event_id': f"stockout_{datetime.utcnow().timestamp()}",
            'trigger': 'stockout_alert',
            'product_id': data.get('product_id'),
            'product_name': data.get('product_name'),
            'current_stock': data.get('current_stock', 0),
            'min_threshold': data.get('min_threshold', 0),
            'severity': data.get('severity', 'medium'),
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_data': data
        }
        
        webhook_events.append(event)
        
        # Trigger subscribed webhooks
        triggered_count = trigger_subscribed_webhooks('stockout_alert', event)
        
        return jsonify({
            'success': True,
            'event_id': event['event_id'],
            'webhooks_triggered': triggered_count
        })
        
    except Exception as e:
        logger.error(f"Error processing stockout webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/overstock', methods=['POST'])
def overstock_webhook():
    """Webhook endpoint for overstock warnings (Zapier trigger)"""
    try:
        data = request.get_json()
        
        event = {
            'event_id': f"overstock_{datetime.utcnow().timestamp()}",
            'trigger': 'overstock_warning',
            'product_id': data.get('product_id'),
            'product_name': data.get('product_name'),
            'current_stock': data.get('current_stock', 0),
            'max_threshold': data.get('max_threshold', 0),
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_data': data
        }
        
        webhook_events.append(event)
        
        # Trigger subscribed webhooks
        triggered_count = trigger_subscribed_webhooks('overstock_warning', event)
        
        return jsonify({
            'success': True,
            'event_id': event['event_id'],
            'webhooks_triggered': triggered_count
        })
        
    except Exception as e:
        logger.error(f"Error processing overstock webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/supplier_request', methods=['POST'])
def supplier_request_webhook():
    """Webhook endpoint for new supplier requests (Zapier trigger)"""
    try:
        data = request.get_json()
        
        event = {
            'event_id': f"supplier_req_{datetime.utcnow().timestamp()}",
            'trigger': 'supplier_request',
            'request_id': data.get('request_id'),
            'supplier_id': data.get('supplier_id'),
            'request_type': data.get('request_type'),
            'priority': data.get('priority', 'medium'),
            'description': data.get('description', ''),
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_data': data
        }
        
        webhook_events.append(event)
        
        # Trigger subscribed webhooks
        triggered_count = trigger_subscribed_webhooks('supplier_request', event)
        
        return jsonify({
            'success': True,
            'event_id': event['event_id'],
            'webhooks_triggered': triggered_count
        })
        
    except Exception as e:
        logger.error(f"Error processing supplier request webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/reorder_generated', methods=['POST'])
def reorder_generated_webhook():
    """Webhook endpoint for generated reorders (Zapier trigger)"""
    try:
        data = request.get_json()
        
        event = {
            'event_id': f"reorder_{datetime.utcnow().timestamp()}",
            'trigger': 'reorder_generated',
            'order_id': data.get('order_id'),
            'product_id': data.get('product_id'),
            'supplier_id': data.get('supplier_id'),
            'quantity': data.get('quantity', 0),
            'estimated_cost': data.get('estimated_cost', 0),
            'status': data.get('status', 'pending'),
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_data': data
        }
        
        webhook_events.append(event)
        
        # Trigger subscribed webhooks
        triggered_count = trigger_subscribed_webhooks('reorder_generated', event)
        
        return jsonify({
            'success': True,
            'event_id': event['event_id'],
            'webhooks_triggered': triggered_count
        })
        
    except Exception as e:
        logger.error(f"Error processing reorder webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/forecast_updated', methods=['POST'])
def forecast_updated_webhook():
    """Webhook endpoint for forecast updates (Zapier trigger)"""
    try:
        data = request.get_json()
        
        event = {
            'event_id': f"forecast_{datetime.utcnow().timestamp()}",
            'trigger': 'forecast_updated',
            'product_id': data.get('product_id'),
            'predicted_demand': data.get('predicted_demand', 0),
            'confidence_level': data.get('confidence_level', 0),
            'trend_direction': data.get('trend_direction', 'stable'),
            'forecast_period_days': data.get('forecast_period_days', 30),
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_data': data
        }
        
        webhook_events.append(event)
        
        # Trigger subscribed webhooks
        triggered_count = trigger_subscribed_webhooks('forecast_updated', event)
        
        return jsonify({
            'success': True,
            'event_id': event['event_id'],
            'webhooks_triggered': triggered_count
        })
        
    except Exception as e:
        logger.error(f"Error processing forecast webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/events', methods=['GET'])
def get_webhook_events():
    """Get recent webhook events"""
    # Get events from last 24 hours
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    recent_events = [
        event for event in webhook_events
        if datetime.fromisoformat(event['timestamp']) > cutoff_time
    ]
    
    return jsonify({
        'events': recent_events,
        'total_count': len(recent_events)
    })

@webhooks_bp.route('/test', methods=['POST'])
def test_webhook():
    """Test webhook endpoint for Zapier integration testing"""
    try:
        data = request.get_json()
        
        test_event = {
            'event_id': f"test_{datetime.utcnow().timestamp()}",
            'trigger': 'test_event',
            'message': 'This is a test webhook event',
            'test_data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        webhook_events.append(test_event)
        
        # Trigger any test subscriptions
        triggered_count = trigger_subscribed_webhooks('test_event', test_event)
        
        return jsonify({
            'success': True,
            'message': 'Test webhook processed successfully',
            'event': test_event,
            'webhooks_triggered': triggered_count
        })
        
    except Exception as e:
        logger.error(f"Error processing test webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/zapier/auth', methods=['POST'])
def zapier_auth():
    """Authentication endpoint for Zapier"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        
        # In production, validate API key against database
        if api_key and len(api_key) > 10:
            return jsonify({
                'success': True,
                'user_id': 'zapier_user',
                'permissions': ['read', 'write', 'webhook']
            })
        else:
            return jsonify({'error': 'Invalid API key'}), 401
            
    except Exception as e:
        logger.error(f"Error in Zapier auth: {str(e)}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/zapier/triggers/sample', methods=['GET'])
def zapier_sample_data():
    """Provide sample data for Zapier trigger setup"""
    trigger_type = request.args.get('trigger', 'stockout_alert')
    
    sample_data = {
        'stockout_alert': {
            'product_id': 'PROD001',
            'product_name': 'Sample Product',
            'current_stock': 5,
            'min_threshold': 10,
            'severity': 'medium',
            'timestamp': datetime.utcnow().isoformat()
        },
        'overstock_warning': {
            'product_id': 'PROD002',
            'product_name': 'Another Product',
            'current_stock': 150,
            'max_threshold': 100,
            'timestamp': datetime.utcnow().isoformat()
        },
        'supplier_request': {
            'request_id': 'REQ001',
            'supplier_id': 'SUP001',
            'request_type': 'quote',
            'priority': 'high',
            'description': 'Request for product quote',
            'timestamp': datetime.utcnow().isoformat()
        },
        'reorder_generated': {
            'order_id': 'ORD001',
            'product_id': 'PROD001',
            'supplier_id': 'SUP001',
            'quantity': 50,
            'estimated_cost': 500.00,
            'status': 'pending_approval',
            'timestamp': datetime.utcnow().isoformat()
        },
        'forecast_updated': {
            'product_id': 'PROD001',
            'predicted_demand': 75,
            'confidence_level': 85,
            'trend_direction': 'increasing',
            'forecast_period_days': 30,
            'timestamp': datetime.utcnow().isoformat()
        }
    }
    
    return jsonify(sample_data.get(trigger_type, sample_data['stockout_alert']))

def trigger_subscribed_webhooks(trigger_event, event_data):
    """Trigger all subscribed webhooks for an event"""
    triggered_count = 0
    
    for subscription in webhook_subscriptions.values():
        if (subscription['trigger_event'] == trigger_event and 
            subscription['status'] == 'active'):
            
            # Check filters
            if passes_filters(event_data, subscription.get('filters', {})):
                # In production, send HTTP POST to webhook_url
                logger.info(f"Triggering webhook: {subscription['webhook_url']}")
                
                # Update subscription stats
                subscription['last_triggered'] = datetime.utcnow().isoformat()
                subscription['total_triggers'] += 1
                
                triggered_count += 1
    
    return triggered_count

def passes_filters(event_data, filters):
    """Check if event data passes subscription filters"""
    if not filters:
        return True
    
    for key, value in filters.items():
        if key in event_data and event_data[key] != value:
            return False
    
    return True

def generate_webhook_signature(payload, secret):
    """Generate webhook signature for security"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature"""
    expected_signature = generate_webhook_signature(payload, secret)
    return hmac.compare_digest(signature, expected_signature)


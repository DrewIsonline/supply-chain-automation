from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
import json

reorder_bp = Blueprint('reorder', __name__)
logger = logging.getLogger(__name__)

# In-memory storage for demo (replace with database in production)
reorder_rules = {}
reorder_history = {}
pending_orders = {}
approval_workflows = {}

@reorder_bp.route('/status', methods=['GET'])
def reorder_status():
    """Get auto-reorder bot status"""
    return jsonify({
        'bot': 'auto_reorder',
        'status': 'active',
        'features': [
            'smart_trigger_configuration',
            'automated_po_generation',
            'approval_workflow_management',
            'supplier_integration',
            'order_tracking',
            'cost_optimization'
        ],
        'active_rules': len(reorder_rules),
        'pending_orders': len(pending_orders)
    })

@reorder_bp.route('/rules', methods=['GET'])
def get_all_rules():
    """Get all reorder rules"""
    return jsonify({
        'rules': list(reorder_rules.values()),
        'total_count': len(reorder_rules)
    })

@reorder_bp.route('/rules/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    """Get specific reorder rule"""
    if rule_id not in reorder_rules:
        return jsonify({'error': 'Reorder rule not found'}), 404
    
    return jsonify(reorder_rules[rule_id])

@reorder_bp.route('/rules', methods=['POST'])
def create_reorder_rule():
    """Create new smart reorder rule"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'trigger_type', 'reorder_quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        rule_id = f"rule_{datetime.utcnow().timestamp()}"
        
        reorder_rules[rule_id] = {
            'rule_id': rule_id,
            'product_id': data['product_id'],
            'product_name': data.get('product_name', ''),
            'trigger_type': data['trigger_type'],  # threshold, time_based, demand_forecast, seasonal
            'trigger_value': data.get('trigger_value', 0),
            'reorder_quantity': data['reorder_quantity'],
            'supplier_id': data.get('supplier_id', ''),
            'max_cost': data.get('max_cost', 0),
            'approval_required': data.get('approval_required', False),
            'approval_threshold': data.get('approval_threshold', 1000),
            'lead_time_days': data.get('lead_time_days', 7),
            'safety_stock': data.get('safety_stock', 0),
            'seasonal_adjustment': data.get('seasonal_adjustment', False),
            'status': 'active',
            'created_date': datetime.utcnow().isoformat(),
            'last_triggered': None,
            'total_triggers': 0
        }
        
        logger.info(f"Created reorder rule: {rule_id}")
        
        return jsonify({
            'success': True,
            'rule': reorder_rules[rule_id]
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating reorder rule: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reorder_bp.route('/rules/<rule_id>', methods=['PUT'])
def update_reorder_rule(rule_id):
    """Update reorder rule"""
    try:
        if rule_id not in reorder_rules:
            return jsonify({'error': 'Reorder rule not found'}), 404
        
        data = request.get_json()
        rule = reorder_rules[rule_id]
        
        # Update allowed fields
        updatable_fields = ['trigger_type', 'trigger_value', 'reorder_quantity', 
                          'supplier_id', 'max_cost', 'approval_required', 
                          'approval_threshold', 'lead_time_days', 'safety_stock', 
                          'seasonal_adjustment', 'status']
        
        for field in updatable_fields:
            if field in data:
                rule[field] = data[field]
        
        rule['last_updated'] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated reorder rule: {rule_id}")
        
        return jsonify({
            'success': True,
            'rule': rule
        })
        
    except Exception as e:
        logger.error(f"Error updating reorder rule: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reorder_bp.route('/trigger', methods=['POST'])
def trigger_reorder():
    """Manually trigger reorder for a product"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        product_id = data['product_id']
        quantity = data['quantity']
        
        # Find applicable reorder rule
        applicable_rule = None
        for rule in reorder_rules.values():
            if rule['product_id'] == product_id and rule['status'] == 'active':
                applicable_rule = rule
                break
        
        if not applicable_rule:
            return jsonify({'error': 'No active reorder rule found for this product'}), 404
        
        # Create reorder
        order_result = create_reorder(applicable_rule, quantity, 'manual_trigger')
        
        return jsonify({
            'success': True,
            'order': order_result
        })
        
    except Exception as e:
        logger.error(f"Error triggering reorder: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reorder_bp.route('/check-triggers', methods=['POST'])
def check_reorder_triggers():
    """Check all reorder triggers and execute if conditions are met"""
    try:
        data = request.get_json()
        inventory_data = data.get('inventory_data', {})
        
        triggered_orders = []
        
        for rule in reorder_rules.values():
            if rule['status'] != 'active':
                continue
            
            product_id = rule['product_id']
            
            # Check if trigger conditions are met
            should_trigger = False
            trigger_reason = ""
            
            if rule['trigger_type'] == 'threshold':
                current_stock = inventory_data.get(product_id, {}).get('current_stock', 0)
                if current_stock <= rule['trigger_value']:
                    should_trigger = True
                    trigger_reason = f"Stock level ({current_stock}) below threshold ({rule['trigger_value']})"
            
            elif rule['trigger_type'] == 'time_based':
                # Check if enough time has passed since last order
                last_triggered = rule.get('last_triggered')
                if last_triggered:
                    last_date = datetime.fromisoformat(last_triggered)
                    days_since = (datetime.utcnow() - last_date).days
                    if days_since >= rule['trigger_value']:
                        should_trigger = True
                        trigger_reason = f"Time-based trigger: {days_since} days since last order"
                else:
                    should_trigger = True
                    trigger_reason = "First time trigger"
            
            elif rule['trigger_type'] == 'demand_forecast':
                # Check demand forecast data
                forecast_data = inventory_data.get(product_id, {}).get('demand_forecast', {})
                predicted_demand = forecast_data.get('predicted_demand', 0)
                current_stock = inventory_data.get(product_id, {}).get('current_stock', 0)
                
                if current_stock < predicted_demand:
                    should_trigger = True
                    trigger_reason = f"Current stock ({current_stock}) below predicted demand ({predicted_demand})"
            
            if should_trigger:
                # Calculate reorder quantity (can include seasonal adjustments)
                reorder_qty = rule['reorder_quantity']
                
                if rule.get('seasonal_adjustment', False):
                    # Simple seasonal adjustment (can be enhanced)
                    current_month = datetime.utcnow().month
                    if current_month in [11, 12, 1]:  # Holiday season
                        reorder_qty = int(reorder_qty * 1.5)
                
                # Create reorder
                order_result = create_reorder(rule, reorder_qty, trigger_reason)
                triggered_orders.append(order_result)
                
                # Update rule
                rule['last_triggered'] = datetime.utcnow().isoformat()
                rule['total_triggers'] += 1
        
        logger.info(f"Checked triggers, created {len(triggered_orders)} orders")
        
        return jsonify({
            'success': True,
            'triggered_orders': triggered_orders,
            'total_triggered': len(triggered_orders)
        })
        
    except Exception as e:
        logger.error(f"Error checking reorder triggers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reorder_bp.route('/orders', methods=['GET'])
def get_all_orders():
    """Get all reorders"""
    return jsonify({
        'orders': list(pending_orders.values()),
        'total_count': len(pending_orders)
    })

@reorder_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get specific reorder details"""
    if order_id not in pending_orders:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify(pending_orders[order_id])

@reorder_bp.route('/orders/<order_id>/approve', methods=['POST'])
def approve_order(order_id):
    """Approve pending reorder"""
    try:
        if order_id not in pending_orders:
            return jsonify({'error': 'Order not found'}), 404
        
        data = request.get_json()
        order = pending_orders[order_id]
        
        if order['status'] != 'pending_approval':
            return jsonify({'error': 'Order is not pending approval'}), 400
        
        order['status'] = 'approved'
        order['approved_by'] = data.get('approved_by', 'system')
        order['approved_date'] = datetime.utcnow().isoformat()
        order['approval_notes'] = data.get('notes', '')
        
        # Send to supplier (in production, integrate with supplier systems)
        send_order_to_supplier(order)
        
        # Trigger webhook for approved order
        trigger_reorder_webhook(order)
        
        logger.info(f"Approved reorder: {order_id}")
        
        return jsonify({
            'success': True,
            'order': order
        })
        
    except Exception as e:
        logger.error(f"Error approving order: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reorder_bp.route('/orders/<order_id>/reject', methods=['POST'])
def reject_order(order_id):
    """Reject pending reorder"""
    try:
        if order_id not in pending_orders:
            return jsonify({'error': 'Order not found'}), 404
        
        data = request.get_json()
        order = pending_orders[order_id]
        
        if order['status'] != 'pending_approval':
            return jsonify({'error': 'Order is not pending approval'}), 400
        
        order['status'] = 'rejected'
        order['rejected_by'] = data.get('rejected_by', 'system')
        order['rejected_date'] = datetime.utcnow().isoformat()
        order['rejection_reason'] = data.get('reason', '')
        
        logger.info(f"Rejected reorder: {order_id}")
        
        return jsonify({
            'success': True,
            'order': order
        })
        
    except Exception as e:
        logger.error(f"Error rejecting order: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reorder_bp.route('/history', methods=['GET'])
def get_reorder_history():
    """Get reorder history"""
    return jsonify({
        'history': list(reorder_history.values()),
        'total_count': len(reorder_history)
    })

@reorder_bp.route('/analytics', methods=['GET'])
def get_reorder_analytics():
    """Get reorder analytics and insights"""
    try:
        # Calculate analytics from reorder data
        total_rules = len(reorder_rules)
        active_rules = len([r for r in reorder_rules.values() if r['status'] == 'active'])
        total_orders = len(pending_orders) + len(reorder_history)
        pending_approval = len([o for o in pending_orders.values() if o['status'] == 'pending_approval'])
        
        # Calculate cost savings and efficiency metrics
        total_cost_saved = 0
        avg_lead_time = 0
        
        if reorder_history:
            total_cost_saved = sum(h.get('cost_saved', 0) for h in reorder_history.values())
            avg_lead_time = sum(h.get('actual_lead_time', 0) for h in reorder_history.values()) / len(reorder_history)
        
        analytics = {
            'summary': {
                'total_rules': total_rules,
                'active_rules': active_rules,
                'total_orders': total_orders,
                'pending_approval': pending_approval
            },
            'performance': {
                'total_cost_saved': total_cost_saved,
                'average_lead_time_days': round(avg_lead_time, 1),
                'automation_rate': round((total_orders / max(total_rules, 1)) * 100, 1)
            },
            'trends': {
                'orders_this_month': len([o for o in pending_orders.values() 
                                        if datetime.fromisoformat(o['created_date']).month == datetime.utcnow().month]),
                'most_triggered_product': get_most_triggered_product()
            }
        }
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

def create_reorder(rule, quantity, trigger_reason):
    """Create a new reorder based on rule"""
    order_id = f"order_{datetime.utcnow().timestamp()}"
    
    # Calculate estimated cost
    estimated_cost = quantity * rule.get('unit_cost', 0)
    
    # Determine if approval is required
    requires_approval = (
        rule.get('approval_required', False) or 
        estimated_cost > rule.get('approval_threshold', 1000)
    )
    
    order = {
        'order_id': order_id,
        'rule_id': rule['rule_id'],
        'product_id': rule['product_id'],
        'product_name': rule.get('product_name', ''),
        'supplier_id': rule.get('supplier_id', ''),
        'quantity': quantity,
        'estimated_cost': estimated_cost,
        'trigger_reason': trigger_reason,
        'status': 'pending_approval' if requires_approval else 'approved',
        'created_date': datetime.utcnow().isoformat(),
        'expected_delivery': (datetime.utcnow() + timedelta(days=rule.get('lead_time_days', 7))).isoformat(),
        'priority': 'high' if 'stockout' in trigger_reason.lower() else 'medium'
    }
    
    pending_orders[order_id] = order
    
    # If no approval required, send directly to supplier
    if not requires_approval:
        send_order_to_supplier(order)
        trigger_reorder_webhook(order)
    
    return order

def send_order_to_supplier(order):
    """Send order to supplier (integration point)"""
    # In production, integrate with supplier systems/APIs
    order['status'] = 'sent_to_supplier'
    order['sent_date'] = datetime.utcnow().isoformat()
    
    logger.info(f"Sent order to supplier: {order['order_id']}")

def trigger_reorder_webhook(order):
    """Trigger webhook for reorder event (for Zapier integration)"""
    webhook_payload = {
        'trigger': 'reorder_generated',
        'order_id': order['order_id'],
        'product_id': order['product_id'],
        'supplier_id': order['supplier_id'],
        'quantity': order['quantity'],
        'estimated_cost': order['estimated_cost'],
        'status': order['status'],
        'timestamp': order['created_date']
    }
    
    # In production, send to configured webhook URLs
    logger.info(f"Webhook triggered for reorder: {order['order_id']}")
    return webhook_payload

def get_most_triggered_product():
    """Get the product with most reorder triggers"""
    product_counts = {}
    
    for rule in reorder_rules.values():
        product_id = rule['product_id']
        triggers = rule.get('total_triggers', 0)
        
        if product_id not in product_counts:
            product_counts[product_id] = {
                'product_id': product_id,
                'product_name': rule.get('product_name', ''),
                'total_triggers': triggers
            }
        else:
            product_counts[product_id]['total_triggers'] += triggers
    
    if not product_counts:
        return None
    
    return max(product_counts.values(), key=lambda x: x['total_triggers'])


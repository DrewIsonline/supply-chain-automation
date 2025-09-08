from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
import json

supplier_bp = Blueprint('supplier', __name__)
logger = logging.getLogger(__name__)

# In-memory storage for demo (replace with database in production)
suppliers_data = {}
supplier_requests = {}
supplier_performance = {}

@supplier_bp.route('/status', methods=['GET'])
def supplier_status():
    """Get supplier management bot status"""
    return jsonify({
        'bot': 'supplier_visibility',
        'status': 'active',
        'features': [
            'supplier_onboarding',
            'request_intake_automation',
            'performance_tracking',
            'communication_automation',
            'document_management',
            'compliance_monitoring'
        ],
        'total_suppliers': len(suppliers_data),
        'pending_requests': len([r for r in supplier_requests.values() if r['status'] == 'pending'])
    })

@supplier_bp.route('/suppliers', methods=['GET'])
def get_all_suppliers():
    """Get all suppliers"""
    return jsonify({
        'suppliers': list(suppliers_data.values()),
        'total_count': len(suppliers_data)
    })

@supplier_bp.route('/suppliers/<supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """Get specific supplier details"""
    if supplier_id not in suppliers_data:
        return jsonify({'error': 'Supplier not found'}), 404
    
    supplier = suppliers_data[supplier_id].copy()
    
    # Add performance data if available
    if supplier_id in supplier_performance:
        supplier['performance'] = supplier_performance[supplier_id]
    
    return jsonify(supplier)

@supplier_bp.route('/suppliers', methods=['POST'])
def add_supplier():
    """Add new supplier (onboarding automation)"""
    try:
        data = request.get_json()
        
        required_fields = ['supplier_id', 'name', 'contact_email']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        supplier_id = data['supplier_id']
        
        suppliers_data[supplier_id] = {
            'supplier_id': supplier_id,
            'name': data['name'],
            'contact_email': data['contact_email'],
            'contact_phone': data.get('contact_phone', ''),
            'address': data.get('address', ''),
            'website': data.get('website', ''),
            'categories': data.get('categories', []),
            'payment_terms': data.get('payment_terms', ''),
            'lead_time_days': data.get('lead_time_days', 0),
            'minimum_order': data.get('minimum_order', 0),
            'status': 'active',
            'onboarding_date': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat(),
            'compliance_status': 'pending_review',
            'documents': []
        }
        
        # Initialize performance tracking
        supplier_performance[supplier_id] = {
            'supplier_id': supplier_id,
            'total_orders': 0,
            'on_time_deliveries': 0,
            'quality_score': 0,
            'response_time_hours': 0,
            'last_performance_update': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Added new supplier: {supplier_id}")
        
        return jsonify({
            'success': True,
            'supplier': suppliers_data[supplier_id]
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding supplier: {str(e)}")
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/suppliers/<supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """Update supplier information"""
    try:
        if supplier_id not in suppliers_data:
            return jsonify({'error': 'Supplier not found'}), 404
        
        data = request.get_json()
        supplier = suppliers_data[supplier_id]
        
        # Update allowed fields
        updatable_fields = ['name', 'contact_email', 'contact_phone', 'address', 
                          'website', 'categories', 'payment_terms', 'lead_time_days', 
                          'minimum_order', 'status']
        
        for field in updatable_fields:
            if field in data:
                supplier[field] = data[field]
        
        supplier['last_updated'] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated supplier: {supplier_id}")
        
        return jsonify({
            'success': True,
            'supplier': supplier
        })
        
    except Exception as e:
        logger.error(f"Error updating supplier: {str(e)}")
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/requests', methods=['GET'])
def get_all_requests():
    """Get all supplier requests"""
    return jsonify({
        'requests': list(supplier_requests.values()),
        'total_count': len(supplier_requests)
    })

@supplier_bp.route('/requests', methods=['POST'])
def create_supplier_request():
    """Create new supplier request (intake automation)"""
    try:
        data = request.get_json()
        
        required_fields = ['request_type', 'supplier_id', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        request_id = f"req_{datetime.utcnow().timestamp()}"
        
        supplier_requests[request_id] = {
            'request_id': request_id,
            'request_type': data['request_type'],  # quote, order, information, complaint, etc.
            'supplier_id': data['supplier_id'],
            'description': data['description'],
            'priority': data.get('priority', 'medium'),
            'status': 'pending',
            'created_date': datetime.utcnow().isoformat(),
            'due_date': data.get('due_date', ''),
            'assigned_to': data.get('assigned_to', ''),
            'products': data.get('products', []),
            'quantity': data.get('quantity', 0),
            'budget': data.get('budget', 0),
            'notes': data.get('notes', ''),
            'attachments': data.get('attachments', []),
            'responses': []
        }
        
        # Auto-assign based on request type and supplier
        auto_assign_request(request_id)
        
        # Send notification (webhook trigger)
        trigger_supplier_request_webhook(supplier_requests[request_id])
        
        logger.info(f"Created supplier request: {request_id}")
        
        return jsonify({
            'success': True,
            'request': supplier_requests[request_id]
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating supplier request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/requests/<request_id>', methods=['PUT'])
def update_request(request_id):
    """Update supplier request status"""
    try:
        if request_id not in supplier_requests:
            return jsonify({'error': 'Request not found'}), 404
        
        data = request.get_json()
        request_obj = supplier_requests[request_id]
        
        # Update status and add response
        if 'status' in data:
            request_obj['status'] = data['status']
        
        if 'response' in data:
            response = {
                'response_id': f"resp_{datetime.utcnow().timestamp()}",
                'message': data['response'],
                'responder': data.get('responder', 'system'),
                'timestamp': datetime.utcnow().isoformat()
            }
            request_obj['responses'].append(response)
        
        request_obj['last_updated'] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated supplier request: {request_id}")
        
        return jsonify({
            'success': True,
            'request': request_obj
        })
        
    except Exception as e:
        logger.error(f"Error updating request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/performance', methods=['GET'])
def get_all_performance():
    """Get performance data for all suppliers"""
    return jsonify({
        'performance': list(supplier_performance.values()),
        'total_suppliers': len(supplier_performance)
    })

@supplier_bp.route('/performance/<supplier_id>', methods=['GET'])
def get_supplier_performance(supplier_id):
    """Get performance data for specific supplier"""
    if supplier_id not in supplier_performance:
        return jsonify({'error': 'Supplier performance data not found'}), 404
    
    return jsonify(supplier_performance[supplier_id])

@supplier_bp.route('/performance/<supplier_id>', methods=['POST'])
def update_supplier_performance(supplier_id):
    """Update supplier performance metrics"""
    try:
        if supplier_id not in suppliers_data:
            return jsonify({'error': 'Supplier not found'}), 404
        
        data = request.get_json()
        
        if supplier_id not in supplier_performance:
            supplier_performance[supplier_id] = {
                'supplier_id': supplier_id,
                'total_orders': 0,
                'on_time_deliveries': 0,
                'quality_score': 0,
                'response_time_hours': 0
            }
        
        performance = supplier_performance[supplier_id]
        
        # Update performance metrics
        if 'delivery_status' in data:
            performance['total_orders'] += 1
            if data['delivery_status'] == 'on_time':
                performance['on_time_deliveries'] += 1
        
        if 'quality_score' in data:
            # Calculate running average
            current_score = performance.get('quality_score', 0)
            new_score = data['quality_score']
            total_orders = performance.get('total_orders', 1)
            performance['quality_score'] = ((current_score * (total_orders - 1)) + new_score) / total_orders
        
        if 'response_time_hours' in data:
            # Calculate running average
            current_time = performance.get('response_time_hours', 0)
            new_time = data['response_time_hours']
            total_orders = performance.get('total_orders', 1)
            performance['response_time_hours'] = ((current_time * (total_orders - 1)) + new_time) / total_orders
        
        # Calculate overall performance score
        on_time_rate = performance['on_time_deliveries'] / max(performance['total_orders'], 1)
        quality_score = performance['quality_score'] / 100  # Normalize to 0-1
        response_score = max(0, 1 - (performance['response_time_hours'] / 48))  # 48 hours = 0 score
        
        performance['overall_score'] = (on_time_rate * 0.4 + quality_score * 0.4 + response_score * 0.2) * 100
        performance['last_performance_update'] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated performance for supplier: {supplier_id}")
        
        return jsonify({
            'success': True,
            'performance': performance
        })
        
    except Exception as e:
        logger.error(f"Error updating supplier performance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/communication/send', methods=['POST'])
def send_communication():
    """Send automated communication to supplier"""
    try:
        data = request.get_json()
        
        required_fields = ['supplier_id', 'message_type', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        supplier_id = data['supplier_id']
        
        if supplier_id not in suppliers_data:
            return jsonify({'error': 'Supplier not found'}), 404
        
        supplier = suppliers_data[supplier_id]
        
        communication = {
            'communication_id': f"comm_{datetime.utcnow().timestamp()}",
            'supplier_id': supplier_id,
            'message_type': data['message_type'],  # email, sms, webhook
            'content': data['content'],
            'recipient': supplier['contact_email'],
            'status': 'sent',
            'sent_date': datetime.utcnow().isoformat(),
            'delivery_status': 'pending'
        }
        
        # In production, integrate with email/SMS services
        logger.info(f"Sent communication to supplier {supplier_id}: {data['message_type']}")
        
        return jsonify({
            'success': True,
            'communication': communication
        })
        
    except Exception as e:
        logger.error(f"Error sending communication: {str(e)}")
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/compliance/<supplier_id>', methods=['GET'])
def get_supplier_compliance(supplier_id):
    """Get supplier compliance status"""
    if supplier_id not in suppliers_data:
        return jsonify({'error': 'Supplier not found'}), 404
    
    supplier = suppliers_data[supplier_id]
    
    compliance_data = {
        'supplier_id': supplier_id,
        'compliance_status': supplier.get('compliance_status', 'pending_review'),
        'documents': supplier.get('documents', []),
        'certifications': supplier.get('certifications', []),
        'last_audit_date': supplier.get('last_audit_date', ''),
        'next_audit_due': supplier.get('next_audit_due', ''),
        'compliance_score': supplier.get('compliance_score', 0)
    }
    
    return jsonify(compliance_data)

def auto_assign_request(request_id):
    """Auto-assign request based on type and supplier"""
    if request_id not in supplier_requests:
        return
    
    request_obj = supplier_requests[request_id]
    request_type = request_obj['request_type']
    
    # Simple auto-assignment logic (can be enhanced)
    if request_type in ['quote', 'order']:
        request_obj['assigned_to'] = 'procurement_team'
        request_obj['priority'] = 'high'
    elif request_type == 'complaint':
        request_obj['assigned_to'] = 'quality_team'
        request_obj['priority'] = 'high'
    else:
        request_obj['assigned_to'] = 'supplier_relations'
        request_obj['priority'] = 'medium'

def trigger_supplier_request_webhook(request_data):
    """Trigger webhook for new supplier request (for Zapier integration)"""
    webhook_payload = {
        'trigger': 'supplier_request',
        'request_id': request_data['request_id'],
        'supplier_id': request_data['supplier_id'],
        'request_type': request_data['request_type'],
        'priority': request_data['priority'],
        'description': request_data['description'],
        'timestamp': request_data['created_date']
    }
    
    # In production, send to configured webhook URLs
    logger.info(f"Webhook triggered for supplier request: {request_data['request_id']}")
    return webhook_payload


from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
import json

inventory_bp = Blueprint('inventory', __name__)
logger = logging.getLogger(__name__)

# In-memory storage for demo (replace with database in production)
inventory_data = {}
inventory_rules = {}
inventory_alerts = []

@inventory_bp.route('/status', methods=['GET'])
def inventory_status():
    """Get inventory management bot status"""
    return jsonify({
        'bot': 'inventory_management',
        'status': 'active',
        'features': [
            'real_time_tracking',
            'stockout_alerts',
            'overstock_warnings',
            'multi_location_sync',
            'automated_reorder_triggers'
        ],
        'total_products': len(inventory_data),
        'active_alerts': len(inventory_alerts)
    })

@inventory_bp.route('/products', methods=['GET'])
def get_all_products():
    """Get all products in inventory"""
    return jsonify({
        'products': list(inventory_data.values()),
        'total_count': len(inventory_data)
    })

@inventory_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get specific product inventory details"""
    if product_id not in inventory_data:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify(inventory_data[product_id])

@inventory_bp.route('/products', methods=['POST'])
def add_product():
    """Add new product to inventory tracking"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'name', 'current_stock', 'min_threshold', 'max_threshold']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        product_id = data['product_id']
        
        inventory_data[product_id] = {
            'product_id': product_id,
            'name': data['name'],
            'sku': data.get('sku', ''),
            'current_stock': data['current_stock'],
            'min_threshold': data['min_threshold'],
            'max_threshold': data['max_threshold'],
            'unit': data.get('unit', 'units'),
            'location': data.get('location', 'main_warehouse'),
            'supplier': data.get('supplier', ''),
            'cost_per_unit': data.get('cost_per_unit', 0),
            'last_updated': datetime.utcnow().isoformat(),
            'status': determine_stock_status(data['current_stock'], data['min_threshold'], data['max_threshold'])
        }
        
        # Check for alerts
        check_inventory_alerts(product_id)
        
        logger.info(f"Added product to inventory: {product_id}")
        
        return jsonify({
            'success': True,
            'product': inventory_data[product_id]
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product inventory levels"""
    try:
        if product_id not in inventory_data:
            return jsonify({'error': 'Product not found'}), 404
        
        data = request.get_json()
        product = inventory_data[product_id]
        
        # Update fields
        if 'current_stock' in data:
            product['current_stock'] = data['current_stock']
        if 'min_threshold' in data:
            product['min_threshold'] = data['min_threshold']
        if 'max_threshold' in data:
            product['max_threshold'] = data['max_threshold']
        
        product['last_updated'] = datetime.utcnow().isoformat()
        product['status'] = determine_stock_status(
            product['current_stock'], 
            product['min_threshold'], 
            product['max_threshold']
        )
        
        # Check for alerts
        check_inventory_alerts(product_id)
        
        logger.info(f"Updated product inventory: {product_id}")
        
        return jsonify({
            'success': True,
            'product': product
        })
        
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all inventory alerts"""
    return jsonify({
        'alerts': inventory_alerts,
        'total_count': len(inventory_alerts)
    })

@inventory_bp.route('/alerts/stockout', methods=['GET'])
def get_stockout_alerts():
    """Get stockout alerts for Zapier webhook"""
    stockout_alerts = [alert for alert in inventory_alerts if alert['type'] == 'stockout']
    return jsonify({
        'alerts': stockout_alerts,
        'count': len(stockout_alerts)
    })

@inventory_bp.route('/alerts/overstock', methods=['GET'])
def get_overstock_alerts():
    """Get overstock alerts for Zapier webhook"""
    overstock_alerts = [alert for alert in inventory_alerts if alert['type'] == 'overstock']
    return jsonify({
        'alerts': overstock_alerts,
        'count': len(overstock_alerts)
    })

@inventory_bp.route('/sync', methods=['POST'])
def sync_inventory():
    """Sync inventory from external systems (ERP, POS, etc.)"""
    try:
        data = request.get_json()
        
        if 'products' not in data:
            return jsonify({'error': 'No products data provided'}), 400
        
        updated_products = []
        new_alerts = []
        
        for product_data in data['products']:
            product_id = product_data.get('product_id')
            if not product_id:
                continue
            
            if product_id in inventory_data:
                # Update existing product
                inventory_data[product_id]['current_stock'] = product_data.get('current_stock', inventory_data[product_id]['current_stock'])
                inventory_data[product_id]['last_updated'] = datetime.utcnow().isoformat()
                inventory_data[product_id]['status'] = determine_stock_status(
                    inventory_data[product_id]['current_stock'],
                    inventory_data[product_id]['min_threshold'],
                    inventory_data[product_id]['max_threshold']
                )
                updated_products.append(product_id)
                
                # Check for new alerts
                alerts = check_inventory_alerts(product_id)
                new_alerts.extend(alerts)
        
        logger.info(f"Synced inventory for {len(updated_products)} products")
        
        return jsonify({
            'success': True,
            'updated_products': updated_products,
            'new_alerts': len(new_alerts)
        })
        
    except Exception as e:
        logger.error(f"Error syncing inventory: {str(e)}")
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/forecast/demand', methods=['POST'])
def update_demand_forecast():
    """Update demand forecast for inventory planning"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id or product_id not in inventory_data:
            return jsonify({'error': 'Product not found'}), 404
        
        forecast_data = {
            'product_id': product_id,
            'predicted_demand': data.get('predicted_demand', 0),
            'forecast_period': data.get('forecast_period', 30),
            'confidence_level': data.get('confidence_level', 0.8),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Store forecast data (in production, save to database)
        inventory_data[product_id]['demand_forecast'] = forecast_data
        
        # Calculate recommended stock levels based on forecast
        recommended_stock = calculate_recommended_stock(forecast_data)
        inventory_data[product_id]['recommended_stock'] = recommended_stock
        
        return jsonify({
            'success': True,
            'forecast': forecast_data,
            'recommended_stock': recommended_stock
        })
        
    except Exception as e:
        logger.error(f"Error updating demand forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

def determine_stock_status(current_stock, min_threshold, max_threshold):
    """Determine stock status based on thresholds"""
    if current_stock <= min_threshold:
        return 'stockout'
    elif current_stock >= max_threshold:
        return 'overstock'
    else:
        return 'normal'

def check_inventory_alerts(product_id):
    """Check and generate inventory alerts"""
    if product_id not in inventory_data:
        return []
    
    product = inventory_data[product_id]
    new_alerts = []
    
    # Check for stockout
    if product['current_stock'] <= product['min_threshold']:
        alert = {
            'id': f"stockout_{product_id}_{datetime.utcnow().timestamp()}",
            'type': 'stockout',
            'product_id': product_id,
            'product_name': product['name'],
            'current_stock': product['current_stock'],
            'min_threshold': product['min_threshold'],
            'severity': 'high' if product['current_stock'] == 0 else 'medium',
            'message': f"Stock low for {product['name']}: {product['current_stock']} units remaining",
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_data': {
                'trigger': 'stockout_alert',
                'product': product
            }
        }
        inventory_alerts.append(alert)
        new_alerts.append(alert)
    
    # Check for overstock
    elif product['current_stock'] >= product['max_threshold']:
        alert = {
            'id': f"overstock_{product_id}_{datetime.utcnow().timestamp()}",
            'type': 'overstock',
            'product_id': product_id,
            'product_name': product['name'],
            'current_stock': product['current_stock'],
            'max_threshold': product['max_threshold'],
            'severity': 'medium',
            'message': f"Overstock warning for {product['name']}: {product['current_stock']} units in stock",
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_data': {
                'trigger': 'overstock_warning',
                'product': product
            }
        }
        inventory_alerts.append(alert)
        new_alerts.append(alert)
    
    return new_alerts

def calculate_recommended_stock(forecast_data):
    """Calculate recommended stock levels based on demand forecast"""
    predicted_demand = forecast_data.get('predicted_demand', 0)
    forecast_period = forecast_data.get('forecast_period', 30)
    confidence_level = forecast_data.get('confidence_level', 0.8)
    
    # Simple calculation (can be enhanced with more sophisticated algorithms)
    safety_stock = predicted_demand * 0.2  # 20% safety stock
    recommended_min = predicted_demand + safety_stock
    recommended_max = predicted_demand * 2
    
    return {
        'recommended_min': int(recommended_min),
        'recommended_max': int(recommended_max),
        'safety_stock': int(safety_stock),
        'calculation_date': datetime.utcnow().isoformat()
    }


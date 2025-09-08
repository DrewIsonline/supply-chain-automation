import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.inventory import inventory_bp
from src.routes.supplier import supplier_bp
from src.routes.reorder import reorder_bp
from src.routes.forecasting import forecasting_bp
from src.routes.webhooks import webhooks_bp
from src.routes.subscription import subscription_bp
import logging
from datetime import datetime

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'supply_chain_automation_secret_key_2024'

# Enable CORS for all routes
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register all blueprints
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(supplier_bp, url_prefix='/api/suppliers')
app.register_blueprint(reorder_bp, url_prefix='/api/reorder')
app.register_blueprint(forecasting_bp, url_prefix='/api/forecasting')
app.register_blueprint(webhooks_bp, url_prefix='/api/webhooks')
app.register_blueprint(subscription_bp, url_prefix='/api/subscription')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# Main orchestrator endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'services': {
            'inventory_bot': 'active',
            'supplier_bot': 'active',
            'reorder_bot': 'active',
            'forecasting_bot': 'active'
        }
    })

@app.route('/api/orchestrator/status', methods=['GET'])
def orchestrator_status():
    """Get status of all supply chain automation bots"""
    return jsonify({
        'orchestrator': 'active',
        'bots': {
            'inventory_management': {
                'status': 'active',
                'last_update': datetime.utcnow().isoformat(),
                'features': ['stock_monitoring', 'stockout_alerts', 'overstock_warnings']
            },
            'supplier_visibility': {
                'status': 'active',
                'last_update': datetime.utcnow().isoformat(),
                'features': ['supplier_onboarding', 'request_intake', 'performance_tracking']
            },
            'auto_reorder': {
                'status': 'active',
                'last_update': datetime.utcnow().isoformat(),
                'features': ['smart_triggers', 'automated_po', 'approval_workflow']
            },
            'demand_forecasting': {
                'status': 'active',
                'last_update': datetime.utcnow().isoformat(),
                'features': ['trend_analysis', 'seasonal_detection', 'predictive_analytics']
            }
        }
    })

@app.route('/api/orchestrator/process', methods=['POST'])
def process_supply_chain_request():
    """Main orchestrator endpoint for processing supply chain automation requests"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        request_type = data.get('type')
        payload = data.get('payload', {})
        
        logger.info(f"Processing supply chain request: {request_type}")
        
        # Route to appropriate bot based on request type
        if request_type == 'inventory_check':
            # Route to inventory management bot
            result = process_inventory_request(payload)
        elif request_type == 'supplier_request':
            # Route to supplier visibility bot
            result = process_supplier_request(payload)
        elif request_type == 'reorder_trigger':
            # Route to auto-reorder bot
            result = process_reorder_request(payload)
        elif request_type == 'demand_forecast':
            # Route to forecasting bot
            result = process_forecasting_request(payload)
        else:
            return jsonify({'error': f'Unknown request type: {request_type}'}), 400
        
        return jsonify({
            'success': True,
            'request_type': request_type,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing supply chain request: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_inventory_request(payload):
    """Process inventory management requests"""
    # This will be implemented by the inventory bot
    return {
        'bot': 'inventory_management',
        'action': 'processed',
        'data': payload
    }

def process_supplier_request(payload):
    """Process supplier visibility requests"""
    # This will be implemented by the supplier bot
    return {
        'bot': 'supplier_visibility',
        'action': 'processed',
        'data': payload
    }

def process_reorder_request(payload):
    """Process auto-reorder requests"""
    # This will be implemented by the reorder bot
    return {
        'bot': 'auto_reorder',
        'action': 'processed',
        'data': payload
    }

def process_forecasting_request(payload):
    """Process demand forecasting requests"""
    # This will be implemented by the forecasting bot
    return {
        'bot': 'demand_forecasting',
        'action': 'processed',
        'data': payload
    }

# Zapier integration endpoints
@app.route('/api/zapier/triggers', methods=['GET'])
def zapier_triggers():
    """List available triggers for Zapier integration"""
    return jsonify({
        'triggers': [
            {
                'key': 'stockout_alert',
                'name': 'Stock Out Alert',
                'description': 'Triggered when inventory falls below minimum threshold',
                'webhook_url': '/api/webhooks/stockout'
            },
            {
                'key': 'overstock_warning',
                'name': 'Overstock Warning',
                'description': 'Triggered when inventory exceeds maximum threshold',
                'webhook_url': '/api/webhooks/overstock'
            },
            {
                'key': 'supplier_request',
                'name': 'New Supplier Request',
                'description': 'Triggered when a new supplier request is received',
                'webhook_url': '/api/webhooks/supplier_request'
            },
            {
                'key': 'reorder_generated',
                'name': 'Reorder Generated',
                'description': 'Triggered when an automatic reorder is generated',
                'webhook_url': '/api/webhooks/reorder_generated'
            },
            {
                'key': 'forecast_updated',
                'name': 'Forecast Updated',
                'description': 'Triggered when demand forecast is updated',
                'webhook_url': '/api/webhooks/forecast_updated'
            }
        ]
    })

@app.route('/api/zapier/actions', methods=['GET'])
def zapier_actions():
    """List available actions for Zapier integration"""
    return jsonify({
        'actions': [
            {
                'key': 'update_inventory',
                'name': 'Update Inventory',
                'description': 'Update inventory levels for a product',
                'endpoint': '/api/inventory/update'
            },
            {
                'key': 'create_supplier_request',
                'name': 'Create Supplier Request',
                'description': 'Create a new supplier request',
                'endpoint': '/api/suppliers/request'
            },
            {
                'key': 'trigger_reorder',
                'name': 'Trigger Reorder',
                'description': 'Manually trigger a reorder for a product',
                'endpoint': '/api/reorder/trigger'
            },
            {
                'key': 'update_forecast',
                'name': 'Update Forecast',
                'description': 'Update demand forecast parameters',
                'endpoint': '/api/forecasting/update'
            }
        ]
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    logger.info("Starting Supply Chain Automation Orchestrator...")
    app.run(host='0.0.0.0', port=5001, debug=True)


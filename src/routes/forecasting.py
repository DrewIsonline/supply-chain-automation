from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
import json
import math

forecasting_bp = Blueprint('forecasting', __name__)
logger = logging.getLogger(__name__)

# In-memory storage for demo (replace with database in production)
forecast_data = {}
historical_data = {}
market_trends = {}
forecast_models = {}

@forecasting_bp.route('/status', methods=['GET'])
def forecasting_status():
    """Get demand forecasting bot status"""
    return jsonify({
        'bot': 'demand_forecasting',
        'status': 'active',
        'features': [
            'historical_data_analysis',
            'seasonal_trend_detection',
            'demand_forecasting',
            'market_trend_integration',
            'predictive_analytics',
            'accuracy_tracking'
        ],
        'active_forecasts': len(forecast_data),
        'historical_records': len(historical_data)
    })

@forecasting_bp.route('/forecasts', methods=['GET'])
def get_all_forecasts():
    """Get all demand forecasts"""
    return jsonify({
        'forecasts': list(forecast_data.values()),
        'total_count': len(forecast_data)
    })

@forecasting_bp.route('/forecasts/<product_id>', methods=['GET'])
def get_product_forecast(product_id):
    """Get demand forecast for specific product"""
    if product_id not in forecast_data:
        return jsonify({'error': 'Forecast not found for this product'}), 404
    
    return jsonify(forecast_data[product_id])

@forecasting_bp.route('/forecasts', methods=['POST'])
def create_forecast():
    """Create new demand forecast"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'forecast_period_days']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        product_id = data['product_id']
        forecast_period = data['forecast_period_days']
        
        # Get historical data for the product
        historical = historical_data.get(product_id, [])
        
        if len(historical) < 7:  # Need at least 7 data points
            return jsonify({'error': 'Insufficient historical data for forecasting'}), 400
        
        # Generate forecast using simple moving average and trend analysis
        forecast_result = generate_demand_forecast(product_id, historical, forecast_period)
        
        forecast_data[product_id] = {
            'product_id': product_id,
            'product_name': data.get('product_name', ''),
            'forecast_period_days': forecast_period,
            'predicted_demand': forecast_result['predicted_demand'],
            'confidence_level': forecast_result['confidence_level'],
            'trend_direction': forecast_result['trend_direction'],
            'seasonal_factor': forecast_result['seasonal_factor'],
            'forecast_breakdown': forecast_result['daily_forecast'],
            'model_used': forecast_result['model_used'],
            'created_date': datetime.utcnow().isoformat(),
            'valid_until': (datetime.utcnow() + timedelta(days=forecast_period)).isoformat(),
            'accuracy_score': forecast_result.get('accuracy_score', 0)
        }
        
        # Trigger webhook for forecast update
        trigger_forecast_webhook(forecast_data[product_id])
        
        logger.info(f"Created demand forecast for product: {product_id}")
        
        return jsonify({
            'success': True,
            'forecast': forecast_data[product_id]
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecasting_bp.route('/historical', methods=['POST'])
def add_historical_data():
    """Add historical sales/demand data"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'date', 'demand']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        product_id = data['product_id']
        
        if product_id not in historical_data:
            historical_data[product_id] = []
        
        historical_record = {
            'date': data['date'],
            'demand': data['demand'],
            'sales': data.get('sales', 0),
            'price': data.get('price', 0),
            'promotions': data.get('promotions', False),
            'external_factors': data.get('external_factors', {}),
            'added_date': datetime.utcnow().isoformat()
        }
        
        historical_data[product_id].append(historical_record)
        
        # Keep only last 365 days of data
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        historical_data[product_id] = [
            record for record in historical_data[product_id]
            if datetime.fromisoformat(record['date']) > cutoff_date
        ]
        
        # Sort by date
        historical_data[product_id].sort(key=lambda x: x['date'])
        
        logger.info(f"Added historical data for product: {product_id}")
        
        return jsonify({
            'success': True,
            'total_records': len(historical_data[product_id])
        })
        
    except Exception as e:
        logger.error(f"Error adding historical data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecasting_bp.route('/historical/<product_id>', methods=['GET'])
def get_historical_data(product_id):
    """Get historical data for product"""
    if product_id not in historical_data:
        return jsonify({'error': 'No historical data found for this product'}), 404
    
    return jsonify({
        'product_id': product_id,
        'historical_data': historical_data[product_id],
        'total_records': len(historical_data[product_id])
    })

@forecasting_bp.route('/trends', methods=['GET'])
def get_market_trends():
    """Get market trends data"""
    return jsonify({
        'trends': list(market_trends.values()),
        'total_trends': len(market_trends)
    })

@forecasting_bp.route('/trends', methods=['POST'])
def add_market_trend():
    """Add market trend data"""
    try:
        data = request.get_json()
        
        required_fields = ['trend_id', 'category', 'trend_value']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        trend_id = data['trend_id']
        
        market_trends[trend_id] = {
            'trend_id': trend_id,
            'category': data['category'],
            'trend_value': data['trend_value'],
            'trend_direction': data.get('trend_direction', 'stable'),
            'impact_factor': data.get('impact_factor', 1.0),
            'source': data.get('source', ''),
            'date_recorded': datetime.utcnow().isoformat(),
            'valid_until': data.get('valid_until', '')
        }
        
        logger.info(f"Added market trend: {trend_id}")
        
        return jsonify({
            'success': True,
            'trend': market_trends[trend_id]
        })
        
    except Exception as e:
        logger.error(f"Error adding market trend: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecasting_bp.route('/analytics', methods=['GET'])
def get_forecasting_analytics():
    """Get forecasting analytics and performance metrics"""
    try:
        total_forecasts = len(forecast_data)
        active_forecasts = len([f for f in forecast_data.values() 
                              if datetime.fromisoformat(f['valid_until']) > datetime.utcnow()])
        
        # Calculate average accuracy
        accuracy_scores = [f.get('accuracy_score', 0) for f in forecast_data.values() if f.get('accuracy_score', 0) > 0]
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
        
        # Get trend summary
        trend_summary = {}
        for trend in market_trends.values():
            category = trend['category']
            if category not in trend_summary:
                trend_summary[category] = {'count': 0, 'avg_impact': 0}
            trend_summary[category]['count'] += 1
            trend_summary[category]['avg_impact'] += trend.get('impact_factor', 1.0)
        
        for category in trend_summary:
            trend_summary[category]['avg_impact'] /= trend_summary[category]['count']
        
        analytics = {
            'summary': {
                'total_forecasts': total_forecasts,
                'active_forecasts': active_forecasts,
                'average_accuracy': round(avg_accuracy, 2),
                'total_products_tracked': len(historical_data)
            },
            'performance': {
                'forecast_accuracy_trend': calculate_accuracy_trend(),
                'most_accurate_model': get_most_accurate_model(),
                'seasonal_patterns_detected': count_seasonal_patterns()
            },
            'market_trends': trend_summary
        }
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecasting_bp.route('/models', methods=['GET'])
def get_forecast_models():
    """Get available forecasting models"""
    return jsonify({
        'models': [
            {
                'model_id': 'moving_average',
                'name': 'Moving Average',
                'description': 'Simple moving average with trend adjustment',
                'best_for': 'Stable demand patterns'
            },
            {
                'model_id': 'exponential_smoothing',
                'name': 'Exponential Smoothing',
                'description': 'Weighted average giving more importance to recent data',
                'best_for': 'Trending demand patterns'
            },
            {
                'model_id': 'seasonal_decomposition',
                'name': 'Seasonal Decomposition',
                'description': 'Separates trend, seasonal, and irregular components',
                'best_for': 'Seasonal demand patterns'
            },
            {
                'model_id': 'linear_regression',
                'name': 'Linear Regression',
                'description': 'Linear trend-based forecasting',
                'best_for': 'Linear growth patterns'
            }
        ]
    })

@forecasting_bp.route('/accuracy/<product_id>', methods=['POST'])
def update_forecast_accuracy(product_id):
    """Update forecast accuracy based on actual results"""
    try:
        if product_id not in forecast_data:
            return jsonify({'error': 'Forecast not found for this product'}), 404
        
        data = request.get_json()
        
        required_fields = ['actual_demand', 'period_end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        forecast = forecast_data[product_id]
        predicted_demand = forecast['predicted_demand']
        actual_demand = data['actual_demand']
        
        # Calculate accuracy metrics
        error = abs(predicted_demand - actual_demand)
        percentage_error = (error / max(actual_demand, 1)) * 100
        accuracy = max(0, 100 - percentage_error)
        
        # Update forecast with accuracy data
        forecast['actual_demand'] = actual_demand
        forecast['forecast_error'] = error
        forecast['percentage_error'] = round(percentage_error, 2)
        forecast['accuracy_score'] = round(accuracy, 2)
        forecast['accuracy_updated'] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated forecast accuracy for product {product_id}: {accuracy}%")
        
        return jsonify({
            'success': True,
            'accuracy_metrics': {
                'predicted_demand': predicted_demand,
                'actual_demand': actual_demand,
                'forecast_error': error,
                'percentage_error': round(percentage_error, 2),
                'accuracy_score': round(accuracy, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating forecast accuracy: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_demand_forecast(product_id, historical, forecast_period):
    """Generate demand forecast using multiple models"""
    try:
        # Extract demand values
        demands = [record['demand'] for record in historical[-30:]]  # Last 30 days
        
        if len(demands) < 7:
            raise ValueError("Insufficient data for forecasting")
        
        # Simple moving average
        ma_forecast = sum(demands[-7:]) / 7  # 7-day moving average
        
        # Trend calculation
        if len(demands) >= 14:
            recent_avg = sum(demands[-7:]) / 7
            older_avg = sum(demands[-14:-7]) / 7
            trend = (recent_avg - older_avg) / 7  # Daily trend
        else:
            trend = 0
        
        # Seasonal factor (simplified)
        seasonal_factor = 1.0
        current_day = datetime.utcnow().weekday()
        if len(demands) >= 14:
            # Calculate weekly pattern
            weekly_pattern = {}
            for i, record in enumerate(historical[-14:]):
                day = datetime.fromisoformat(record['date']).weekday()
                if day not in weekly_pattern:
                    weekly_pattern[day] = []
                weekly_pattern[day].append(record['demand'])
            
            if current_day in weekly_pattern:
                day_avg = sum(weekly_pattern[current_day]) / len(weekly_pattern[current_day])
                overall_avg = sum(demands[-14:]) / 14
                seasonal_factor = day_avg / max(overall_avg, 1)
        
        # Generate daily forecast
        daily_forecast = []
        base_demand = ma_forecast
        
        for day in range(forecast_period):
            # Apply trend
            daily_demand = base_demand + (trend * day)
            
            # Apply seasonal factor
            day_of_week = (current_day + day) % 7
            if day_of_week in [5, 6]:  # Weekend
                daily_demand *= 0.8  # Assume lower weekend demand
            
            daily_demand *= seasonal_factor
            daily_demand = max(0, daily_demand)  # Ensure non-negative
            
            daily_forecast.append({
                'date': (datetime.utcnow() + timedelta(days=day)).isoformat()[:10],
                'predicted_demand': round(daily_demand, 2)
            })
        
        # Calculate total predicted demand
        total_predicted = sum(day['predicted_demand'] for day in daily_forecast)
        
        # Determine confidence level based on data quality
        confidence = min(95, 60 + (len(demands) * 2))  # More data = higher confidence
        
        # Determine trend direction
        if trend > 0.1:
            trend_direction = 'increasing'
        elif trend < -0.1:
            trend_direction = 'decreasing'
        else:
            trend_direction = 'stable'
        
        return {
            'predicted_demand': round(total_predicted, 2),
            'confidence_level': confidence,
            'trend_direction': trend_direction,
            'seasonal_factor': round(seasonal_factor, 2),
            'daily_forecast': daily_forecast,
            'model_used': 'moving_average_with_trend',
            'accuracy_score': 0  # Will be updated when actual data is available
        }
        
    except Exception as e:
        logger.error(f"Error generating forecast: {str(e)}")
        raise

def trigger_forecast_webhook(forecast):
    """Trigger webhook for forecast update (for Zapier integration)"""
    webhook_payload = {
        'trigger': 'forecast_updated',
        'product_id': forecast['product_id'],
        'predicted_demand': forecast['predicted_demand'],
        'confidence_level': forecast['confidence_level'],
        'trend_direction': forecast['trend_direction'],
        'forecast_period_days': forecast['forecast_period_days'],
        'timestamp': forecast['created_date']
    }
    
    # In production, send to configured webhook URLs
    logger.info(f"Webhook triggered for forecast update: {forecast['product_id']}")
    return webhook_payload

def calculate_accuracy_trend():
    """Calculate accuracy trend over time"""
    # Simplified implementation
    recent_forecasts = [f for f in forecast_data.values() 
                       if f.get('accuracy_score', 0) > 0]
    
    if len(recent_forecasts) < 2:
        return 'insufficient_data'
    
    recent_accuracy = sum(f['accuracy_score'] for f in recent_forecasts[-5:]) / min(5, len(recent_forecasts))
    older_accuracy = sum(f['accuracy_score'] for f in recent_forecasts[-10:-5]) / min(5, len(recent_forecasts) - 5)
    
    if recent_accuracy > older_accuracy + 5:
        return 'improving'
    elif recent_accuracy < older_accuracy - 5:
        return 'declining'
    else:
        return 'stable'

def get_most_accurate_model():
    """Get the most accurate forecasting model"""
    model_accuracy = {}
    
    for forecast in forecast_data.values():
        if forecast.get('accuracy_score', 0) > 0:
            model = forecast.get('model_used', 'unknown')
            if model not in model_accuracy:
                model_accuracy[model] = []
            model_accuracy[model].append(forecast['accuracy_score'])
    
    if not model_accuracy:
        return 'no_data'
    
    # Calculate average accuracy for each model
    avg_accuracy = {}
    for model, scores in model_accuracy.items():
        avg_accuracy[model] = sum(scores) / len(scores)
    
    return max(avg_accuracy, key=avg_accuracy.get)

def count_seasonal_patterns():
    """Count products with detected seasonal patterns"""
    seasonal_count = 0
    
    for forecast in forecast_data.values():
        if abs(forecast.get('seasonal_factor', 1.0) - 1.0) > 0.1:
            seasonal_count += 1
    
    return seasonal_count


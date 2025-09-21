"""
Main Flask application
"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from routes.stock_routes import stock_bp
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app(config_name='default'):
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Enable CORS for all routes
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(stock_bp)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'KyzerEye Stock Data API',
            'version': '1.0.0'
        })
    
    # API documentation endpoint
    @app.route('/api')
    def api_info():
        """API information and available endpoints"""
        return jsonify({
            'service': 'KyzerEye Stock Data API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'api_info': '/api',
                'stocks': {
                    'get_all_symbols': 'GET /api/stocks/',
                    'sync_symbols': 'POST /api/stocks/sync',
                    'get_stock_data': 'GET /api/stocks/<symbol>',
                    'fetch_stock_data': 'POST /api/stocks/<symbol>/fetch',
                    'fetch_all_data': 'POST /api/stocks/fetch-all',
                    'get_latest_data': 'GET /api/stocks/latest',
                    'get_stock_info': 'GET /api/stocks/<symbol>/info'
                }
            },
            'example_requests': {
                'sync_symbols': {
                    'method': 'POST',
                    'url': '/api/stocks/sync',
                    'body': '{"filename": "stock_symbols.txt"}'
                },
                'fetch_single_stock': {
                    'method': 'POST',
                    'url': '/api/stocks/AAPL/fetch',
                    'body': '{"period": "1y"}'
                },
                'fetch_all_stocks': {
                    'method': 'POST',
                    'url': '/api/stocks/fetch-all',
                    'body': '{"period": "1y", "delay": 1.0}'
                },
                'get_stock_data': {
                    'method': 'GET',
                    'url': '/api/stocks/AAPL?start_date=2023-01-01&end_date=2023-12-31'
                }
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'success': False,
            'error': 'Endpoint not found',
            'message': 'Check /api for available endpoints'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Check server logs for details'
        }), 500
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5001)

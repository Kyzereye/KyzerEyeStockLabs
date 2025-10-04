"""
Flask routes for stock data API
"""
from flask import Blueprint, jsonify, request
from services.stock_service import StockService
import logging

logger = logging.getLogger(__name__)

# Create blueprint
stock_bp = Blueprint('stocks', __name__, url_prefix='/api/stocks')

@stock_bp.route('/', methods=['GET'])
def get_all_symbols():
    """Get all stock symbols"""
    try:
        service = StockService()
        symbols = service.get_all_symbols()
        return jsonify({
            'success': True,
            'data': symbols,
            'count': len(symbols)
        })
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stock_bp.route('/sync', methods=['POST'])
def sync_symbols_from_file():
    """Sync stock symbols from file to database"""
    try:
        filename = request.json.get('filename', 'stock_symbols.txt') if request.is_json else 'stock_symbols.txt'
        
        service = StockService()
        result = service.sync_symbols_from_file(filename)
        
        return jsonify({
            'success': True,
            'message': f'Synced {len(result["success"])} symbols successfully',
            'data': result
        })
    except Exception as e:
        logger.error(f"Error syncing symbols: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stock_bp.route('/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """Get stock data for a specific symbol"""
    try:
        service = StockService()
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        days = request.args.get('days')
        include_ema = request.args.get('include_ema', 'false').lower() == 'true'
        
        # Convert string dates to date objects if provided
        from datetime import datetime, timedelta
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        # If days parameter is provided and > 0, calculate start_date
        if days and not start_date_obj:
            days_int = int(days)
            if days_int > 0:  # Only limit data if days > 0
                end_date_obj = datetime.now().date() if not end_date_obj else end_date_obj
                start_date_obj = end_date_obj - timedelta(days=days_int)
            # If days = 0, we want all available data, so don't set start_date_obj
        
        # Use appropriate method based on whether EMA is requested
        if include_ema:
            data = service.get_stock_data_with_ema(symbol.upper(), start_date_obj, end_date_obj)
        else:
            data = service.get_stock_data(symbol.upper(), start_date_obj, end_date_obj)
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"Error getting stock data for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stock_bp.route('/<symbol>/fetch', methods=['POST'])
def fetch_stock_data(symbol):
    """Fetch and store stock data for a specific symbol"""
    try:
        service = StockService()
        
        # Get period from request body
        period = '1y'  # default
        if request.is_json and request.json:
            period = request.json.get('period', '1y')
        
        result = service.fetch_and_store_stock_data(symbol.upper(), period)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'Successfully fetched and stored data for {symbol.upper()}',
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stock_bp.route('/fetch-all', methods=['POST'])
def fetch_all_stocks_data():
    """Fetch and store data for all symbols"""
    try:
        service = StockService()
        
        # Get parameters from request body
        period = '1y'  # default
        delay = 1.0    # default
        
        if request.is_json and request.json:
            period = request.json.get('period', '1y')
            delay = request.json.get('delay', 1.0)
        
        result = service.fetch_all_stocks_data(period, delay)
        
        return jsonify({
            'success': True,
            'message': f'Fetch completed for {result["total_symbols"]} symbols',
            'data': result
        })
    except Exception as e:
        logger.error(f"Error fetching all stocks data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stock_bp.route('/latest', methods=['GET'])
def get_latest_data():
    """Get latest data for all stocks"""
    try:
        service = StockService()
        data = service.get_latest_data_for_all_stocks()
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"Error getting latest data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stock_bp.route('/<symbol>/info', methods=['GET'])
def get_stock_info(symbol):
    """Get basic information about a stock symbol"""
    try:
        service = StockService()
        symbol_id = service.get_symbol_id(symbol.upper())
        
        if not symbol_id:
            return jsonify({
                'success': False,
                'error': f'Symbol {symbol.upper()} not found'
            }), 404
        
        # Get symbol details
        symbols = service.get_all_symbols()
        symbol_info = next((s for s in symbols if s['symbol'] == symbol.upper()), None)
        
        if not symbol_info:
            return jsonify({
                'success': False,
                'error': f'Symbol {symbol.upper()} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': symbol_info
        })
    except Exception as e:
        logger.error(f"Error getting stock info for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

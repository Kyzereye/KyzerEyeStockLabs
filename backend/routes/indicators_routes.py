"""
Flask routes for technical indicators API
"""
from flask import Blueprint, jsonify, request
from services.technical_indicators import TechnicalIndicatorsService
from utils.database import get_db_connection
from config.indicators_config import get_enabled_indicators, INDICATOR_CONFIGS
import logging

logger = logging.getLogger(__name__)

# Create blueprint
indicators_bp = Blueprint('indicators', __name__, url_prefix='/api/indicators')

@indicators_bp.route('/', methods=['GET'])
def get_enabled_indicators_list():
    """Get list of enabled indicators"""
    try:
        enabled = get_enabled_indicators()
        return jsonify({
            'success': True,
            'enabled_indicators': enabled,
            'count': len(enabled)
        })
    except Exception as e:
        logger.error(f"Error getting enabled indicators: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@indicators_bp.route('/config', methods=['GET'])
def get_indicators_config():
    """Get full indicators configuration"""
    try:
        return jsonify({
            'success': True,
            'config': INDICATOR_CONFIGS
        })
    except Exception as e:
        logger.error(f"Error getting indicators config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@indicators_bp.route('/<symbol>', methods=['GET'])
def get_symbol_indicators(symbol):
    """Get technical indicators for a specific symbol"""
    try:
        db = get_db_connection()
        if not db.connect():
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        # Get symbol ID
        symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
        symbol_result = db.execute_query(symbol_query, (symbol.upper(),))
        
        if not symbol_result:
            return jsonify({
                'success': False,
                'error': f'Symbol {symbol.upper()} not found'
            }), 404
        
        symbol_id = symbol_result[0]['id']
        
        # Get query parameters
        indicator_name = request.args.get('indicator')
        period = request.args.get('period')
        limit = request.args.get('limit', 100, type=int)
        
        # Build query
        query = """
            SELECT date, indicator_name, value, period
            FROM technical_indicators
            WHERE symbol_id = %s
        """
        params = [symbol_id]
        
        if indicator_name:
            query += " AND indicator_name LIKE %s"
            params.append(f"%{indicator_name}%")
        
        if period:
            query += " AND period = %s"
            params.append(int(period))
        
        query += " ORDER BY date DESC, indicator_name"
        query += f" LIMIT {limit}"
        
        result = db.execute_query(query, params)
        
        if not result:
            return jsonify({
                'success': True,
                'symbol': symbol.upper(),
                'data': [],
                'message': 'No indicators found for this symbol'
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'data': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting indicators for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.disconnect()

@indicators_bp.route('/<symbol>/calculate', methods=['POST'])
def calculate_indicators_for_symbol(symbol):
    """Calculate and store indicators for a specific symbol"""
    try:
        db = get_db_connection()
        if not db.connect():
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        # Get symbol ID
        symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
        symbol_result = db.execute_query(symbol_query, (symbol.upper(),))
        
        if not symbol_result:
            return jsonify({
                'success': False,
                'error': f'Symbol {symbol.upper()} not found'
            }), 404
        
        symbol_id = symbol_result[0]['id']
        
        # Get stock data
        data_query = """
            SELECT date, open, high, low, close, volume
            FROM daily_stock_data
            WHERE symbol_id = %s
            ORDER BY date ASC
        """
        data_result = db.execute_query(data_query, (symbol_id,))
        
        if not data_result:
            return jsonify({
                'success': False,
                'error': f'No stock data found for {symbol.upper()}'
            }), 404
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(data_result)
        
        # Calculate indicators
        service = TechnicalIndicatorsService()
        success = service.calculate_and_store_indicators(symbol_id, df)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully calculated indicators for {symbol.upper()}',
                'data_points': len(df)
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to calculate indicators for {symbol.upper()}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error calculating indicators for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.disconnect()

@indicators_bp.route('/calculate-all', methods=['POST'])
def calculate_all_indicators():
    """Calculate indicators for all symbols with stock data"""
    try:
        db = get_db_connection()
        if not db.connect():
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        # Get all symbols with data
        symbols_query = """
            SELECT DISTINCT s.id, s.symbol, COUNT(d.id) as data_count
            FROM stock_symbols s
            INNER JOIN daily_stock_data d ON s.id = d.symbol_id
            GROUP BY s.id, s.symbol
            HAVING data_count > 0
            ORDER BY s.symbol
        """
        symbols_result = db.execute_query(symbols_query)
        
        if not symbols_result:
            return jsonify({
                'success': False,
                'error': 'No symbols found with stock data'
            }), 404
        
        # Calculate indicators for each symbol
        service = TechnicalIndicatorsService()
        results = {
            'success': [],
            'failed': [],
            'total_symbols': len(symbols_result)
        }
        
        for symbol_data in symbols_result:
            symbol_id = symbol_data['id']
            symbol_name = symbol_data['symbol']
            
            try:
                # Get stock data for this symbol
                data_query = """
                    SELECT date, open, high, low, close, volume
                    FROM daily_stock_data
                    WHERE symbol_id = %s
                    ORDER BY date ASC
                """
                data_result = db.execute_query(data_query, (symbol_id,))
                
                if data_result:
                    import pandas as pd
                    df = pd.DataFrame(data_result)
                    success = service.calculate_and_store_indicators(symbol_id, df)
                    
                    if success:
                        results['success'].append({
                            'symbol': symbol_name,
                            'data_points': len(df)
                        })
                    else:
                        results['failed'].append(symbol_name)
                else:
                    results['failed'].append(symbol_name)
                    
            except Exception as e:
                logger.error(f"Error processing {symbol_name}: {e}")
                results['failed'].append(symbol_name)
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(symbols_result)} symbols',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error calculating all indicators: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.disconnect()

@indicators_bp.route('/latest/<symbol>', methods=['GET'])
def get_latest_indicators(symbol):
    """Get latest indicator values for a specific symbol"""
    try:
        db = get_db_connection()
        if not db.connect():
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        # Get symbol ID
        symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
        symbol_result = db.execute_query(symbol_query, (symbol.upper(),))
        
        if not symbol_result:
            return jsonify({
                'success': False,
                'error': f'Symbol {symbol.upper()} not found'
            }), 404
        
        symbol_id = symbol_result[0]['id']
        
        # Get latest indicators
        query = """
            SELECT t1.date, t1.indicator_name, t1.value, t1.period
            FROM technical_indicators t1
            INNER JOIN (
                SELECT indicator_name, MAX(date) as max_date
                FROM technical_indicators
                WHERE symbol_id = %s
                GROUP BY indicator_name
            ) t2 ON t1.indicator_name = t2.indicator_name 
                 AND t1.date = t2.max_date
            WHERE t1.symbol_id = %s
            ORDER BY t1.indicator_name
        """
        result = db.execute_query(query, (symbol_id, symbol_id))
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'data': result,
            'count': len(result) if result else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting latest indicators for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.disconnect()

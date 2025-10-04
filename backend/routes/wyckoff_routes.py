#!/usr/bin/env python3
"""
Wyckoff Analysis API Routes
Flask blueprint for Wyckoff Method analysis endpoints
"""

from flask import Blueprint, jsonify, request
from services.wyckoff_analysis import WyckoffAnalysisService
from utils.database import get_db_connection
import pandas as pd
import logging

logger = logging.getLogger(__name__)

wyckoff_bp = Blueprint('wyckoff', __name__, url_prefix='/api/wyckoff')

@wyckoff_bp.route('/', methods=['GET'])
def get_wyckoff_info():
    """Get Wyckoff analysis API information"""
    return jsonify({
        'service': 'Wyckoff Method Analysis API',
        'version': '1.0.0',
        'description': 'Technical analysis using Wyckoff Method principles',
        'endpoints': {
            'analyze_all': 'POST /api/wyckoff/analyze-all',
            'analyze_symbol': 'POST /api/wyckoff/<symbol>/analyze',
            'get_report': 'GET /api/wyckoff/report',
            'get_phases': 'GET /api/wyckoff/<symbol>/phases',
            'get_signals': 'GET /api/wyckoff/<symbol>/signals'
        },
        'wyckoff_phases': {
            'accumulation': 'Sideways movement with increasing volume - institutional buying',
            'distribution': 'Sideways movement with decreasing volume - institutional selling',
            'markup': 'Uptrend with volume confirmation - price advance',
            'markdown': 'Downtrend - price decline'
        },
        'analysis_components': [
            'Price action patterns',
            'Volume-price relationships',
            'Support and resistance levels',
            'Wyckoff phase identification',
            'Trading signals generation',
            'Overall Wyckoff score'
        ]
    })

@wyckoff_bp.route('/analyze-all', methods=['POST'])
def analyze_all_stocks():
    """Analyze all stocks using Wyckoff Method"""
    try:
        # Get all symbols with data
        db = get_db_connection()
        if not db.connect():
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        # Get symbols with stock data
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
        
        # Initialize Wyckoff analysis service
        wyckoff_service = WyckoffAnalysisService()
        analysis_results = []
        
        for symbol_data in symbols_result:
            symbol_id = symbol_data['id']
            symbol_name = symbol_data['symbol']
            
            try:
                # Get stock data
                data_query = """
                    SELECT date, open, high, low, close, volume
                    FROM daily_stock_data
                    WHERE symbol_id = %s
                    ORDER BY date ASC
                """
                data_result = db.execute_query(data_query, (symbol_id,))
                
                if data_result:
                    df = pd.DataFrame(data_result)
                    df['date'] = pd.to_datetime(df['date'])
                    
                    # Perform Wyckoff analysis
                    analysis = wyckoff_service.analyze_wyckoff_phases(df, symbol_name)
                    analysis_results.append(analysis)
                else:
                    analysis_results.append({
                        'symbol': symbol_name,
                        'error': 'No stock data found'
                    })
                    
            except Exception as e:
                logger.error(f"Error analyzing {symbol_name}: {e}")
                analysis_results.append({
                    'symbol': symbol_name,
                    'error': str(e)
                })
        
        # Generate comprehensive report
        report = wyckoff_service.generate_wyckoff_report(analysis_results)
        
        return jsonify({
            'success': True,
            'message': f'Analyzed {len(symbols_result)} stocks using Wyckoff Method',
            'report': report
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_all_stocks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.disconnect()

@wyckoff_bp.route('/<symbol>/analyze', methods=['POST'])
def analyze_symbol(symbol):
    """Analyze a specific symbol using Wyckoff Method"""
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
                'error': f'Symbol {symbol.upper()} not found in database'
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
        
        # Perform Wyckoff analysis
        df = pd.DataFrame(data_result)
        df['date'] = pd.to_datetime(df['date'])
        
        wyckoff_service = WyckoffAnalysisService()
        analysis = wyckoff_service.analyze_wyckoff_phases(df, symbol.upper())
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.disconnect()

@wyckoff_bp.route('/report', methods=['GET'])
def get_wyckoff_report():
    """Get a quick Wyckoff analysis report for all stocks"""
    try:
        # Get recent analysis or perform new analysis
        # For now, we'll perform a quick analysis
        
        db = get_db_connection()
        if not db.connect():
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        # Get symbols with data
        symbols_query = """
            SELECT DISTINCT s.id, s.symbol
            FROM stock_symbols s
            INNER JOIN daily_stock_data d ON s.id = d.symbol_id
            GROUP BY s.id, s.symbol
            HAVING COUNT(d.id) > 0
            ORDER BY s.symbol
        """
        symbols_result = db.execute_query(symbols_query)
        
        if not symbols_result:
            return jsonify({
                'success': False,
                'error': 'No symbols found with stock data'
            }), 404
        
        # Quick analysis for summary
        wyckoff_service = WyckoffAnalysisService()
        quick_analysis = []
        
        for symbol_data in symbols_result[:5]:  # Limit to 5 for quick report
            symbol_id = symbol_data['id']
            symbol_name = symbol_data['symbol']
            
            try:
                # Get recent data (last 60 days)
                data_query = """
                    SELECT date, open, high, low, close, volume
                    FROM daily_stock_data
                    WHERE symbol_id = %s
                    ORDER BY date DESC
                    LIMIT 60
                """
                data_result = db.execute_query(data_query, (symbol_id,))
                
                if data_result:
                    df = pd.DataFrame(data_result)
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date').reset_index(drop=True)
                    
                    analysis = wyckoff_service.analyze_wyckoff_phases(df, symbol_name)
                    quick_analysis.append({
                        'symbol': symbol_name,
                        'current_phase': analysis.get('current_phase', {}).get('phase', 'Unknown'),
                        'wyckoff_score': analysis.get('wyckoff_score', {}).get('total_score', 0),
                        'signal': analysis.get('signals', {}).get('primary_signal', 'HOLD'),
                        'confidence': analysis.get('current_phase', {}).get('confidence', 0)
                    })
                    
            except Exception as e:
                logger.error(f"Error in quick analysis for {symbol_name}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'report_type': 'Quick Wyckoff Analysis',
            'total_symbols_available': len(symbols_result),
            'analyzed_symbols': len(quick_analysis),
            'analysis_results': quick_analysis,
            'note': 'This is a quick analysis. Use /api/wyckoff/analyze-all for comprehensive analysis.'
        })
        
    except Exception as e:
        logger.error(f"Error generating Wyckoff report: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.disconnect()

@wyckoff_bp.route('/<symbol>/phases', methods=['GET'])
def get_symbol_phases(symbol):
    """Get Wyckoff phases for a specific symbol"""
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
                'error': f'Symbol {symbol.upper()} not found in database'
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
        
        # Perform Wyckoff analysis
        df = pd.DataFrame(data_result)
        df['date'] = pd.to_datetime(df['date'])
        
        wyckoff_service = WyckoffAnalysisService()
        analysis = wyckoff_service.analyze_wyckoff_phases(df, symbol.upper())
        
        if 'error' in analysis:
            return jsonify({
                'success': False,
                'error': analysis['error']
            }), 500
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'current_phase': analysis['current_phase'],
            'phases': analysis['phases'],
            'volume_analysis': analysis['volume_analysis']
        })
        
    except Exception as e:
        logger.error(f"Error getting phases for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.disconnect()

@wyckoff_bp.route('/<symbol>/signals', methods=['GET'])
def get_symbol_signals(symbol):
    """Get Wyckoff trading signals for a specific symbol"""
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
                'error': f'Symbol {symbol.upper()} not found in database'
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
        
        # Perform Wyckoff analysis
        df = pd.DataFrame(data_result)
        df['date'] = pd.to_datetime(df['date'])
        
        wyckoff_service = WyckoffAnalysisService()
        analysis = wyckoff_service.analyze_wyckoff_phases(df, symbol.upper())
        
        if 'error' in analysis:
            return jsonify({
                'success': False,
                'error': analysis['error']
            }), 500
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'current_price': analysis['current_price'],
            'signals': analysis['signals'],
            'support_resistance': analysis['support_resistance'],
            'wyckoff_score': analysis['wyckoff_score']
        })
        
    except Exception as e:
        logger.error(f"Error getting signals for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.disconnect()


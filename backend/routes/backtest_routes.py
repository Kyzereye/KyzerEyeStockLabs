#!/usr/bin/env python3
"""
Backtest API Routes
Flask blueprint for backtest results and analysis endpoints
"""

from flask import Blueprint, jsonify, request
from services.wyckoff_backtest import WyckoffBacktestEngine
from utils.database import get_db_connection
import pandas as pd
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

backtest_bp = Blueprint('backtest', __name__, url_prefix='/api/backtest')

@backtest_bp.route('/', methods=['GET'])
def get_backtest_info():
    """Get backtest API information"""
    return jsonify({
        'service': 'Wyckoff Backtest API',
        'version': '1.0.0',
        'description': 'Backtesting and analysis for Wyckoff Method trading strategies',
        'endpoints': {
            'run_backtest': 'POST /api/backtest/run',
            'get_backtest_results': 'GET /api/backtest/results',
            'get_symbol_backtest': 'GET /api/backtest/<symbol>',
            'get_available_reports': 'GET /api/backtest/reports',
            'get_report': 'GET /api/backtest/reports/<filename>'
        },
        'features': [
            'Wyckoff phase analysis',
            'Trade simulation',
            'Performance metrics',
            'Risk analysis',
            'Historical backtest reports'
        ]
    })

@backtest_bp.route('/run', methods=['POST'])
def run_backtest():
    """Run Wyckoff backtest on all stocks or specific symbol"""
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol')
        initial_capital = data.get('initial_capital', 100000.0)
        
        # Initialize backtest engine
        engine = WyckoffBacktestEngine(initial_capital=initial_capital)
        
        # Get symbols to backtest
        db = get_db_connection()
        if not db.connect():
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        if symbol:
            # Backtest specific symbol
            symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
            symbol_result = db.execute_query(symbol_query, (symbol.upper(),))
            
            if not symbol_result:
                return jsonify({
                    'success': False,
                    'error': f'Symbol {symbol.upper()} not found in database'
                }), 404
            
            symbols = [{'id': symbol_result[0]['id'], 'symbol': symbol.upper()}]
        else:
            # Backtest all symbols
            symbols_query = """
                SELECT DISTINCT s.id, s.symbol, COUNT(d.id) as data_count
                FROM stock_symbols s
                INNER JOIN daily_stock_data d ON s.id = d.symbol_id
                GROUP BY s.id, s.symbol
                HAVING data_count > 0
                ORDER BY s.symbol
            """
            symbols = db.execute_query(symbols_query)
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'No symbols found with stock data'
            }), 404
        
        # Run backtests
        results = []
        for symbol_data in symbols:
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
                    df.set_index('date', inplace=True)
                    
                    # Run backtest
                    backtest_result = engine.run_backtest(df, symbol_name)
                    
                    # Convert to JSON-serializable format
                    result_dict = convert_backtest_result_to_dict(backtest_result)
                    results.append(result_dict)
                
            except Exception as e:
                logger.error(f"Error running backtest for {symbol_name}: {e}")
                results.append({
                    'symbol': symbol_name,
                    'error': str(e)
                })
        
        db.disconnect()
        
        # Generate summary
        successful_results = [r for r in results if 'error' not in r]
        
        summary = {
            'total_symbols': len(symbols),
            'successful_backtests': len(successful_results),
            'failed_backtests': len(results) - len(successful_results),
            'total_initial_capital': initial_capital * len(symbols),
            'total_final_value': sum(r['performance_metrics']['final_value'] for r in successful_results),
            'overall_return_percent': 0
        }
        
        if summary['total_initial_capital'] > 0:
            summary['overall_return_percent'] = (
                (summary['total_final_value'] / summary['total_initial_capital']) - 1
            ) * 100
        
        return jsonify({
            'success': True,
            'message': f'Backtest completed for {len(symbols)} symbols',
            'summary': summary,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in run_backtest: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@backtest_bp.route('/results', methods=['GET'])
def get_latest_backtest_results():
    """Get the most recent backtest results"""
    try:
        # Look for the most recent backtest report file
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        report_files = []
        
        for filename in os.listdir(backend_dir):
            if filename.startswith('wyckoff_backtest_report_') and filename.endswith('.json'):
                report_files.append(filename)
        
        if not report_files:
            return jsonify({
                'success': False,
                'error': 'No backtest reports found'
            }), 404
        
        # Get the most recent report
        latest_report = sorted(report_files)[-1]
        report_path = os.path.join(backend_dir, latest_report)
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        return jsonify({
            'success': True,
            'report_filename': latest_report,
            'report_data': report_data
        })
        
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@backtest_bp.route('/<symbol>', methods=['GET'])
def get_symbol_backtest(symbol):
    """Get backtest results for a specific symbol"""
    try:
        # Run backtest for specific symbol
        engine = WyckoffBacktestEngine()
        
        db = get_db_connection()
        if not db.connect():
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        # Get symbol data
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
        
        # Run backtest
        df = pd.DataFrame(data_result)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        backtest_result = engine.run_backtest(df, symbol.upper())
        result_dict = convert_backtest_result_to_dict(backtest_result)
        
        db.disconnect()
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'backtest_result': result_dict
        })
        
    except Exception as e:
        logger.error(f"Error getting backtest for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@backtest_bp.route('/reports', methods=['GET'])
def get_available_reports():
    """Get list of available backtest reports"""
    try:
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        report_files = []
        
        for filename in os.listdir(backend_dir):
            if filename.startswith('wyckoff_backtest_report_') and filename.endswith('.json'):
                file_path = os.path.join(backend_dir, filename)
                file_stats = os.stat(file_path)
                
                report_files.append({
                    'filename': filename,
                    'created': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    'size': file_stats.st_size
                })
        
        # Sort by creation time (newest first)
        report_files.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'reports': report_files
        })
        
    except Exception as e:
        logger.error(f"Error getting available reports: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@backtest_bp.route('/reports/<filename>', methods=['GET'])
def get_report(filename):
    """Get specific backtest report"""
    try:
        # Validate filename
        if not filename.startswith('wyckoff_backtest_report_') or not filename.endswith('.json'):
            return jsonify({
                'success': False,
                'error': 'Invalid report filename'
            }), 400
        
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        report_path = os.path.join(backend_dir, filename)
        
        if not os.path.exists(report_path):
            return jsonify({
                'success': False,
                'error': 'Report file not found'
            }), 404
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'report_data': report_data
        })
        
    except Exception as e:
        logger.error(f"Error getting report {filename}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def convert_backtest_result_to_dict(result):
    """Convert BacktestResults dataclass to dictionary"""
    return {
        'symbol': result.symbol,
        'start_date': result.start_date.isoformat(),
        'end_date': result.end_date.isoformat(),
        'total_days': result.total_days,
        'performance_metrics': result.performance_metrics,
        'phase_analysis': result.phase_analysis,
        'trades': [
            {
                'symbol': t.symbol,
                'entry_date': t.entry_date.isoformat(),
                'exit_date': t.exit_date.isoformat() if t.exit_date else None,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'action': t.action.value,
                'shares': t.shares,
                'entry_phase': t.entry_phase.value,
                'exit_phase': t.exit_phase.value if t.exit_phase else None,
                'pnl': t.pnl,
                'pnl_percent': t.pnl_percent,
                'duration_days': t.duration_days,
                'entry_reasoning': t.entry_reasoning,
                'exit_reasoning': t.exit_reasoning
            }
            for t in result.trades
        ],
        'signals': [
            {
                'date': s.date.isoformat(),
                'phase': s.phase.value,
                'action': s.action.value,
                'price': s.price,
                'volume_ratio': s.volume_ratio,
                'confidence': s.confidence,
                'reasoning': s.reasoning,
                'support_level': s.support_level,
                'resistance_level': s.resistance_level
            }
            for s in result.signals
        ],
        'equity_curve': [
            {'date': date.isoformat(), 'value': value}
            for date, value in result.equity_curve
        ]
    }

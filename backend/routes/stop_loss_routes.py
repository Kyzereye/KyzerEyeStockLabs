#!/usr/bin/env python3
"""
Stop Loss Optimization API Routes
"""

from flask import Blueprint, request, jsonify
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import logging

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.stop_loss_optimizer import StopLossOptimizer
from utils.database import get_db_connection

logger = logging.getLogger(__name__)

# Create blueprint
stop_loss_bp = Blueprint('stop_loss', __name__)

@stop_loss_bp.route('/api/stop-loss/optimize/<symbol>', methods=['GET'])
def optimize_stop_loss(symbol):
    """Optimize stop loss for a specific symbol"""
    try:
        # Get parameters
        initial_capital = float(request.args.get('initial_capital', 100000))
        
        # Get stock data
        db = get_db_connection()
        
        # Get symbol ID
        symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
        symbol_result = db.execute_query(symbol_query, (symbol.upper(),))
        
        if not symbol_result:
            return jsonify({'error': f'Symbol {symbol} not found'}), 404
        
        symbol_id = symbol_result[0]['id']
        
        # Get stock data
        data_query = """
            SELECT date, open, high, low, close, volume
            FROM daily_stock_data 
            WHERE symbol_id = %s 
            ORDER BY date
        """
        data_result = db.execute_query(data_query, (symbol_id,))
        
        if not data_result:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        # Convert to DataFrame
        df = pd.DataFrame(data_result)
        df['date'] = pd.to_datetime(df['date'])
        
        # Convert decimal columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].astype(float)
        
        # Run optimization
        optimizer = StopLossOptimizer(initial_capital=initial_capital)
        optimization = optimizer.optimize_stop_loss(df, symbol.upper())
        
        # Convert results to JSON-serializable format
        result = {
            'symbol': optimization.symbol,
            'analysis_date': optimization.analysis_date.isoformat(),
            'overall_optimal': optimization.overall_optimal,
            'stop_loss_range': optimization.stop_loss_range,
            'test_intervals': optimization.test_intervals,
            'monthly_results': [],
            'quarterly_results': [],
            'yearly_results': []
        }
        
        # Convert monthly results
        for monthly in optimization.monthly_results:
            result['monthly_results'].append({
                'period_start': monthly.period_start.isoformat(),
                'period_end': monthly.period_end.isoformat(),
                'optimal_stop_loss': monthly.optimal_stop_loss,
                'total_return': monthly.total_return,
                'win_rate': monthly.win_rate,
                'max_drawdown': monthly.max_drawdown,
                'sharpe_ratio': monthly.sharpe_ratio,
                'total_trades': monthly.total_trades,
                'winning_trades': monthly.winning_trades,
                'losing_trades': monthly.losing_trades,
                'avg_win': monthly.avg_win,
                'avg_loss': monthly.avg_loss,
                'profit_factor': monthly.profit_factor,
                'trades': monthly.trades
            })
        
        # Convert quarterly results
        for quarterly in optimization.quarterly_results:
            result['quarterly_results'].append({
                'period_start': quarterly.period_start.isoformat(),
                'period_end': quarterly.period_end.isoformat(),
                'optimal_stop_loss': quarterly.optimal_stop_loss,
                'total_return': quarterly.total_return,
                'win_rate': quarterly.win_rate,
                'max_drawdown': quarterly.max_drawdown,
                'sharpe_ratio': quarterly.sharpe_ratio,
                'total_trades': quarterly.total_trades,
                'winning_trades': quarterly.winning_trades,
                'losing_trades': quarterly.losing_trades,
                'avg_win': quarterly.avg_win,
                'avg_loss': quarterly.avg_loss,
                'profit_factor': quarterly.profit_factor,
                'trades': quarterly.trades
            })
        
        # Convert yearly results
        for yearly in optimization.yearly_results:
            result['yearly_results'].append({
                'period_start': yearly.period_start.isoformat(),
                'period_end': yearly.period_end.isoformat(),
                'optimal_stop_loss': yearly.optimal_stop_loss,
                'total_return': yearly.total_return,
                'win_rate': yearly.win_rate,
                'max_drawdown': yearly.max_drawdown,
                'sharpe_ratio': yearly.sharpe_ratio,
                'total_trades': yearly.total_trades,
                'winning_trades': yearly.winning_trades,
                'losing_trades': yearly.losing_trades,
                'avg_win': yearly.avg_win,
                'avg_loss': yearly.avg_loss,
                'profit_factor': yearly.profit_factor,
                'trades': yearly.trades
            })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error optimizing stop loss for {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@stop_loss_bp.route('/api/stop-loss/optimize-all', methods=['GET'])
def optimize_stop_loss_all():
    """Optimize stop loss for all symbols"""
    try:
        # Get parameters
        initial_capital = float(request.args.get('initial_capital', 100000))
        
        # Get all symbols
        db = get_db_connection()
        symbols_query = "SELECT symbol FROM stock_symbols ORDER BY symbol"
        symbols_result = db.execute_query(symbols_query)
        
        if not symbols_result:
            return jsonify({'error': 'No symbols found'}), 404
        
        results = {
            'analysis_date': datetime.now().isoformat(),
            'initial_capital': initial_capital,
            'symbols': []
        }
        
        optimizer = StopLossOptimizer(initial_capital=initial_capital)
        
        for symbol_row in symbols_result:
            symbol = symbol_row['symbol']
            
            try:
                # Get symbol ID
                symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
                symbol_result = db.execute_query(symbol_query, (symbol,))
                
                if not symbol_result:
                    continue
                
                symbol_id = symbol_result[0]['id']
                
                # Get stock data
                data_query = """
                    SELECT date, open, high, low, close, volume
                    FROM daily_stock_data 
                    WHERE symbol_id = %s 
                    ORDER BY date
                """
                data_result = db.execute_query(data_query, (symbol_id,))
                
                if not data_result or len(data_result) < 100:  # Need sufficient data
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(data_result)
                df['date'] = pd.to_datetime(df['date'])
                
                # Run optimization
                optimization = optimizer.optimize_stop_loss(df, symbol)
                
                # Add simplified result
                results['symbols'].append({
                    'symbol': symbol,
                    'overall_optimal': optimization.overall_optimal,
                    'monthly_count': len(optimization.monthly_results),
                    'quarterly_count': len(optimization.quarterly_results),
                    'yearly_count': len(optimization.yearly_results)
                })
                
            except Exception as e:
                logger.error(f"Error optimizing stop loss for {symbol}: {str(e)}")
                continue
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error optimizing stop loss for all symbols: {str(e)}")
        return jsonify({'error': str(e)}), 500

@stop_loss_bp.route('/api/stop-loss/summary/<symbol>', methods=['GET'])
def get_stop_loss_summary(symbol):
    """Get a summary of stop loss optimization results for a symbol"""
    try:
        # Get parameters
        initial_capital = float(request.args.get('initial_capital', 100000))
        
        # Get stock data
        db = get_db_connection()
        
        # Get symbol ID
        symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
        symbol_result = db.execute_query(symbol_query, (symbol.upper(),))
        
        if not symbol_result:
            return jsonify({'error': f'Symbol {symbol} not found'}), 404
        
        symbol_id = symbol_result[0]['id']
        
        # Get stock data
        data_query = """
            SELECT date, open, high, low, close, volume
            FROM daily_stock_data 
            WHERE symbol_id = %s 
            ORDER BY date
        """
        data_result = db.execute_query(data_query, (symbol_id,))
        
        if not data_result:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        # Convert to DataFrame
        df = pd.DataFrame(data_result)
        df['date'] = pd.to_datetime(df['date'])
        
        # Convert decimal columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].astype(float)
        
        # Run optimization
        optimizer = StopLossOptimizer(initial_capital=initial_capital)
        optimization = optimizer.optimize_stop_loss(df, symbol.upper())
        
        # Calculate summary statistics
        monthly_stops = [r.optimal_stop_loss for r in optimization.monthly_results]
        quarterly_stops = [r.optimal_stop_loss for r in optimization.quarterly_results]
        yearly_stops = [r.optimal_stop_loss for r in optimization.yearly_results]
        
        summary = {
            'symbol': optimization.symbol,
            'analysis_date': optimization.analysis_date.isoformat(),
            'overall_optimal': optimization.overall_optimal,
            'statistics': {
                'monthly': {
                    'count': len(monthly_stops),
                    'min': min(monthly_stops) if monthly_stops else 0,
                    'max': max(monthly_stops) if monthly_stops else 0,
                    'avg': sum(monthly_stops) / len(monthly_stops) if monthly_stops else 0,
                    'median': sorted(monthly_stops)[len(monthly_stops)//2] if monthly_stops else 0
                },
                'quarterly': {
                    'count': len(quarterly_stops),
                    'min': min(quarterly_stops) if quarterly_stops else 0,
                    'max': max(quarterly_stops) if quarterly_stops else 0,
                    'avg': sum(quarterly_stops) / len(quarterly_stops) if quarterly_stops else 0,
                    'median': sorted(quarterly_stops)[len(quarterly_stops)//2] if quarterly_stops else 0
                },
                'yearly': {
                    'count': len(yearly_stops),
                    'min': min(yearly_stops) if yearly_stops else 0,
                    'max': max(yearly_stops) if yearly_stops else 0,
                    'avg': sum(yearly_stops) / len(yearly_stops) if yearly_stops else 0,
                    'median': sorted(yearly_stops)[len(yearly_stops)//2] if yearly_stops else 0
                }
            },
            'recommendations': {
                'conservative': min(monthly_stops + quarterly_stops + yearly_stops) if (monthly_stops or quarterly_stops or yearly_stops) else optimization.overall_optimal,
                'moderate': optimization.overall_optimal,
                'aggressive': max(monthly_stops + quarterly_stops + yearly_stops) if (monthly_stops or quarterly_stops or yearly_stops) else optimization.overall_optimal
            }
        }
        
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting stop loss summary for {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

#!/usr/bin/env python3
"""
Run Wyckoff Backtest
Execute Wyckoff backtest on all stocks and generate comprehensive reports
"""

import sys
import os
import json
from datetime import datetime
import pandas as pd

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from services.wyckoff_backtest import WyckoffBacktestEngine
from utils.database import get_db_connection

def get_all_symbols_with_data():
    """Get all symbols that have stock data"""
    db = get_db_connection()
    if not db.connect():
        print("❌ Failed to connect to database")
        return []
    
    try:
        query = """
            SELECT DISTINCT s.id, s.symbol, COUNT(d.id) as data_count
            FROM stock_symbols s
            INNER JOIN daily_stock_data d ON s.id = d.symbol_id
            GROUP BY s.id, s.symbol
            HAVING data_count > 0
            ORDER BY s.symbol
        """
        result = db.execute_query(query)
        return result
    except Exception as e:
        print(f"❌ Error getting symbols: {e}")
        return []
    finally:
        db.disconnect()

def get_stock_data_for_symbol(symbol_id: int):
    """Get stock data for a specific symbol"""
    db = get_db_connection()
    if not db.connect():
        return None
    
    try:
        query = """
            SELECT date, open, high, low, close, volume
            FROM daily_stock_data
            WHERE symbol_id = %s
            ORDER BY date ASC
        """
        result = db.execute_query(query, (symbol_id,))
        
        if not result:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(result)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except Exception as e:
        print(f"❌ Error getting stock data: {e}")
        return None
    finally:
        db.disconnect()

def run_wyckoff_backtest():
    """Run Wyckoff backtest on all stocks"""
    print("🚀 Wyckoff Method Backtest Engine")
    print("=" * 60)
    
    # Initialize backtest engine
    engine = WyckoffBacktestEngine(initial_capital=100000.0)
    
    # Get all symbols with data
    symbols = get_all_symbols_with_data()
    if not symbols:
        print("❌ No symbols found with stock data")
        return
    
    print(f"📊 Found {len(symbols)} symbols for backtesting:")
    for symbol in symbols:
        print(f"  - {symbol['symbol']}: {symbol['data_count']} data points")
    
    print(f"\n🔄 Starting Wyckoff backtests...")
    print("-" * 60)
    
    all_results = []
    
    for i, symbol_data in enumerate(symbols, 1):
        symbol_id = symbol_data['id']
        symbol_name = symbol_data['symbol']
        
        print(f"\n[{i}/{len(symbols)}] Running backtest for {symbol_name}...")
        
        try:
            # Get stock data
            df = get_stock_data_for_symbol(symbol_id)
            if df is None or df.empty:
                print(f"  ❌ No data found for {symbol_name}")
                continue
            
            print(f"  📊 Data: {len(df)} rows from {df.index[0].date()} to {df.index[-1].date()}")
            
            # Run backtest
            results = engine.run_backtest(df, symbol_name)
            all_results.append(results)
            
            # Print summary
            print(f"  📈 Results:")
            print(f"    💰 Final Value: ${results.performance_metrics['final_value']:,.2f}")
            print(f"    📊 Total Return: {results.performance_metrics['total_return_percent']:.2f}%")
            print(f"    🎯 Total Trades: {results.performance_metrics['total_trades']}")
            print(f"    🏆 Win Rate: {results.performance_metrics['win_rate']:.1f}%")
            print(f"    📉 Max Drawdown: {results.performance_metrics['max_drawdown_percent']:.2f}%")
            
        except Exception as e:
            print(f"  ❌ Error running backtest for {symbol_name}: {e}")
            continue
    
    if not all_results:
        print("❌ No successful backtests completed")
        return
    
    # Generate comprehensive report
    print(f"\n📋 Generating Comprehensive Report...")
    report = generate_backtest_report(all_results)
    
    # Display summary
    print(f"\n" + "=" * 60)
    print(f"🎉 WYCKOFF BACKTEST SUMMARY")
    print(f"=" * 60)
    
    print(f"📊 Backtests Completed: {len(all_results)}")
    print(f"📅 Period: {report['summary']['start_date']} to {report['summary']['end_date']}")
    print(f"💰 Total Initial Capital: ${report['summary']['total_initial_capital']:,.2f}")
    print(f"💰 Total Final Value: ${report['summary']['total_final_value']:,.2f}")
    print(f"📈 Total Return: {report['summary']['total_return_percent']:.2f}%")
    
    print(f"\n🏆 TOP PERFORMERS:")
    for i, performer in enumerate(report['top_performers'][:3], 1):
        print(f"  {i}. {performer['symbol']}: {performer['total_return_percent']:.2f}% return")
        print(f"     Trades: {performer['total_trades']} | Win Rate: {performer['win_rate']:.1f}%")
        print(f"     Sharpe: {performer['sharpe_ratio']:.2f} | Drawdown: {performer['max_drawdown_percent']:.2f}%")
    
    print(f"\n📊 PHASE ANALYSIS:")
    for phase, count in report['phase_analysis']['phase_counts'].items():
        print(f"  {phase}: {count} occurrences")
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"wyckoff_backtest_report_{timestamp}.json"
    
    try:
        with open(report_filename, 'w') as f:
            # Convert dataclasses to dict for JSON serialization
            json_report = convert_results_to_json(report)
            json.dump(json_report, f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {report_filename}")
    except Exception as e:
        print(f"\n⚠️  Could not save report file: {e}")
    
    print(f"\n✅ Wyckoff backtest completed!")

def generate_backtest_report(results):
    """Generate comprehensive backtest report"""
    if not results:
        return {}
    
    # Calculate summary statistics
    total_initial_capital = sum(100000.0 for _ in results)  # Assuming $100k per stock
    total_final_value = sum(r.performance_metrics['final_value'] for r in results)
    total_return_percent = ((total_final_value / total_initial_capital) - 1) * 100
    
    # Get date range
    start_dates = [r.start_date for r in results]
    end_dates = [r.end_date for r in results]
    
    # Top performers
    top_performers = sorted(
        results,
        key=lambda x: x.performance_metrics['total_return_percent'],
        reverse=True
    )[:5]
    
    # Phase analysis
    all_phase_counts = {}
    for result in results:
        for phase, count in result.phase_analysis['phase_counts'].items():
            all_phase_counts[phase] = all_phase_counts.get(phase, 0) + count
    
    return {
        'report_date': datetime.now().isoformat(),
        'summary': {
            'total_symbols': len(results),
            'start_date': min(start_dates).strftime('%Y-%m-%d'),
            'end_date': max(end_dates).strftime('%Y-%m-%d'),
            'total_initial_capital': total_initial_capital,
            'total_final_value': total_final_value,
            'total_return_percent': total_return_percent
        },
        'top_performers': [
            {
                'symbol': r.symbol,
                'total_return_percent': r.performance_metrics['total_return_percent'],
                'final_value': r.performance_metrics['final_value'],
                'total_trades': r.performance_metrics['total_trades'],
                'win_rate': r.performance_metrics['win_rate'],
                'sharpe_ratio': r.performance_metrics['sharpe_ratio'],
                'max_drawdown_percent': r.performance_metrics['max_drawdown_percent']
            }
            for r in top_performers
        ],
        'phase_analysis': {
            'phase_counts': all_phase_counts,
            'total_signals': sum(r.phase_analysis['total_signals'] for r in results)
        },
        'detailed_results': results
    }

def convert_results_to_json(report):
    """Convert dataclass results to JSON-serializable format"""
    json_report = report.copy()
    
    # Convert detailed results
    if 'detailed_results' in json_report:
        json_results = []
        for result in json_report['detailed_results']:
            json_result = {
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
            json_results.append(json_result)
        json_report['detailed_results'] = json_results
    
    return json_report

def main():
    """Main function"""
    print("📈 Wyckoff Method Backtest Engine")
    print("This will run comprehensive Wyckoff backtests on all your stocks")
    print()
    
    # Confirm before proceeding
    try:
        confirm = input("Run Wyckoff backtest on all stocks? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return
    
    # Start backtesting
    run_wyckoff_backtest()

if __name__ == "__main__":
    main()

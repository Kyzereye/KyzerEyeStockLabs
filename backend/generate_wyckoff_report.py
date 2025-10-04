#!/usr/bin/env python3
"""
Generate Wyckoff Analysis Report
Standalone script to analyze all stocks using Wyckoff Method
"""

import sys
import os
import json
from datetime import datetime
import pandas as pd

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from services.wyckoff_analysis import WyckoffAnalysisService
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
        return df
    except Exception as e:
        print(f"❌ Error getting stock data: {e}")
        return None
    finally:
        db.disconnect()

def generate_wyckoff_report():
    """Generate comprehensive Wyckoff report for all stocks"""
    print("🔍 Wyckoff Method Analysis Report")
    print("=" * 60)
    
    # Get all symbols with data
    symbols = get_all_symbols_with_data()
    if not symbols:
        print("❌ No symbols found with stock data")
        return
    
    print(f"📊 Found {len(symbols)} symbols with data:")
    for symbol in symbols:
        print(f"  - {symbol['symbol']}: {symbol['data_count']} data points")
    
    # Initialize Wyckoff analysis service
    wyckoff_service = WyckoffAnalysisService()
    analysis_results = []
    
    print(f"\n🔄 Analyzing stocks using Wyckoff Method...")
    print("-" * 60)
    
    for i, symbol in enumerate(symbols, 1):
        symbol_id = symbol['id']
        symbol_name = symbol['symbol']
        
        print(f"[{i}/{len(symbols)}] Analyzing {symbol_name}...", end=" ")
        
        try:
            # Get stock data
            df = get_stock_data_for_symbol(symbol_id)
            if df is None or df.empty:
                print("❌ No data")
                analysis_results.append({
                    'symbol': symbol_name,
                    'error': 'No stock data found'
                })
                continue
            
            # Perform Wyckoff analysis
            analysis = wyckoff_service.analyze_wyckoff_phases(df, symbol_name)
            analysis_results.append(analysis)
            
            # Print quick summary
            if 'error' in analysis:
                print(f"❌ Error: {analysis['error']}")
            else:
                current_phase = analysis['current_phase']['phase']
                score = analysis['wyckoff_score']['total_score']
                grade = analysis['wyckoff_score']['grade']
                signal = analysis['signals']['primary_signal']
                print(f"✅ {current_phase} | Score: {score}/100 ({grade}) | Signal: {signal}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            analysis_results.append({
                'symbol': symbol_name,
                'error': str(e)
            })
    
    # Generate comprehensive report
    print(f"\n📋 Generating Comprehensive Report...")
    report = wyckoff_service.generate_wyckoff_report(analysis_results)
    
    # Display summary
    print("\n" + "=" * 60)
    print("📊 WYCKOFF ANALYSIS SUMMARY")
    print("=" * 60)
    
    summary = report['summary']
    print(f"Total Stocks Analyzed: {summary['total_stocks_analyzed']}")
    print(f"Successful Analyses: {summary['successful_analyses']}")
    print(f"Buy Signals: {summary['buy_signals']}")
    print(f"Sell Signals: {summary['sell_signals']}")
    print(f"Hold Signals: {summary['hold_signals']}")
    
    print(f"\n📈 PHASE DISTRIBUTION:")
    for phase, count in report['phase_distribution'].items():
        print(f"  {phase}: {count} stocks")
    
    print(f"\n🏆 GRADE DISTRIBUTION:")
    for grade, count in report['grade_distribution'].items():
        print(f"  Grade {grade}: {count} stocks")
    
    print(f"\n🥇 TOP PERFORMERS:")
    for i, performer in enumerate(report['top_performers'][:3], 1):
        print(f"  {i}. {performer['symbol']}: {performer['score']}/100 ({performer['grade']}) - {performer['current_phase']} - {performer['signal']}")
    
    if report['best_opportunities']:
        print(f"\n💎 BEST OPPORTUNITIES (High Score + Buy Signal):")
        for i, opportunity in enumerate(report['best_opportunities'][:3], 1):
            print(f"  {i}. {opportunity['symbol']}: ${opportunity['current_price']:.2f}")
            print(f"     Score: {opportunity['score']}/100 | Phase: {opportunity['current_phase']} | Confidence: {opportunity['confidence']:.1%}")
            print(f"     Reasoning: {', '.join(opportunity['reasoning'])}")
    
    # Save detailed report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"wyckoff_report_{timestamp}.json"
    
    try:
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {report_filename}")
    except Exception as e:
        print(f"\n⚠️  Could not save report file: {e}")
    
    # Display detailed analysis for each stock
    print(f"\n📋 DETAILED ANALYSIS:")
    print("-" * 60)
    
    for result in analysis_results:
        if 'error' in result:
            print(f"\n❌ {result['symbol']}: {result['error']}")
            continue
        
        symbol = result['symbol']
        current_phase = result['current_phase']
        wyckoff_score = result['wyckoff_score']
        signals = result['signals']
        volume_analysis = result['volume_analysis']
        
        print(f"\n📊 {symbol}")
        print(f"  Current Price: ${result['current_price']:.2f}")
        print(f"  Current Phase: {current_phase['phase']} (Confidence: {current_phase['confidence']:.1%})")
        print(f"  Wyckoff Score: {wyckoff_score['total_score']}/100 (Grade: {wyckoff_score['grade']})")
        print(f"  Primary Signal: {signals['primary_signal']}")
        print(f"  Volume Analysis: {volume_analysis['volume_analysis']}")
        
        if signals['reasoning']:
            print(f"  Reasoning: {', '.join(signals['reasoning'])}")
        
        # Show recent phases found
        phases = result['phases']
        for phase_name, phase_list in phases.items():
            if phase_list:
                print(f"  Recent {phase_name.title()} Periods: {len(phase_list)}")
    
    print(f"\n✅ Wyckoff analysis completed!")
    print(f"📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Wyckoff Analysis Report Generator")
            print("Usage: python3 generate_wyckoff_report.py")
            print("Generates comprehensive Wyckoff Method analysis for all stocks")
            return
    
    generate_wyckoff_report()

if __name__ == "__main__":
    main()


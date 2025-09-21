#!/usr/bin/env python3
"""
Calculate technical indicators for existing stock data
"""

import sys
import os
import pandas as pd
from typing import List

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from services.technical_indicators import TechnicalIndicatorsService
from utils.database import get_db_connection
from config.indicators_config import get_enabled_indicators

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
        return df
    except Exception as e:
        print(f"❌ Error getting stock data: {e}")
        return None
    finally:
        db.disconnect()

def calculate_indicators_for_all_symbols():
    """Calculate indicators for all symbols with data"""
    print("🔍 Finding symbols with stock data...")
    
    symbols = get_all_symbols_with_data()
    if not symbols:
        print("❌ No symbols found with stock data")
        return
    
    print(f"📊 Found {len(symbols)} symbols with data:")
    for symbol in symbols:
        print(f"  - {symbol['symbol']}: {symbol['data_count']} data points")
    
    # Initialize the indicators service
    service = TechnicalIndicatorsService()
    
    enabled_indicators = get_enabled_indicators()
    print(f"\n📈 Enabled indicators: {', '.join(enabled_indicators)}")
    
    success_count = 0
    failed_count = 0
    
    for symbol in symbols:
        symbol_id = symbol['id']
        symbol_name = symbol['symbol']
        
        print(f"\n🔄 Processing {symbol_name}...")
        
        # Get stock data
        df = get_stock_data_for_symbol(symbol_id)
        if df is None or df.empty:
            print(f"  ⚠️  No data found for {symbol_name}")
            failed_count += 1
            continue
        
        print(f"  📊 Data: {len(df)} rows from {df['date'].min()} to {df['date'].max()}")
        
        # Calculate and store indicators
        try:
            success = service.calculate_and_store_indicators(symbol_id, df)
            if success:
                print(f"  ✅ Successfully calculated indicators for {symbol_name}")
                success_count += 1
            else:
                print(f"  ❌ Failed to calculate indicators for {symbol_name}")
                failed_count += 1
        except Exception as e:
            print(f"  ❌ Error processing {symbol_name}: {e}")
            failed_count += 1
    
    # Summary
    print(f"\n🎉 Calculation completed!")
    print(f"  ✅ Successful: {success_count} symbols")
    print(f"  ❌ Failed: {failed_count} symbols")
    print(f"  📊 Total processed: {len(symbols)} symbols")

def calculate_indicators_for_symbol(symbol: str):
    """Calculate indicators for a specific symbol"""
    db = get_db_connection()
    if not db.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        # Get symbol ID
        symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
        symbol_result = db.execute_query(symbol_query, (symbol.upper(),))
        
        if not symbol_result:
            print(f"❌ Symbol {symbol.upper()} not found in database")
            return
        
        symbol_id = symbol_result[0]['id']
        print(f"📊 Processing {symbol.upper()} (ID: {symbol_id})...")
        
        # Get stock data
        df = get_stock_data_for_symbol(symbol_id)
        if df is None or df.empty:
            print(f"❌ No stock data found for {symbol.upper()}")
            return
        
        print(f"📊 Data: {len(df)} rows from {df['date'].min()} to {df['date'].max()}")
        
        # Calculate and store indicators
        service = TechnicalIndicatorsService()
        success = service.calculate_and_store_indicators(symbol_id, df)
        
        if success:
            print(f"✅ Successfully calculated indicators for {symbol.upper()}")
        else:
            print(f"❌ Failed to calculate indicators for {symbol.upper()}")
            
    except Exception as e:
        print(f"❌ Error processing {symbol}: {e}")
    finally:
        db.disconnect()

def main():
    """Main function"""
    print("📈 Technical Indicators Calculator")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Calculate for specific symbol
        symbol = sys.argv[1].upper()
        calculate_indicators_for_symbol(symbol)
    else:
        # Calculate for all symbols
        calculate_indicators_for_all_symbols()

if __name__ == "__main__":
    main()

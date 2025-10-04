#!/usr/bin/env python3
"""
Update Database from 3-Year CSV Files
Read 3-year CSV data and update the database
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from utils.database import get_db_connection

def update_database_from_csv():
    """Update database with 3-year CSV data"""
    print("🔄 Updating Database with 3-Year CSV Data")
    print("=" * 50)
    
    # Connect to database
    db = get_db_connection()
    if not db.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        # Get all symbols
        symbols_query = "SELECT id, symbol FROM stock_symbols"
        symbols_result = db.execute_query(symbols_query)
        
        if not symbols_result:
            print("❌ No symbols found in database")
            return
        
        print(f"📊 Found {len(symbols_result)} symbols to update")
        
        total_stored = 0
        
        for symbol_data in symbols_result:
            symbol_id = symbol_data['id']
            symbol = symbol_data['symbol']
            
            print(f"\n📈 Processing {symbol}...")
            
            # Read CSV file
            csv_path = f"../get_stock_data/csv_files/{symbol}_historical_data.csv"
            
            if not os.path.exists(csv_path):
                print(f"  ⚠️  CSV file not found: {csv_path}")
                continue
            
            try:
                # Read CSV data
                df = pd.read_csv(csv_path)
                df['Date'] = pd.to_datetime(df['Date'])
                
                print(f"  📊 CSV Data: {len(df)} rows from {df['Date'].min().date()} to {df['Date'].max().date()}")
                
                # Store in database
                stored_count = 0
                
                for _, row in df.iterrows():
                    try:
                        # Insert data with ON DUPLICATE KEY UPDATE
                        insert_query = """
                            INSERT INTO daily_stock_data (symbol_id, date, open, high, low, close, volume)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                open = VALUES(open),
                                high = VALUES(high),
                                low = VALUES(low),
                                close = VALUES(close),
                                volume = VALUES(volume)
                        """
                        
                        db.execute_query(insert_query, (
                            symbol_id,
                            row['Date'].date(),
                            float(row['Open']),
                            float(row['High']),
                            float(row['Low']),
                            float(row['Close']),
                            int(row['Volume'])
                        ))
                        
                        stored_count += 1
                        
                    except Exception as e:
                        print(f"    ⚠️  Error storing record for {row['Date'].date()}: {e}")
                        continue
                
                print(f"  ✅ Stored {stored_count} records for {symbol}")
                total_stored += stored_count
                
            except Exception as e:
                print(f"  ❌ Error processing {symbol}: {e}")
                continue
        
        print(f"\n🎉 Database Update Complete!")
        print(f"📊 Total records stored: {total_stored}")
        
        # Verify data ranges
        print(f"\n📋 Final Database Data Ranges:")
        print("-" * 40)
        
        for symbol_data in symbols_result:
            symbol_id = symbol_data['id']
            symbol = symbol_data['symbol']
            
            range_query = """
                SELECT 
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    COUNT(*) as total_records
                FROM daily_stock_data 
                WHERE symbol_id = %s
            """
            range_result = db.execute_query(range_query, (symbol_id,))
            
            if range_result:
                earliest = range_result[0]['earliest_date']
                latest = range_result[0]['latest_date']
                records = range_result[0]['total_records']
                days = (latest - earliest).days
                years = days / 365.25
                print(f"  📊 {symbol}: {earliest} to {latest} ({records} records, {years:.1f} years)")
        
    except Exception as e:
        print(f"❌ Error during database update: {e}")
    finally:
        db.disconnect()

def main():
    """Main function"""
    update_database_from_csv()

if __name__ == "__main__":
    main()

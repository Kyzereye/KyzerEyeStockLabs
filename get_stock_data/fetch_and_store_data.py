#!/usr/bin/env python3
"""
Fetch stock data and store in both CSV files and MySQL database
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add the backend directory to the path to import database utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from stock_scraper import StockDataScraper
from utils.database import get_db_connection
from models.stock_models import StockSymbol

def store_data_in_database(stock_data_dict):
    """Store stock data in MySQL database"""
    db = get_db_connection()
    
    if not db.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        stored_count = 0
        
        for symbol, df in stock_data_dict.items():
            print(f"📊 Storing {symbol} data in database...")
            
            # Get symbol ID
            symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
            symbol_result = db.execute_query(symbol_query, (symbol.upper(),))
            
            if not symbol_result:
                print(f"  ⚠️  Symbol {symbol} not found in database, skipping...")
                continue
                
            symbol_id = symbol_result[0]['id']
            
            # Prepare data for insertion
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
            
            data_to_insert = []
            for _, row in df.iterrows():
                data_to_insert.append((
                    symbol_id,
                    row['Date'],
                    row.get('Open'),
                    row.get('High'),
                    row.get('Low'),
                    row.get('Close'),
                    row.get('Volume')
                ))
            
            # Insert data
            rows_inserted = db.execute_many(insert_query, data_to_insert)
            stored_count += rows_inserted
            print(f"  ✅ Stored {rows_inserted} rows for {symbol}")
        
        print(f"\n🎉 Successfully stored {stored_count} total rows in database!")
        return True
        
    except Exception as e:
        print(f"❌ Error storing data in database: {e}")
        return False
    finally:
        db.disconnect()

def main():
    """Fetch stock data and store in CSV files and database"""
    print("🚀 KyzerEye Stock Data Fetcher")
    print("=" * 50)
    
    # Create scraper
    scraper = StockDataScraper()
    
    # Load stock symbols from file
    symbols = scraper.load_symbols_from_file("stock_symbols.txt")
    
    if not symbols:
        print("❌ No symbols found in stock_symbols.txt. Please add symbols to the file.")
        return
    
    print(f"📈 Fetching 1 year of data for {len(symbols)} stocks...")
    print(f"   Symbols: {', '.join(symbols)}")
    
    # Get data for all symbols
    stock_data = scraper.get_multiple_stocks_data(symbols, period='1y', delay=1.0)
    
    if stock_data:
        print(f"\n✅ Successfully retrieved data for {len(stock_data)} stocks")
        
        # Print summary
        for symbol, df in stock_data.items():
            if not df.empty and 'Date' in df.columns:
                min_date = df['Date'].min()
                max_date = df['Date'].max()
                print(f"  📊 {symbol}: {len(df)} rows ({min_date} to {max_date})")
            else:
                print(f"  ❌ {symbol}: No data")
        
        # Save to CSV files (existing functionality)
        print(f"\n💾 Saving to CSV files...")
        scraper.save_multiple_to_csv(stock_data, individual_files=True)
        scraper.save_multiple_to_csv(
            stock_data, 
            individual_files=False, 
            combined_file="portfolio_1year_data.csv"
        )
        print("✅ CSV files saved successfully!")
        
        # Store in database (new functionality)
        print(f"\n🗄️  Storing in MySQL database...")
        if store_data_in_database(stock_data):
            print("✅ Database storage completed!")
        else:
            print("❌ Database storage failed!")
        
        print(f"\n🎉 All done! Data saved to both CSV files and database.")
        
    else:
        print("❌ Failed to retrieve any stock data")

if __name__ == "__main__":
    main()

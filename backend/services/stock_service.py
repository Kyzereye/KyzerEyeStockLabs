"""
Stock data service - integrates with existing scraper
"""
import sys
import os
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional, Any
import logging

# Add the parent directory to sys.path to import the existing scraper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'get_stock_data'))

from stock_scraper import StockDataScraper
from models.stock_models import StockSymbol, DailyStockData, TechnicalIndicator
from utils.database import get_db_connection

logger = logging.getLogger(__name__)

class StockService:
    """Service class for stock data operations"""
    
    def __init__(self):
        self.db = get_db_connection()
        self.scraper = StockDataScraper()  # Use existing scraper
    
    def load_symbols_from_file(self, filename: str = "stock_symbols.txt") -> List[str]:
        """Load stock symbols from file (using existing scraper method)"""
        return self.scraper.load_symbols_from_file(filename)
    
    def get_symbol_id(self, symbol: str) -> Optional[int]:
        """Get symbol ID from database"""
        query = "SELECT id FROM stock_symbols WHERE symbol = %s"
        result = self.db.execute_query(query, (symbol.upper(),))
        return result[0]['id'] if result else None
    
    def insert_stock_symbol(self, symbol: str, company_name: str = None, 
                          market_cap: int = None) -> bool:
        """Insert or update stock symbol"""
        # Check if symbol exists
        existing_id = self.get_symbol_id(symbol)
        
        if existing_id:
            # Update existing symbol
            query = """
                UPDATE stock_symbols 
                SET company_name = %s, market_cap = %s, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = %s
            """
            return self.db.execute_insert(query, (company_name, market_cap, symbol.upper()))
        else:
            # Insert new symbol
            query = """
                INSERT INTO stock_symbols (symbol, company_name, market_cap)
                VALUES (%s, %s, %s)
            """
            return self.db.execute_insert(query, (symbol.upper(), company_name, market_cap))
    
    def sync_symbols_from_file(self, filename: str = "stock_symbols.txt") -> Dict[str, Any]:
        """Sync symbols from file to database"""
        symbols = self.load_symbols_from_file(filename)
        results = {'success': [], 'failed': [], 'updated': 0, 'inserted': 0}
        
        for symbol in symbols:
            try:
                if self.insert_stock_symbol(symbol):
                    symbol_id = self.get_symbol_id(symbol)
                    if symbol_id:
                        results['success'].append(symbol)
                        results['inserted'] += 1
                    else:
                        results['failed'].append(symbol)
                else:
                    results['failed'].append(symbol)
            except Exception as e:
                logger.error(f"Failed to sync symbol {symbol}: {e}")
                results['failed'].append(symbol)
        
        return results
    
    def fetch_and_store_stock_data(self, symbol: str, period: str = '1y') -> Dict[str, Any]:
        """Fetch stock data from Yahoo Finance and store in database"""
        try:
            # Get symbol ID
            symbol_id = self.get_symbol_id(symbol)
            if not symbol_id:
                return {'success': False, 'error': f'Symbol {symbol} not found in database'}
            
            # Fetch data using existing scraper
            df = self.scraper.get_stock_data(symbol, period)
            if df is None or df.empty:
                return {'success': False, 'error': f'No data returned for {symbol}'}
            
            # Store data in database
            stored_count = self._store_daily_data(symbol_id, df)
            
            return {
                'success': True,
                'symbol': symbol,
                'period': period,
                'records_fetched': len(df),
                'records_stored': stored_count
            }
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _store_daily_data(self, symbol_id: int, df: pd.DataFrame) -> int:
        """Store daily stock data in database"""
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
        
        return self.db.execute_many(insert_query, data_to_insert)
    
    def fetch_all_stocks_data(self, period: str = '1y', delay: float = 1.0) -> Dict[str, Any]:
        """Fetch data for all symbols in database"""
        # Get all symbols from database
        query = "SELECT symbol FROM stock_symbols ORDER BY symbol"
        symbols_data = self.db.execute_query(query)
        
        if not symbols_data:
            return {'success': False, 'error': 'No symbols found in database'}
        
        symbols = [row['symbol'] for row in symbols_data]
        results = {'success': [], 'failed': [], 'total_symbols': len(symbols)}
        
        for symbol in symbols:
            result = self.fetch_and_store_stock_data(symbol, period)
            if result['success']:
                results['success'].append(result)
            else:
                results['failed'].append({'symbol': symbol, 'error': result['error']})
        
        return results
    
    def get_stock_data(self, symbol: str, start_date: date = None, end_date: date = None) -> List[Dict]:
        """Get stock data from database"""
        symbol_id = self.get_symbol_id(symbol)
        if not symbol_id:
            return []
        
        query = """
            SELECT * FROM daily_stock_data 
            WHERE symbol_id = %s
        """
        params = [symbol_id]
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY date DESC"
        
        return self.db.execute_query(query, params)
    
    def get_all_symbols(self) -> List[Dict]:
        """Get all stock symbols from database"""
        query = "SELECT * FROM stock_symbols ORDER BY symbol"
        return self.db.execute_query(query)
    
    def get_latest_data_for_all_stocks(self) -> List[Dict]:
        """Get latest data for all stocks"""
        query = """
            SELECT s.symbol, s.company_name, d.date, d.close, d.volume, d.high, d.low
            FROM stock_symbols s
            LEFT JOIN daily_stock_data d ON s.id = d.symbol_id
            WHERE d.date = (
                SELECT MAX(date) 
                FROM daily_stock_data 
                WHERE symbol_id = s.id
            )
            ORDER BY s.symbol
        """
        return self.db.execute_query(query)

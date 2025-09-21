"""
Technical Indicators Service
Calculates and stores technical indicators using the configuration
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.indicators_config import INDICATOR_CONFIGS, get_enabled_indicators, get_indicator_periods
from utils.database import get_db_connection
from models.stock_models import TechnicalIndicator

logger = logging.getLogger(__name__)

class TechnicalIndicatorsService:
    """Service for calculating and storing technical indicators"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index)"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate EMA (Exponential Moving Average)"""
        return df['close'].ewm(span=period).mean()
    
    def calculate_sma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate SMA (Simple Moving Average)"""
        return df['close'].rolling(window=period).mean()
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR (Average True Range)"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    def calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3, smooth_k: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        # Convert to float to avoid decimal type issues
        df_numeric = df[['high', 'low', 'close']].astype(float)
        
        lowest_low = df_numeric['low'].rolling(window=k_period).min()
        highest_high = df_numeric['high'].rolling(window=k_period).max()
        
        k_percent = 100 * ((df_numeric['close'] - lowest_low) / (highest_high - lowest_low))
        k_percent_smooth = k_percent.rolling(window=smooth_k).mean()
        d_percent = k_percent_smooth.rolling(window=d_period).mean()
        
        return {
            'k': k_percent_smooth,
            'd': d_percent
        }
    
    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        # Convert to float to avoid decimal type issues
        df_numeric = df[['high', 'low', 'close']].astype(float)
        
        highest_high = df_numeric['high'].rolling(window=period).max()
        lowest_low = df_numeric['low'].rolling(window=period).min()
        williams_r = -100 * ((highest_high - df_numeric['close']) / (highest_high - lowest_low))
        return williams_r
    
    def calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        # Convert to float to avoid decimal type issues
        df_numeric = df[['high', 'low', 'close']].astype(float)
        
        typical_price = (df_numeric['high'] + df_numeric['low'] + df_numeric['close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci
    
    def calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Money Flow Index"""
        # Convert to float to avoid decimal type issues
        df_numeric = df[['high', 'low', 'close', 'volume']].astype(float)
        
        typical_price = (df_numeric['high'] + df_numeric['low'] + df_numeric['close']) / 3
        money_flow = typical_price * df_numeric['volume']
        
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=period).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=period).sum()
        
        mfi = 100 - (100 / (1 + (positive_flow / negative_flow)))
        return mfi
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict[str, Dict[str, pd.Series]]:
        """Calculate all enabled indicators"""
        indicators = {}
        
        # Sort dataframe by date to ensure proper calculation
        df = df.sort_values('date').reset_index(drop=True)
        
        for indicator_name, config in INDICATOR_CONFIGS.items():
            if not config.get('enabled', False):
                continue
                
            try:
                if indicator_name == 'RSI':
                    periods = get_indicator_periods('RSI')
                    indicators['RSI'] = {}
                    for period in periods:
                        indicators['RSI'][f'RSI_{period}'] = self.calculate_rsi(df, period)
                
                elif indicator_name == 'EMA':
                    periods = get_indicator_periods('EMA')
                    indicators['EMA'] = {}
                    for period in periods:
                        indicators['EMA'][f'EMA_{period}'] = self.calculate_ema(df, period)
                
                elif indicator_name == 'SMA':
                    periods = get_indicator_periods('SMA')
                    indicators['SMA'] = {}
                    for period in periods:
                        indicators['SMA'][f'SMA_{period}'] = self.calculate_sma(df, period)
                
                elif indicator_name == 'ATR':
                    periods = get_indicator_periods('ATR')
                    indicators['ATR'] = {}
                    for period in periods:
                        indicators['ATR'][f'ATR_{period}'] = self.calculate_atr(df, period)
                
                elif indicator_name == 'MACD':
                    macd_config = config
                    macd_result = self.calculate_macd(
                        df, 
                        macd_config['fast_period'], 
                        macd_config['slow_period'], 
                        macd_config['signal_period']
                    )
                    indicators['MACD'] = {
                        'MACD': macd_result['macd'],
                        'MACD_Signal': macd_result['signal'],
                        'MACD_Histogram': macd_result['histogram']
                    }
                
                elif indicator_name == 'BOLLINGER_BANDS':
                    bb_config = config
                    bb_result = self.calculate_bollinger_bands(
                        df, 
                        bb_config['period'], 
                        bb_config['std_dev']
                    )
                    indicators['BOLLINGER_BANDS'] = {
                        'BB_Upper': bb_result['upper'],
                        'BB_Middle': bb_result['middle'],
                        'BB_Lower': bb_result['lower']
                    }
                
                elif indicator_name == 'STOCHASTIC':
                    stoch_config = config
                    stoch_result = self.calculate_stochastic(
                        df,
                        stoch_config['k_period'],
                        stoch_config['d_period'],
                        stoch_config['smooth_k']
                    )
                    indicators['STOCHASTIC'] = {
                        'Stoch_K': stoch_result['k'],
                        'Stoch_D': stoch_result['d']
                    }
                
                elif indicator_name == 'WILLIAMS_R':
                    period = config['period']
                    indicators['WILLIAMS_R'] = {
                        f'Williams_R_{period}': self.calculate_williams_r(df, period)
                    }
                
                elif indicator_name == 'CCI':
                    period = config['period']
                    indicators['CCI'] = {
                        f'CCI_{period}': self.calculate_cci(df, period)
                    }
                
                elif indicator_name == 'MFI':
                    period = config['period']
                    indicators['MFI'] = {
                        f'MFI_{period}': self.calculate_mfi(df, period)
                    }
                    
            except Exception as e:
                logger.error(f"Error calculating {indicator_name}: {e}")
                continue
        
        return indicators
    
    def store_indicators_in_database(self, symbol_id: int, df: pd.DataFrame, indicators: Dict[str, Dict[str, pd.Series]]):
        """Store calculated indicators in database"""
        if not self.db.connect():
            logger.error("Failed to connect to database")
            return False
        
        try:
            stored_count = 0
            
            for indicator_type, indicator_data in indicators.items():
                for indicator_name, values in indicator_data.items():
                    # Extract period from indicator name if present
                    period = None
                    if '_' in indicator_name:
                        try:
                            period = int(indicator_name.split('_')[-1])
                        except ValueError:
                            period = None
                    
                    # Prepare data for insertion
                    insert_query = """
                        INSERT INTO technical_indicators (symbol_id, date, indicator_name, value, period)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        value = VALUES(value)
                    """
                    
                    data_to_insert = []
                    for idx, row in df.iterrows():
                        if pd.notna(values.iloc[idx]):
                            data_to_insert.append((
                                symbol_id,
                                row['date'],
                                indicator_name,
                                float(values.iloc[idx]),
                                period
                            ))
                    
                    if data_to_insert:
                        rows_inserted = self.db.execute_many(insert_query, data_to_insert)
                        stored_count += rows_inserted
                        logger.info(f"Stored {rows_inserted} {indicator_name} values for symbol_id {symbol_id}")
            
            logger.info(f"Total indicators stored: {stored_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing indicators: {e}")
            return False
        finally:
            self.db.disconnect()
    
    def calculate_and_store_indicators(self, symbol_id: int, df: pd.DataFrame):
        """Calculate and store all indicators for a symbol"""
        logger.info(f"Calculating indicators for symbol_id {symbol_id}")
        
        # Calculate all indicators
        indicators = self.calculate_all_indicators(df)
        
        # Store in database
        success = self.store_indicators_in_database(symbol_id, df, indicators)
        
        if success:
            logger.info(f"Successfully calculated and stored indicators for symbol_id {symbol_id}")
        else:
            logger.error(f"Failed to store indicators for symbol_id {symbol_id}")
        
        return success

# Example usage
if __name__ == "__main__":
    # Test the service
    service = TechnicalIndicatorsService()
    
    enabled_indicators = get_enabled_indicators()
    print(f"Enabled indicators: {', '.join(enabled_indicators)}")
    
    # Create sample data for testing
    sample_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100),
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 5000000, 100)
    })
    
    print("\nCalculating indicators for sample data...")
    indicators = service.calculate_all_indicators(sample_data)
    
    for indicator_type, data in indicators.items():
        print(f"\n{indicator_type}:")
        for name, values in data.items():
            print(f"  {name}: {len(values.dropna())} valid values")

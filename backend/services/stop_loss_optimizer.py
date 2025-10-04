#!/usr/bin/env python3
"""
Stop Loss Optimization Service
Analyzes historical data to find optimal stop loss percentages for different time periods
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

@dataclass
class StopLossResult:
    """Stop loss optimization result"""
    period_start: datetime
    period_end: datetime
    optimal_stop_loss: float
    total_return: float
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float
    trades: List[Dict]

@dataclass
class StopLossOptimization:
    """Complete stop loss optimization analysis"""
    symbol: str
    analysis_date: datetime
    overall_optimal: float
    monthly_results: List[StopLossResult]
    quarterly_results: List[StopLossResult]
    yearly_results: List[StopLossResult]
    stop_loss_range: Tuple[float, float]
    test_intervals: List[float]

class StopLossOptimizer:
    """Optimizes stop loss percentages based on historical data"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.stop_loss_range = (0.02, 0.20)  # 2% to 20%
        self.test_intervals = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12, 0.15, 0.18, 0.20]
        
    def optimize_stop_loss(self, df: pd.DataFrame, symbol: str) -> StopLossOptimization:
        """Run complete stop loss optimization analysis"""
        logger.info(f"Starting stop loss optimization for {symbol}")
        
        # Ensure data is sorted by date
        df = df.sort_values('date').reset_index(drop=True)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Remove any rows with invalid dates
        df = df.dropna(subset=['date'])
        
        # Convert decimal columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].astype(float)
        
        # Generate trading signals (simplified version)
        signals = self._generate_trading_signals(df)
        
        # Run optimization for different time periods
        monthly_results = self._optimize_by_period(df, signals, 'monthly')
        quarterly_results = self._optimize_by_period(df, signals, 'quarterly')
        yearly_results = self._optimize_by_period(df, signals, 'yearly')
        
        # Find overall optimal stop loss
        overall_optimal = self._find_overall_optimal(df, signals)
        
        return StopLossOptimization(
            symbol=symbol,
            analysis_date=datetime.now(),
            overall_optimal=overall_optimal,
            monthly_results=monthly_results,
            quarterly_results=quarterly_results,
            yearly_results=yearly_results,
            stop_loss_range=self.stop_loss_range,
            test_intervals=self.test_intervals
        )
    
    def _generate_trading_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Generate simplified trading signals based on price action"""
        signals = []
        
        # Simple momentum-based signals
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['rsi'] = self._calculate_rsi(df['close'], 14)
        
        for i in range(50, len(df)):  # Start after enough data for indicators
            current_price = df.iloc[i]['close']
            sma_20 = df.iloc[i]['sma_20']
            sma_50 = df.iloc[i]['sma_50']
            rsi = df.iloc[i]['rsi']
            
            # Buy signal: Price above both SMAs, RSI not overbought
            if (current_price > sma_20 and current_price > sma_50 and 
                rsi < 70 and rsi > 30):
                signals.append({
                    'date': df.iloc[i]['date'],
                    'action': 'BUY',
                    'price': current_price,
                    'volume': df.iloc[i]['volume']
                })
            
            # Sell signal: Price below both SMAs, RSI not oversold
            elif (current_price < sma_20 and current_price < sma_50 and 
                  rsi > 30 and rsi < 70):
                signals.append({
                    'date': df.iloc[i]['date'],
                    'action': 'SELL',
                    'price': current_price,
                    'volume': df.iloc[i]['volume']
                })
        
        return signals
    
    def _optimize_by_period(self, df: pd.DataFrame, signals: List[Dict], period_type: str) -> List[StopLossResult]:
        """Optimize stop loss for different time periods"""
        results = []
        
        if period_type == 'monthly':
            periods = self._get_monthly_periods(df)
        elif period_type == 'quarterly':
            periods = self._get_quarterly_periods(df)
        elif period_type == 'yearly':
            periods = self._get_yearly_periods(df)
        else:
            return results
        
        for period_start, period_end in periods:
            # Filter signals for this period
            period_signals = [s for s in signals if period_start <= s['date'] <= period_end]
            
            if len(period_signals) < 5:  # Need minimum signals for meaningful analysis
                continue
            
            # Test different stop loss percentages
            best_result = None
            best_score = -float('inf')
            
            for stop_loss_pct in self.test_intervals:
                result = self._backtest_with_stop_loss(df, period_signals, stop_loss_pct, period_start, period_end)
                
                # Score based on Sharpe ratio and win rate
                score = result.sharpe_ratio * 0.6 + (result.win_rate / 100) * 0.4
                
                if score > best_score:
                    best_score = score
                    best_result = result
            
            if best_result:
                results.append(best_result)
        
        return results
    
    def _get_monthly_periods(self, df: pd.DataFrame) -> List[Tuple[datetime, datetime]]:
        """Get monthly periods from data"""
        periods = []
        start_date = df['date'].min()
        end_date = df['date'].max()
        
        # Start from beginning of month
        current = start_date.replace(day=1)
        while current <= end_date:
            # Calculate next month
            if current.month == 12:
                next_month = current.replace(year=current.year + 1, month=1, day=1)
            else:
                next_month = current.replace(month=current.month + 1, day=1)
            
            period_start = current
            period_end = min(next_month - timedelta(days=1), end_date)
            
            periods.append((period_start, period_end))
            current = next_month
        
        return periods
    
    def _get_quarterly_periods(self, df: pd.DataFrame) -> List[Tuple[datetime, datetime]]:
        """Get quarterly periods from data"""
        periods = []
        start_date = df['date'].min()
        end_date = df['date'].max()
        
        # Start from beginning of quarter
        quarter_start_month = ((start_date.month - 1) // 3) * 3 + 1
        current = start_date.replace(month=quarter_start_month, day=1)
        
        while current <= end_date:
            # Calculate end of quarter
            if current.month in [1, 2, 3]:
                quarter_end = current.replace(month=3, day=31)
            elif current.month in [4, 5, 6]:
                quarter_end = current.replace(month=6, day=30)
            elif current.month in [7, 8, 9]:
                quarter_end = current.replace(month=9, day=30)
            else:
                quarter_end = current.replace(month=12, day=31)
            
            period_start = current
            period_end = min(quarter_end, end_date)
            
            periods.append((period_start, period_end))
            
            # Move to next quarter
            if current.month >= 10:  # Q4 (Oct, Nov, Dec)
                current = current.replace(year=current.year + 1, month=1, day=1)
            elif current.month >= 7:  # Q3 (Jul, Aug, Sep)
                current = current.replace(month=10, day=1)
            elif current.month >= 4:  # Q2 (Apr, May, Jun)
                current = current.replace(month=7, day=1)
            else:  # Q1 (Jan, Feb, Mar)
                current = current.replace(month=4, day=1)
        
        return periods
    
    def _get_yearly_periods(self, df: pd.DataFrame) -> List[Tuple[datetime, datetime]]:
        """Get yearly periods from data"""
        periods = []
        start_date = df['date'].min()
        end_date = df['date'].max()
        
        current_year = start_date.year
        end_year = end_date.year
        
        while current_year <= end_year:
            period_start = datetime(current_year, 1, 1)
            period_end = datetime(current_year, 12, 31)
            
            # Adjust for actual data range
            period_start = max(period_start, start_date)
            period_end = min(period_end, end_date)
            
            periods.append((period_start, period_end))
            current_year += 1
        
        return periods
    
    def _backtest_with_stop_loss(self, df: pd.DataFrame, signals: List[Dict], 
                                stop_loss_pct: float, period_start: datetime, 
                                period_end: datetime) -> StopLossResult:
        """Run backtest with specific stop loss percentage"""
        
        capital = self.initial_capital
        position = None
        trades = []
        equity_curve = [capital]
        
        # Filter data for this period
        period_data = df[(df['date'] >= period_start) & (df['date'] <= period_end)].copy()
        
        for signal in signals:
            if signal['action'] == 'BUY' and position is None:
                # Open long position
                shares = capital / signal['price']
                position = {
                    'shares': shares,
                    'entry_price': signal['price'],
                    'entry_date': signal['date'],
                    'entry_capital': capital
                }
            
            elif signal['action'] == 'SELL' and position is not None:
                # Close long position
                exit_price = signal['price']
                exit_date = signal['date']
                
                # Check for stop loss
                stop_loss_price = position['entry_price'] * (1 - stop_loss_pct)
                if exit_price <= stop_loss_price:
                    exit_price = stop_loss_price
                    exit_reason = 'Stop Loss'
                else:
                    exit_reason = 'Signal'
                
                # Calculate trade result
                pnl = (exit_price - position['entry_price']) * position['shares']
                pnl_percent = (exit_price - position['entry_price']) / position['entry_price'] * 100
                capital += pnl
                
                trades.append({
                    'entry_date': position['entry_date'],
                    'exit_date': exit_date,
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'shares': position['shares'],
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'exit_reason': exit_reason
                })
                
                equity_curve.append(capital)
                position = None
        
        # Close any remaining position at end of period
        if position is not None:
            last_price = period_data.iloc[-1]['close']
            exit_date = period_data.iloc[-1]['date']
            
            pnl = (last_price - position['entry_price']) * position['shares']
            pnl_percent = (last_price - position['entry_price']) / position['entry_price'] * 100
            capital += pnl
            
            trades.append({
                'entry_date': position['entry_date'],
                'exit_date': exit_date,
                'entry_price': position['entry_price'],
                'exit_price': last_price,
                'shares': position['shares'],
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'exit_reason': 'Period End'
            })
            
            equity_curve.append(capital)
        
        # Calculate performance metrics
        if not trades:
            return StopLossResult(
                period_start=period_start,
                period_end=period_end,
                optimal_stop_loss=stop_loss_pct,
                total_return=0,
                win_rate=0,
                max_drawdown=0,
                sharpe_ratio=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0,
                avg_loss=0,
                profit_factor=0,
                trades=[]
            )
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        total_return = (capital - self.initial_capital) / self.initial_capital * 100
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        
        # Calculate max drawdown
        peak = self.initial_capital
        max_dd = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        # Calculate Sharpe ratio (simplified)
        returns = [t['pnl_percent'] for t in trades]
        sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        return StopLossResult(
            period_start=period_start,
            period_end=period_end,
            optimal_stop_loss=stop_loss_pct,
            total_return=total_return,
            win_rate=win_rate,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe_ratio,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            trades=trades
        )
    
    def _find_overall_optimal(self, df: pd.DataFrame, signals: List[Dict]) -> float:
        """Find overall optimal stop loss for entire dataset"""
        best_stop_loss = 0.08  # Default
        best_score = -float('inf')
        
        for stop_loss_pct in self.test_intervals:
            result = self._backtest_with_stop_loss(df, signals, stop_loss_pct, 
                                                df['date'].min(), df['date'].max())
            
            # Score based on multiple factors
            score = (result.sharpe_ratio * 0.4 + 
                    (result.win_rate / 100) * 0.3 + 
                    (result.total_return / 100) * 0.2 + 
                    (1 - result.max_drawdown / 100) * 0.1)
            
            if score > best_score:
                best_score = score
                best_stop_loss = stop_loss_pct
        
        return best_stop_loss
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

# Example usage
if __name__ == "__main__":
    # This would be called from the API routes
    pass

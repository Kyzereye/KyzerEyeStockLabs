#!/usr/bin/env python3
"""
EMA Trading System

Simple moving average trading strategy:
- BUY signal: Price moves above 50 EMA
- SELL signal: Price drops below 21 EMA
- Only one trade at a time (no overlapping trades)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class EMASignal:
    """EMA trading signal"""
    date: datetime
    signal_type: str  # 'BUY' or 'SELL'
    price: float
    ema_21: float
    ema_50: float
    reasoning: str
    confidence: float
    atr: Optional[float] = None
    trailing_stop: Optional[float] = None

@dataclass
class EMATrade:
    """EMA trade record"""
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    entry_signal: str
    exit_signal: str
    shares: int
    pnl: Optional[float]
    pnl_percent: Optional[float]
    duration_days: Optional[int]
    exit_reason: Optional[str] = None  # 'EMA_SIGNAL' or 'TRAILING_STOP'

@dataclass
class EMAResults:
    """Complete EMA trading results"""
    symbol: str
    start_date: datetime
    end_date: datetime
    total_days: int
    trades: List[EMATrade]
    signals: List[EMASignal]
    performance_metrics: Dict
    equity_curve: List[Tuple[datetime, float]]

class EMATradingEngine:
    """
    EMA Trading Engine
    
    Implements a simple EMA crossover strategy:
    - BUY when price > 50 EMA
    - SELL when price < 21 EMA
    - Only one trade at a time
    """
    
    def __init__(self, initial_capital: float = 100000, atr_period: int = 14, atr_multiplier: float = 2.0):
        self.initial_capital = initial_capital
        self.ema_21_period = 21
        self.ema_50_period = 50
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range (ATR)"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR as EMA of True Range
        atr = true_range.ewm(span=period, adjust=False).mean()
        
        return atr
    
    def run_analysis(self, df: pd.DataFrame, symbol: str) -> EMAResults:
        """
        Run EMA trading analysis
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            
        Returns:
            EMAResults object with complete analysis
        """
        logger.info(f"Starting EMA analysis for {symbol}")
        
        if len(df) < self.ema_50_period:
            raise ValueError(f"Not enough data for EMA analysis. Need at least {self.ema_50_period} days")
        
        # Calculate EMAs and ATR
        df['ema_21'] = self.calculate_ema(df['close'], self.ema_21_period)
        df['ema_50'] = self.calculate_ema(df['close'], self.ema_50_period)
        df['atr'] = self.calculate_atr(df, self.atr_period)
        
        # Generate signals
        signals = self._generate_signals(df)
        
        # Execute trades
        trades = self._execute_trades(df, signals)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(trades)
        
        # Generate equity curve
        equity_curve = self._generate_equity_curve(df, trades)
        
        return EMAResults(
            symbol=symbol,
            start_date=df.index[0],
            end_date=df.index[-1],
            total_days=len(df),
            trades=trades,
            signals=signals,
            performance_metrics=performance_metrics,
            equity_curve=equity_curve
        )
    
    def _generate_signals(self, df: pd.DataFrame) -> List[EMASignal]:
        """Generate EMA trading signals with trailing stop management"""
        signals = []
        in_trade = False
        current_trailing_stop = None
        highest_price_since_entry = None
        
        # Start from max(ema_50_period, atr_period) to ensure both are calculated
        start_index = max(self.ema_50_period, self.atr_period)
        
        for i in range(start_index, len(df)):
            current_price = df.iloc[i]['close']
            ema_21 = df.iloc[i]['ema_21']
            ema_50 = df.iloc[i]['ema_50']
            atr = df.iloc[i]['atr']
            date = df.index[i]
            
            # Skip if indicators are not calculated yet
            if pd.isna(ema_21) or pd.isna(ema_50) or pd.isna(atr):
                continue
            
            # BUY signal: Price closes above 50 EMA (only if not in trade)
            if not in_trade and current_price > ema_50:
                # Check if this is a new signal (price closed below 50 EMA in previous period)
                if i > 0 and df.iloc[i-1]['close'] <= df.iloc[i-1]['ema_50']:
                    confidence = min(0.9, abs(current_price - ema_50) / ema_50 * 10)
                    # Set initial trailing stop
                    current_trailing_stop = current_price - (atr * self.atr_multiplier)
                    highest_price_since_entry = current_price
                    
                    signals.append(EMASignal(
                        date=date,
                        signal_type='BUY',
                        price=current_price,
                        ema_21=ema_21,
                        ema_50=ema_50,
                        reasoning=f"Price {current_price:.2f} closed above 50 EMA {ema_50:.2f}",
                        confidence=confidence,
                        atr=atr,
                        trailing_stop=current_trailing_stop
                    ))
                    in_trade = True
            
            # Update trailing stop and check for sell signals (only if in trade)
            elif in_trade:
                # Update highest price since entry
                if highest_price_since_entry is None or current_price > highest_price_since_entry:
                    highest_price_since_entry = current_price
                    # Update trailing stop: highest price - (ATR * multiplier)
                    current_trailing_stop = highest_price_since_entry - (atr * self.atr_multiplier)
                
                # Check for SELL signals: Price below 21 EMA OR below trailing stop
                sell_triggered = False
                sell_reason = ""
                
                if current_price < ema_21:
                    # Check if this is a new signal (price closed above 21 EMA in previous period)
                    if i > 0 and df.iloc[i-1]['close'] >= df.iloc[i-1]['ema_21']:
                        sell_triggered = True
                        sell_reason = f"Price {current_price:.2f} closed below 21 EMA {ema_21:.2f}"
                
                elif current_trailing_stop is not None and current_price < current_trailing_stop:
                    sell_triggered = True
                    sell_reason = f"Price {current_price:.2f} hit trailing stop {current_trailing_stop:.2f}"
                
                if sell_triggered:
                    confidence = min(0.9, abs(current_price - ema_21) / ema_21 * 10)
                    signals.append(EMASignal(
                        date=date,
                        signal_type='SELL',
                        price=current_price,
                        ema_21=ema_21,
                        ema_50=ema_50,
                        reasoning=sell_reason,
                        confidence=confidence,
                        atr=atr,
                        trailing_stop=current_trailing_stop
                    ))
                    in_trade = False
                    current_trailing_stop = None
                    highest_price_since_entry = None
        
        return signals
    
    def _execute_trades(self, df: pd.DataFrame, signals: List[EMASignal]) -> List[EMATrade]:
        """Execute trades based on signals using next day's open prices"""
        trades = []
        current_position = None
        available_capital = self.initial_capital
        
        # Create a mapping of dates to DataFrame indices for quick lookup
        date_to_index = {df.index[i]: i for i in range(len(df))}
        
        for signal in signals:
            if signal.signal_type == 'BUY' and current_position is None:
                # Find the next day's open price for entry
                signal_index = date_to_index.get(signal.date)
                if signal_index is not None and signal_index + 1 < len(df):
                    next_day_open = df.iloc[signal_index + 1]['open']
                    shares = int(available_capital / next_day_open)
                    if shares > 0:
                        current_position = {
                            'entry_date': signal.date,
                            'entry_price': next_day_open,
                            'entry_signal': signal.reasoning,
                            'shares': shares
                        }
                        available_capital -= shares * next_day_open
                        logger.info(f"Opened BUY position: {shares} shares at ${next_day_open:.2f} (next day open)")
            
            elif signal.signal_type == 'SELL' and current_position is not None:
                # Find the next day's open price for exit
                signal_index = date_to_index.get(signal.date)
                if signal_index is not None and signal_index + 1 < len(df):
                    next_day_open = df.iloc[signal_index + 1]['open']
                    shares = current_position['shares']
                    pnl = shares * (next_day_open - current_position['entry_price'])
                    pnl_percent = (next_day_open - current_position['entry_price']) / current_position['entry_price'] * 100
                    duration = (signal.date - current_position['entry_date']).days
                    
                    # Determine exit reason
                    exit_reason = 'TRAILING_STOP' if 'trailing stop' in signal.reasoning.lower() else 'EMA_SIGNAL'
                    
                    trade = EMATrade(
                        entry_date=current_position['entry_date'],
                        exit_date=signal.date,
                        entry_price=current_position['entry_price'],
                        exit_price=next_day_open,
                        entry_signal=current_position['entry_signal'],
                        exit_signal=signal.reasoning,
                        shares=shares,
                        pnl=pnl,
                        pnl_percent=pnl_percent,
                        duration_days=duration,
                        exit_reason=exit_reason
                    )
                    
                    trades.append(trade)
                    available_capital += shares * next_day_open
                    
                    logger.info(f"Closed position: PnL ${pnl:.2f} ({pnl_percent:.2f}%) over {duration} days")
                    current_position = None
        
        # Close any remaining position at the end
        if current_position is not None:
            final_price = df.iloc[-1]['close']
            final_date = df.index[-1]
            shares = current_position['shares']
            pnl = shares * (final_price - current_position['entry_price'])
            pnl_percent = (final_price - current_position['entry_price']) / current_position['entry_price'] * 100
            duration = (final_date - current_position['entry_date']).days
            
            trade = EMATrade(
                entry_date=current_position['entry_date'],
                exit_date=final_date,
                entry_price=current_position['entry_price'],
                exit_price=final_price,
                entry_signal=current_position['entry_signal'],
                exit_signal="End of period - position closed",
                shares=shares,
                pnl=pnl,
                pnl_percent=pnl_percent,
                duration_days=duration
            )
            
            trades.append(trade)
            logger.info(f"Closed final position: PnL ${pnl:.2f} ({pnl_percent:.2f}%) over {duration} days")
        
        return trades
    
    def _calculate_performance_metrics(self, trades: List[EMATrade]) -> Dict:
        """Calculate performance metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_return_percent': 0.0,
                'avg_trade_duration': 0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t.pnl for t in trades if t.pnl is not None)
        total_return_percent = (total_pnl / self.initial_capital) * 100
        
        avg_duration = sum(t.duration_days for t in trades if t.duration_days is not None) / total_trades
        
        # Calculate max drawdown
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in trades:
            if trade.pnl is not None:
                cumulative_pnl += trade.pnl
                if cumulative_pnl > peak:
                    peak = cumulative_pnl
                drawdown = peak - cumulative_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return_percent': total_return_percent,
            'avg_trade_duration': avg_duration,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': 0.0  # Simplified for now
        }
    
    def _generate_equity_curve(self, df: pd.DataFrame, trades: List[EMATrade]) -> List[Tuple[datetime, float]]:
        """Generate equity curve"""
        equity_curve = []
        current_equity = self.initial_capital
        
        # Create a mapping of dates to trade PnL
        trade_pnl_by_date = {}
        for trade in trades:
            if trade.exit_date and trade.pnl is not None:
                trade_pnl_by_date[trade.exit_date] = trade.pnl
        
        for date in df.index:
            if date in trade_pnl_by_date:
                current_equity += trade_pnl_by_date[date]
            equity_curve.append((date, current_equity))
        
        return equity_curve

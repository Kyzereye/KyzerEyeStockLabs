#!/usr/bin/env python3
"""
Wyckoff Backtest Algorithm
Comprehensive backtesting system for Wyckoff Method trading strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class WyckoffPhase(Enum):
    """Wyckoff Phase enumeration"""
    ACCUMULATION = "Accumulation"
    DISTRIBUTION = "Distribution"
    MARKUP = "Markup"
    MARKDOWN = "Markdown"

class TradeAction(Enum):
    """Trade action enumeration"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class WyckoffSignal:
    """Wyckoff trading signal"""
    date: datetime
    phase: WyckoffPhase
    action: TradeAction
    price: float
    volume_ratio: float
    confidence: float
    reasoning: str
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None

@dataclass
class Trade:
    """Individual trade record"""
    symbol: str
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    action: TradeAction
    shares: int
    entry_phase: WyckoffPhase
    exit_phase: Optional[WyckoffPhase]
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    duration_days: Optional[int] = None
    entry_reasoning: str = ""
    exit_reasoning: str = ""

@dataclass
class BacktestResults:
    """Complete backtest results"""
    symbol: str
    start_date: datetime
    end_date: datetime
    total_days: int
    trades: List[Trade]
    signals: List[WyckoffSignal]
    performance_metrics: Dict
    phase_analysis: Dict
    equity_curve: List[Tuple[datetime, float]]

class WyckoffBacktestEngine:
    """
    Wyckoff Method Backtesting Engine
    
    Analyzes historical data chronologically and simulates trades based on
    Wyckoff phase identification and trading signals.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize backtest engine
        
        Args:
            initial_capital: Starting capital for backtesting
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.volume_threshold = 1.5  # Volume must be 1.5x average
        self.price_change_threshold = 0.02  # 2% price change threshold
        
        # Trade simulation parameters
        self.position_size_percent = 0.95  # Use 95% of capital per trade
        self.stop_loss_percent = 0.08  # 8% stop loss
        self.take_profit_percent = 0.15  # 15% take profit
        self.max_trade_duration = 60  # Maximum 60 days per trade
        
    def run_backtest(self, df: pd.DataFrame, symbol: str) -> BacktestResults:
        """
        Run complete Wyckoff backtest on historical data
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            
        Returns:
            Complete backtest results
        """
        print(f"🚀 Starting Wyckoff Backtest for {symbol}")
        print(f"📅 Period: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        
        # Prepare data
        df = self._prepare_data(df)
        
        # Initialize tracking variables
        current_position = None
        trades = []
        signals = []
        equity_curve = []
        
        # Reset capital for this backtest
        self.current_capital = self.initial_capital
        
        # Analyze each day chronologically
        for i in range(30, len(df)):  # Start after 30 days for indicators
            current_date = df.index[i]
            current_data = df.iloc[:i+1]  # All data up to current day
            
            # Analyze current Wyckoff phase
            phase_analysis = self._analyze_current_phase(current_data)
            signal = self._generate_signal(current_data, phase_analysis, current_date)
            signals.append(signal)
            
            # Handle existing position
            if current_position:
                current_position = self._update_position(current_position, current_data, signal)
                
                # Check for exit conditions
                if self._should_exit_position(current_position, current_data, signal):
                    trade = self._close_position(current_position, current_data.iloc[-1], signal)
                    trades.append(trade)
                    current_position = None
            
            # Check for new entry
            if not current_position and signal.action != TradeAction.HOLD:
                position = self._enter_position(signal, current_data.iloc[-1])
                if position:
                    current_position = position
            
            # Update equity curve
            portfolio_value = self._calculate_portfolio_value(current_position, current_data.iloc[-1])
            equity_curve.append((current_date, portfolio_value))
        
        # Close any remaining position
        if current_position:
            final_signal = WyckoffSignal(
                date=df.index[-1],
                phase=WyckoffPhase.MARKUP,
                action=TradeAction.HOLD,
                price=df.iloc[-1]['close'],
                volume_ratio=1.0,
                confidence=0.0,
                reasoning="End of backtest period"
            )
            trade = self._close_position(current_position, df.iloc[-1], final_signal)
            trades.append(trade)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(trades, equity_curve)
        
        # Analyze phases
        phase_analysis = self._analyze_phases(signals)
        
        print(f"✅ Backtest Complete!")
        print(f"📊 Total Trades: {len(trades)}")
        print(f"💰 Final Portfolio Value: ${portfolio_value:,.2f}")
        print(f"📈 Total Return: {((portfolio_value / self.initial_capital) - 1) * 100:.2f}%")
        
        return BacktestResults(
            symbol=symbol,
            start_date=df.index[30],
            end_date=df.index[-1],
            total_days=len(df) - 30,
            trades=trades,
            signals=signals,
            performance_metrics=performance_metrics,
            phase_analysis=phase_analysis,
            equity_curve=equity_curve
        )
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data with technical indicators"""
        df = df.copy()
        
        # Convert to float to avoid decimal issues
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Calculate technical indicators
        df['price_change'] = df['close'].pct_change()
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['high_volume'] = df['volume_ratio'] > self.volume_threshold
        
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # Price relative to moving averages
        df['price_vs_sma20'] = (df['close'] / df['sma_20'] - 1) * 100
        df['price_vs_sma50'] = (df['close'] / df['sma_50'] - 1) * 100
        
        # Volatility
        df['atr_14'] = self._calculate_atr(df, 14)
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        
        # Range analysis
        df['daily_range'] = (df['high'] - df['low']) / df['close']
        df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        return df
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(window=period).mean()
    
    def _analyze_current_phase(self, df: pd.DataFrame) -> Dict:
        """Analyze current Wyckoff phase based on recent data"""
        if len(df) < 20:
            return {
                'phase': WyckoffPhase.MARKUP,
                'confidence': 0.5,
                'price_trend': 0.0,
                'volume_trend': 1.0,
                'volatility': 0.0
            }
        
        recent_data = df.tail(20)  # Last 20 days
        current_price = df['close'].iloc[-1]
        
        # Analyze price action
        price_trend = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
        volume_trend = recent_data['volume_ratio'].mean()
        volatility = recent_data['volatility'].mean()
        
        # Determine phase based on Wyckoff principles
        if abs(price_trend) < 0.02 and volume_trend > 1.2:
            phase = WyckoffPhase.ACCUMULATION
            confidence = 0.8
        elif abs(price_trend) < 0.02 and volume_trend < 0.8:
            phase = WyckoffPhase.DISTRIBUTION
            confidence = 0.8
        elif price_trend > 0.05 and volume_trend > 1.1:
            phase = WyckoffPhase.MARKUP
            confidence = 0.9
        elif price_trend < -0.05:
            phase = WyckoffPhase.MARKDOWN
            confidence = 0.9
        else:
            phase = WyckoffPhase.MARKUP
            confidence = 0.6
        
        return {
            'phase': phase,
            'confidence': confidence,
            'price_trend': price_trend,
            'volume_trend': volume_trend,
            'volatility': volatility,
            'price': current_price
        }
    
    def _generate_signal(self, df: pd.DataFrame, phase_analysis: Dict, date: datetime) -> WyckoffSignal:
        """Generate Wyckoff trading signal"""
        phase = phase_analysis['phase']
        confidence = phase_analysis['confidence']
        price = phase_analysis['price']
        volume_trend = phase_analysis['volume_trend']
        
        # Determine action based on Wyckoff phase
        if phase == WyckoffPhase.ACCUMULATION:
            if volume_trend > 1.5:
                action = TradeAction.BUY
                reasoning = "High volume accumulation - institutional buying"
            else:
                action = TradeAction.HOLD
                reasoning = "Accumulation phase - waiting for volume confirmation"
        elif phase == WyckoffPhase.DISTRIBUTION:
            if volume_trend > 1.5:
                action = TradeAction.SELL
                reasoning = "High volume distribution - institutional selling"
            else:
                action = TradeAction.HOLD
                reasoning = "Distribution phase - waiting for volume confirmation"
        elif phase == WyckoffPhase.MARKUP:
            action = TradeAction.BUY
            reasoning = "Strong uptrend with volume confirmation"
        elif phase == WyckoffPhase.MARKDOWN:
            action = TradeAction.SELL
            reasoning = "Downtrend phase - avoid long positions"
        else:
            action = TradeAction.HOLD
            reasoning = "Markup phase - uptrend continuation"
        
        # Calculate support/resistance levels
        support, resistance = self._calculate_support_resistance(df)
        
        return WyckoffSignal(
            date=date,
            phase=phase,
            action=action,
            price=price,
            volume_ratio=volume_trend,
            confidence=confidence,
            reasoning=reasoning,
            support_level=support,
            resistance_level=resistance
        )
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """Calculate support and resistance levels"""
        if len(df) < 50:
            return None, None
        
        # Look for pivot highs and lows in recent data
        recent_data = df.tail(50)
        
        # Find pivot lows (support)
        pivot_lows = []
        for i in range(5, len(recent_data) - 5):
            if (recent_data['low'].iloc[i] < recent_data['low'].iloc[i-5:i].min() and 
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i+1:i+6].min()):
                pivot_lows.append(recent_data['low'].iloc[i])
        
        # Find pivot highs (resistance)
        pivot_highs = []
        for i in range(5, len(recent_data) - 5):
            if (recent_data['high'].iloc[i] > recent_data['high'].iloc[i-5:i].max() and 
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i+1:i+6].max()):
                pivot_highs.append(recent_data['high'].iloc[i])
        
        # Get nearest levels
        current_price = recent_data['close'].iloc[-1]
        
        support = None
        resistance = None
        
        if pivot_lows:
            support = max([p for p in pivot_lows if p < current_price], default=None)
        
        if pivot_highs:
            resistance = min([p for p in pivot_highs if p > current_price], default=None)
        
        return support, resistance
    
    def _enter_position(self, signal: WyckoffSignal, current_data: pd.Series) -> Optional[Trade]:
        """Enter a new position based on signal"""
        if signal.action == TradeAction.HOLD:
            return None
        
        # Calculate position size
        position_value = self.current_capital * self.position_size_percent
        shares = int(position_value / signal.price)
        
        if shares <= 0:
            return None
        
        # Calculate stop loss and take profit levels
        if signal.action == TradeAction.BUY:
            stop_loss = signal.price * (1 - self.stop_loss_percent)
            take_profit = signal.price * (1 + self.take_profit_percent)
        else:  # SELL (short)
            stop_loss = signal.price * (1 + self.stop_loss_percent)
            take_profit = signal.price * (1 - self.take_profit_percent)
        
        return Trade(
            symbol="",  # Will be set by caller
            entry_date=signal.date,
            exit_date=None,
            entry_price=signal.price,
            exit_price=None,
            action=signal.action,
            shares=shares,
            entry_phase=signal.phase,
            exit_phase=None,
            entry_reasoning=signal.reasoning
        )
    
    def _update_position(self, position: Trade, df: pd.DataFrame, signal: WyckoffSignal) -> Trade:
        """Update existing position with current signal"""
        # Position is updated in place, just return it
        return position
    
    def _should_exit_position(self, position: Trade, df: pd.DataFrame, signal: WyckoffSignal) -> bool:
        """Determine if position should be exited"""
        current_price = df['close'].iloc[-1]
        days_held = (signal.date - position.entry_date).days
        
        # Time-based exit
        if days_held >= self.max_trade_duration:
            return True
        
        # Stop loss / Take profit
        if position.action == TradeAction.BUY:
            if current_price <= position.entry_price * (1 - self.stop_loss_percent):
                return True
            if current_price >= position.entry_price * (1 + self.take_profit_percent):
                return True
        else:  # SELL (short)
            if current_price >= position.entry_price * (1 + self.stop_loss_percent):
                return True
            if current_price <= position.entry_price * (1 - self.take_profit_percent):
                return True
        
        # Phase-based exit
        if position.action == TradeAction.BUY and signal.phase == WyckoffPhase.DISTRIBUTION:
            return True
        if position.action == TradeAction.SELL and signal.phase == WyckoffPhase.ACCUMULATION:
            return True
        
        return False
    
    def _close_position(self, position: Trade, current_data: pd.Series, signal: WyckoffSignal) -> Trade:
        """Close existing position"""
        current_price = current_data['close']
        
        # Calculate P&L
        if position.action == TradeAction.BUY:
            pnl = (current_price - position.entry_price) * position.shares
        else:  # SELL (short)
            pnl = (position.entry_price - current_price) * position.shares
        
        pnl_percent = (pnl / (position.entry_price * position.shares)) * 100
        duration_days = (signal.date - position.entry_date).days
        
        # Update capital
        self.current_capital += pnl
        
        # Update position
        position.exit_date = signal.date
        position.exit_price = current_price
        position.exit_phase = signal.phase
        position.pnl = pnl
        position.pnl_percent = pnl_percent
        position.duration_days = duration_days
        position.exit_reasoning = signal.reasoning
        
        return position
    
    def _calculate_portfolio_value(self, position: Trade, current_data: pd.Series) -> float:
        """Calculate current portfolio value"""
        if not position:
            return self.current_capital
        
        current_price = current_data['close']
        
        if position.action == TradeAction.BUY:
            unrealized_pnl = (current_price - position.entry_price) * position.shares
        else:  # SELL (short)
            unrealized_pnl = (position.entry_price - current_price) * position.shares
        
        return self.current_capital + unrealized_pnl
    
    def _calculate_performance_metrics(self, trades: List[Trade], equity_curve: List[Tuple[datetime, float]]) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return {
                'total_return': 0.0,
                'total_return_percent': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl and t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl and t.pnl < 0])
        
        # Returns
        final_value = equity_curve[-1][1] if equity_curve else self.initial_capital
        total_return = final_value - self.initial_capital
        total_return_percent = (total_return / self.initial_capital) * 100
        
        # Win/Loss analysis
        wins = [t.pnl for t in trades if t.pnl and t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl and t.pnl < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        # Drawdown calculation
        equity_values = [value for _, value in equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_percent = max_drawdown * 100
        
        # Sharpe ratio (simplified)
        if len(equity_values) > 1:
            returns = [equity_values[i] / equity_values[i-1] - 1 for i in range(1, len(equity_values))]
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_return': total_return,
            'total_return_percent': total_return_percent,
            'final_value': final_value,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown_percent': max_drawdown_percent,
            'sharpe_ratio': sharpe_ratio
        }
    
    def _analyze_phases(self, signals: List[WyckoffSignal]) -> Dict:
        """Analyze Wyckoff phases throughout the backtest"""
        if not signals:
            return {}
        
        phase_counts = {}
        phase_durations = {}
        phase_performance = {}
        
        current_phase = None
        phase_start = None
        
        for signal in signals:
            if signal.phase != current_phase:
                # Phase change
                if current_phase and phase_start:
                    duration = (signal.date - phase_start).days
                    phase_name = current_phase.value
                    
                    if phase_name not in phase_durations:
                        phase_durations[phase_name] = []
                    phase_durations[phase_name].append(duration)
                
                current_phase = signal.phase
                phase_start = signal.date
            
            # Count phases
            phase_name = signal.phase.value
            phase_counts[phase_name] = phase_counts.get(phase_name, 0) + 1
        
        # Calculate average durations
        avg_durations = {}
        for phase, durations in phase_durations.items():
            avg_durations[phase] = np.mean(durations) if durations else 0
        
        return {
            'phase_counts': phase_counts,
            'avg_durations': avg_durations,
            'total_signals': len(signals)
        }

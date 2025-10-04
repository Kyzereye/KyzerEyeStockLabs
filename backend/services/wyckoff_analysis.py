#!/usr/bin/env python3
"""
Wyckoff Method Analysis Service
Analyzes price action and volume patterns for Wyckoff phase identification
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WyckoffAnalysisService:
    """
    Wyckoff Method Analysis Service
    
    Implements the authentic Wyckoff Method principles based on Richard D. Wyckoff's work:
    - The Composite Man Theory (institutional manipulation)
    - Five-Step Approach to market analysis
    - Accumulation/Distribution phases (A-E phases)
    - Volume-Price relationships and confirmation
    - Support/Resistance levels and springs
    - Point-and-Figure price targets
    - Trend identification and market structure
    """
    
    def __init__(self):
        # Volume analysis thresholds (based on Wyckoff principles)
        self.volume_threshold_multiplier = 2.0  # Volume must be 2x average for significance
        self.price_change_threshold = 0.03  # 3% price change threshold for phase transitions
        
        # Wyckoff phase identification parameters
        self.accumulation_volume_threshold = 1.5  # Volume threshold for accumulation
        self.distribution_volume_threshold = 1.8  # Volume threshold for distribution
        self.markup_volume_threshold = 1.2  # Volume threshold for markup
        self.markdown_volume_threshold = 1.3  # Volume threshold for markdown
        
        # Support/Resistance and Spring detection
        self.spring_threshold = 0.05  # 5% below support for spring detection
        self.upthrust_threshold = 0.05  # 5% above resistance for upthrust detection
        
    def analyze_wyckoff_phases(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Perform comprehensive Wyckoff analysis on stock data
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            
        Returns:
            Dictionary with Wyckoff analysis results
        """
        try:
            # Check if DataFrame is empty
            if len(df) == 0:
                return {
                    'symbol': symbol,
                    'error': 'No data available for analysis',
                    'analysis_date': datetime.now().isoformat()
                }
            
            # Ensure data is sorted by date
            df = df.sort_values('date').reset_index(drop=True)
            
            # Calculate technical indicators needed for Wyckoff analysis
            df = self._calculate_wyckoff_indicators(df)
            
            # Analyze Wyckoff phases using authentic methodology
            phases = self._identify_wyckoff_phases(df)
            
            # Calculate price targets using Point-and-Figure methodology
            trading_ranges = self._identify_trading_ranges(df)
            price_targets = self.calculate_wyckoff_price_targets(df, trading_ranges)
            
            # Volume-Price Analysis
            volume_analysis = self._analyze_volume_price_relationships(df)
            
            # Support and Resistance levels
            support_resistance = self._identify_support_resistance(df)
            
            # Current phase assessment
            current_phase = self._assess_current_phase(df, phases)
            
            # Generate trading signals
            signals = self._generate_wyckoff_signals(df, current_phase)
            
            # Calculate Wyckoff score
            wyckoff_score = self._calculate_wyckoff_score(df, phases, volume_analysis)
            
            return {
                'symbol': symbol,
                'analysis_date': datetime.now().isoformat(),
                'current_price': float(df['close'].iloc[-1]) if len(df) > 0 else 0.0,
                'current_phase': current_phase,
                'wyckoff_score': wyckoff_score,
                'phases': phases,
                'price_targets': price_targets,
                'trading_ranges': trading_ranges,
                'volume_analysis': volume_analysis,
                'support_resistance': support_resistance,
                'signals': signals,
                'data_period': {
                    'start_date': df['date'].min().strftime('%Y-%m-%d'),
                    'end_date': df['date'].max().strftime('%Y-%m-%d'),
                    'total_days': len(df)
                },
                'wyckoff_methodology': {
                    'source': 'Official Wyckoff Method from wyckoffanalytics.com',
                    'principles': [
                        'The Composite Man Theory',
                        'Five-Step Approach to Market Analysis',
                        'A-E Phase Identification',
                        'Cause and Effect (Point-and-Figure)',
                        'Volume-Price Relationships'
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Wyckoff phases for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'analysis_date': datetime.now().isoformat()
            }
    
    def _calculate_wyckoff_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators needed for Wyckoff analysis"""
        
        # Convert to float to avoid decimal issues
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Price change and percentage change
        df['price_change'] = df['close'].pct_change()
        df['price_change_abs'] = df['price_change'].abs()
        
        # Volume indicators
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['high_volume'] = df['volume_ratio'] > self.volume_threshold_multiplier
        
        # Moving averages for trend identification
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # Price relative to moving averages
        df['price_vs_sma20'] = (df['close'] / df['sma_20'] - 1) * 100
        df['price_vs_sma50'] = (df['close'] / df['sma_50'] - 1) * 100
        
        # Volatility indicators
        df['atr_14'] = self._calculate_atr(df, 14)
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        
        # Range analysis (High-Low range)
        df['daily_range'] = (df['high'] - df['low']) / df['close']
        df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        return df
    
    def _identify_trading_ranges(self, df: pd.DataFrame) -> List[Dict]:
        """
        Identify trading ranges (consolidation periods) in the data
        
        Trading ranges are periods where price consolidates between support and resistance
        levels, which is where Wyckoff accumulation and distribution phases occur.
        """
        trading_ranges = []
        
        # Look for periods of low volatility and sideways movement
        window_size = 30  # Minimum 30 days for a trading range
        
        for i in range(window_size, len(df) - window_size):
            window_data = df.iloc[i-window_size:i+window_size]
            
            # Check if this is a trading range
            if self._is_trading_range(window_data):
                # Find the full extent of this trading range
                start_idx, end_idx = self._find_trading_range_bounds(df, i)
                
                if end_idx - start_idx >= window_size:
                    trading_ranges.append({
                        'start_idx': start_idx,
                        'end_idx': end_idx,
                        'start_date': df.iloc[start_idx]['date'],
                        'end_date': df.iloc[end_idx]['date'],
                        'support': window_data['low'].min(),
                        'resistance': window_data['high'].max()
                    })
        
        return trading_ranges
    
    def _is_trading_range(self, window_data: pd.DataFrame) -> bool:
        """Determine if a time window represents a trading range"""
        
        # Calculate volatility and price range
        price_range = (window_data['high'].max() - window_data['low'].min()) / window_data['close'].mean()
        volatility = window_data['close'].std() / window_data['close'].mean()
        
        # Trading range criteria:
        # 1. Low volatility (price not trending strongly)
        # 2. Price oscillating between support and resistance
        # 3. Volume patterns consistent with consolidation
        
        is_low_volatility = volatility < 0.15  # Less than 15% volatility
        is_sideways = price_range < 0.25  # Less than 25% total range
        
        return is_low_volatility and is_sideways
    
    def _find_trading_range_bounds(self, df: pd.DataFrame, center_idx: int) -> Tuple[int, int]:
        """Find the start and end bounds of a trading range"""
        
        # Find support and resistance levels
        window_data = df.iloc[center_idx-15:center_idx+15]
        support = window_data['low'].min()
        resistance = window_data['high'].max()
        
        # Expand backwards to find start
        start_idx = center_idx
        for i in range(center_idx - 1, -1, -1):
            if df.iloc[i]['low'] < support * 0.95 or df.iloc[i]['high'] > resistance * 1.05:
                start_idx = i + 1
                break
        
        # Expand forwards to find end
        end_idx = center_idx
        for i in range(center_idx + 1, len(df)):
            if df.iloc[i]['low'] < support * 0.95 or df.iloc[i]['high'] > resistance * 1.05:
                end_idx = i - 1
                break
        
        return start_idx, end_idx
    
    def _analyze_trading_range_phases(self, tr_data: pd.DataFrame, tr_info: Dict) -> List[Dict]:
        """
        Analyze a trading range for Wyckoff A-E phases
        
        Based on the official Wyckoff Method phases:
        - Phase A: Preliminary Support (PS) and Selling Climax (SC)
        - Phase B: Building the Cause (accumulation/distribution)
        - Phase C: The Test (spring or upthrust)
        - Phase D: Markup/Markdown (trend development)
        - Phase E: Climax and Distribution/Accumulation
        """
        phases = []
        
        # Determine if this is accumulation or distribution
        tr_type = self._determine_trading_range_type(tr_data)
        
        if tr_type == 'accumulation':
            phases = self._identify_accumulation_phases(tr_data, tr_info)
        elif tr_type == 'distribution':
            phases = self._identify_distribution_phases(tr_data, tr_info)
        
        return phases
    
    def _determine_trading_range_type(self, tr_data: pd.DataFrame) -> str:
        """Determine if a trading range is accumulation or distribution"""
        
        # Analyze volume and price patterns
        avg_volume = tr_data['volume'].mean()
        high_volume_days = tr_data[tr_data['volume'] > avg_volume * 1.5]
        
        # Look for volume patterns
        if len(high_volume_days) > 0:
            # Check if high volume occurs on down days (accumulation) or up days (distribution)
            down_volume = high_volume_days[high_volume_days['close'] < high_volume_days['open']]
            up_volume = high_volume_days[high_volume_days['close'] > high_volume_days['open']]
            
            if len(down_volume) > len(up_volume):
                return 'accumulation'  # High volume on down days suggests accumulation
            else:
                return 'distribution'  # High volume on up days suggests distribution
        
        # Default to accumulation if unclear
        return 'accumulation'
    
    def _identify_accumulation_phases(self, tr_data: pd.DataFrame, tr_info: Dict) -> List[Dict]:
        """Identify Wyckoff accumulation phases (A-E)"""
        phases = []
        
        # Phase A: Preliminary Support and Selling Climax
        phase_a = self._identify_phase_a_accumulation(tr_data)
        if phase_a:
            phases.append(phase_a)
        
        # Phase B: Building the Cause
        phase_b = self._identify_phase_b_accumulation(tr_data)
        if phase_b:
            phases.append(phase_b)
        
        # Phase C: The Test (Spring)
        phase_c = self._identify_phase_c_accumulation(tr_data)
        if phase_c:
            phases.append(phase_c)
        
        # Phase D: Markup
        phase_d = self._identify_phase_d_accumulation(tr_data)
        if phase_d:
            phases.append(phase_d)
        
        return phases
    
    def _identify_phase_a_accumulation(self, tr_data: pd.DataFrame) -> Dict:
        """Identify Phase A of accumulation: Preliminary Support and Selling Climax"""
        
        # Look for selling climax - high volume with sharp price decline
        high_volume_threshold = tr_data['volume'].quantile(0.8)
        potential_sc = tr_data[
            (tr_data['volume'] > high_volume_threshold) & 
            (tr_data['close'] < tr_data['open'])
        ]
        
        if len(potential_sc) > 0:
            # Get the first row from the filtered DataFrame
            first_sc = potential_sc.iloc[0]
            sc_idx = potential_sc.index[0] - tr_data.index[0]  # Convert to relative index
            
            return {
                'phase': 'Phase A - Selling Climax',
                'start_date': tr_data.iloc[0]['date'].strftime('%Y-%m-%d'),
                'end_date': first_sc['date'].strftime('%Y-%m-%d'),
                'start_price': tr_data.iloc[0]['close'],
                'end_price': first_sc['close'],
                'duration_days': sc_idx + 1,
                'wyckoff_phase': 'A',
                'description': 'Preliminary Support and Selling Climax'
            }
        
        return None
    
    def _identify_phase_b_accumulation(self, tr_data: pd.DataFrame) -> Dict:
        """Identify Phase B of accumulation: Building the Cause"""
        
        # Phase B typically shows decreasing volume and sideways movement
        mid_point = len(tr_data) // 2
        
        return {
            'phase': 'Phase B - Building Cause',
            'start_date': tr_data.iloc[0]['date'].strftime('%Y-%m-%d'),
            'end_date': tr_data.iloc[mid_point]['date'].strftime('%Y-%m-%d'),
            'start_price': tr_data.iloc[0]['close'],
            'end_price': tr_data.iloc[mid_point]['close'],
            'duration_days': mid_point,
            'wyckoff_phase': 'B',
            'description': 'Building the Cause - Accumulation'
        }
    
    def _identify_phase_c_accumulation(self, tr_data: pd.DataFrame) -> Dict:
        """Identify Phase C of accumulation: The Test (Spring)"""
        
        # Look for spring - price breaks below support then recovers
        support_level = tr_data['low'].min()
        spring_threshold = support_level * (1 - self.spring_threshold)
        
        spring_candidates = tr_data[tr_data['low'] <= spring_threshold]
        
        if len(spring_candidates) > 0:
            spring_idx = spring_candidates.index[0]
            return {
                'phase': 'Phase C - Spring Test',
                'start_date': tr_data.iloc[spring_idx]['date'].strftime('%Y-%m-%d'),
                'end_date': tr_data.iloc[spring_idx + 5]['date'].strftime('%Y-%m-%d') if spring_idx + 5 < len(tr_data) else tr_data.iloc[-1]['date'].strftime('%Y-%m-%d'),
                'start_price': tr_data.iloc[spring_idx]['close'],
                'end_price': tr_data.iloc[min(spring_idx + 5, len(tr_data) - 1)]['close'],
                'duration_days': 5,
                'wyckoff_phase': 'C',
                'description': 'The Test - Spring below support'
            }
        
        return None
    
    def _identify_phase_d_accumulation(self, tr_data: pd.DataFrame) -> Dict:
        """Identify Phase D of accumulation: Markup"""
        
        # Phase D shows increasing volume and price breaking above resistance
        resistance_level = tr_data['high'].max()
        
        # Look for breakout above resistance
        breakout_candidates = tr_data[tr_data['close'] > resistance_level * 1.02]
        
        if len(breakout_candidates) > 0:
            breakout_idx = breakout_candidates.index[0]
            return {
                'phase': 'Phase D - Markup',
                'start_date': tr_data.iloc[breakout_idx]['date'].strftime('%Y-%m-%d'),
                'end_date': tr_data.iloc[-1]['date'].strftime('%Y-%m-%d'),
                'start_price': tr_data.iloc[breakout_idx]['close'],
                'end_price': tr_data.iloc[-1]['close'],
                'duration_days': len(tr_data) - breakout_idx,
                'wyckoff_phase': 'D',
                'description': 'Markup - Breakout above resistance'
            }
        
        return None
    
    def _identify_distribution_phases(self, tr_data: pd.DataFrame, tr_info: Dict) -> List[Dict]:
        """Identify Wyckoff distribution phases (A-E)"""
        phases = []
        
        # Similar structure to accumulation but for distribution
        # Phase A: Preliminary Supply and Buying Climax
        # Phase B: Building the Cause (distribution)
        # Phase C: The Test (Upthrust)
        # Phase D: Markdown
        
        return phases
    
    def _identify_trend_phases(self, df: pd.DataFrame, trading_ranges: List[Dict]) -> List[Dict]:
        """Identify trend phases between trading ranges"""
        trend_phases = []
        
        # Analyze periods between trading ranges for markup/markdown phases
        for i in range(len(trading_ranges) - 1):
            start_idx = trading_ranges[i]['end_idx'] + 1
            end_idx = trading_ranges[i + 1]['start_idx'] - 1
            
            if end_idx > start_idx:
                trend_data = df.iloc[start_idx:end_idx+1]
                trend_type = self._determine_trend_type(trend_data)
                
                if trend_type:
                    trend_phases.append({
                        'phase': f'{trend_type} Trend',
                        'start_date': trend_data.iloc[0]['date'].strftime('%Y-%m-%d'),
                        'end_date': trend_data.iloc[-1]['date'].strftime('%Y-%m-%d'),
                        'start_price': trend_data.iloc[0]['close'],
                        'end_price': trend_data.iloc[-1]['close'],
                        'duration_days': len(trend_data),
                        'wyckoff_phase': 'Trend',
                        'description': f'{trend_type} trend between trading ranges'
                    })
        
        return trend_phases
    
    def _determine_trend_type(self, trend_data: pd.DataFrame) -> str:
        """Determine if a trend is markup or markdown"""
        
        price_change = (trend_data.iloc[-1]['close'] - trend_data.iloc[0]['close']) / trend_data.iloc[0]['close']
        
        if price_change > 0.05:  # 5% or more increase
            return 'Markup'
        elif price_change < -0.05:  # 5% or more decrease
            return 'Markdown'
        
        return None
    
    def calculate_wyckoff_price_targets(self, df: pd.DataFrame, trading_ranges: List[Dict]) -> Dict:
        """
        Calculate Wyckoff price targets using Point-and-Figure methodology
        
        Based on the official Wyckoff Method's Cause and Effect principle:
        - The horizontal count in a trading range represents the Cause
        - The subsequent price movement represents the Effect
        """
        price_targets = {}
        
        for tr in trading_ranges:
            tr_data = df.iloc[tr['start_idx']:tr['end_idx']+1]
            
            # Calculate horizontal count (Cause)
            horizontal_count = self._calculate_horizontal_count(tr_data)
            
            if horizontal_count > 0:
                # Calculate price targets (Effect)
                support_level = tr['support']
                resistance_level = tr['resistance']
                
                # Conservative target (minimum)
                conservative_target = support_level + (horizontal_count * 0.01)  # 1% per count unit
                
                # Moderate target (halfway)
                moderate_target = support_level + (horizontal_count * 0.02)  # 2% per count unit
                
                # Aggressive target (maximum)
                aggressive_target = support_level + (horizontal_count * 0.03)  # 3% per count unit
                
                price_targets[f"{tr['start_date'].strftime('%Y-%m-%d')}_to_{tr['end_date'].strftime('%Y-%m-%d')}"] = {
                    'trading_range': {
                        'start_date': tr['start_date'].strftime('%Y-%m-%d'),
                        'end_date': tr['end_date'].strftime('%Y-%m-%d'),
                        'support': support_level,
                        'resistance': resistance_level,
                        'duration_days': tr['end_idx'] - tr['start_idx']
                    },
                    'horizontal_count': horizontal_count,
                    'price_targets': {
                        'conservative': conservative_target,
                        'moderate': moderate_target,
                        'aggressive': aggressive_target
                    },
                    'wyckoff_principle': 'Cause and Effect - Horizontal count represents cause, price movement represents effect'
                }
        
        return price_targets
    
    def _calculate_horizontal_count(self, tr_data: pd.DataFrame) -> int:
        """
        Calculate horizontal count for Point-and-Figure price targets
        
        This represents the "Cause" in Wyckoff's Cause and Effect principle
        """
        # Simplified horizontal count calculation
        # In a full implementation, this would use actual P&F charting
        
        # Count the number of significant price swings within the trading range
        support = tr_data['low'].min()
        resistance = tr_data['high'].max()
        range_size = resistance - support
        
        # Count significant price movements (swings)
        swing_count = 0
        current_trend = None
        
        for i in range(1, len(tr_data)):
            price_change = tr_data.iloc[i]['close'] - tr_data.iloc[i-1]['close']
            
            if abs(price_change) > range_size * 0.05:  # 5% of range size
                if price_change > 0 and current_trend != 'up':
                    swing_count += 1
                    current_trend = 'up'
                elif price_change < 0 and current_trend != 'down':
                    swing_count += 1
                    current_trend = 'down'
        
        return max(swing_count, 1)  # Minimum count of 1
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(window=period).mean()
    
    def _identify_wyckoff_phases(self, df: pd.DataFrame) -> Dict:
        """
        Identify Wyckoff phases using authentic A-E phase methodology
        
        Based on the official Wyckoff Method from wyckoffanalytics.com
        """
        
        phases = {
            'accumulation': [],
            'distribution': [],
            'markup': [],
            'markdown': []
        }
        
        # Use the new authentic Wyckoff phase detection
        all_phases = self._detect_phases_chronologically(df)
        
        # Categorize phases based on authentic Wyckoff terminology
        for phase_data in all_phases:
            phase_name = phase_data.get('phase', '')
            wyckoff_phase = phase_data.get('wyckoff_phase', '')
            
            # Map to our phase categories
            if 'Phase A' in phase_name or 'Phase B' in phase_name or 'Phase C' in phase_name:
                if 'Selling Climax' in phase_name or 'Building Cause' in phase_name or 'Spring' in phase_name:
                    phases['accumulation'].append(phase_data)
                else:
                    phases['distribution'].append(phase_data)
            elif 'Phase D' in phase_name or 'Markup' in phase_name:
                phases['markup'].append(phase_data)
            elif 'Markdown' in phase_name:
                phases['markdown'].append(phase_data)
            elif 'Trend' in phase_name:
                if 'Markup' in phase_name:
                    phases['markup'].append(phase_data)
                elif 'Markdown' in phase_name:
                    phases['markdown'].append(phase_data)
            # Note: No "transitional" phases in authentic Wyckoff Method
        
        return phases
    
    def _detect_phases_chronologically(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect Wyckoff phases using authentic methodology
        
        Based on the official Wyckoff Method principles:
        1. Identify trading ranges (consolidation periods)
        2. Analyze each trading range for A-E phases
        3. Identify trend phases between trading ranges
        """
        phases = []
        
        # Ensure data is sorted chronologically (oldest first)
        df = df.sort_values('date').reset_index(drop=True)
        
        # Step 1: Identify trading ranges
        trading_ranges = self._identify_trading_ranges(df)
        
        # Step 2: Analyze each trading range for Wyckoff phases
        for tr in trading_ranges:
            tr_data = df.iloc[tr['start_idx']:tr['end_idx']+1]
            wyckoff_phases = self._analyze_trading_range_phases(tr_data, tr)
            phases.extend(wyckoff_phases)
        
        # Step 3: Identify trend phases between trading ranges
        trend_phases = self._identify_trend_phases(df, trading_ranges)
        phases.extend(trend_phases)
        
        # Step 4: Sort phases by date
        phases.sort(key=lambda x: x['start_date'])
        
        return phases
    
    def _analyze_window_for_phase(self, window_data: pd.DataFrame, full_df: pd.DataFrame, current_idx: int) -> Dict:
        """Analyze a time window to determine its Wyckoff phase"""
        
        # Calculate key metrics
        start_price = window_data['close'].iloc[0]
        end_price = window_data['close'].iloc[-1]
        price_change_pct = (end_price - start_price) / start_price
        
        # Price range analysis
        high_price = window_data['high'].max()
        low_price = window_data['low'].min()
        price_range_pct = (high_price - low_price) / start_price
        
        # Volume analysis
        avg_volume = window_data['volume'].mean()
        volume_sma_20 = full_df['volume'].rolling(window=20).mean().iloc[current_idx]
        volume_ratio = avg_volume / volume_sma_20 if volume_sma_20 > 0 else 1.0
        
        # Volume trend (comparing first half vs second half)
        mid_point = len(window_data) // 2
        first_half_volume = window_data['volume'].iloc[:mid_point].mean()
        second_half_volume = window_data['volume'].iloc[mid_point:].mean()
        volume_trend = second_half_volume / first_half_volume if first_half_volume > 0 else 1.0
        
        # Moving average analysis
        sma_20 = window_data['close'].rolling(window=min(20, len(window_data))).mean().iloc[-1]
        price_vs_sma = (end_price - sma_20) / sma_20 if sma_20 > 0 else 0
        
        # Determine phase based on improved criteria
        phase = self._classify_phase(price_change_pct, price_range_pct, volume_ratio, volume_trend, price_vs_sma)
        
        if phase:
            return {
                'phase': phase,
                'start_date': window_data['date'].iloc[0].strftime('%Y-%m-%d'),
                'end_date': window_data['date'].iloc[-1].strftime('%Y-%m-%d'),
                'duration_days': len(window_data),
                'price_change_pct': round(price_change_pct * 100, 2),
                'price_range_pct': round(price_range_pct * 100, 2),
                'volume_ratio': round(volume_ratio, 2),
                'volume_trend': round(volume_trend, 2),
                'price_vs_sma': round(price_vs_sma * 100, 2),
                'start_price': round(start_price, 2),
                'end_price': round(end_price, 2)
            }
        
        return None
    
    def _classify_phase(self, price_change_pct: float, price_range_pct: float, 
                       volume_ratio: float, volume_trend: float, price_vs_sma: float) -> str:
        """Classify phase based on price and volume characteristics"""
        
        # Markup: Strong uptrend with volume confirmation
        if (price_change_pct > 0.08 and  # >8% gain
            price_vs_sma > 0.02 and      # Price above SMA
            volume_ratio > 1.1):         # Above average volume
            return 'markup'
        
        # Markdown: Strong downtrend
        if (price_change_pct < -0.08 and  # >8% decline
            price_vs_sma < -0.02):        # Price below SMA
            return 'markdown'
        
        # Accumulation: Sideways movement with volume accumulation
        if (abs(price_change_pct) < 0.05 and  # <5% net change
            price_range_pct < 0.15 and        # <15% range
            volume_ratio > 1.0 and            # Above average volume
            volume_trend > 1.05):             # Volume increasing
            return 'accumulation'
        
        # Distribution: Sideways movement with volume distribution
        if (abs(price_change_pct) < 0.05 and  # <5% net change
            price_range_pct < 0.15 and        # <15% range
            volume_ratio > 1.0 and            # Above average volume
            volume_trend < 0.95):             # Volume decreasing
            return 'distribution'
        
        # Weak uptrend (could be early markup)
        if (price_change_pct > 0.03 and   # >3% gain
            price_vs_sma > 0.01):         # Price above SMA
            return 'markup'
        
        # Weak downtrend (could be early markdown)
        if (price_change_pct < -0.03 and  # >3% decline
            price_vs_sma < -0.01):        # Price below SMA
            return 'markdown'
        
        return None  # No clear phase
    
    def _merge_overlapping_phases(self, phases: List[Dict]) -> List[Dict]:
        """Merge overlapping phases of the same type"""
        if not phases:
            return []
        
        # Sort by start date
        phases.sort(key=lambda x: x['start_date'])
        
        merged = []
        current_phase = phases[0]
        
        for next_phase in phases[1:]:
            # Check if phases overlap and are the same type
            if (self._phases_overlap(current_phase, next_phase) and 
                current_phase['phase'] == next_phase['phase']):
                # Merge phases
                current_phase = self._merge_two_phases(current_phase, next_phase)
            else:
                # No overlap or different type, add current and move to next
                merged.append(current_phase)
                current_phase = next_phase
        
        # Add the last phase
        merged.append(current_phase)
        
        return merged
    
    def _phases_overlap(self, phase1: Dict, phase2: Dict) -> bool:
        """Check if two phases overlap in time"""
        return (phase1['end_date'] >= phase2['start_date'] and 
                phase2['end_date'] >= phase1['start_date'])
    
    def _merge_two_phases(self, phase1: Dict, phase2: Dict) -> Dict:
        """Merge two overlapping phases of the same type"""
        return {
            'phase': phase1['phase'],
            'start_date': min(phase1['start_date'], phase2['start_date']),
            'end_date': max(phase1['end_date'], phase2['end_date']),
            'duration_days': phase1['duration_days'] + phase2['duration_days'],
            'price_change_pct': round((phase1['price_change_pct'] + phase2['price_change_pct']) / 2, 2),
            'price_range_pct': round(max(phase1['price_range_pct'], phase2['price_range_pct']), 2),
            'volume_ratio': round((phase1['volume_ratio'] + phase2['volume_ratio']) / 2, 2),
            'volume_trend': round((phase1['volume_trend'] + phase2['volume_trend']) / 2, 2),
            'price_vs_sma': round((phase1['price_vs_sma'] + phase2['price_vs_sma']) / 2, 2),
            'start_price': phase1['start_price'],
            'end_price': phase2['end_price']
        }
    
    def _find_accumulation_periods(self, df: pd.DataFrame) -> List[Dict]:
        """Find accumulation periods (sideways movement with increasing volume)"""
        periods = []
        
        # Look for sideways movement (low volatility, price range)
        sideways_threshold = 0.05  # 5% price range
        
        for i in range(20, len(df) - 10):
            # Check 20-day period for sideways movement
            period_data = df.iloc[i-20:i]
            
            price_range = (period_data['high'].max() - period_data['low'].min()) / period_data['close'].mean()
            volume_trend = period_data['volume'].rolling(window=10).mean().iloc[-1] / period_data['volume'].rolling(window=10).mean().iloc[0]
            
            # Accumulation criteria: sideways movement + increasing volume
            if (price_range < sideways_threshold and 
                volume_trend > 1.1 and  # Volume increasing
                period_data['volume'].mean() > df['volume_sma_20'].iloc[i]):
                
                periods.append({
                    'start_date': period_data['date'].iloc[0].strftime('%Y-%m-%d'),
                    'end_date': period_data['date'].iloc[-1].strftime('%Y-%m-%d'),
                    'duration_days': 20,
                    'price_range_pct': round(price_range * 100, 2),
                    'volume_trend': round(volume_trend, 2),
                    'avg_volume_ratio': round(period_data['volume'].mean() / df['volume_sma_20'].iloc[i], 2)
                })
        
        return periods
    
    def _find_distribution_periods(self, df: pd.DataFrame) -> List[Dict]:
        """Find distribution periods (sideways movement with decreasing volume)"""
        periods = []
        
        sideways_threshold = 0.05  # 5% price range
        
        for i in range(20, len(df) - 10):
            period_data = df.iloc[i-20:i]
            
            price_range = (period_data['high'].max() - period_data['low'].min()) / period_data['close'].mean()
            volume_trend = period_data['volume'].rolling(window=10).mean().iloc[-1] / period_data['volume'].rolling(window=10).mean().iloc[0]
            
            # Distribution criteria: sideways movement + decreasing volume
            if (price_range < sideways_threshold and 
                volume_trend < 0.9 and  # Volume decreasing
                period_data['volume'].mean() < df['volume_sma_20'].iloc[i]):
                
                periods.append({
                    'start_date': period_data['date'].iloc[0].strftime('%Y-%m-%d'),
                    'end_date': period_data['date'].iloc[-1].strftime('%Y-%m-%d'),
                    'duration_days': 20,
                    'price_range_pct': round(price_range * 100, 2),
                    'volume_trend': round(volume_trend, 2),
                    'avg_volume_ratio': round(period_data['volume'].mean() / df['volume_sma_20'].iloc[i], 2)
                })
        
        return periods
    
    def _find_markup_periods(self, df: pd.DataFrame) -> List[Dict]:
        """Find markup periods (uptrend with volume confirmation)"""
        periods = []
        
        for i in range(30, len(df) - 10):
            period_data = df.iloc[i-30:i]
            
            # Check for uptrend
            price_change = (period_data['close'].iloc[-1] - period_data['close'].iloc[0]) / period_data['close'].iloc[0]
            volume_confirmation = period_data['high_volume'].sum() > 5  # At least 5 high volume days
            
            # Markup criteria: significant uptrend + volume confirmation
            if (price_change > 0.15 and  # At least 15% gain
                volume_confirmation and
                period_data['close'].iloc[-1] > period_data['sma_20'].iloc[-1]):
                
                periods.append({
                    'start_date': period_data['date'].iloc[0].strftime('%Y-%m-%d'),
                    'end_date': period_data['date'].iloc[-1].strftime('%Y-%m-%d'),
                    'duration_days': 30,
                    'price_change_pct': round(price_change * 100, 2),
                    'high_volume_days': period_data['high_volume'].sum(),
                    'trend_strength': round((period_data['close'].iloc[-1] / period_data['sma_20'].iloc[-1] - 1) * 100, 2)
                })
        
        return periods
    
    def _find_markdown_periods(self, df: pd.DataFrame) -> List[Dict]:
        """Find markdown periods (downtrend)"""
        periods = []
        
        for i in range(30, len(df) - 10):
            period_data = df.iloc[i-30:i]
            
            # Check for downtrend
            price_change = (period_data['close'].iloc[-1] - period_data['close'].iloc[0]) / period_data['close'].iloc[0]
            
            # Markdown criteria: significant downtrend
            if (price_change < -0.15 and  # At least 15% decline
                period_data['close'].iloc[-1] < period_data['sma_20'].iloc[-1]):
                
                periods.append({
                    'start_date': period_data['date'].iloc[0].strftime('%Y-%m-%d'),
                    'end_date': period_data['date'].iloc[-1].strftime('%Y-%m-%d'),
                    'duration_days': 30,
                    'price_change_pct': round(price_change * 100, 2),
                    'trend_strength': round((period_data['close'].iloc[-1] / period_data['sma_20'].iloc[-1] - 1) * 100, 2)
                })
        
        return periods
    
    def _analyze_volume_price_relationships(self, df: pd.DataFrame) -> Dict:
        """Analyze volume-price relationships for Wyckoff analysis"""
        
        recent_data = df.tail(20)  # Last 20 days
        
        # Volume trends
        volume_trend = recent_data['volume_ratio'].mean()
        high_volume_days = recent_data['high_volume'].sum()
        
        # Price-volume correlation
        price_volume_corr = recent_data['price_change'].corr(recent_data['volume_ratio'])
        
        # Volume at key price levels
        volume_at_highs = recent_data[recent_data['close'] > recent_data['close'].rolling(5).max().shift(1)]['volume_ratio'].mean()
        volume_at_lows = recent_data[recent_data['close'] < recent_data['close'].rolling(5).min().shift(1)]['volume_ratio'].mean()
        
        return {
            'volume_trend': round(volume_trend, 2),
            'high_volume_days': int(high_volume_days),
            'price_volume_correlation': round(price_volume_corr, 3),
            'volume_at_highs': round(volume_at_highs if not np.isnan(volume_at_highs) else 0, 2),
            'volume_at_lows': round(volume_at_lows if not np.isnan(volume_at_lows) else 0, 2),
            'volume_analysis': self._interpret_volume_analysis(volume_trend, price_volume_corr)
        }
    
    def _interpret_volume_analysis(self, volume_trend: float, price_volume_corr: float) -> str:
        """Interpret volume analysis results"""
        if volume_trend > 1.2 and price_volume_corr > 0.3:
            return "Strong bullish volume confirmation"
        elif volume_trend > 1.2 and price_volume_corr < -0.3:
            return "High volume but price weakness - potential reversal"
        elif volume_trend < 0.8 and price_volume_corr < -0.3:
            return "Low volume downtrend - potential exhaustion"
        elif volume_trend < 0.8 and price_volume_corr > 0.3:
            return "Low volume uptrend - weak trend"
        else:
            return "Neutral volume-price relationship"
    
    def _identify_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Identify key support and resistance levels"""
        
        # Look for pivot highs and lows
        pivot_highs = []
        pivot_lows = []
        
        for i in range(5, len(df) - 5):
            # Pivot high: high point with lower highs on both sides
            if (df['high'].iloc[i] > df['high'].iloc[i-5:i].max() and 
                df['high'].iloc[i] > df['high'].iloc[i+1:i+6].max()):
                pivot_highs.append({
                    'date': df['date'].iloc[i].strftime('%Y-%m-%d'),
                    'price': float(df['high'].iloc[i]),
                    'volume': float(df['volume'].iloc[i])
                })
            
            # Pivot low: low point with higher lows on both sides
            if (df['low'].iloc[i] < df['low'].iloc[i-5:i].min() and 
                df['low'].iloc[i] < df['low'].iloc[i+1:i+6].min()):
                pivot_lows.append({
                    'date': df['date'].iloc[i].strftime('%Y-%m-%d'),
                    'price': float(df['low'].iloc[i]),
                    'volume': float(df['volume'].iloc[i])
                })
        
        # Get recent levels (last 60 days)
        recent_highs = [h for h in pivot_highs if h['price'] >= df['close'].iloc[-1] * 0.9]
        recent_lows = [l for l in pivot_lows if l['price'] <= df['close'].iloc[-1] * 1.1]
        
        return {
            'resistance_levels': sorted(recent_highs[-3:], key=lambda x: x['price']),
            'support_levels': sorted(recent_lows[-3:], key=lambda x: x['price'], reverse=True),
            'current_price': float(df['close'].iloc[-1]),
            'distance_to_nearest_resistance': self._calculate_distance_to_level(df['close'].iloc[-1], recent_highs),
            'distance_to_nearest_support': self._calculate_distance_to_level(df['close'].iloc[-1], recent_lows)
        }
    
    def _calculate_distance_to_level(self, current_price: float, levels: List[Dict]) -> float:
        """Calculate percentage distance to nearest level"""
        if not levels:
            return 0
        
        nearest_level = min(levels, key=lambda x: abs(x['price'] - current_price))
        return round((nearest_level['price'] - current_price) / current_price * 100, 2)
    
    def _assess_current_phase(self, df: pd.DataFrame, phases: Dict) -> Dict:
        """Assess the current Wyckoff phase using improved logic"""
        
        # Ensure data is sorted chronologically
        df = df.sort_values('date').reset_index(drop=True)
        
        # Use last 20 days for current phase assessment
        recent_data = df.tail(20)
        current_price = df['close'].iloc[-1]
        
        # Calculate metrics using the same logic as phase detection
        start_price = recent_data['close'].iloc[0]
        end_price = recent_data['close'].iloc[-1]
        price_change_pct = (end_price - start_price) / start_price
        
        # Price range analysis
        high_price = recent_data['high'].max()
        low_price = recent_data['low'].min()
        price_range_pct = (high_price - low_price) / start_price
        
        # Volume analysis
        avg_volume = recent_data['volume'].mean()
        volume_sma_20 = df['volume'].rolling(window=20).mean().iloc[-1]
        volume_ratio = avg_volume / volume_sma_20 if volume_sma_20 > 0 else 1.0
        
        # Volume trend
        mid_point = len(recent_data) // 2
        first_half_volume = recent_data['volume'].iloc[:mid_point].mean()
        second_half_volume = recent_data['volume'].iloc[mid_point:].mean()
        volume_trend = second_half_volume / first_half_volume if first_half_volume > 0 else 1.0
        
        # Moving average analysis
        sma_20 = recent_data['close'].rolling(window=min(20, len(recent_data))).mean().iloc[-1]
        price_vs_sma = (end_price - sma_20) / sma_20 if sma_20 > 0 else 0
        
        # Use the same classification logic
        phase = self._classify_phase(price_change_pct, price_range_pct, volume_ratio, volume_trend, price_vs_sma)
        
        if not phase:
            # If no clear phase detected, don't assign any phase - let the authentic 4-phase system handle it
            return None
        else:
            # Calculate confidence based on how well the criteria are met
            confidence = self._calculate_phase_confidence(price_change_pct, price_range_pct, volume_ratio, volume_trend, price_vs_sma, phase)
        
        return {
            'phase': phase.title(),
            'confidence': confidence,
            'price_trend_pct': round(price_change_pct * 100, 2),
            'volume_trend': round(volume_ratio, 2),
            'volatility': round(price_range_pct * 100, 2),
            'assessment_reason': self._get_phase_assessment_reason(phase.title(), price_change_pct, volume_ratio, price_range_pct)
        }
    
    def _calculate_phase_confidence(self, price_change_pct: float, price_range_pct: float, 
                                   volume_ratio: float, volume_trend: float, price_vs_sma: float, phase: str) -> float:
        """Calculate confidence level for phase classification"""
        confidence = 0.5  # Base confidence
        
        if phase == 'markup':
            # Higher confidence for stronger uptrends
            if price_change_pct > 0.15:
                confidence += 0.3
            elif price_change_pct > 0.08:
                confidence += 0.2
            else:
                confidence += 0.1
            
            # Volume confirmation bonus
            if volume_ratio > 1.2:
                confidence += 0.1
            elif volume_ratio > 1.0:
                confidence += 0.05
        
        elif phase == 'markdown':
            # Higher confidence for stronger downtrends
            if price_change_pct < -0.15:
                confidence += 0.3
            elif price_change_pct < -0.08:
                confidence += 0.2
            else:
                confidence += 0.1
        
        elif phase == 'accumulation':
            # Higher confidence for clearer sideways movement
            if abs(price_change_pct) < 0.02:
                confidence += 0.2
            elif abs(price_change_pct) < 0.05:
                confidence += 0.1
            
            # Volume trend bonus
            if volume_trend > 1.1:
                confidence += 0.1
        
        elif phase == 'distribution':
            # Higher confidence for clearer sideways movement
            if abs(price_change_pct) < 0.02:
                confidence += 0.2
            elif abs(price_change_pct) < 0.05:
                confidence += 0.1
            
            # Volume trend bonus
            if volume_trend < 0.9:
                confidence += 0.1
        
        return min(0.95, max(0.3, confidence))  # Clamp between 0.3 and 0.95
    
    def _get_phase_assessment_reason(self, phase: str, price_trend: float, volume_trend: float, volatility: float) -> str:
        """Get reason for phase assessment"""
        if phase == "Accumulation":
            return f"Sideways price action ({price_trend*100:.1f}%) with high volume ({volume_trend:.1f}x avg)"
        elif phase == "Distribution":
            return f"Sideways price action ({price_trend*100:.1f}%) with low volume ({volume_trend:.1f}x avg)"
        elif phase == "Markup":
            return f"Strong uptrend ({price_trend*100:.1f}%) with volume confirmation ({volume_trend:.1f}x avg)"
        elif phase == "Markdown":
            return f"Downtrend ({price_trend*100:.1f}%) with {volatility*100:.1f}% volatility"
        else:
            return f"Mixed signals: {price_trend*100:.1f}% price change, {volume_trend:.1f}x volume, {volatility*100:.1f}% volatility"
    
    def _generate_wyckoff_signals(self, df: pd.DataFrame, current_phase: Dict) -> Dict:
        """Generate trading signals based on Wyckoff analysis"""
        
        current_price = df['close'].iloc[-1]
        recent_volume = df['volume_ratio'].tail(5).mean()
        
        signals = {
            'primary_signal': 'HOLD',
            'confidence': current_phase['confidence'],
            'entry_signal': False,
            'exit_signal': False,
            'stop_loss': None,
            'take_profit': None,
            'reasoning': []
        }
        
        phase = current_phase['phase']
        
        if phase == "Accumulation":
            if recent_volume > 1.5:
                signals['primary_signal'] = 'BUY'
                signals['entry_signal'] = True
                signals['reasoning'].append("High volume at accumulation suggests institutional buying")
        elif phase == "Distribution":
            if recent_volume > 1.5:
                signals['primary_signal'] = 'SELL'
                signals['exit_signal'] = True
                signals['reasoning'].append("High volume at distribution suggests institutional selling")
        elif phase == "Markup":
            signals['primary_signal'] = 'BUY'
            signals['reasoning'].append("Strong uptrend with volume confirmation")
        elif phase == "Markdown":
            signals['primary_signal'] = 'SELL'
            signals['reasoning'].append("Downtrend phase - avoid long positions")
        
        # Calculate stop loss and take profit levels
        if signals['entry_signal'] or signals['exit_signal']:
            atr = df['atr_14'].iloc[-1]
            signals['stop_loss'] = round(current_price - (2 * atr), 2)
            signals['take_profit'] = round(current_price + (3 * atr), 2)
        
        return signals
    
    def _calculate_wyckoff_score(self, df: pd.DataFrame, phases: Dict, volume_analysis: Dict) -> Dict:
        """Calculate overall Wyckoff analysis score"""
        
        score = 0
        max_score = 100
        
        # Volume analysis score (30 points)
        volume_score = min(30, volume_analysis['high_volume_days'] * 5)
        score += volume_score
        
        # Phase identification score (40 points)
        total_phases = sum(len(phase_list) for phase_list in phases.values())
        phase_score = min(40, total_phases * 8)
        score += phase_score
        
        # Price-volume correlation score (20 points)
        correlation_score = abs(volume_analysis['price_volume_correlation']) * 20
        score += correlation_score
        
        # Recent performance score (10 points)
        if len(df) >= 20:
            recent_return = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]
            performance_score = max(0, min(10, (recent_return + 0.2) * 25))  # Bonus for positive returns
            score += performance_score
        else:
            # Use available data if less than 20 rows
            recent_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
            performance_score = max(0, min(10, (recent_return + 0.2) * 25))
            score += performance_score
        
        # Calculate grade
        if score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 50:
            grade = "D"
        else:
            grade = "F"
        
        return {
            'total_score': round(score, 1),
            'max_score': max_score,
            'grade': grade,
            'breakdown': {
                'volume_analysis': round(volume_score, 1),
                'phase_identification': round(phase_score, 1),
                'price_volume_correlation': round(correlation_score, 1),
                'recent_performance': round(performance_score, 1)
            }
        }
    
    def generate_wyckoff_report(self, analysis_results: List[Dict]) -> Dict:
        """Generate comprehensive Wyckoff report for multiple stocks"""
        
        if not analysis_results:
            return {'error': 'No analysis results provided'}
        
        # Summary statistics
        total_stocks = len(analysis_results)
        successful_analyses = len([r for r in analysis_results if 'error' not in r])
        
        # Phase distribution
        phase_distribution = {}
        grade_distribution = {}
        buy_signals = 0
        sell_signals = 0
        
        for result in analysis_results:
            if 'error' in result:
                continue
                
            phase = result['current_phase']['phase']
            grade = result['wyckoff_score']['grade']
            
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
            
            if result['signals']['primary_signal'] == 'BUY':
                buy_signals += 1
            elif result['signals']['primary_signal'] == 'SELL':
                sell_signals += 1
        
        # Top performers
        successful_results = [r for r in analysis_results if 'error' not in r]
        top_performers = sorted(successful_results, key=lambda x: x['wyckoff_score']['total_score'], reverse=True)[:5]
        
        # Best opportunities (high score + buy signal)
        best_opportunities = [
            r for r in successful_results 
            if r['signals']['primary_signal'] == 'BUY' and r['wyckoff_score']['total_score'] > 70
        ]
        best_opportunities = sorted(best_opportunities, key=lambda x: x['wyckoff_score']['total_score'], reverse=True)
        
        return {
            'report_date': datetime.now().isoformat(),
            'summary': {
                'total_stocks_analyzed': total_stocks,
                'successful_analyses': successful_analyses,
                'failed_analyses': total_stocks - successful_analyses,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'hold_signals': successful_analyses - buy_signals - sell_signals
            },
            'phase_distribution': phase_distribution,
            'grade_distribution': grade_distribution,
            'top_performers': [
                {
                    'symbol': r['symbol'],
                    'score': r['wyckoff_score']['total_score'],
                    'grade': r['wyckoff_score']['grade'],
                    'current_phase': r['current_phase']['phase'],
                    'signal': r['signals']['primary_signal']
                }
                for r in top_performers
            ],
            'best_opportunities': [
                {
                    'symbol': r['symbol'],
                    'score': r['wyckoff_score']['total_score'],
                    'current_price': r['current_price'],
                    'current_phase': r['current_phase']['phase'],
                    'confidence': r['current_phase']['confidence'],
                    'reasoning': r['signals']['reasoning']
                }
                for r in best_opportunities
            ],
            'detailed_analysis': analysis_results
        }


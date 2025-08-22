"""Chart pattern recognition module."""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from scipy.signal import argrelextrema
import logging

logger = logging.getLogger(__name__)


class PatternRecognizer:
    """Recognize various chart patterns in price data."""
    
    def __init__(self, data: pd.DataFrame):
        """Initialize with OHLCV data.
        
        Args:
            data: DataFrame with columns Open, High, Low, Close, Volume
        """
        self.data = data
        self.patterns_found = []
        
    def find_peaks_troughs(
        self, 
        price_series: pd.Series, 
        order: int = 5
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Find local peaks and troughs in price series."""
        peaks = argrelextrema(price_series.values, np.greater, order=order)[0]
        troughs = argrelextrema(price_series.values, np.less, order=order)[0]
        return peaks, troughs
    
    def detect_ma_crossover(
        self, 
        fast_period: int = 20, 
        slow_period: int = 50
    ) -> List[Dict[str, Any]]:
        """Detect moving average crossovers."""
        signals = []
        
        # Calculate MAs
        ma_fast = self.data['Close'].rolling(window=fast_period).mean()
        ma_slow = self.data['Close'].rolling(window=slow_period).mean()
        
        # Find crossovers
        crossover = np.where(
            (ma_fast.shift(1) <= ma_slow.shift(1)) & 
            (ma_fast > ma_slow)
        )[0]
        
        crossunder = np.where(
            (ma_fast.shift(1) >= ma_slow.shift(1)) & 
            (ma_fast < ma_slow)
        )[0]
        
        # Create signals
        for idx in crossover:
            if idx < len(self.data):
                signals.append({
                    'type': 'MA_CROSSOVER_BUY',
                    'date': self.data.index[idx],
                    'price': self.data['Close'].iloc[idx],
                    'confidence': 0.7,
                    'details': f'MA{fast_period} crossed above MA{slow_period}'
                })
                
        for idx in crossunder:
            if idx < len(self.data):
                signals.append({
                    'type': 'MA_CROSSOVER_SELL',
                    'date': self.data.index[idx],
                    'price': self.data['Close'].iloc[idx],
                    'confidence': 0.7,
                    'details': f'MA{fast_period} crossed below MA{slow_period}'
                })
                
        return signals
    
    def detect_rsi_divergence(self, rsi_period: int = 14) -> List[Dict[str, Any]]:
        """Detect RSI divergences."""
        from .indicators import TechnicalIndicators
        
        signals = []
        rsi = TechnicalIndicators.rsi(self.data['Close'], period=rsi_period)
        
        # Find peaks and troughs
        price_peaks, price_troughs = self.find_peaks_troughs(self.data['Close'])
        rsi_peaks, rsi_troughs = self.find_peaks_troughs(rsi)
        
        # Bullish divergence: price makes lower low, RSI makes higher low
        for i in range(1, len(price_troughs)):
            if price_troughs[i] < len(self.data) - 1:
                # Find corresponding RSI trough
                rsi_trough_idx = np.where(
                    (rsi_troughs >= price_troughs[i-1]) & 
                    (rsi_troughs <= price_troughs[i])
                )[0]
                
                if len(rsi_trough_idx) >= 2:
                    price_ll = (self.data['Low'].iloc[price_troughs[i]] < 
                               self.data['Low'].iloc[price_troughs[i-1]])
                    rsi_hl = (rsi.iloc[rsi_troughs[rsi_trough_idx[-1]]] > 
                             rsi.iloc[rsi_troughs[rsi_trough_idx[0]]])
                    
                    if price_ll and rsi_hl:
                        signals.append({
                            'type': 'RSI_BULLISH_DIVERGENCE',
                            'date': self.data.index[price_troughs[i]],
                            'price': self.data['Close'].iloc[price_troughs[i]],
                            'confidence': 0.8,
                            'details': 'Bullish RSI divergence detected'
                        })
        
        # Bearish divergence: price makes higher high, RSI makes lower high
        for i in range(1, len(price_peaks)):
            if price_peaks[i] < len(self.data) - 1:
                # Find corresponding RSI peak
                rsi_peak_idx = np.where(
                    (rsi_peaks >= price_peaks[i-1]) & 
                    (rsi_peaks <= price_peaks[i])
                )[0]
                
                if len(rsi_peak_idx) >= 2:
                    price_hh = (self.data['High'].iloc[price_peaks[i]] > 
                               self.data['High'].iloc[price_peaks[i-1]])
                    rsi_lh = (rsi.iloc[rsi_peaks[rsi_peak_idx[-1]]] < 
                             rsi.iloc[rsi_peaks[rsi_peak_idx[0]]])
                    
                    if price_hh and rsi_lh:
                        signals.append({
                            'type': 'RSI_BEARISH_DIVERGENCE',
                            'date': self.data.index[price_peaks[i]],
                            'price': self.data['Close'].iloc[price_peaks[i]],
                            'confidence': 0.8,
                            'details': 'Bearish RSI divergence detected'
                        })
        
        return signals
    
    def detect_support_resistance_breakout(
        self, 
        lookback: int = 50,
        threshold: float = 0.02
    ) -> List[Dict[str, Any]]:
        """Detect support/resistance breakouts."""
        from .indicators import TechnicalIndicators
        
        signals = []
        
        # Get support/resistance levels
        levels = TechnicalIndicators.support_resistance_levels(
            self.data.iloc[-lookback:], 
            window=20
        )
        
        current_price = self.data['Close'].iloc[-1]
        prev_price = self.data['Close'].iloc[-2]
        
        # Check resistance breakout
        for resistance in levels['resistance']:
            if prev_price < resistance * (1 - threshold) and current_price > resistance:
                signals.append({
                    'type': 'RESISTANCE_BREAKOUT',
                    'date': self.data.index[-1],
                    'price': current_price,
                    'confidence': 0.75,
                    'details': f'Broke above resistance at {resistance:.2f}'
                })
        
        # Check support breakdown
        for support in levels['support']:
            if prev_price > support * (1 + threshold) and current_price < support:
                signals.append({
                    'type': 'SUPPORT_BREAKDOWN',
                    'date': self.data.index[-1],
                    'price': current_price,
                    'confidence': 0.75,
                    'details': f'Broke below support at {support:.2f}'
                })
        
        return signals
    
    def detect_candlestick_patterns(self) -> List[Dict[str, Any]]:
        """Detect candlestick patterns (hammer, shooting star, engulfing)."""
        signals = []
        
        for i in range(2, len(self.data)):
            o, h, l, c = (self.data['Open'].iloc[i], 
                         self.data['High'].iloc[i],
                         self.data['Low'].iloc[i], 
                         self.data['Close'].iloc[i])
            
            prev_o, prev_c = (self.data['Open'].iloc[i-1], 
                             self.data['Close'].iloc[i-1])
            
            body = abs(c - o)
            full_range = h - l
            
            if full_range == 0:
                continue
                
            # Hammer pattern
            if (c > o and  # Bullish
                (o - l) > 2 * body and  # Long lower shadow
                (h - c) < 0.1 * body):  # Small upper shadow
                signals.append({
                    'type': 'HAMMER_BULLISH',
                    'date': self.data.index[i],
                    'price': c,
                    'confidence': 0.65,
                    'details': 'Bullish hammer pattern'
                })
            
            # Shooting star pattern  
            elif (c < o and  # Bearish
                  (h - o) > 2 * body and  # Long upper shadow
                  (c - l) < 0.1 * body):  # Small lower shadow
                signals.append({
                    'type': 'SHOOTING_STAR_BEARISH',
                    'date': self.data.index[i],
                    'price': c,
                    'confidence': 0.65,
                    'details': 'Bearish shooting star pattern'
                })
            
            # Bullish engulfing
            if (prev_c < prev_o and  # Previous bearish
                c > o and  # Current bullish
                o < prev_c and  # Opens below previous close
                c > prev_o):  # Closes above previous open
                signals.append({
                    'type': 'BULLISH_ENGULFING',
                    'date': self.data.index[i],
                    'price': c,
                    'confidence': 0.7,
                    'details': 'Bullish engulfing pattern'
                })
            
            # Bearish engulfing
            elif (prev_c > prev_o and  # Previous bullish
                  c < o and  # Current bearish
                  o > prev_c and  # Opens above previous close
                  c < prev_o):  # Closes below previous open
                signals.append({
                    'type': 'BEARISH_ENGULFING',
                    'date': self.data.index[i],
                    'price': c,
                    'confidence': 0.7,
                    'details': 'Bearish engulfing pattern'
                })
        
        return signals
    
    def analyze_all_patterns(self) -> List[Dict[str, Any]]:
        """Run all pattern detection methods and return combined signals."""
        all_signals = []
        
        # MA Crossover
        all_signals.extend(self.detect_ma_crossover())
        
        # RSI Divergence
        all_signals.extend(self.detect_rsi_divergence())
        
        # Support/Resistance Breakout
        all_signals.extend(self.detect_support_resistance_breakout())
        
        # Candlestick Patterns
        all_signals.extend(self.detect_candlestick_patterns())
        
        # Sort by date
        all_signals.sort(key=lambda x: x['date'], reverse=True)
        
        return all_signals
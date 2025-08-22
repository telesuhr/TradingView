"""Strategy runner for backtesting different trading strategies."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..analysis import TechnicalIndicators, PatternRecognizer
from .engine import BacktestEngine

logger = logging.getLogger(__name__)


class StrategyRunner:
    """Run backtests for different trading strategies."""
    
    def __init__(self, data: pd.DataFrame):
        """Initialize strategy runner.
        
        Args:
            data: OHLCV DataFrame with Date index
        """
        self.data = data
        self.engine = BacktestEngine()
        self.results = {}
        
    def run_pattern_strategy(
        self,
        patterns: List[str],
        position_size: float = 0.1,
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Run backtest for specific patterns.
        
        Args:
            patterns: List of pattern types to trade on
            position_size: Position size as fraction of capital
            confidence_threshold: Minimum confidence level for signals
            
        Returns:
            Backtest results dictionary
        """
        self.engine.reset()
        
        # Initialize pattern recognizer
        recognizer = PatternRecognizer(self.data)
        
        # Process each day
        for i in range(100, len(self.data)):  # Start after warmup period
            current_data = self.data.iloc[:i+1]
            current_date = self.data.index[i]
            current_price = self.data['Close'].iloc[i]
            
            # Update pattern recognizer data
            recognizer.data = current_data
            
            # Get signals for current day
            signals = recognizer.analyze_all_patterns()
            
            # Filter signals
            valid_signals = [
                s for s in signals 
                if s['date'] == current_date 
                and s['type'] in patterns
                and s['confidence'] >= confidence_threshold
            ]
            
            # Check stops
            self.engine.check_stops(
                self.data['High'].iloc[i],
                self.data['Low'].iloc[i],
                current_date
            )
            
            # Execute signals
            if valid_signals:
                # Use highest confidence signal
                best_signal = max(valid_signals, key=lambda x: x['confidence'])
                self.engine.execute_signal(
                    best_signal,
                    current_price,
                    current_date,
                    position_size
                )
            
            # Update equity
            self.engine.update_equity(current_price, current_date)
        
        # Close any open positions
        if self.engine.positions:
            self.engine.close_position(
                self.data['Close'].iloc[-1],
                self.data.index[-1]
            )
        
        # Calculate metrics
        metrics = self.engine.calculate_metrics()
        
        return {
            'metrics': metrics,
            'equity_curve': pd.DataFrame(self.engine.equity_curve),
            'trades': self.engine.get_trade_history(),
            'patterns_used': patterns
        }
    
    def optimize_pattern_combinations(
        self,
        min_patterns: int = 1,
        max_patterns: int = 3
    ) -> pd.DataFrame:
        """Find best pattern combinations through backtesting.
        
        Args:
            min_patterns: Minimum number of patterns to combine
            max_patterns: Maximum number of patterns to combine
            
        Returns:
            DataFrame with results for each combination
        """
        from itertools import combinations
        
        # Available patterns
        all_patterns = [
            'MA_CROSSOVER_BUY',
            'MA_CROSSOVER_SELL',
            'RSI_BULLISH_DIVERGENCE',
            'RSI_BEARISH_DIVERGENCE',
            'RESISTANCE_BREAKOUT',
            'SUPPORT_BREAKDOWN',
            'HAMMER_BULLISH',
            'SHOOTING_STAR_BEARISH',
            'BULLISH_ENGULFING',
            'BEARISH_ENGULFING'
        ]
        
        results = []
        
        # Test different combinations
        for r in range(min_patterns, max_patterns + 1):
            for pattern_combo in combinations(all_patterns, r):
                logger.info(f"Testing pattern combination: {pattern_combo}")
                
                try:
                    # Run backtest
                    result = self.run_pattern_strategy(list(pattern_combo))
                    
                    # Store results
                    results.append({
                        'patterns': ', '.join(pattern_combo),
                        'num_patterns': len(pattern_combo),
                        'total_trades': result['metrics']['total_trades'],
                        'win_rate': result['metrics']['win_rate'],
                        'total_return': result['metrics']['total_return'],
                        'sharpe_ratio': result['metrics']['sharpe_ratio'],
                        'max_drawdown': result['metrics']['max_drawdown'],
                        'profit_factor': result['metrics']['profit_factor']
                    })
                    
                except Exception as e:
                    logger.error(f"Error testing {pattern_combo}: {e}")
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Sort by total return
        results_df.sort_values('total_return', ascending=False, inplace=True)
        
        return results_df
    
    def run_indicator_strategy(
        self,
        indicator_rules: Dict[str, Any],
        position_size: float = 0.1
    ) -> Dict[str, Any]:
        """Run backtest using technical indicator rules.
        
        Args:
            indicator_rules: Dictionary defining indicator-based rules
            position_size: Position size as fraction of capital
            
        Returns:
            Backtest results dictionary
        """
        self.engine.reset()
        
        # Calculate indicators
        indicators = TechnicalIndicators()
        
        # Add indicators to data
        data_with_indicators = self.data.copy()
        
        # Example: Add common indicators
        data_with_indicators['SMA20'] = indicators.sma(self.data['Close'], 20)
        data_with_indicators['SMA50'] = indicators.sma(self.data['Close'], 50)
        data_with_indicators['RSI'] = indicators.rsi(self.data['Close'])
        
        macd_data = indicators.macd(self.data['Close'])
        data_with_indicators['MACD'] = macd_data['macd']
        data_with_indicators['MACD_Signal'] = macd_data['signal']
        
        bb_data = indicators.bollinger_bands(self.data['Close'])
        data_with_indicators['BB_Upper'] = bb_data['upper']
        data_with_indicators['BB_Lower'] = bb_data['lower']
        
        # Process each day
        for i in range(50, len(data_with_indicators)):  # Start after indicator warmup
            current_date = data_with_indicators.index[i]
            current_price = data_with_indicators['Close'].iloc[i]
            
            # Check stops
            self.engine.check_stops(
                data_with_indicators['High'].iloc[i],
                data_with_indicators['Low'].iloc[i],
                current_date
            )
            
            # Generate signals based on rules
            signal = None
            
            # Example rules (can be customized via indicator_rules parameter)
            if 'ma_crossover' in indicator_rules:
                if (data_with_indicators['SMA20'].iloc[i] > data_with_indicators['SMA50'].iloc[i] and
                    data_with_indicators['SMA20'].iloc[i-1] <= data_with_indicators['SMA50'].iloc[i-1]):
                    signal = {
                        'type': 'BUY',
                        'date': current_date,
                        'price': current_price,
                        'confidence': 0.8
                    }
                elif (data_with_indicators['SMA20'].iloc[i] < data_with_indicators['SMA50'].iloc[i] and
                      data_with_indicators['SMA20'].iloc[i-1] >= data_with_indicators['SMA50'].iloc[i-1]):
                    signal = {
                        'type': 'SELL',
                        'date': current_date,
                        'price': current_price,
                        'confidence': 0.8
                    }
            
            # Execute signal if generated
            if signal:
                self.engine.execute_signal(
                    signal,
                    current_price,
                    current_date,
                    position_size
                )
            
            # Update equity
            self.engine.update_equity(current_price, current_date)
        
        # Close any open positions
        if self.engine.positions:
            self.engine.close_position(
                data_with_indicators['Close'].iloc[-1],
                data_with_indicators.index[-1]
            )
        
        # Calculate metrics
        metrics = self.engine.calculate_metrics()
        
        return {
            'metrics': metrics,
            'equity_curve': pd.DataFrame(self.engine.equity_curve),
            'trades': self.engine.get_trade_history(),
            'indicator_rules': indicator_rules
        }
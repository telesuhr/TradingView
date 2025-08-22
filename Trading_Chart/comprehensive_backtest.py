"""Comprehensive backtesting with longer periods and multiple strategies."""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector
from src.analysis import TechnicalIndicators, PatternRecognizer
from src.backtest import StrategyRunner

def analyze_data_period(data):
    """Analyze the data period and quality."""
    print("=== Data Analysis ===")
    print(f"Total trading days: {len(data)}")
    print(f"Date range: {data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}")
    
    # Calculate actual period
    total_days = (data.index.max() - data.index.min()).days
    trading_days = len(data)
    
    print(f"Calendar days: {total_days}")
    print(f"Trading days: {trading_days}")
    print(f"Trading days ratio: {trading_days/total_days:.1%}")
    
    # Price statistics
    print(f"\nPrice Statistics:")
    print(f"Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    print(f"Price volatility (daily): {data['Close'].pct_change().std()*100:.2f}%")
    print(f"Average volume: {data['Volume'].mean():,.0f}")
    
    return total_days, trading_days

def test_individual_strategies(data):
    """Test individual trading strategies."""
    print("\n=== Individual Strategy Testing ===")
    
    runner = StrategyRunner(data)
    strategies = {
        'MA Crossover': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
        'RSI Divergence': ['RSI_BULLISH_DIVERGENCE', 'RSI_BEARISH_DIVERGENCE'],
        'Support/Resistance': ['RESISTANCE_BREAKOUT', 'SUPPORT_BREAKDOWN'],
        'Bullish Candlesticks': ['HAMMER_BULLISH', 'BULLISH_ENGULFING'],
        'Bearish Candlesticks': ['SHOOTING_STAR_BEARISH', 'BEARISH_ENGULFING'],
    }
    
    results = {}
    
    for strategy_name, patterns in strategies.items():
        print(f"\nTesting: {strategy_name}")
        print("  Patterns:", ', '.join(patterns))
        
        try:
            result = runner.run_pattern_strategy(
                patterns=patterns,
                position_size=0.1,
                confidence_threshold=0.7
            )
            
            metrics = result['metrics']
            results[strategy_name] = metrics
            
            print(f"  Results:")
            print(f"    Total trades: {metrics['total_trades']}")
            print(f"    Win rate: {metrics['win_rate']:.1f}%")
            print(f"    Total return: {metrics['total_return']:+.2f}%")
            print(f"    Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"    Max drawdown: {metrics['max_drawdown']:.2f}%")
            print(f"    Profit factor: {metrics['profit_factor']:.2f}")
            
            # Show trade details if trades exist
            trades_df = result['trades']
            if not trades_df.empty:
                print(f"    Avg win: ${metrics['avg_win']:.2f}")
                print(f"    Avg loss: ${metrics['avg_loss']:.2f}")
                print(f"    Best trade: ${trades_df['pnl'].max():.2f}")
                print(f"    Worst trade: ${trades_df['pnl'].min():.2f}")
        
        except Exception as e:
            print(f"  Error: {e}")
            results[strategy_name] = None
    
    return results

def test_position_sizes(data):
    """Test different position sizes."""
    print("\n=== Position Size Analysis ===")
    
    runner = StrategyRunner(data)
    
    # Use best performing patterns (MA Crossover + Engulfing patterns)
    best_patterns = ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL', 'BULLISH_ENGULFING', 'BEARISH_ENGULFING']
    
    position_sizes = [0.05, 0.1, 0.2, 0.3]  # 5%, 10%, 20%, 30%
    
    print(f"Testing position sizes with patterns: {', '.join(best_patterns)}")
    
    for pos_size in position_sizes:
        print(f"\nPosition size: {pos_size:.1%}")
        
        try:
            result = runner.run_pattern_strategy(
                patterns=best_patterns,
                position_size=pos_size,
                confidence_threshold=0.7
            )
            
            metrics = result['metrics']
            
            print(f"  Total return: {metrics['total_return']:+.2f}%")
            print(f"  Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"  Max drawdown: {metrics['max_drawdown']:.2f}%")
            print(f"  Risk-adjusted return: {metrics['total_return']/abs(metrics['max_drawdown']) if metrics['max_drawdown'] != 0 else 0:.2f}")
            
        except Exception as e:
            print(f"  Error: {e}")

def test_confidence_thresholds(data):
    """Test different confidence thresholds."""
    print("\n=== Confidence Threshold Analysis ===")
    
    runner = StrategyRunner(data)
    
    # Use MA Crossover patterns (most frequent)
    test_patterns = ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL']
    
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    print(f"Testing confidence thresholds with patterns: {', '.join(test_patterns)}")
    
    for threshold in thresholds:
        print(f"\nConfidence threshold: {threshold:.1%}")
        
        try:
            result = runner.run_pattern_strategy(
                patterns=test_patterns,
                position_size=0.1,
                confidence_threshold=threshold
            )
            
            metrics = result['metrics']
            
            print(f"  Total trades: {metrics['total_trades']}")
            print(f"  Win rate: {metrics['win_rate']:.1f}%")
            print(f"  Total return: {metrics['total_return']:+.2f}%")
            print(f"  Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
            
        except Exception as e:
            print(f"  Error: {e}")

def show_recent_signals(data):
    """Show recent trading signals."""
    print("\n=== Recent Trading Signals ===")
    
    recognizer = PatternRecognizer(data)
    signals = recognizer.analyze_all_patterns()
    
    # Group by date and show recent signals
    recent_signals = [s for s in signals if s['date'] >= data.index[-30]]  # Last 30 days
    
    if recent_signals:
        print(f"Found {len(recent_signals)} signals in last 30 trading days:")
        print("\nSignal Details:")
        
        # Sort by date
        recent_signals.sort(key=lambda x: x['date'])
        
        for signal in recent_signals:
            signal_type = "📈 BUY " if 'BUY' in signal['type'] or 'BULLISH' in signal['type'] else "📉 SELL"
            print(f"  {signal['date'].strftime('%Y-%m-%d')}: {signal_type} @ ${signal['price']:.2f}")
            print(f"    Type: {signal['type']}")
            print(f"    Confidence: {signal['confidence']:.1%}")
            print(f"    Details: {signal['details']}")
            print()
    else:
        print("No recent signals found")

def main():
    """Main comprehensive backtesting function."""
    print("=== Comprehensive LME Copper Backtesting ===\n")
    
    # Test with different time periods
    periods = [
        ("6 months", 180),
        ("1 year", 365),
        ("2 years", 730),
        ("3 years", 1095)
    ]
    
    for period_name, days in periods:
        print(f"\n{'='*60}")
        print(f"TESTING PERIOD: {period_name.upper()} ({days} days)")
        print('='*60)
        
        try:
            # Load data
            print("Loading data...")
            with SQLServerConnector() as conn:
                data = conn.get_lme_copper_data(
                    start_date=datetime.now() - timedelta(days=days)
                )
            
            if len(data) < 100:
                print(f"Insufficient data: only {len(data)} days available")
                continue
                
            # Analyze data period
            total_days, trading_days = analyze_data_period(data)
            
            # Only run full analysis on sufficient data
            if trading_days < 100:
                print("Insufficient trading days for reliable backtesting")
                continue
                
            # Test individual strategies
            strategy_results = test_individual_strategies(data)
            
            # Find best strategy
            best_strategy = None
            best_return = float('-inf')
            
            for name, result in strategy_results.items():
                if result and result['total_return'] > best_return:
                    best_return = result['total_return']
                    best_strategy = name
            
            if best_strategy:
                print(f"\n🏆 Best performing strategy: {best_strategy}")
                print(f"   Return: {best_return:+.2f}%")
            
            # Only do detailed analysis on longest period
            if period_name == "3 years":
                test_position_sizes(data)
                test_confidence_thresholds(data)
                show_recent_signals(data)
            
        except Exception as e:
            print(f"Error testing {period_name}: {e}")
    
    print(f"\n{'='*60}")
    print("BACKTESTING COMPLETE")
    print('='*60)
    print("\nKey Insights:")
    print("1. Longer periods provide more reliable backtest results")
    print("2. Position sizing significantly affects risk/return profile")
    print("3. Higher confidence thresholds reduce trade frequency but may improve quality")
    print("4. Combine multiple pattern types for better diversification")

if __name__ == "__main__":
    main()
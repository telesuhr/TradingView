"""Demo analysis script without GUI dependencies."""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector
from src.analysis import TechnicalIndicators, PatternRecognizer
from src.backtest import StrategyRunner

def main():
    """Run demo analysis."""
    print("=== LME Copper Trading System Demo ===\n")
    
    # Load data
    print("1. Loading LME Copper data...")
    with SQLServerConnector() as conn:
        data = conn.get_lme_copper_data(
            start_date=datetime.now() - timedelta(days=365)  # 1 year
        )
    
    print(f"   Loaded {len(data)} days of data")
    print(f"   Date range: {data.index.min()} to {data.index.max()}")
    print(f"   Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    
    # Technical Analysis
    print("\n2. Technical Analysis...")
    indicators = TechnicalIndicators()
    
    # Calculate indicators
    sma_20 = indicators.sma(data['Close'], 20)
    sma_50 = indicators.sma(data['Close'], 50)
    rsi = indicators.rsi(data['Close'])
    macd_data = indicators.macd(data['Close'])
    
    print(f"   Current SMA20: ${sma_20.iloc[-1]:.2f}")
    print(f"   Current SMA50: ${sma_50.iloc[-1]:.2f}")
    print(f"   Current RSI: {rsi.iloc[-1]:.1f}")
    print(f"   Current MACD: {macd_data['macd'].iloc[-1]:.2f}")
    
    # Pattern Recognition
    print("\n3. Pattern Recognition...")
    recognizer = PatternRecognizer(data)
    signals = recognizer.analyze_all_patterns()
    
    # Show recent signals
    recent_signals = [s for s in signals if s['date'] >= data.index[-30]]
    print(f"   Found {len(recent_signals)} signals in last 30 days")
    
    if recent_signals:
        print("\n   Recent signals:")
        for signal in recent_signals[-5:]:  # Last 5 signals
            print(f"   - {signal['date'].strftime('%Y-%m-%d')}: {signal['type']} @ ${signal['price']:.2f} (confidence: {signal['confidence']:.1%})")
    
    # Backtesting
    print("\n4. Backtesting...")
    runner = StrategyRunner(data)
    
    # Test MA Crossover strategy
    print("   Testing MA Crossover strategy...")
    ma_result = runner.run_pattern_strategy(
        patterns=['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
        position_size=0.1,
        confidence_threshold=0.7
    )
    
    ma_metrics = ma_result['metrics']
    print(f"   - Total trades: {ma_metrics['total_trades']}")
    print(f"   - Win rate: {ma_metrics['win_rate']:.1f}%")
    print(f"   - Total return: {ma_metrics['total_return']:.1f}%")
    print(f"   - Sharpe ratio: {ma_metrics['sharpe_ratio']:.2f}")
    print(f"   - Max drawdown: {ma_metrics['max_drawdown']:.1f}%")
    
    # Test RSI Divergence strategy
    print("\n   Testing RSI Divergence strategy...")
    rsi_result = runner.run_pattern_strategy(
        patterns=['RSI_BULLISH_DIVERGENCE', 'RSI_BEARISH_DIVERGENCE'],
        position_size=0.1,
        confidence_threshold=0.8
    )
    
    rsi_metrics = rsi_result['metrics']
    print(f"   - Total trades: {rsi_metrics['total_trades']}")
    print(f"   - Win rate: {rsi_metrics['win_rate']:.1f}%")
    print(f"   - Total return: {rsi_metrics['total_return']:.1f}%")
    print(f"   - Sharpe ratio: {rsi_metrics['sharpe_ratio']:.2f}")
    print(f"   - Max drawdown: {rsi_metrics['max_drawdown']:.1f}%")
    
    # Pattern optimization
    print("\n5. Pattern Optimization...")
    print("   Finding best pattern combinations (this may take a moment)...")
    
    try:
        optimization_results = runner.optimize_pattern_combinations(
            min_patterns=1,
            max_patterns=2  # Reduced for faster execution
        )
        
        print(f"   Tested {len(optimization_results)} pattern combinations")
        
        if not optimization_results.empty:
            top_3 = optimization_results.head(3)
            print("\n   Top 3 performing combinations:")
            for i, (idx, row) in enumerate(top_3.iterrows(), 1):
                print(f"   {i}. {row['patterns']}")
                print(f"      - Win rate: {row['win_rate']:.1f}%")
                print(f"      - Return: {row['total_return']:.1f}%")
                print(f"      - Sharpe: {row['sharpe_ratio']:.2f}")
    
    except Exception as e:
        print(f"   Optimization error: {e}")
    
    print("\n=== Demo Complete ===")
    print("\nTo run the full GUI application:")
    print("1. Install PyQt5: pip install PyQt5")
    print("2. Run: python main.py")

if __name__ == "__main__":
    main()
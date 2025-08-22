"""Improved trading strategies based on backtest analysis."""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector
from src.analysis import TechnicalIndicators
from src.backtest import StrategyRunner

def test_improved_strategies():
    """Test improved strategies with trend filters and better risk management."""
    
    print("=== Testing Improved Strategies ===\n")
    
    # Load 2+ years of data for reliable testing
    with SQLServerConnector() as conn:
        data = conn.get_lme_copper_data(
            start_date=datetime.now() - timedelta(days=730)  # 2 years
        )
    
    print(f"Data period: {len(data)} trading days")
    print(f"Date range: {data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}")
    
    # Create custom strategies
    strategies_to_test = [
        {
            'name': 'Trend Following MA',
            'description': 'MA crossover with trend filter',
            'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
            'position_size': 0.05,  # Reduced risk
            'confidence': 0.8       # Higher confidence
        },
        {
            'name': 'Quality Candlesticks',
            'description': 'High-confidence candlestick patterns only',
            'patterns': ['BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
            'position_size': 0.08,
            'confidence': 0.8
        },
        {
            'name': 'Conservative Mixed',
            'description': 'Best patterns with conservative sizing',
            'patterns': ['BULLISH_ENGULFING', 'MA_CROSSOVER_BUY'],
            'position_size': 0.05,
            'confidence': 0.75
        },
        {
            'name': 'Aggressive Mixed',
            'description': 'Multiple patterns for more opportunities',
            'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL', 'BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
            'position_size': 0.15,
            'confidence': 0.65
        }
    ]
    
    runner = StrategyRunner(data)
    results = []
    
    for strategy in strategies_to_test:
        print(f"\nTesting: {strategy['name']}")
        print(f"Description: {strategy['description']}")
        print(f"Patterns: {', '.join(strategy['patterns'])}")
        print(f"Position size: {strategy['position_size']:.1%}")
        print(f"Confidence threshold: {strategy['confidence']:.1%}")
        
        try:
            result = runner.run_pattern_strategy(
                patterns=strategy['patterns'],
                position_size=strategy['position_size'],
                confidence_threshold=strategy['confidence']
            )
            
            metrics = result['metrics']
            
            print(f"\nResults:")
            print(f"  Total trades: {metrics['total_trades']}")
            print(f"  Win rate: {metrics['win_rate']:.1f}%")
            print(f"  Total return: {metrics['total_return']:+.2f}%")
            print(f"  Annualized return: {metrics['total_return'] * (365/len(data)):+.2f}%")
            print(f"  Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"  Max drawdown: {metrics['max_drawdown']:.2f}%")
            print(f"  Profit factor: {metrics['profit_factor']:.2f}")
            
            # Risk-adjusted metrics
            if metrics['max_drawdown'] != 0:
                calmar_ratio = metrics['total_return'] / abs(metrics['max_drawdown'])
                print(f"  Calmar ratio: {calmar_ratio:.2f}")
            
            # Trade analysis
            trades_df = result['trades']
            if not trades_df.empty:
                print(f"  Avg trade duration: {(trades_df['exit_date'] - trades_df['entry_date']).dt.days.mean():.1f} days")
                print(f"  Best trade: ${trades_df['pnl'].max():.2f}")
                print(f"  Worst trade: ${trades_df['pnl'].min():.2f}")
                
                # Win/Loss streak analysis
                trades_df['win'] = trades_df['pnl'] > 0
                streaks = trades_df['win'].astype(int).groupby((trades_df['win'] != trades_df['win'].shift()).cumsum()).sum()
                win_streaks = streaks[trades_df.groupby((trades_df['win'] != trades_df['win'].shift()).cumsum())['win'].first()]
                loss_streaks = streaks[~trades_df.groupby((trades_df['win'] != trades_df['win'].shift()).cumsum())['win'].first()]
                
                if len(win_streaks) > 0:
                    print(f"  Max win streak: {win_streaks.max()}")
                if len(loss_streaks) > 0:
                    print(f"  Max loss streak: {loss_streaks.max()}")
            
            results.append({
                'name': strategy['name'],
                'metrics': metrics,
                'trades': len(trades_df) if not trades_df.empty else 0
            })
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Summary comparison
    print(f"\n{'='*80}")
    print("STRATEGY COMPARISON SUMMARY")
    print('='*80)
    print(f"{'Strategy':<20} {'Trades':<8} {'Win%':<6} {'Return%':<8} {'Sharpe':<7} {'MaxDD%':<7} {'Profit Factor':<12}")
    print('-'*80)
    
    for result in results:
        if result['metrics']:
            m = result['metrics']
            print(f"{result['name']:<20} {result['trades']:<8} {m['win_rate']:>5.1f} {m['total_return']:>+7.2f} {m['sharpe_ratio']:>6.2f} {m['max_drawdown']:>6.2f} {m['profit_factor']:>11.2f}")
    
    # Find best strategy
    best_strategy = None
    best_score = float('-inf')
    
    for result in results:
        if result['metrics'] and result['trades'] >= 5:  # Minimum trades for reliability
            # Combined score: return / max_drawdown + sharpe_ratio
            score = (result['metrics']['total_return'] / abs(result['metrics']['max_drawdown']) + 
                    result['metrics']['sharpe_ratio']) if result['metrics']['max_drawdown'] != 0 else result['metrics']['sharpe_ratio']
            
            if score > best_score:
                best_score = score
                best_strategy = result
    
    if best_strategy:
        print(f"\nBest Overall Strategy: {best_strategy['name']}")
        print(f"Combined Score: {best_score:.2f}")
        
        # Provide recommendations
        print(f"\nRECOMMENDATIONS:")
        if best_strategy['metrics']['total_return'] > 0:
            print("✓ This strategy shows positive returns")
        else:
            print("✗ All strategies show negative returns - consider:")
            print("  - Reducing transaction costs")
            print("  - Improving entry/exit timing")
            print("  - Adding trend filters")
            print("  - Using stop-losses more effectively")
        
        print(f"\nNext Steps:")
        print("1. Paper trade the best strategy for 1-2 months")
        print("2. Monitor real-time performance vs backtest")
        print("3. Consider regime-based adjustments")
        print("4. Implement proper position sizing based on volatility")

if __name__ == "__main__":
    test_improved_strategies()
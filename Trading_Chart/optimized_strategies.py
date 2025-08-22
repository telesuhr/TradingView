"""Optimized strategies based on multi-symbol analysis findings."""

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
from src.backtest import StrategyRunner

def run_optimized_analysis():
    """Run analysis with optimized parameters based on findings."""
    print("=== Optimized Multi-Strategy Analysis ===\n")
    
    # Focus on symbols that showed some activity
    symbols = {
        'LMCADS03 Comdty': 'LME Copper',
        'XAU Comdty': 'Gold',
        'SI1 Comdty': 'Silver Futures',
        'SPX Index': 'S&P 500',
        'C 1 Comdty': 'Corn',
        'GC1 Comdty': 'Gold Futures',
    }
    
    # Optimized strategies with lower confidence thresholds
    strategies = {
        'MA_Relaxed': {
            'name': 'MA Crossover Relaxed',
            'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
            'position_size': 0.08,
            'confidence': 0.60  # Lowered from 0.80
        },
        'Candlestick_Active': {
            'name': 'Active Candlesticks',
            'patterns': ['BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
            'position_size': 0.10,
            'confidence': 0.60  # Lowered from 0.75
        },
        'Mixed_Active': {
            'name': 'Mixed Active',
            'patterns': ['MA_CROSSOVER_BUY', 'BULLISH_ENGULFING', 'MA_CROSSOVER_SELL', 'BEARISH_ENGULFING'],
            'position_size': 0.08,
            'confidence': 0.55  # Lowered from 0.70
        },
        'Breakout_Active': {
            'name': 'Breakout Active',
            'patterns': ['RESISTANCE_BREAKOUT', 'SUPPORT_BREAKDOWN'],
            'position_size': 0.12,
            'confidence': 0.65
        },
        'All_Patterns': {
            'name': 'All Patterns',
            'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL', 'BULLISH_ENGULFING', 
                        'BEARISH_ENGULFING', 'HAMMER_BULLISH', 'SHOOTING_STAR_BEARISH'],
            'position_size': 0.06,
            'confidence': 0.50  # Very low threshold for maximum activity
        }
    }
    
    print(f"Testing {len(strategies)} optimized strategies on {len(symbols)} symbols")
    print("Key changes: Lower confidence thresholds for more trade generation\n")
    
    results = []
    
    for symbol, symbol_name in symbols.items():
        print(f"Analyzing {symbol_name} ({symbol})...")
        
        # Load 1 year of data
        try:
            with SQLServerConnector() as conn:
                query = f"""
                    SELECT 
                        Market_Date as [Date],
                        Opening_Price as [Open],
                        Daily_High as [High],
                        Daily_Low as [Low],
                        Closing_Price as [Close],
                        volume as [Volume]
                    FROM MarketData
                    WHERE market_name = '{symbol}'
                        AND Market_Date >= ?
                    ORDER BY Market_Date ASC
                """
                
                start_date = datetime.now() - timedelta(days=365)
                data = pd.read_sql_query(
                    query, 
                    conn.connection,
                    params=[start_date],
                    parse_dates=['Date']
                )
                
                if not data.empty:
                    data.set_index('Date', inplace=True)
                    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                    data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, errors='coerce')
                    data.sort_index(inplace=True)
                    
        except Exception as e:
            print(f"  Error loading data: {e}")
            continue
        
        if data.empty or len(data) < 100:
            print(f"  Insufficient data ({len(data)} days)")
            continue
            
        print(f"  Loaded {len(data)} days")
        runner = StrategyRunner(data)
        
        # Test each strategy
        for strategy_key, strategy in strategies.items():
            print(f"    {strategy['name']}...", end=" ")
            
            try:
                result = runner.run_pattern_strategy(
                    patterns=strategy['patterns'],
                    position_size=strategy['position_size'],
                    confidence_threshold=strategy['confidence']
                )
                
                metrics = result['metrics']
                trades_df = result['trades']
                
                # Calculate additional metrics
                trade_frequency = metrics['total_trades'] / len(data) * 252 if len(data) > 0 else 0
                avg_trade_days = (trades_df['exit_date'] - trades_df['entry_date']).dt.days.mean() if not trades_df.empty else 0
                
                results.append({
                    'Symbol': symbol_name,
                    'Strategy': strategy['name'],
                    'Trades': metrics['total_trades'],
                    'Win Rate': metrics['win_rate'],
                    'Total Return': metrics['total_return'],
                    'Sharpe Ratio': metrics['sharpe_ratio'],
                    'Max Drawdown': metrics['max_drawdown'],
                    'Profit Factor': metrics['profit_factor'],
                    'Trade Frequency': trade_frequency,
                    'Avg Trade Days': avg_trade_days,
                    'Best Trade': trades_df['pnl'].max() if not trades_df.empty else 0,
                    'Worst Trade': trades_df['pnl'].min() if not trades_df.empty else 0
                })
                
                print(f"{metrics['total_trades']} trades, {metrics['win_rate']:.1f}% win, {metrics['total_return']:+.2f}%")
                
            except Exception as e:
                print(f"Error: {str(e)[:30]}...")
        
        print()
    
    # Display comprehensive results
    if results:
        df = pd.DataFrame(results)
        
        print("="*120)
        print("OPTIMIZED STRATEGY RESULTS")
        print("="*120)
        
        # Filter out zero-trade strategies for ranking
        active_df = df[df['Trades'] > 0].copy()
        
        if not active_df.empty:
            # Sort by Total Return
            active_df = active_df.sort_values('Total Return', ascending=False)
            
            print(f"\nACTIVE STRATEGIES (Generated Trades):")
            print("-"*120)
            print(f"{'Rank':<4} {'Symbol':<15} {'Strategy':<20} {'Trades':<6} {'Win%':<6} {'Return%':<8} {'Sharpe':<7} {'MaxDD%':<7} {'PF':<5}")
            print("-"*120)
            
            for i, (_, row) in enumerate(active_df.iterrows(), 1):
                print(f"{i:<4} {row['Symbol']:<15} {row['Strategy']:<20} {row['Trades']:<6} "
                      f"{row['Win Rate']:>5.1f} {row['Total Return']:>+7.2f} {row['Sharpe Ratio']:>6.2f} "
                      f"{row['Max Drawdown']:>6.2f} {row['Profit Factor']:>4.2f}")
            
            # Strategy effectiveness analysis
            print(f"\nSTRATEGY EFFECTIVENESS ANALYSIS:")
            print("-"*80)
            
            strategy_stats = active_df.groupby('Strategy').agg({
                'Total Return': ['count', 'mean', 'std', 'min', 'max'],
                'Trades': 'mean',
                'Win Rate': 'mean',
                'Trade Frequency': 'mean'
            }).round(2)
            
            for strategy in strategy_stats.index:
                strategy_data = active_df[active_df['Strategy'] == strategy]
                profitable_count = len(strategy_data[strategy_data['Total Return'] > 0])
                
                print(f"\n{strategy}:")
                print(f"  Tested on: {len(strategy_data)} symbols")
                print(f"  Profitable: {profitable_count}/{len(strategy_data)} ({profitable_count/len(strategy_data)*100:.1f}%)")
                print(f"  Avg Return: {strategy_data['Total Return'].mean():+.2f}% (±{strategy_data['Total Return'].std():.2f}%)")
                print(f"  Avg Trades/Year: {strategy_data['Trade Frequency'].mean():.1f}")
                print(f"  Best: {strategy_data['Total Return'].max():+.2f}% | Worst: {strategy_data['Total Return'].min():+.2f}%")
            
            # Symbol performance ranking
            print(f"\nSYMBOL PERFORMANCE RANKING:")
            print("-"*60)
            
            symbol_performance = active_df.groupby('Symbol').agg({
                'Total Return': ['mean', 'max', 'count'],
                'Trades': 'mean'
            }).round(2)
            
            symbol_performance['avg_return'] = symbol_performance[('Total Return', 'mean')]
            symbol_performance = symbol_performance.sort_values('avg_return', ascending=False)
            
            for symbol in symbol_performance.index:
                symbol_data = active_df[active_df['Symbol'] == symbol]
                best_strategy = symbol_data.loc[symbol_data['Total Return'].idxmax(), 'Strategy']
                best_return = symbol_data['Total Return'].max()
                
                print(f"{symbol:<15} Best: {best_strategy} ({best_return:+.2f}%) | "
                      f"Avg: {symbol_data['Total Return'].mean():+.2f}% | "
                      f"Active strategies: {len(symbol_data)}")
            
            # Top recommendations
            print(f"\nTOP RECOMMENDATIONS:")
            print("-"*50)
            
            if len(active_df) > 0:
                # Best overall return
                best = active_df.iloc[0]
                print(f"1. Highest Return: {best['Symbol']} - {best['Strategy']}")
                print(f"   {best['Total Return']:+.2f}% return, {best['Trades']} trades, {best['Win Rate']:.1f}% win rate")
                
                # Best risk-adjusted (Sharpe > 0)
                good_sharpe = active_df[active_df['Sharpe Ratio'] > 0]
                if not good_sharpe.empty:
                    best_sharpe = good_sharpe.sort_values('Sharpe Ratio', ascending=False).iloc[0]
                    print(f"\n2. Best Risk-Adjusted: {best_sharpe['Symbol']} - {best_sharpe['Strategy']}")
                    print(f"   Sharpe: {best_sharpe['Sharpe Ratio']:.2f}, Return: {best_sharpe['Total Return']:+.2f}%")
                
                # Most active (highest trade frequency)
                most_active = active_df.sort_values('Trade Frequency', ascending=False).iloc[0]
                print(f"\n3. Most Active: {most_active['Symbol']} - {most_active['Strategy']}")
                print(f"   {most_active['Trade Frequency']:.1f} trades/year, {most_active['Total Return']:+.2f}% return")
        
        else:
            print("No active strategies found - all confidence thresholds may still be too high")
        
        # Show inactive strategies for debugging
        inactive_df = df[df['Trades'] == 0]
        if not inactive_df.empty:
            print(f"\nINACTIVE STRATEGIES ({len(inactive_df)} combinations):")
            print("These strategies generated no trades - consider further lowering confidence thresholds")
            
            inactive_summary = inactive_df.groupby(['Strategy']).size().sort_values(ascending=False)
            for strategy, count in inactive_summary.items():
                print(f"  {strategy}: {count} symbols with no trades")
        
        # Export results
        output_file = f"optimized_strategy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)
        print(f"\nDetailed results exported to: {output_file}")
        
        return df
    
    else:
        print("No results generated")
        return None

if __name__ == "__main__":
    results = run_optimized_analysis()
    
    print(f"\nKEY INSIGHTS:")
    print("1. Lower confidence thresholds increase trade generation")
    print("2. Different symbols respond better to different strategies")
    print("3. Trade frequency vs profitability trade-off is crucial")
    print("4. Consider symbol-specific strategy optimization")
    print("\nNext: Fine-tune the best performing combinations for live trading")
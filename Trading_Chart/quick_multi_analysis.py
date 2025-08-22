"""Quick multi-strategy comparison for key symbols."""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector
from src.backtest import StrategyRunner

def quick_analysis():
    """Quick analysis of top strategies on selected symbols."""
    print("=== Quick Multi-Strategy Comparison ===\n")
    
    # Limited set of symbols for faster analysis
    symbols = {
        'LMCADS03 Comdty': 'LME Copper',
        'XAU Comdty': 'Gold',
        'GC1 Comdty': 'Gold Futures', 
        'SI1 Comdty': 'Silver Futures',
        'SPX Index': 'S&P 500',
    }
    
    # Top performing strategy configurations (based on previous analysis)
    strategies = {
        'MA_Conservative': {
            'name': 'Conservative MA',
            'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
            'position_size': 0.05,
            'confidence': 0.80
        },
        'Quality_Candlesticks': {
            'name': 'Quality Candlesticks',
            'patterns': ['BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
            'position_size': 0.08,
            'confidence': 0.75
        },
        'Mixed_Balanced': {
            'name': 'Mixed Balanced',
            'patterns': ['MA_CROSSOVER_BUY', 'BULLISH_ENGULFING'],
            'position_size': 0.06,
            'confidence': 0.70
        }
    }
    
    results = []
    
    print(f"Testing {len(strategies)} strategies on {len(symbols)} symbols")
    print("Analysis period: 1 year\n")
    
    for symbol, symbol_name in symbols.items():
        print(f"Analyzing {symbol_name} ({symbol})...")
        
        # Load data
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
                
                start_date = datetime.now() - timedelta(days=365)  # 1 year
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
            
        print(f"  Loaded {len(data)} days of data")
        runner = StrategyRunner(data)
        
        # Test each strategy
        for strategy_key, strategy in strategies.items():
            print(f"  Testing {strategy['name']}...", end=" ")
            
            try:
                result = runner.run_pattern_strategy(
                    patterns=strategy['patterns'],
                    position_size=strategy['position_size'],
                    confidence_threshold=strategy['confidence']
                )
                
                metrics = result['metrics']
                
                # Calculate additional metrics
                annualized_return = metrics['total_return'] * (365 / len(data)) if len(data) > 0 else 0
                
                results.append({
                    'Symbol': symbol_name,
                    'Strategy': strategy['name'],
                    'Trades': metrics['total_trades'],
                    'Win Rate': metrics['win_rate'],
                    'Total Return': metrics['total_return'],
                    'Annualized Return': annualized_return,
                    'Sharpe Ratio': metrics['sharpe_ratio'],
                    'Max Drawdown': metrics['max_drawdown'],
                    'Profit Factor': metrics['profit_factor'],
                    'Data Days': len(data)
                })
                
                print(f"{metrics['total_trades']} trades, {metrics['total_return']:+.1f}%")
                
            except Exception as e:
                print(f"Error: {str(e)[:50]}...")
                
        print()
    
    # Display results
    if results:
        df = pd.DataFrame(results)
        
        print("="*100)
        print("COMPREHENSIVE RESULTS")
        print("="*100)
        
        # Sort by Total Return
        df_sorted = df.sort_values('Total Return', ascending=False)
        
        print(f"\n{'Rank':<4} {'Symbol':<15} {'Strategy':<20} {'Trades':<6} {'Win%':<6} {'Return%':<8} {'Ann.Ret%':<8} {'Sharpe':<7} {'MaxDD%':<7}")
        print("-"*100)
        
        for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
            print(f"{i:<4} {row['Symbol']:<15} {row['Strategy']:<20} {row['Trades']:<6} "
                  f"{row['Win Rate']:>5.1f} {row['Total Return']:>+7.2f} {row['Annualized Return']:>+7.2f} "
                  f"{row['Sharpe Ratio']:>6.2f} {row['Max Drawdown']:>6.2f}")
        
        # Strategy Performance Summary
        print(f"\nSTRATEGY PERFORMANCE SUMMARY:")
        print("-"*60)
        strategy_summary = df.groupby('Strategy').agg({
            'Total Return': ['mean', 'std', 'min', 'max'],
            'Win Rate': 'mean',
            'Trades': 'mean',
            'Sharpe Ratio': 'mean'
        }).round(2)
        
        for strategy in strategy_summary.index:
            returns = df[df['Strategy'] == strategy]['Total Return']
            print(f"\n{strategy}:")
            print(f"  Avg Return: {returns.mean():+.2f}% (±{returns.std():.2f}%)")
            print(f"  Best: {returns.max():+.2f}% | Worst: {returns.min():+.2f}%")
            print(f"  Profitable: {len(returns[returns > 0])}/{len(returns)} symbols")
        
        # Symbol Performance Summary
        print(f"\nSYMBOL PERFORMANCE SUMMARY:")
        print("-"*60)
        
        for symbol in df['Symbol'].unique():
            symbol_data = df[df['Symbol'] == symbol]
            returns = symbol_data['Total Return']
            best_strategy = symbol_data.loc[symbol_data['Total Return'].idxmax(), 'Strategy']
            
            print(f"\n{symbol}:")
            print(f"  Best Strategy: {best_strategy} ({returns.max():+.2f}%)")
            print(f"  Avg Return: {returns.mean():+.2f}%")
            print(f"  Profitable Strategies: {len(returns[returns > 0])}/{len(returns)}")
        
        # Top Recommendations
        print(f"\nTOP RECOMMENDATIONS:")
        print("-"*40)
        
        # Best overall
        best_overall = df_sorted.iloc[0]
        print(f"1. Best Overall Performance:")
        print(f"   {best_overall['Symbol']} - {best_overall['Strategy']}")
        print(f"   Return: {best_overall['Total Return']:+.2f}% ({best_overall['Trades']} trades)")
        
        # Most consistent strategy (lowest std dev)
        strategy_consistency = df.groupby('Strategy')['Total Return'].std().sort_values()
        most_consistent = strategy_consistency.index[0]
        consistent_avg = df[df['Strategy'] == most_consistent]['Total Return'].mean()
        
        print(f"\n2. Most Consistent Strategy:")
        print(f"   {most_consistent}")
        print(f"   Avg Return: {consistent_avg:+.2f}% (σ={strategy_consistency.iloc[0]:.2f}%)")
        
        # Best risk-adjusted (highest Sharpe)
        best_sharpe = df_sorted.sort_values('Sharpe Ratio', ascending=False).iloc[0]
        
        print(f"\n3. Best Risk-Adjusted:")
        print(f"   {best_sharpe['Symbol']} - {best_sharpe['Strategy']}")
        print(f"   Sharpe Ratio: {best_sharpe['Sharpe Ratio']:.2f}")
        
        # Export results
        output_file = f"quick_strategy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)
        print(f"\n4. Results exported to: {output_file}")
        
        return df
    
    else:
        print("No results to display")
        return None

if __name__ == "__main__":
    results = quick_analysis()
    
    print(f"\nNext steps:")
    print("1. Review the top performing combinations")
    print("2. Consider paper trading the best strategy for validation") 
    print("3. Run full analysis with more symbols: python multi_strategy_analyzer.py")
    print("4. Add more strategies based on these results")
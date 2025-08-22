"""Multi-strategy and multi-symbol trading analysis system."""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector
from src.backtest import StrategyRunner

class MultiStrategyAnalyzer:
    """Analyze multiple trading strategies across multiple symbols."""
    
    def __init__(self):
        self.symbols = {
            # Major Commodities
            'LMCADS03 Comdty': 'LME Copper',
            'XAU Comdty': 'Gold',
            'XAG Comdty': 'Silver',
            'GC1 Comdty': 'Gold Futures',
            'SI1 Comdty': 'Silver Futures',
            'PL1 Comdty': 'Platinum',
            'PA1 Comdty': 'Palladium',
            
            # Agricultural
            'C 1 Comdty': 'Corn',
            'S 1 Comdty': 'Soybeans',
            'W 1 Comdty': 'Wheat',
            'CT1 Comdty': 'Cotton',
            'SB1 Comdty': 'Sugar',
            'CC1 Comdty': 'Cocoa',
            'KC1 Comdty': 'Coffee',
            
            # Energy (if available)
            'CLA Comdty': 'Crude Oil',
            
            # Major FX Pairs
            'EURUSD Curncy': 'EUR/USD',
            'GBPUSD Curncy': 'GBP/USD',
            'USDJPY Curncy': 'USD/JPY',
            
            # Major Indices
            'SPX Index': 'S&P 500',
            'DJI Index': 'Dow Jones',
            'NDX Index': 'NASDAQ 100',
        }
        
        # Define comprehensive strategy configurations
        self.strategies = {
            'MA_Fast': {
                'name': 'Fast MA Crossover',
                'description': 'Quick moving average signals',
                'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
                'position_size': 0.10,
                'confidence': 0.70
            },
            'MA_Conservative': {
                'name': 'Conservative MA',
                'description': 'High confidence MA signals only',
                'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
                'position_size': 0.05,
                'confidence': 0.85
            },
            'Candlestick_Aggressive': {
                'name': 'Aggressive Candlesticks',
                'description': 'All candlestick patterns',
                'patterns': ['BULLISH_ENGULFING', 'BEARISH_ENGULFING', 'HAMMER_BULLISH', 'SHOOTING_STAR_BEARISH'],
                'position_size': 0.15,
                'confidence': 0.65
            },
            'Candlestick_Quality': {
                'name': 'Quality Candlesticks',
                'description': 'High-quality candlestick patterns only',
                'patterns': ['BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
                'position_size': 0.10,
                'confidence': 0.80
            },
            'RSI_Divergence': {
                'name': 'RSI Divergence',
                'description': 'RSI divergence signals',
                'patterns': ['RSI_BULLISH_DIVERGENCE', 'RSI_BEARISH_DIVERGENCE'],
                'position_size': 0.12,
                'confidence': 0.75
            },
            'Breakout': {
                'name': 'S&R Breakout',
                'description': 'Support/Resistance breakouts',
                'patterns': ['RESISTANCE_BREAKOUT', 'SUPPORT_BREAKDOWN'],
                'position_size': 0.08,
                'confidence': 0.75
            },
            'Mixed_Conservative': {
                'name': 'Mixed Conservative',
                'description': 'Best patterns, conservative sizing',
                'patterns': ['MA_CROSSOVER_BUY', 'BULLISH_ENGULFING'],
                'position_size': 0.06,
                'confidence': 0.80
            },
            'Mixed_Balanced': {
                'name': 'Mixed Balanced',
                'description': 'Balanced approach with multiple patterns',
                'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL', 'BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
                'position_size': 0.10,
                'confidence': 0.70
            },
            'Mixed_Aggressive': {
                'name': 'Mixed Aggressive',
                'description': 'All patterns for maximum opportunities',
                'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL', 'BULLISH_ENGULFING', 'BEARISH_ENGULFING', 
                           'HAMMER_BULLISH', 'SHOOTING_STAR_BEARISH'],
                'position_size': 0.15,
                'confidence': 0.60
            }
        }
        
        self.results = {}
        
    def load_symbol_data(self, symbol: str, days: int = 730) -> pd.DataFrame:
        """Load data for a specific symbol."""
        try:
            with SQLServerConnector() as conn:
                # Modify query for different symbols
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
                
                start_date = datetime.now() - timedelta(days=days)
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
                
                return data
                
        except Exception as e:
            print(f"Error loading {symbol}: {e}")
            return pd.DataFrame()
    
    def run_strategy_on_symbol(self, symbol: str, strategy_key: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Run a single strategy on a single symbol."""
        if data.empty or len(data) < 100:
            return None
            
        strategy = self.strategies[strategy_key]
        runner = StrategyRunner(data)
        
        try:
            result = runner.run_pattern_strategy(
                patterns=strategy['patterns'],
                position_size=strategy['position_size'],
                confidence_threshold=strategy['confidence']
            )
            
            metrics = result['metrics']
            trades_df = result['trades']
            
            # Add custom metrics
            additional_metrics = {
                'symbol': symbol,
                'strategy': strategy_key,
                'data_points': len(data),
                'date_range': f"{data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}",
                'annualized_return': metrics['total_return'] * (365 / len(data)) if len(data) > 0 else 0,
                'calmar_ratio': metrics['total_return'] / abs(metrics['max_drawdown']) if metrics['max_drawdown'] != 0 else 0,
                'avg_trade_duration': (trades_df['exit_date'] - trades_df['entry_date']).dt.days.mean() if not trades_df.empty else 0,
                'trade_frequency': metrics['total_trades'] / len(data) * 252 if len(data) > 0 else 0,  # Trades per year
                'win_loss_ratio': abs(metrics['avg_win'] / metrics['avg_loss']) if metrics['avg_loss'] != 0 else 0
            }
            
            metrics.update(additional_metrics)
            return metrics
            
        except Exception as e:
            print(f"Error running {strategy_key} on {symbol}: {e}")
            return None
    
    def analyze_all_combinations(self, days: int = 730):
        """Analyze all strategy-symbol combinations."""
        print("=== Multi-Strategy Multi-Symbol Analysis ===\n")
        print(f"Analysis period: {days} days (~{days/365:.1f} years)")
        print(f"Symbols: {len(self.symbols)}")
        print(f"Strategies: {len(self.strategies)}")
        print(f"Total combinations: {len(self.symbols) * len(self.strategies)}")
        print("\nLoading data and running backtests...\n")
        
        all_results = []
        
        for symbol, symbol_name in self.symbols.items():
            print(f"Analyzing {symbol_name} ({symbol})...")
            
            # Load data
            data = self.load_symbol_data(symbol, days)
            
            if data.empty:
                print(f"  No data available for {symbol}")
                continue
                
            print(f"  Loaded {len(data)} trading days")
            
            # Run each strategy
            symbol_results = []
            
            for strategy_key, strategy_config in self.strategies.items():
                print(f"  Running {strategy_config['name']}...", end=" ")
                
                result = self.run_strategy_on_symbol(symbol, strategy_key, data)
                
                if result:
                    symbol_results.append(result)
                    all_results.append(result)
                    print(f"Done ({result['total_trades']} trades, {result['total_return']:+.2f}%)")
                else:
                    print("Failed")
            
            print(f"  Completed {len(symbol_results)} strategies for {symbol_name}\n")
        
        # Convert to DataFrame for analysis
        if all_results:
            self.results_df = pd.DataFrame(all_results)
            self.display_comprehensive_results()
        else:
            print("No results to analyze")
    
    def display_comprehensive_results(self):
        """Display comprehensive analysis results."""
        df = self.results_df
        
        print("=" * 120)
        print("COMPREHENSIVE RESULTS SUMMARY")
        print("=" * 120)
        
        # Overall statistics
        print(f"\nOverall Statistics:")
        print(f"Total combinations analyzed: {len(df)}")
        print(f"Profitable strategies: {len(df[df['total_return'] > 0])}")
        print(f"Profitability rate: {len(df[df['total_return'] > 0]) / len(df) * 100:.1f}%")
        print(f"Average return: {df['total_return'].mean():+.2f}%")
        print(f"Best return: {df['total_return'].max():+.2f}%")
        print(f"Worst return: {df['total_return'].min():+.2f}%")
        
        # Top performers
        print(f"\nTOP 10 PERFORMING COMBINATIONS:")
        print("-" * 120)
        top_10 = df.nlargest(10, 'total_return')
        
        header = f"{'Rank':<4} {'Symbol':<15} {'Strategy':<20} {'Trades':<6} {'Win%':<6} {'Return%':<8} {'Ann.Ret%':<8} {'Sharpe':<7} {'MaxDD%':<7} {'Calmar':<7}"
        print(header)
        print("-" * 120)
        
        for i, (_, row) in enumerate(top_10.iterrows(), 1):
            symbol_name = self.symbols.get(row['symbol'], row['symbol'][:15])
            print(f"{i:<4} {symbol_name:<15} {row['strategy']:<20} {row['total_trades']:<6} "
                  f"{row['win_rate']:>5.1f} {row['total_return']:>+7.2f} {row['annualized_return']:>+7.2f} "
                  f"{row['sharpe_ratio']:>6.2f} {row['max_drawdown']:>6.2f} {row['calmar_ratio']:>6.2f}")
        
        # Strategy comparison
        print(f"\nSTRATEGY PERFORMANCE COMPARISON:")
        print("-" * 80)
        strategy_summary = df.groupby('strategy').agg({
            'total_return': ['mean', 'std', 'min', 'max'],
            'win_rate': 'mean',
            'total_trades': 'mean',
            'sharpe_ratio': 'mean',
            'max_drawdown': 'mean'
        }).round(2)
        
        strategy_summary.columns = ['_'.join(col).strip() for col in strategy_summary.columns.values]
        
        print(f"{'Strategy':<20} {'Avg Ret%':<8} {'Std%':<6} {'Min%':<6} {'Max%':<6} {'Avg Win%':<7} {'Avg Trades':<10} {'Avg Sharpe':<10}")
        print("-" * 80)
        
        for strategy in strategy_summary.index:
            row = strategy_summary.loc[strategy]
            print(f"{strategy:<20} {row['total_return_mean']:>+7.2f} {row['total_return_std']:>5.2f} "
                  f"{row['total_return_min']:>+5.2f} {row['total_return_max']:>+5.2f} {row['win_rate_mean']:>6.1f} "
                  f"{row['total_trades_mean']:>9.1f} {row['sharpe_ratio_mean']:>9.2f}")
        
        # Symbol comparison (if multiple symbols)
        if len(self.symbols) > 1:
            print(f"\nSYMBOL PERFORMANCE COMPARISON:")
            print("-" * 80)
            symbol_summary = df.groupby('symbol').agg({
                'total_return': ['mean', 'std', 'count'],
                'win_rate': 'mean',
                'total_trades': 'mean'
            }).round(2)
            
            symbol_summary.columns = ['_'.join(col).strip() for col in symbol_summary.columns.values]
            
            for symbol in symbol_summary.index:
                symbol_name = self.symbols.get(symbol, symbol)
                row = symbol_summary.loc[symbol]
                print(f"{symbol_name:<20} Avg Return: {row['total_return_mean']:+.2f}% "
                      f"Std: {row['total_return_std']:.2f}% Strategies tested: {row['total_return_count']}")
        
        # Risk-adjusted rankings
        print(f"\nRISK-ADJUSTED PERFORMANCE (Calmar Ratio):")
        print("-" * 120)
        risk_adj = df[df['max_drawdown'] < -0.1].nlargest(10, 'calmar_ratio')  # Exclude strategies with minimal drawdown
        
        if not risk_adj.empty:
            print(header)
            print("-" * 120)
            
            for i, (_, row) in enumerate(risk_adj.iterrows(), 1):
                symbol_name = self.symbols.get(row['symbol'], row['symbol'][:15])
                print(f"{i:<4} {symbol_name:<15} {row['strategy']:<20} {row['total_trades']:<6} "
                      f"{row['win_rate']:>5.1f} {row['total_return']:>+7.2f} {row['annualized_return']:>+7.2f} "
                      f"{row['sharpe_ratio']:>6.2f} {row['max_drawdown']:>6.2f} {row['calmar_ratio']:>6.2f}")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        print("-" * 50)
        
        best_overall = df.loc[df['total_return'].idxmax()]
        best_risk_adj = df.loc[df['calmar_ratio'].idxmax()] if df['calmar_ratio'].max() > 0 else best_overall
        
        print(f"1. Best Overall Return:")
        print(f"   {self.symbols.get(best_overall['symbol'], best_overall['symbol'])} - {best_overall['strategy']}")
        print(f"   Return: {best_overall['total_return']:+.2f}%, Trades: {best_overall['total_trades']}")
        
        if best_risk_adj['strategy'] != best_overall['strategy']:
            print(f"\n2. Best Risk-Adjusted Return:")
            print(f"   {self.symbols.get(best_risk_adj['symbol'], best_risk_adj['symbol'])} - {best_risk_adj['strategy']}")
            print(f"   Calmar Ratio: {best_risk_adj['calmar_ratio']:.2f}")
        
        # Export results
        output_file = f"strategy_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)
        print(f"\n3. Detailed results exported to: {output_file}")
        
        return df

def add_more_symbols():
    """Function to add more symbols to the analysis."""
    print("\nTo add more symbols, edit the 'symbols' dictionary in MultiStrategyAnalyzer.__init__():")
    print("Available LME symbols (examples):")
    print("'LMAHDS03 Comdty': 'LME Aluminum'")
    print("'LMZSDS03 Comdty': 'LME Zinc'") 
    print("'LMNIDS03 Comdty': 'LME Nickel'")
    print("'LMPBDS03 Comdty': 'LME Lead'")
    print("'LMSNDS03 Comdty': 'LME Tin'")
    print("\nCheck your MarketData table for available market_name values")

def main():
    """Main function to run multi-strategy analysis."""
    
    analyzer = MultiStrategyAnalyzer()
    
    # Run analysis with 2 years of data
    analyzer.analyze_all_combinations(days=730)
    
    print(f"\nAnalysis complete!")
    add_more_symbols()

if __name__ == "__main__":
    main()
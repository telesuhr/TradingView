"""Discover available symbols in MarketData table for multi-symbol analysis."""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector

def discover_symbols():
    """Discover available symbols in the MarketData table."""
    print("=== Available Symbols Discovery ===\n")
    
    try:
        with SQLServerConnector() as conn:
            # Get all unique symbols
            cursor = conn.connection.cursor()
            
            print("Querying MarketData table for available symbols...\n")
            
            cursor.execute("""
                SELECT 
                    market_name,
                    COUNT(*) as record_count,
                    MIN(Market_Date) as earliest_date,
                    MAX(Market_Date) as latest_date,
                    AVG(Closing_Price) as avg_price,
                    AVG(volume) as avg_volume
                FROM MarketData
                GROUP BY market_name
                ORDER BY record_count DESC
            """)
            
            results = cursor.fetchall()
            
            if results:
                print(f"Found {len(results)} unique symbols:")
                print("-" * 100)
                print(f"{'Symbol':<25} {'Records':<8} {'Date Range':<25} {'Avg Price':<12} {'Avg Volume':<12}")
                print("-" * 100)
                
                symbols_for_config = {}
                
                for row in results:
                    symbol = row[0]
                    count = row[1]
                    start_date = row[2].strftime('%Y-%m-%d') if row[2] else 'N/A'
                    end_date = row[3].strftime('%Y-%m-%d') if row[3] else 'N/A'
                    avg_price = f"${row[4]:,.2f}" if row[4] else 'N/A'
                    avg_volume = f"{row[5]:,.0f}" if row[5] else 'N/A'
                    
                    print(f"{symbol:<25} {count:<8} {start_date} to {end_date:<8} {avg_price:<12} {avg_volume:<12}")
                    
                    # Generate suggested name for config
                    if 'LME' in symbol.upper() or 'LM' in symbol.upper():
                        if 'COPPER' in symbol.upper() or 'CADS' in symbol:
                            symbols_for_config[symbol] = 'LME Copper'
                        elif 'ALUMINUM' in symbol.upper() or 'AHDS' in symbol:
                            symbols_for_config[symbol] = 'LME Aluminum'
                        elif 'ZINC' in symbol.upper() or 'ZSDS' in symbol:
                            symbols_for_config[symbol] = 'LME Zinc'
                        elif 'NICKEL' in symbol.upper() or 'NIDS' in symbol:
                            symbols_for_config[symbol] = 'LME Nickel'
                        elif 'LEAD' in symbol.upper() or 'PBDS' in symbol:
                            symbols_for_config[symbol] = 'LME Lead'
                        elif 'TIN' in symbol.upper() or 'SNDS' in symbol:
                            symbols_for_config[symbol] = 'LME Tin'
                        else:
                            # Generic LME name
                            symbols_for_config[symbol] = f"LME {symbol.split()[0] if ' ' in symbol else symbol[:10]}"
                    else:
                        # Non-LME symbol
                        symbols_for_config[symbol] = symbol.replace('Comdty', '').strip()
                
                # Generate configuration code
                print("\n" + "=" * 100)
                print("CONFIGURATION CODE FOR MULTI-SYMBOL ANALYSIS")
                print("=" * 100)
                print("\nAdd this to MultiStrategyAnalyzer.__init__() symbols dictionary:")
                print("\nself.symbols = {")
                
                # Show top 10 symbols by record count
                top_symbols = list(symbols_for_config.items())[:10]
                
                for i, (symbol, name) in enumerate(top_symbols):
                    comma = "," if i < len(top_symbols) - 1 else ""
                    print(f"    '{symbol}': '{name}'{comma}")
                
                print("}")
                
                # Filter criteria suggestions
                print(f"\nSUGGESTED FILTERING CRITERIA:")
                print("-" * 50)
                
                # Symbols with good data coverage (>500 records)
                good_coverage = [s for s in results if s[1] > 500]
                print(f"Symbols with >500 records: {len(good_coverage)}")
                
                # Recent symbols (data within last year)
                from datetime import datetime, timedelta
                one_year_ago = datetime.now() - timedelta(days=365)
                recent_symbols = [s for s in results if s[3] and s[3] > one_year_ago]
                print(f"Symbols with data within last year: {len(recent_symbols)}")
                
                # High volume symbols
                high_volume = [s for s in results if s[5] and s[5] > 10000]
                print(f"Symbols with average volume >10,000: {len(high_volume)}")
                
                # Recommended symbols for analysis
                recommended = []
                for row in results:
                    if (row[1] > 200 and  # At least 200 records
                        row[3] and row[3] > one_year_ago and  # Recent data
                        row[5] and row[5] > 1000):  # Reasonable volume
                        recommended.append((row[0], symbols_for_config.get(row[0], row[0])))
                
                print(f"\nRECOMMENDED SYMBOLS FOR ANALYSIS ({len(recommended)} total):")
                print("-" * 60)
                for symbol, name in recommended[:15]:  # Show top 15
                    print(f"'{symbol}': '{name}',")
                
            else:
                print("No symbols found in MarketData table")
                
    except Exception as e:
        print(f"Error discovering symbols: {e}")

def test_symbol_data(symbol: str):
    """Test data quality for a specific symbol."""
    print(f"\n=== Testing Data Quality for {symbol} ===")
    
    try:
        with SQLServerConnector() as conn:
            cursor = conn.connection.cursor()
            
            # Detailed analysis
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT Market_Date) as unique_dates,
                    MIN(Market_Date) as start_date,
                    MAX(Market_Date) as end_date,
                    AVG(Closing_Price) as avg_close,
                    STDEV(Closing_Price) as price_volatility,
                    COUNT(CASE WHEN volume > 0 THEN 1 END) as records_with_volume,
                    COUNT(CASE WHEN Closing_Price IS NULL OR Closing_Price = 0 THEN 1 END) as missing_prices
                FROM MarketData
                WHERE market_name = ?
            """, (symbol,))
            
            result = cursor.fetchone()
            
            if result:
                print(f"Total records: {result[0]}")
                print(f"Unique dates: {result[1]}")
                print(f"Date range: {result[2]} to {result[3]}")
                print(f"Average price: ${result[4]:.2f}")
                print(f"Price volatility: ${result[5]:.2f}")
                print(f"Records with volume: {result[6]} ({result[6]/result[0]*100:.1f}%)")
                print(f"Missing/zero prices: {result[7]} ({result[7]/result[0]*100:.1f}%)")
                
                # Data quality score
                completeness = (result[0] - result[7]) / result[0]
                volume_coverage = result[6] / result[0]
                
                quality_score = (completeness * 0.6 + volume_coverage * 0.4) * 100
                print(f"Data quality score: {quality_score:.1f}/100")
                
                if quality_score >= 80:
                    print("✓ Excellent data quality - suitable for backtesting")
                elif quality_score >= 60:
                    print("~ Good data quality - suitable with caution")
                else:
                    print("✗ Poor data quality - not recommended for backtesting")
                    
                return quality_score >= 60
            else:
                print("No data found for this symbol")
                return False
                
    except Exception as e:
        print(f"Error testing {symbol}: {e}")
        return False

def main():
    """Main function for symbol discovery."""
    discover_symbols()
    
    print(f"\n{'='*60}")
    print("NEXT STEPS:")
    print('='*60)
    print("1. Copy the recommended symbols configuration above")
    print("2. Edit multi_strategy_analyzer.py and update the symbols dictionary")
    print("3. Run: python multi_strategy_analyzer.py")
    print("\nTo test individual symbols, use test_symbol_data('SYMBOL_NAME')")

if __name__ == "__main__":
    main()
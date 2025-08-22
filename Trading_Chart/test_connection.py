"""Test SQL Server connection and data retrieval."""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector


def test_connection():
    """Test database connection and data retrieval."""
    print("Testing SQL Server connection...")
    
    try:
        with SQLServerConnector() as conn:
            print("[OK] Connection successful!")
            
            # Test latest price
            print("\nFetching latest LME Copper price...")
            latest = conn.get_latest_price()
            if latest:
                print(f"[OK] Latest price: {latest['close']:.2f} on {latest['date']}")
            else:
                print("[ERROR] No data found")
            
            # Test historical data
            print("\nFetching historical data (last 30 days)...")
            start_date = datetime.now() - timedelta(days=30)
            data = conn.get_lme_copper_data(start_date=start_date)
            
            if not data.empty:
                print(f"[OK] Retrieved {len(data)} days of data")
                print(f"\nSample data (last 5 days):")
                print(data.tail())
                
                # Check data quality
                print(f"\nData quality check:")
                print(f"- Date range: {data.index.min()} to {data.index.max()}")
                print(f"- Missing values: {data.isnull().sum().sum()}")
                print(f"- Price range: {data['Close'].min():.2f} - {data['Close'].max():.2f}")
            else:
                print("[ERROR] No historical data found")
                
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print("\nPlease check:")
        print("1. .env file exists with correct database credentials")
        print("2. SQL Server is running and accessible")
        print("3. MarketData table exists with LMCADS03 Comdty data")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    test_connection()
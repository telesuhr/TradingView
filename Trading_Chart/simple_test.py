"""Simple direct connection test."""

import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Environment variables:")
print(f"DB_SERVER: {os.getenv('DB_SERVER')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_TRUSTED_CONNECTION: {os.getenv('DB_TRUSTED_CONNECTION')}")

# Direct connection using working connection string from debug
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')

conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)

print(f"\nConnection string: {conn_str.replace(password, '***')}")

try:
    print("\nConnecting...")
    conn = pyodbc.connect(conn_str)
    print("[SUCCESS] Connected!")
    
    cursor = conn.cursor()
    
    # Test LME data query
    cursor.execute("""
        SELECT TOP 5 
            Market_Date as Date,
            Opening_Price as Open,
            Daily_High as High,
            Daily_Low as Low,
            Closing_Price as Close,
            volume as Volume
        FROM MarketData
        WHERE market_name = 'LMCADS03 Comdty'
        ORDER BY Market_Date DESC
    """)
    
    print("\nLME Copper data (latest 5 records):")
    for row in cursor.fetchall():
        print(f"  {row[0]}: OHLC({row[1]}, {row[2]}, {row[3]}, {row[4]}) Vol={row[5]}")
    
    conn.close()
    print("\n[SUCCESS] Data retrieval test passed!")
    
except Exception as e:
    print(f"[ERROR] {e}")
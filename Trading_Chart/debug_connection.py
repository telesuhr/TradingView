"""Debug SQL Server connection settings."""

import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== SQL Server Connection Debug ===\n")

# Show current settings (without password)
print("Environment variables:")
print(f"DB_SERVER: {os.getenv('DB_SERVER', 'NOT SET')}")
print(f"DB_NAME: {os.getenv('DB_NAME', 'NOT SET')}")
print(f"DB_USER: {os.getenv('DB_USER', 'NOT SET')}")
print(f"DB_PASSWORD: {'SET' if os.getenv('DB_PASSWORD') else 'NOT SET'}")
print(f"DB_TRUSTED_CONNECTION: {os.getenv('DB_TRUSTED_CONNECTION', 'NOT SET')}")

# Check available ODBC drivers
print("\n\nAvailable ODBC Drivers:")
drivers = pyodbc.drivers()
for driver in drivers:
    print(f"  - {driver}")

# Try connection with more detailed error handling
print("\n\nAttempting connection...")

server = os.getenv('DB_SERVER', 'localhost')
database = os.getenv('DB_NAME', 'TradingData')
trusted = os.getenv('DB_TRUSTED_CONNECTION', 'yes')

# Try different connection strings
connection_strings = []

if trusted.lower() == 'yes':
    # Windows Authentication
    connection_strings.append({
        'name': 'Windows Auth with ODBC Driver 17',
        'string': f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    })
    connection_strings.append({
        'name': 'Windows Auth with SQL Server',
        'string': f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    })
else:
    # SQL Authentication
    username = os.getenv('DB_USER', '')
    password = os.getenv('DB_PASSWORD', '')
    connection_strings.append({
        'name': 'SQL Auth with ODBC Driver 17',
        'string': f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};"
    })

# Test each connection string
for conn_info in connection_strings:
    print(f"\n\nTesting: {conn_info['name']}")
    print(f"Connection string: {conn_info['string'].replace(os.getenv('DB_PASSWORD', ''), '***')}")
    
    try:
        conn = pyodbc.connect(conn_info['string'])
        print("[SUCCESS] Connected!")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        print(f"SQL Server version: {row[0][:50]}...")
        
        # Check if MarketData table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'MarketData'
        """)
        table_exists = cursor.fetchone()[0]
        print(f"MarketData table exists: {'Yes' if table_exists else 'No'}")
        
        if table_exists:
            # Check for LMCADS03 Comdty data
            cursor.execute("""
                SELECT COUNT(*) 
                FROM MarketData 
                WHERE market_name = 'LMCADS03 Comdty'
            """)
            data_count = cursor.fetchone()[0]
            print(f"LMCADS03 Comdty records: {data_count}")
        
        conn.close()
        print("\nRecommended connection string found!")
        break
        
    except pyodbc.Error as e:
        print(f"[FAILED] {e}")

print("\n\n=== Debug Complete ===")
print("\nIf all connections failed, please check:")
print("1. SQL Server service is running")
print("2. Server name is correct (try computername\\instancename)")
print("3. Firewall allows SQL Server connections")
print("4. SQL Server is configured to allow remote connections")
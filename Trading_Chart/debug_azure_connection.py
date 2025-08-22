"""Debug Azure SQL Database connection."""

import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Azure SQL Database Connection Debug ===\n")

server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')

print(f"Server: {server}")
print(f"Database: {database}")
print(f"Username: {username}")
print(f"Password: {'***' if password else 'NOT SET'}")

# Azure SQL Database connection strings to try
connection_strings = [
    {
        'name': 'ODBC Driver 18 (recommended for Azure)',
        'string': f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    },
    {
        'name': 'ODBC Driver 17',
        'string': f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    },
    {
        'name': 'ODBC Driver 17 (TCP prefix)',
        'string': f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=tcp:{server},1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    },
    {
        'name': 'Basic connection',
        'string': f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};"
    }
]

for conn_info in connection_strings:
    print(f"\n\nTrying: {conn_info['name']}")
    
    try:
        print("Connecting...")
        conn = pyodbc.connect(conn_info['string'], timeout=30)
        print("[SUCCESS] Connected!")
        
        # Test query
        cursor = conn.cursor()
        
        # Check SQL Server version
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"SQL Server: {version[:100]}...")
        
        # Check MarketData table
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'MarketData'
        """)
        table_exists = cursor.fetchone()[0]
        print(f"MarketData table exists: {'Yes' if table_exists else 'No'}")
        
        if table_exists:
            # Get sample data
            cursor.execute("""
                SELECT TOP 5 
                    Market_Date, 
                    Closing_Price, 
                    Opening_Price, 
                    Daily_High, 
                    Daily_Low, 
                    volume
                FROM MarketData
                WHERE market_name = 'LMCADS03 Comdty'
                ORDER BY Market_Date DESC
            """)
            
            rows = cursor.fetchall()
            print(f"\nSample data (latest 5 records):")
            for row in rows:
                print(f"  {row[0]}: Close={row[1]}, Open={row[2]}, High={row[3]}, Low={row[4]}, Vol={row[5]}")
        
        conn.close()
        
        # Save working connection string
        print(f"\n\n*** WORKING CONNECTION STRING ***")
        print(f"Use this in your code:")
        print(f"conn_str = \"\"\"{conn_info['string']}\"\"\"")
        break
        
    except pyodbc.Error as e:
        print(f"[FAILED] {e}")
    except Exception as e:
        print(f"[ERROR] {e}")

print("\n\n=== Tips for Azure SQL Database ===")
print("1. Make sure your IP is whitelisted in Azure firewall")
print("2. Use ODBC Driver 17 or 18")
print("3. Include 'Encrypt=yes' for secure connection")
print("4. Check username format (might need @servername)")
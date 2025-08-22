"""Database configuration for SQL Server connection."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQL Server connection parameters
DB_CONFIG: Dict[str, Any] = {
    'driver': '{ODBC Driver 18 for SQL Server}',
    'server': os.getenv('DB_SERVER', 'localhost'),
    'database': os.getenv('DB_NAME', 'TradingData'),
    'username': os.getenv('DB_USER', ''),
    'password': os.getenv('DB_PASSWORD', ''),
    'trusted_connection': os.getenv('DB_TRUSTED_CONNECTION', 'no'),
    'encrypt': 'yes',
    'trust_server_certificate': 'no',
    'connection_timeout': 30
}

# Query templates
QUERIES = {
    'lme_copper_daily': """
        SELECT 
            Market_Date as [Date],
            Opening_Price as [Open],
            Daily_High as [High],
            Daily_Low as [Low],
            Closing_Price as [Close],
            volume as [Volume]
        FROM MarketData
        WHERE market_name = 'LMCADS03 Comdty'
            AND Market_Date >= ?
        ORDER BY Market_Date ASC
    """,
    
    'lme_copper_latest': """
        SELECT TOP 1
            Market_Date as [Date],
            Closing_Price as [Close]
        FROM MarketData
        WHERE market_name = 'LMCADS03 Comdty'
        ORDER BY Market_Date DESC
    """
}
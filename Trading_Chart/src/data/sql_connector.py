"""SQL Server connection and data retrieval module."""

import pyodbc
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from config import DB_CONFIG, QUERIES

logger = logging.getLogger(__name__)


class SQLServerConnector:
    """Handles SQL Server connections and data retrieval for LME Copper data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize SQL Server connector.
        
        Args:
            config: Database configuration dictionary. Uses default if None.
        """
        self.config = config or DB_CONFIG
        self.connection = None
        
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        
    def connect(self):
        """Establish connection to SQL Server."""
        try:
            if self.config['trusted_connection'].lower() == 'yes':
                conn_str = (
                    f"DRIVER={self.config['driver']};"
                    f"SERVER={self.config['server']};"
                    f"DATABASE={self.config['database']};"
                    f"Trusted_Connection=yes;"
                )
            else:
                conn_str = (
                    f"DRIVER={self.config['driver']};"
                    f"SERVER={self.config['server']};"
                    f"DATABASE={self.config['database']};"
                    f"UID={self.config['username']};"
                    f"PWD={self.config['password']};"
                )
            
            # Add Azure-specific parameters if available
            if 'encrypt' in self.config:
                conn_str += f"Encrypt={self.config['encrypt']};"
            if 'trust_server_certificate' in self.config:
                conn_str += f"TrustServerCertificate={self.config['trust_server_certificate']};"
            if 'connection_timeout' in self.config:
                conn_str += f"Connection Timeout={self.config['connection_timeout']};"
            
            self.connection = pyodbc.connect(conn_str)
            logger.info(f"Connected to SQL Server: {self.config['server']}")
            
        except Exception as e:
            logger.error(f"Failed to connect to SQL Server: {e}")
            raise
            
    def disconnect(self):
        """Close SQL Server connection."""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from SQL Server")
            
    def get_lme_copper_data(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Retrieve LME Copper OHLCV data.
        
        Args:
            start_date: Start date for data retrieval. Defaults to 3 years ago.
            end_date: End date for data retrieval. Defaults to today.
            
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume
        """
        if not self.connection:
            raise ConnectionError("Not connected to database")
            
        # Default to 3 years of data
        if start_date is None:
            start_date = datetime.now() - timedelta(days=3*365)
        if end_date is None:
            end_date = datetime.now()
            
        try:
            query = QUERIES['lme_copper_daily']
            df = pd.read_sql_query(
                query, 
                self.connection,
                params=[start_date],
                parse_dates=['Date']
            )
            
            # Filter by end date
            df = df[df['Date'] <= end_date]
            
            # Set Date as index
            df.set_index('Date', inplace=True)
            
            # Ensure data types
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            
            # Sort by date
            df.sort_index(inplace=True)
            
            logger.info(f"Retrieved {len(df)} rows of LME Copper data")
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve LME Copper data: {e}")
            raise
            
    def get_latest_price(self) -> Optional[Dict[str, Any]]:
        """Get the latest LME Copper price.
        
        Returns:
            Dictionary with 'date' and 'close' keys, or None if no data.
        """
        if not self.connection:
            raise ConnectionError("Not connected to database")
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(QUERIES['lme_copper_latest'])
            row = cursor.fetchone()
            
            if row:
                return {
                    'date': row[0],
                    'close': float(row[1])
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve latest price: {e}")
            raise
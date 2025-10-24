"""Configuration management for the application."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # Database A1 (MyLocalData)
    DB_A1_SERVER = os.getenv('DB_A1_SERVER', 'A1')
    DB_A1_DATABASE = os.getenv('DB_A1_DATABASE', 'MyLocalData')
    DB_A1_TRUSTED = os.getenv('DB_A1_TRUSTED', 'yes')
    
    # Database B2 (TempDB and GenesysDB)
    DB_B2_SERVER = os.getenv('DB_B2_SERVER', 'B2')
    DB_B2_TEMPDB = os.getenv('DB_B2_TEMPDB', 'TempDB')
    DB_B2_GENESYSDB = os.getenv('DB_B2_GENESYSDB', 'GenesysDB')
    DB_B2_TRUSTED = os.getenv('DB_B2_TRUSTED', 'yes')
    
    # Query timeouts
    SQL_QUERY_TIMEOUT = int(os.getenv('SQL_QUERY_TIMEOUT', '300'))
    SQL_BULK_TIMEOUT = int(os.getenv('SQL_BULK_TIMEOUT', '600'))
    
    # Cache settings
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'filesystem')
    CACHE_DIR = os.getenv('CACHE_DIR', 'cache')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '3600'))
    
    # Redis settings
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    
    # Application settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '8000'))
    
    @classmethod
    def get_connection_string(cls, server, database, trusted='yes'):
        """Build SQL Server connection string with Trusted Authentication."""
        if trusted.lower() == 'yes':
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
            )
        else:
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
            )

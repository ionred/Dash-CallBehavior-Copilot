"""Database connection and query utilities."""
import pyodbc
import uuid
from contextlib import contextmanager
from config import Config


class DatabaseConnection:
    """Manages database connections and queries."""
    
    def __init__(self, server, database, trusted='yes'):
        """
        Initialize database connection.
        
        Args:
            server: SQL Server name
            database: Database name
            trusted: Use trusted authentication ('yes' or 'no')
        """
        self.connection_string = Config.get_connection_string(server, database, trusted)
        self.timeout = Config.SQL_QUERY_TIMEOUT
    
    def get_connection(self):
        """Get a new database connection."""
        conn = pyodbc.connect(self.connection_string, timeout=self.timeout)
        return conn
    
    @contextmanager
    def get_cursor(self, timeout=None):
        """
        Context manager for database cursor.
        
        Args:
            timeout: Query timeout in seconds (overrides default)
        
        Yields:
            Database cursor
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if timeout is not None:
                cursor.timeout = timeout
            yield cursor
        except pyodbc.OperationalError as e:
            if 'timeout' in str(e).lower():
                raise TimeoutError(f"Query timeout after {timeout or self.timeout} seconds") from e
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @contextmanager
    def transaction(self, timeout=None):
        """
        Context manager for database transaction with rollback support.
        
        Args:
            timeout: Query timeout in seconds (overrides default)
        
        Yields:
            (connection, cursor) tuple
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            conn.autocommit = False
            cursor = conn.cursor()
            if timeout is not None:
                cursor.timeout = timeout
            yield conn, cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def execute_query(self, query, params=None, timeout=None):
        """
        Execute a query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            timeout: Query timeout in seconds
        
        Returns:
            List of result rows
        """
        with self.get_cursor(timeout=timeout) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch all results
            columns = [column[0] for column in cursor.description] if cursor.description else []
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            return [dict(zip(columns, row)) for row in results]
    
    def execute_non_query(self, query, params=None, timeout=None):
        """
        Execute a non-query SQL statement (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query string
            params: Query parameters
            timeout: Query timeout in seconds
        
        Returns:
            Number of affected rows
        """
        with self.get_cursor(timeout=timeout) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            cursor.connection.commit()
            return cursor.rowcount


class TempTableManager:
    """Manages temporary tables with unique naming to avoid collisions."""
    
    @staticmethod
    def generate_temp_table_name(base_name='accountNumbers'):
        """
        Generate a unique temporary table name.
        
        Args:
            base_name: Base name for the temp table
        
        Returns:
            Unique temp table name (e.g., #accountNumbers_abc123)
        """
        unique_id = uuid.uuid4().hex[:8]
        return f"#{base_name}_{unique_id}"
    
    @staticmethod
    def create_account_temp_table(cursor, temp_table_name):
        """
        Create temporary table for account numbers.
        
        Args:
            cursor: Database cursor
            temp_table_name: Name of the temp table
        """
        create_query = f"""
        CREATE TABLE {temp_table_name} (
            accountNumber NVARCHAR(15) NOT NULL PRIMARY KEY CLUSTERED
        )
        """
        cursor.execute(create_query)
    
    @staticmethod
    def drop_temp_table(cursor, temp_table_name):
        """
        Drop temporary table if it exists.
        
        Args:
            cursor: Database cursor
            temp_table_name: Name of the temp table
        """
        drop_query = f"IF OBJECT_ID('tempdb..{temp_table_name}') IS NOT NULL DROP TABLE {temp_table_name}"
        cursor.execute(drop_query)


# Database connection instances
db_a1 = DatabaseConnection(
    server=Config.DB_A1_SERVER,
    database=Config.DB_A1_DATABASE,
    trusted=Config.DB_A1_TRUSTED
)

db_b2_tempdb = DatabaseConnection(
    server=Config.DB_B2_SERVER,
    database=Config.DB_B2_TEMPDB,
    trusted=Config.DB_B2_TRUSTED
)

db_b2_genesysdb = DatabaseConnection(
    server=Config.DB_B2_SERVER,
    database=Config.DB_B2_GENESYSDB,
    trusted=Config.DB_B2_TRUSTED
)

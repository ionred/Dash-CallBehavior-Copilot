"""Repository for eventAccounts table operations."""
from app.utils.database import db_a1
from config import Config


class EventAccountsRepository:
    """Data access layer for eventAccounts table."""
    
    @staticmethod
    def get_account_numbers(event_name, subgroup):
        """
        Get account numbers for a specific event/subgroup.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
        
        Returns:
            List of account numbers
        """
        query = """
        SELECT accountNumber
        FROM dbo.eventAccounts
        WHERE LOWER(eventName) = LOWER(?) AND LOWER(subGroup) = LOWER(?)
        ORDER BY accountNumber
        """
        results = db_a1.execute_query(query, (event_name, subgroup), timeout=Config.SQL_QUERY_TIMEOUT)
        return [row['accountNumber'] for row in results]
    
    @staticmethod
    def get_account_count(event_name, subgroup):
        """
        Get count of account numbers for a specific event/subgroup.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
        
        Returns:
            Count of account numbers
        """
        query = """
        SELECT COUNT(*) as count
        FROM dbo.eventAccounts
        WHERE LOWER(eventName) = LOWER(?) AND LOWER(subGroup) = LOWER(?)
        """
        result = db_a1.execute_query(query, (event_name, subgroup), timeout=Config.SQL_QUERY_TIMEOUT)
        return result[0]['count'] if result else 0
    
    @staticmethod
    def delete_accounts(cursor, event_name, subgroup):
        """
        Delete all account numbers for an event/subgroup (within a transaction).
        
        Args:
            cursor: Database cursor (from transaction context)
            event_name: Name of the event
            subgroup: Subgroup name
        """
        query = """
        DELETE FROM dbo.eventAccounts
        WHERE LOWER(eventName) = LOWER(?) AND LOWER(subGroup) = LOWER(?)
        """
        cursor.execute(query, (event_name, subgroup))
    
    @staticmethod
    def insert_accounts_from_temp(cursor, event_name, subgroup, temp_table_name, append_only=False):
        """
        Insert account numbers from a temporary table (within a transaction).
        
        Args:
            cursor: Database cursor (from transaction context)
            event_name: Name of the event
            subgroup: Subgroup name
            temp_table_name: Name of the temporary table with account numbers
            append_only: If True, only insert accounts that don't already exist
        """
        if append_only:
            # Insert only new accounts (avoid duplicates)
            query = f"""
            INSERT INTO dbo.eventAccounts (eventName, subGroup, accountNumber)
            SELECT ?, ?, t.accountNumber
            FROM {temp_table_name} t
            WHERE NOT EXISTS (
                SELECT 1 
                FROM dbo.eventAccounts ea 
                WHERE LOWER(ea.eventName) = LOWER(?) 
                AND LOWER(ea.subGroup) = LOWER(?) 
                AND ea.accountNumber = t.accountNumber
            )
            """
            cursor.execute(query, (event_name, subgroup, event_name, subgroup))
        else:
            # Insert all accounts
            query = f"""
            INSERT INTO dbo.eventAccounts (eventName, subGroup, accountNumber)
            SELECT ?, ?, accountNumber
            FROM {temp_table_name}
            """
            cursor.execute(query, (event_name, subgroup))
    
    @staticmethod
    def bulk_insert_accounts(cursor, event_name, subgroup, account_numbers):
        """
        Bulk insert account numbers using executemany (within a transaction).
        
        Args:
            cursor: Database cursor (from transaction context)
            event_name: Name of the event
            subgroup: Subgroup name
            account_numbers: List of account numbers
        """
        query = """
        INSERT INTO dbo.eventAccounts (eventName, subGroup, accountNumber)
        VALUES (?, ?, ?)
        """
        data = [(event_name, subgroup, acc) for acc in account_numbers]
        cursor.executemany(query, data)

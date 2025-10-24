"""Repository for callHistory table operations."""
from app.utils.database import db_b2_genesysdb
from config import Config


class CallHistoryRepository:
    """Data access layer for callHistory table."""
    
    @staticmethod
    def get_call_data(temp_table_name, monitor_start, monitor_end):
        """
        Get call history data for accounts in the temporary table.
        
        Args:
            temp_table_name: Name of the temporary table with account numbers
            monitor_start: Start date for call monitoring
            monitor_end: End date for call monitoring
        
        Returns:
            List of dictionaries with call data
        """
        query = f"""
        SELECT 
            callhist.queueName, 
            callhist.TalkTime, 
            callhist.CallDate,
            callhist.accountNumber
        FROM dbo.callHistory callhist
        INNER JOIN {temp_table_name} accounts ON callhist.accountNumber = accounts.accountNumber
        WHERE callhist.CallDate BETWEEN ? AND ?
        ORDER BY callhist.CallDate
        """
        return db_b2_genesysdb.execute_query(
            query, 
            (monitor_start, monitor_end), 
            timeout=Config.SQL_QUERY_TIMEOUT
        )

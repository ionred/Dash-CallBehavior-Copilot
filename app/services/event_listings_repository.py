"""Repository for eventListings table operations."""
from app.utils.database import db_a1
from config import Config


class EventListingsRepository:
    """Data access layer for eventListings table."""
    
    @staticmethod
    def get_all_events():
        """
        Get all events and their subgroups from eventListings table.
        
        Returns:
            List of dictionaries with eventName and subGroup
        """
        query = """
        SELECT eventName, subGroup, eventDate, monitorStart, monitorEnd, Description
        FROM dbo.eventListings
        ORDER BY eventName, subGroup
        """
        return db_a1.execute_query(query, timeout=Config.SQL_QUERY_TIMEOUT)
    
    @staticmethod
    def get_event_details(event_name, subgroup):
        """
        Get details for a specific event and subgroup.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
        
        Returns:
            Dictionary with event details or None if not found
        """
        query = """
        SELECT eventName, subGroup, eventDate, monitorStart, monitorEnd, Description
        FROM dbo.eventListings
        WHERE LOWER(eventName) = LOWER(?) AND LOWER(subGroup) = LOWER(?)
        """
        results = db_a1.execute_query(query, (event_name, subgroup), timeout=Config.SQL_QUERY_TIMEOUT)
        return results[0] if results else None
    
    @staticmethod
    def check_event_exists(event_name, subgroup):
        """
        Check if an event/subgroup combination exists.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
        
        Returns:
            True if exists, False otherwise
        """
        query = """
        SELECT COUNT(*) as count
        FROM dbo.eventListings
        WHERE LOWER(eventName) = LOWER(?) AND LOWER(subGroup) = LOWER(?)
        """
        result = db_a1.execute_query(query, (event_name, subgroup), timeout=Config.SQL_QUERY_TIMEOUT)
        return result[0]['count'] > 0 if result else False
    
    @staticmethod
    def insert_event(cursor, event_name, subgroup, event_date, monitor_start, monitor_end, description):
        """
        Insert a new event listing (within a transaction).
        
        Args:
            cursor: Database cursor (from transaction context)
            event_name: Name of the event
            subgroup: Subgroup name
            event_date: Date of the event
            monitor_start: Start date for monitoring
            monitor_end: End date for monitoring
            description: Event description
        """
        query = """
        INSERT INTO dbo.eventListings (eventName, subGroup, eventDate, monitorStart, monitorEnd, Description)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (event_name, subgroup, event_date, monitor_start, monitor_end, description))
    
    @staticmethod
    def delete_event(cursor, event_name, subgroup):
        """
        Delete an event listing (within a transaction).
        
        Args:
            cursor: Database cursor (from transaction context)
            event_name: Name of the event
            subgroup: Subgroup name
        """
        query = """
        DELETE FROM dbo.eventListings
        WHERE LOWER(eventName) = LOWER(?) AND LOWER(subGroup) = LOWER(?)
        """
        cursor.execute(query, (event_name, subgroup))

"""Repository for memberResearch table operations."""
from app.utils.database import db_a1
from config import Config


class MemberResearchRepository:
    """Data access layer for memberResearch table."""
    
    @staticmethod
    def delete_research_data(cursor, event_name, subgroup):
        """
        Delete research data for an event/subgroup (within a transaction).
        
        Args:
            cursor: Database cursor (from transaction context)
            event_name: Name of the event
            subgroup: Subgroup name
        """
        query = """
        DELETE FROM dbo.memberResearch
        WHERE LOWER(eventName) = LOWER(?) AND LOWER(subGroup) = LOWER(?)
        """
        cursor.execute(query, (event_name, subgroup))
    
    @staticmethod
    def bulk_insert_research_data(cursor, research_data):
        """
        Bulk insert research data using executemany (within a transaction).
        
        Args:
            cursor: Database cursor (from transaction context)
            research_data: List of tuples (eventName, subGroup, queueName, callDate, countOfCalls, averageTalkTime)
        """
        query = """
        INSERT INTO dbo.memberResearch (eventName, subGroup, queueName, CallDate, CountOfCalls, AverageTalkTime)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.executemany(query, research_data)

"""Service layer for event operations."""
import threading
import pandas as pd
from datetime import datetime
from app.services.event_listings_repository import EventListingsRepository
from app.services.event_accounts_repository import EventAccountsRepository
from app.services.call_history_repository import CallHistoryRepository
from app.services.member_research_repository import MemberResearchRepository
from app.utils.database import db_a1, db_b2_genesysdb, TempTableManager
from app.utils.cache import cache_manager
from config import Config


# Global lock for event submission to prevent concurrent writes
_event_submission_lock = threading.Lock()
_event_submission_timeout = 900  # 15 minutes


class EventService:
    """Business logic for event operations."""
    
    @staticmethod
    def get_events_and_subgroups():
        """
        Get all events and their subgroups.
        
        Returns:
            Dictionary with event names as keys and lists of subgroups as values
        """
        events = EventListingsRepository.get_all_events()
        
        # Group by event name
        event_dict = {}
        for event in events:
            event_name = event['eventName']
            subgroup = event['subGroup']
            
            if event_name not in event_dict:
                event_dict[event_name] = []
            
            event_dict[event_name].append({
                'subGroup': subgroup,
                'eventDate': event['eventDate'],
                'monitorStart': event['monitorStart'],
                'monitorEnd': event['monitorEnd'],
                'description': event['Description']
            })
        
        return event_dict
    
    @staticmethod
    def get_event_details(event_name, subgroup):
        """
        Get details for a specific event/subgroup.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
        
        Returns:
            Dictionary with event details
        """
        return EventListingsRepository.get_event_details(event_name, subgroup)
    
    @staticmethod
    def load_account_numbers(event_name, subgroup):
        """
        Load account numbers for an event/subgroup with caching.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
        
        Returns:
            List of account numbers
        """
        # Check cache first
        cache_key = cache_manager.make_cache_key(event_name, subgroup, 'accounts')
        cached_accounts = cache_manager.get(cache_key)
        
        if cached_accounts is not None:
            return cached_accounts
        
        # Load from database
        account_numbers = EventAccountsRepository.get_account_numbers(event_name, subgroup)
        
        # Cache the results
        cache_manager.set(cache_key, account_numbers)
        
        return account_numbers
    
    @staticmethod
    def load_call_data(event_name, subgroup, account_numbers, monitor_start, monitor_end, progress_callback=None):
        """
        Load call history data for an event/subgroup with caching.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
            account_numbers: List of account numbers
            monitor_start: Start date for monitoring
            monitor_end: End date for monitoring
            progress_callback: Optional callback function for progress updates
        
        Returns:
            List of dictionaries with call data
        """
        # Check cache first
        cache_key = cache_manager.make_cache_key(event_name, subgroup, 'raw')
        cached_data = cache_manager.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Generate unique temp table name
        temp_table_name = TempTableManager.generate_temp_table_name('accountNumbers')
        
        # Use GenesysDB connection for call history query
        with db_b2_genesysdb.transaction(timeout=Config.SQL_BULK_TIMEOUT) as (conn, cursor):
            # Create temp table
            if progress_callback:
                progress_callback(f"Creating temporary table for {len(account_numbers):,} accounts...")
            
            TempTableManager.create_account_temp_table(cursor, temp_table_name)
            
            # Insert account numbers into temp table
            if progress_callback:
                progress_callback(f"Inserting {len(account_numbers):,} account records for call history query...")
            
            insert_query = f"INSERT INTO {temp_table_name} (accountNumber) VALUES (?)"
            cursor.executemany(insert_query, [(acc,) for acc in account_numbers])
            
            # Query call history
            if progress_callback:
                progress_callback(f"Querying call history for {len(account_numbers):,} accounts from dates {monitor_start} to {monitor_end}...")
            
            call_data = CallHistoryRepository.get_call_data(temp_table_name, monitor_start, monitor_end)
            
            # Clean up temp table
            TempTableManager.drop_temp_table(cursor, temp_table_name)
        
        # Cache the results
        cache_manager.set(cache_key, call_data)
        
        return call_data
    
    @staticmethod
    def aggregate_call_data(call_data):
        """
        Aggregate call data by event, subgroup, queue, and date.
        
        Args:
            call_data: List of dictionaries with raw call data
        
        Returns:
            List of tuples (eventName, subGroup, queueName, callDate, countOfCalls, averageTalkTime)
        """
        if not call_data:
            return []
        
        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame(call_data)
        
        # Group by queueName and CallDate
        aggregated = df.groupby(['queueName', 'CallDate']).agg({
            'TalkTime': 'mean',
            'accountNumber': 'count'
        }).reset_index()
        
        # Rename columns
        aggregated.columns = ['queueName', 'CallDate', 'AverageTalkTime', 'CountOfCalls']
        
        return aggregated.to_dict('records')
    
    @staticmethod
    def get_top_queues(call_data, top_n=3):
        """
        Get top N queues by call count.
        
        Args:
            call_data: List of dictionaries with call data
            top_n: Number of top queues to return
        
        Returns:
            List of dictionaries with queue statistics
        """
        if not call_data:
            return []
        
        # Count calls by queue
        df = pd.DataFrame(call_data)
        queue_counts = df['queueName'].value_counts().head(top_n)
        total_calls = len(df)
        
        # Calculate percentages
        top_queues = []
        for queue_name, count in queue_counts.items():
            percentage = (count / total_calls) * 100
            top_queues.append({
                'queueName': queue_name,
                'callCount': int(count),
                'percentage': round(percentage, 2)
            })
        
        return top_queues
    
    @staticmethod
    def get_unique_queues(call_data):
        """
        Get list of unique queue names from call data.
        
        Args:
            call_data: List of dictionaries with call data
        
        Returns:
            Sorted list of unique queue names
        """
        if not call_data:
            return []
        
        df = pd.DataFrame(call_data)
        return sorted(df['queueName'].unique().tolist())
    
    @staticmethod
    def filter_call_data_by_queue(call_data, queue_name):
        """
        Filter call data by queue name.
        
        Args:
            call_data: List of dictionaries with call data
            queue_name: Queue name to filter by (case-insensitive)
        
        Returns:
            Filtered list of call data
        """
        if not call_data or not queue_name or queue_name.lower() == 'all':
            return call_data
        
        # Case-insensitive filtering
        return [
            call for call in call_data 
            if call['queueName'].lower() == queue_name.lower()
        ]

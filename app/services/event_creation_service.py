"""Service for creating and managing events."""
import threading
import time
from datetime import datetime
from app.services.event_listings_repository import EventListingsRepository
from app.services.event_accounts_repository import EventAccountsRepository
from app.services.call_history_repository import CallHistoryRepository
from app.services.member_research_repository import MemberResearchRepository
from app.services.event_service import EventService
from app.utils.database import db_a1, db_b2_genesysdb, TempTableManager
from app.utils.cache import cache_manager
from app.utils.csv_validator import CSVValidator
from config import Config


# Global lock for event creation to prevent concurrent writes
_event_creation_lock = threading.Lock()
_event_creation_timeout = 900  # 15 minutes


class EventCreationService:
    """Service for creating new events with transaction management."""
    
    @staticmethod
    def create_event(event_name, subgroup, event_date, monitor_start, monitor_end, 
                     description, account_numbers, progress_callback=None, 
                     overwrite_choice=None):
        """
        Create a new event with account numbers and research data.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
            event_date: Date of the event
            monitor_start: Start date for monitoring
            monitor_end: End date for monitoring
            description: Event description
            account_numbers: List of account numbers
            progress_callback: Optional callback for progress updates
            overwrite_choice: User choice if event exists ('overwrite', 'append', or 'cancel')
        
        Returns:
            Tuple of (success, message, call_data)
        """
        # Try to acquire lock with timeout
        lock_acquired = _event_creation_lock.acquire(timeout=_event_creation_timeout)
        
        if not lock_acquired:
            return False, "Another user is currently creating an event. Please try again later.", None
        
        try:
            return EventCreationService._create_event_internal(
                event_name, subgroup, event_date, monitor_start, monitor_end,
                description, account_numbers, progress_callback, overwrite_choice
            )
        finally:
            _event_creation_lock.release()
    
    @staticmethod
    def _create_event_internal(event_name, subgroup, event_date, monitor_start, monitor_end,
                               description, account_numbers, progress_callback, overwrite_choice):
        """Internal method for creating an event."""
        try:
            # Step 1: Check if event already exists
            if progress_callback:
                progress_callback("Checking if event already exists...")
            
            event_exists = EventListingsRepository.check_event_exists(event_name, subgroup)
            
            if event_exists:
                # Get count of existing account numbers
                existing_count = EventAccountsRepository.get_account_count(event_name, subgroup)
                
                if overwrite_choice is None:
                    # Return info for user to make a choice
                    return 'needs_choice', {
                        'message': f"Event '{event_name}' with subgroup '{subgroup}' already exists with {existing_count:,} account numbers.",
                        'existing_count': existing_count
                    }, None
                
                if overwrite_choice == 'cancel':
                    return False, "User cancelled: event already exists", None
            
            # Determine action based on overwrite choice
            delete_event_listing = False
            delete_accounts = False
            append_only = False
            
            if event_exists:
                if overwrite_choice == 'overwrite':
                    delete_event_listing = True
                    delete_accounts = True
                elif overwrite_choice == 'append':
                    append_only = True
            
            # Step 2: Load accounts into temp table on B2 for call history query
            if progress_callback:
                progress_callback(f"Preparing to query call history for {len(account_numbers):,} accounts...")
            
            temp_table_name = TempTableManager.generate_temp_table_name('accountNumbers')
            
            # Query call history data using temp table on B2
            with db_b2_genesysdb.transaction(timeout=Config.SQL_BULK_TIMEOUT) as (conn, cursor):
                # Create and populate temp table
                if progress_callback:
                    progress_callback(f"Creating temporary table for {len(account_numbers):,} accounts...")
                
                TempTableManager.create_account_temp_table(cursor, temp_table_name)
                
                if progress_callback:
                    progress_callback(f"Inserting {len(account_numbers):,} account records...")
                
                insert_query = f"INSERT INTO {temp_table_name} (accountNumber) VALUES (?)"
                cursor.executemany(insert_query, [(acc,) for acc in account_numbers])
                
                # Query call history
                if progress_callback:
                    progress_callback(f"Querying call history for {len(account_numbers):,} accounts from {monitor_start} to {monitor_end}...")
                
                call_data = CallHistoryRepository.get_call_data(temp_table_name, monitor_start, monitor_end)
                
                # Clean up temp table
                TempTableManager.drop_temp_table(cursor, temp_table_name)
            
            if progress_callback:
                progress_callback(f"{len(call_data):,} calls found for dates {monitor_start} to {monitor_end}. Aggregating data...")
            
            # Step 3: Aggregate call data for memberResearch
            aggregated_data = []
            if call_data:
                agg_records = EventService.aggregate_call_data(call_data)
                for record in agg_records:
                    aggregated_data.append((
                        event_name,
                        subgroup,
                        record['queueName'],
                        record['CallDate'],
                        record['CountOfCalls'],
                        record['AverageTalkTime']
                    ))
            
            # Step 4: Create temp table on A1 for account numbers
            if progress_callback:
                progress_callback("Preparing account data for insertion...")
            
            temp_accounts_table = TempTableManager.generate_temp_table_name('accountNumbersA1')
            
            # Step 5: Execute all database operations in a single transaction on A1
            with db_a1.transaction(timeout=Config.SQL_BULK_TIMEOUT) as (conn, cursor):
                if progress_callback:
                    progress_callback("Starting database transaction...")
                
                # Create temp table for accounts
                TempTableManager.create_account_temp_table(cursor, temp_accounts_table)
                
                # Insert account numbers into temp table
                insert_query = f"INSERT INTO {temp_accounts_table} (accountNumber) VALUES (?)"
                cursor.executemany(insert_query, [(acc,) for acc in account_numbers])
                
                # Delete existing event listing if needed
                if delete_event_listing:
                    if progress_callback:
                        progress_callback("Removing existing event listing...")
                    EventListingsRepository.delete_event(cursor, event_name, subgroup)
                
                # Delete existing accounts if needed
                if delete_accounts:
                    if progress_callback:
                        progress_callback("Removing existing account numbers...")
                    EventAccountsRepository.delete_accounts(cursor, event_name, subgroup)
                
                # Insert/Update event listing (only if new or overwriting)
                if not event_exists or delete_event_listing:
                    if progress_callback:
                        progress_callback("Inserting event listing...")
                    EventListingsRepository.insert_event(
                        cursor, event_name, subgroup, event_date, 
                        monitor_start, monitor_end, description
                    )
                
                # Insert account numbers from temp table
                if progress_callback:
                    progress_callback(f"Inserting {len(account_numbers):,} account numbers...")
                
                EventAccountsRepository.insert_accounts_from_temp(
                    cursor, event_name, subgroup, temp_accounts_table, append_only=append_only
                )
                
                # Delete and insert memberResearch data
                if aggregated_data:
                    if progress_callback:
                        progress_callback("Removing old research data...")
                    MemberResearchRepository.delete_research_data(cursor, event_name, subgroup)
                    
                    if progress_callback:
                        progress_callback(f"Inserting {len(aggregated_data):,} research records...")
                    MemberResearchRepository.bulk_insert_research_data(cursor, aggregated_data)
                
                # Clean up temp table
                TempTableManager.drop_temp_table(cursor, temp_accounts_table)
                
                if progress_callback:
                    progress_callback("Committing transaction...")
            
            # Step 6: Invalidate cache for this event/subgroup
            cache_manager.invalidate_event_cache(event_name, subgroup)
            
            # Step 7: Cache the call data for immediate use
            cache_key = cache_manager.make_cache_key(event_name, subgroup, 'raw')
            cache_manager.set(cache_key, call_data)
            
            if progress_callback:
                progress_callback("Event created successfully!")
            
            return True, "Event created successfully!", call_data
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
            return False, f"Failed to create event: {str(e)}", None
    
    @staticmethod
    def validate_csv_file(file_content):
        """
        Validate CSV file content for account numbers.
        
        Args:
            file_content: String content of CSV file
        
        Returns:
            Tuple of (valid, account_numbers, error_message)
        """
        return CSVValidator.validate_csv_content(file_content)
    
    @staticmethod
    def is_event_creation_in_progress():
        """
        Check if an event creation is currently in progress.
        
        Returns:
            True if locked, False otherwise
        """
        # Try to acquire lock without blocking
        acquired = _event_creation_lock.acquire(blocking=False)
        if acquired:
            _event_creation_lock.release()
            return False
        return True

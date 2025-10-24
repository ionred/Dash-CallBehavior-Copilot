# Dash Call Behavior Analysis Application

A Flask/Dash application for monitoring and analyzing call behavior data associated with events and account subgroups.

## Features

- **Event Management**: Create and manage events with associated account subgroups
- **Call Data Analysis**: Query and visualize call history data from SQL Server
- **Interactive Visualizations**: Line charts and bar charts for call volume analysis
- **Queue Filtering**: Filter call data by queue name
- **Top Queue Statistics**: View top 3 queues by call volume
- **CSV Upload**: Bulk upload account numbers via CSV
- **Caching**: FileSystem and Redis caching support for improved performance
- **Concurrent User Support**: Thread-safe operations with proper locking
- **Transaction Management**: Rollback support for failed operations

## Requirements

- Python 3.8+
- Microsoft SQL Server with ODBC Driver 17
- Access to the following databases:
  - Server A1: MyLocalData (eventListings, eventAccounts, memberResearch)
  - Server B2: GenesysDB (callHistory), TempDB (temporary tables)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Dash-CallBehavior-Copilot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database connection details
```

## Configuration

Edit the `.env` file with your database connection settings:

```
# Database A1 - MyLocalData
DB_A1_SERVER=A1
DB_A1_DATABASE=MyLocalData
DB_A1_TRUSTED=yes

# Database B2 - GenesysDB and TempDB
DB_B2_SERVER=B2
DB_B2_TEMPDB=TempDB
DB_B2_GENESYSDB=GenesysDB
DB_B2_TRUSTED=yes

# Query Timeouts
SQL_QUERY_TIMEOUT=300
SQL_BULK_TIMEOUT=600

# Cache Settings
CACHE_TYPE=filesystem  # or 'redis'
CACHE_DIR=cache
CACHE_DEFAULT_TIMEOUT=3600
```

## Running the Application

### Development Mode (Local)

Using Dash's built-in server:
```bash
python app/main.py
```

Using uvicorn:
```bash
uvicorn run:application --host 0.0.0.0 --port 8000 --reload
```

Or directly with Python:
```bash
python run.py
```

### Production Mode (IIS with httpPlatformHandler)

1. Install the application files on your IIS server
2. Ensure the virtual environment is created and dependencies installed
3. Configure `web.config` with the correct paths
4. The httpPlatformHandler will launch uvicorn automatically

## Usage

### Main Page

1. **Select Event and Subgroup**: Use the dropdowns to choose an event and subgroup
2. **Load Data**: Click "Load Data" to fetch call history for the selected event
3. **View Results**: 
   - Description card shows event details
   - Top 3 Queues card displays the most active queues
   - Line and bar charts visualize call volume over time
4. **Filter by Queue**: Use the queue dropdown to filter visualizations
5. **Clear Data**: Click "Clear Data" to reset selections and hide visualizations

### Creating a New Event

1. Click "Create New Event" button
2. Fill in all required fields:
   - Event Name
   - Subgroup
   - Event Date
   - Monitor Start Date
   - Monitor End Date
   - Description
3. Upload a CSV file with account numbers (one column, one number per row)
4. Click "Submit" to create the event

If the event already exists, you'll be prompted to:
- **Overwrite**: Replace the existing event and all account numbers
- **Append**: Keep existing event details and add new account numbers
- **Cancel**: Cancel the operation

## CSV File Format

The CSV file for account numbers should have:
- One column
- One account number per row
- Optional header row (will be automatically detected and skipped)
- Account numbers should contain only digits
- Maximum 15 characters per account number

Example:
```
accountNumber
000011111
123456
789012
```

## Architecture

### Project Structure
```
Dash-CallBehavior-Copilot/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main Dash application
│   ├── components/          # UI components and callbacks
│   │   ├── __init__.py
│   │   ├── layout.py        # Main layout
│   │   ├── callbacks.py     # Main page callbacks
│   │   └── modal_callbacks.py  # Event creation callbacks
│   ├── services/            # Business logic layer
│   │   ├── event_service.py
│   │   ├── event_creation_service.py
│   │   ├── event_listings_repository.py
│   │   ├── event_accounts_repository.py
│   │   ├── call_history_repository.py
│   │   └── member_research_repository.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── cache.py         # Caching utilities
│       ├── database.py      # Database connections
│       └── csv_validator.py # CSV validation
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── static/                  # Static assets
│   ├── css/
│   └── js/
├── cache/                   # FileSystem cache directory
├── .env                     # Environment variables (not in repo)
├── .env.example            # Example environment variables
├── requirements.txt        # Python dependencies
├── run.py                  # Uvicorn entry point
├── web.config             # IIS configuration
└── README.md
```

### Database Tables

#### eventListings (Server A1, MyLocalData)
- eventName
- subGroup
- eventDate
- monitorStart
- monitorEnd
- Description

#### eventAccounts (Server A1, MyLocalData)
- eventName
- subGroup
- accountNumber (nvarchar(15))

#### callHistory (Server B2, GenesysDB)
- accountNumber
- queueName
- TalkTime
- CallDate

#### memberResearch (Server A1, MyLocalData)
- eventName
- subGroup
- queueName
- CallDate
- CountOfCalls
- AverageTalkTime

#### #accountNumbers (Server B2, TempDB - Temporary)
- accountNumber (nvarchar(15))

## Features and Best Practices

### Caching
- FileSystem cache by default (can switch to Redis)
- Shared cache across users
- Automatic invalidation on event updates
- Cache keys include event name and subgroup

### Concurrency
- Thread-safe event creation with global lock
- Unique temporary table names to avoid collisions
- Transaction management with rollback support
- Timeout protection (15 minutes for event creation)

### Performance
- Bulk insert operations using executemany
- Temporary tables for large dataset operations
- Minimized table locking with deferred commits
- Efficient aggregation using pandas

### Error Handling
- Query timeout protection
- Detailed CSV validation with row-level errors
- Transaction rollback on failures
- User-friendly error messages

## Troubleshooting

### Connection Issues
- Verify ODBC Driver 17 for SQL Server is installed
- Check database connection strings in `.env`
- Ensure Trusted Authentication is configured correctly

### Performance Issues
- Increase query timeouts in `.env` if needed
- Consider switching to Redis cache for better performance
- Check database indexes on eventName, subGroup, and accountNumber fields

### Concurrent User Issues
- Event creation is locked to prevent conflicts
- If stuck, wait for the 15-minute timeout or restart the application
- Check logs for detailed error messages
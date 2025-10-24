# Application Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         Dash/React Frontend (JavaScript)                │     │
│  │  - Event/Subgroup Dropdowns                             │     │
│  │  - Charts (Plotly)                                      │     │
│  │  - Cards (Description, Top Queues)                      │     │
│  │  - Create Event Modal                                   │     │
│  └───────────────────────┬────────────────────────────────┘     │
└────────────────────────────┼───────────────────────────────────┘
                             │ HTTP/WebSocket
                             │
┌────────────────────────────┼───────────────────────────────────┐
│                IIS + httpPlatformHandler                         │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               Uvicorn ASGI Server                        │   │
│  └─────────────────────┬───────────────────────────────────┘   │
└────────────────────────┼─────────────────────────────────────┘
                         │
┌────────────────────────┼─────────────────────────────────────┐
│                Flask/Dash Application                            │
│                        ▼                                         │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              app/components/                          │      │
│  │  - layout.py (UI Structure)                           │      │
│  │  - callbacks.py (Main Page Logic)                     │      │
│  │  - modal_callbacks.py (Event Creation)                │      │
│  └────────────┬─────────────────────────────────────────┘      │
│               │                                                  │
│  ┌────────────▼─────────────────────────────────────────┐      │
│  │              app/services/                            │      │
│  │  - EventService (Business Logic)                      │      │
│  │  - EventCreationService (Event Creation)              │      │
│  │  - *Repository (Data Access Layer)                    │      │
│  └────────────┬─────────────────────────────────────────┘      │
│               │                                                  │
│  ┌────────────▼─────────────────────────────────────────┐      │
│  │              app/utils/                               │      │
│  │  - database.py (DB Connections)                       │      │
│  │  - cache.py (Cache Manager)                           │      │
│  │  - csv_validator.py (CSV Validation)                  │      │
│  └────────────┬─────────────────────────────────────────┘      │
└───────────────┼──────────────────────────────────────────────┘
                │
       ┌────────┴────────┐
       ▼                 ▼
┌────────────┐    ┌────────────┐
│   Cache    │    │  Database  │
│            │    │            │
│ FileSystem │    │ SQL Server │
│    or      │    │            │
│   Redis    │    │  Server A1 │
│            │    │  Server B2 │
└────────────┘    └────────────┘
```

## Data Flow

### Load Data Workflow

```
1. User Interaction
   ├─> Select Event Name → Populate Subgroups
   ├─> Select Subgroup → Enable Load Data Button
   └─> Click Load Data

2. Server Processing
   ├─> Check Cache (cache_manager.get)
   │   └─> If cached: Return immediately
   │
   └─> If not cached:
       ├─> Get Event Details (eventListings)
       ├─> Get Account Numbers (eventAccounts)
       │   └─> Cache account numbers
       │
       ├─> Create Temp Table on B2
       ├─> Insert Accounts to Temp Table
       ├─> Query Call History (callHistory JOIN temp)
       ├─> Drop Temp Table
       └─> Cache raw call data

3. Client Rendering
   ├─> Populate Description Card
   ├─> Calculate Top 3 Queues
   ├─> Populate Queue Dropdown
   ├─> Render Line Chart (call volume over time)
   └─> Render Bar Chart (calls by date)
```

### Create Event Workflow

```
1. User Input
   ├─> Fill Event Details (name, subgroup, dates, description)
   ├─> Upload CSV File
   └─> CSV Validation
       ├─> Check structure (1 column)
       ├─> Check for header
       ├─> Validate digits only
       ├─> Check for duplicates
       └─> Return validated account numbers

2. Existence Check
   ├─> Query eventListings for existing event
   └─> If exists:
       ├─> Get account count
       └─> Show choice modal:
           ├─> Overwrite (delete existing)
           ├─> Append (merge accounts)
           └─> Cancel

3. Transaction Processing (with lock)
   ├─> Acquire Global Lock (15 min timeout)
   │
   ├─> Create Temp Table on B2
   ├─> Insert Accounts to Temp Table
   ├─> Query Call History
   ├─> Drop Temp Table on B2
   │
   ├─> Aggregate Call Data (pandas)
   │   └─> Group by queue, date
   │
   ├─> Begin Transaction on A1
   │   ├─> Create Temp Table for Accounts
   │   ├─> Insert Accounts to Temp
   │   │
   │   ├─> Delete existing (if overwrite)
   │   ├─> Insert/Update eventListings
   │   ├─> Insert Accounts (merge if append)
   │   │
   │   ├─> Delete old memberResearch
   │   ├─> Insert new memberResearch
   │   │
   │   └─> COMMIT
   │
   ├─> Invalidate Cache
   ├─> Cache new call data
   └─> Release Lock

4. Client Response
   ├─> Close Modal
   ├─> Set Event Dropdowns
   ├─> Display Call Data
   └─> Render Charts
```

## Database Schema Relationships

```
┌──────────────────────┐
│   eventListings      │
│  (Server A1)         │
├──────────────────────┤
│ PK: eventName        │◄─────┐
│     subGroup         │      │
├──────────────────────┤      │
│     eventDate        │      │
│     monitorStart     │      │
│     monitorEnd       │      │
│     Description      │      │
└──────────────────────┘      │
                              │
                              │ Foreign Key
┌──────────────────────┐      │ Relationship
│   eventAccounts      │      │
│  (Server A1)         │      │
├──────────────────────┤      │
│ PK: eventName        │──────┘
│     subGroup         │
│     accountNumber    │──────┐
└──────────────────────┘      │
                              │
                              │ Join for
┌──────────────────────┐      │ Call Data
│   callHistory        │      │
│  (Server B2)         │      │
├──────────────────────┤      │
│     accountNumber    │◄─────┘
│     queueName        │
│     TalkTime         │
│     CallDate         │
└──────────────────────┘
         │
         │ Aggregated
         ▼
┌──────────────────────┐
│   memberResearch     │
│  (Server A1)         │
├──────────────────────┤
│ PK: eventName        │
│     subGroup         │
│     queueName        │
│     CallDate         │
├──────────────────────┤
│     CountOfCalls     │
│     AverageTalkTime  │
└──────────────────────┘
```

## Caching Strategy

```
Cache Keys Pattern:
  {data_type}:{event_name_lower}:{subgroup_lower}

Cache Types:
  - "accounts" → List of account numbers
  - "raw" → Raw call data (list of dicts)
  - "aggregated" → Aggregated research data

Cache Invalidation:
  - On event creation (all types)
  - On event overwrite (all types)
  - On account append (accounts type)

Cache Backends:
  - FileSystem (default) → cache/ directory
  - Redis (optional) → Commented in code
```

## Concurrency & Locking

```
Event Creation Lock:
┌─────────────────────────────────────┐
│  Global Lock (_event_creation_lock) │
│  Timeout: 15 minutes                │
├─────────────────────────────────────┤
│  Prevents:                           │
│  - Race conditions                   │
│  - Duplicate inserts                 │
│  - Conflicting transactions          │
├─────────────────────────────────────┤
│  When Acquired:                      │
│  - Before any DB writes              │
│  - Held through entire transaction   │
│  - Released after commit/rollback    │
└─────────────────────────────────────┘

Temp Table Naming:
  #{base_name}_{uuid_8chars}
  Example: #accountNumbers_a1b2c3d4

  Prevents collisions between:
  - Multiple users
  - Multiple sessions
  - Concurrent requests
```

## Error Handling

```
Query Timeouts:
  - SQL_QUERY_TIMEOUT: 300 seconds (default)
  - SQL_BULK_TIMEOUT: 600 seconds (bulk inserts)
  - Raises: TimeoutError with details

Transaction Rollback:
  - On any exception during transaction
  - Automatic via context manager
  - Lock is released even on error

CSV Validation Errors:
  - Empty file
  - Wrong column count
  - Non-digit characters (with row number)
  - Exceeds max length (with row number)
  - Duplicate entries

Database Connection Errors:
  - ODBC driver not installed
  - Server unreachable
  - Authentication failure
  - Database not found
```

## Performance Optimizations

1. **Bulk Operations**
   - executemany for inserts
   - Temp tables for large joins
   - Single transaction for multiple operations

2. **Caching**
   - Account numbers cached per event/subgroup
   - Raw call data cached per event/subgroup
   - Shared cache across users

3. **Indexes** (Recommended)
   ```sql
   -- eventListings
   CREATE INDEX IX_eventListings_eventName ON eventListings(eventName);
   
   -- eventAccounts
   CREATE INDEX IX_eventAccounts_event 
   ON eventAccounts(eventName, subGroup) INCLUDE (accountNumber);
   
   -- callHistory
   CREATE INDEX IX_callHistory_account_date 
   ON callHistory(accountNumber, CallDate) INCLUDE (queueName, TalkTime);
   ```

4. **Data Transfer**
   - Raw data stored server-side only
   - Only aggregated data sent to client
   - Charts rendered from filtered subsets

## Security Considerations

1. **SQL Injection Protection**
   - Parameterized queries throughout
   - No string concatenation for SQL

2. **Authentication**
   - Trusted Authentication (Windows)
   - No credentials in code

3. **Input Validation**
   - CSV validation before processing
   - Date validation
   - Length checks on strings

4. **Transaction Isolation**
   - Proper transaction boundaries
   - Rollback on failure
   - Lock timeout protection

## Deployment Configurations

### Development
```bash
python run.py
# or
uvicorn run:application --reload
```

### Production (IIS)
```xml
<httpPlatform processPath="uvicorn.exe"
              arguments="run:application --host 0.0.0.0 --port %HTTP_PLATFORM_PORT%"
              stdoutLogEnabled="true"
              requestTimeout="00:04:00">
</httpPlatform>
```

### Environment Variables
```
DB_A1_SERVER=ProductionServer1
DB_B2_SERVER=ProductionServer2
CACHE_TYPE=redis
REDIS_HOST=cache-server
DEBUG=False
```

# Quick Start Guide

## Prerequisites

Before running the application, ensure you have:

1. **Python 3.8 or higher** installed
2. **Microsoft SQL Server ODBC Driver 17** installed
   - Windows: Download from Microsoft
   - Linux: `sudo apt-get install msodbcsql17` or equivalent
3. **Access to required databases:**
   - Server A1: MyLocalData database
   - Server B2: GenesysDB and TempDB databases
4. **Database tables created:**
   - `dbo.eventListings` on A1/MyLocalData
   - `dbo.eventAccounts` on A1/MyLocalData
   - `dbo.memberResearch` on A1/MyLocalData
   - `dbo.callHistory` on B2/GenesysDB

## Installation Steps

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd Dash-CallBehavior-Copilot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your database settings
# Use your favorite text editor
nano .env  # or vim, code, notepad, etc.
```

**Important Settings in .env:**
```
# Update these with your actual SQL Server names
DB_A1_SERVER=YourServerA1Name
DB_B2_SERVER=YourServerB2Name

# Adjust timeouts if needed (in seconds)
SQL_QUERY_TIMEOUT=300
SQL_BULK_TIMEOUT=600

# Cache type: filesystem or redis
CACHE_TYPE=filesystem
```

### 3. Verify Installation

```bash
# Run the verification script
python verify.py
```

This will check:
- ✓ All required files are present
- ✓ Python syntax is correct
- ✓ Dependencies are installed

### 4. Run the Application

**Development Mode (recommended for first run):**
```bash
python run.py
```

The application will start at `http://localhost:8000`

**Alternative: Using uvicorn directly:**
```bash
uvicorn run:application --host 0.0.0.0 --port 8000 --reload
```

**Alternative: Using Dash's built-in server:**
```bash
python app/main.py
```

## First Time Usage

### 1. Verify Database Connection

When you first load the application:
- Click the "Refresh" button (↻ icon)
- If events load in the dropdown, database connection is working!
- If you see errors, check your `.env` settings

### 2. Create Your First Event

1. Click "Create New Event"
2. Fill in the form:
   - Event Name: e.g., "Website Launch"
   - Subgroup: e.g., "Beta Users"
   - Event Date: Select the event date
   - Monitor Start: Start of monitoring period
   - Monitor End: End of monitoring period
   - Description: Event details
3. Upload CSV with account numbers
4. Click Submit

**CSV File Example:**
```csv
accountNumber
000011111
123456
789012
```

### 3. Load and View Data

1. Select an event from the dropdown
2. Select a subgroup (auto-selects if only one)
3. Click "Load Data"
4. View the results:
   - Description card
   - Top 3 Queues
   - Line chart (call volume over time)
   - Bar chart (calls by date)
5. Use Queue filter to focus on specific queues

## Database Schema

### eventListings Table
```sql
CREATE TABLE dbo.eventListings (
    eventName NVARCHAR(100) NOT NULL,
    subGroup NVARCHAR(100) NOT NULL,
    eventDate DATE NOT NULL,
    monitorStart DATE NOT NULL,
    monitorEnd DATE NOT NULL,
    Description NVARCHAR(500),
    PRIMARY KEY (eventName, subGroup)
);

CREATE INDEX IX_eventListings_eventName ON dbo.eventListings(eventName);
```

### eventAccounts Table
```sql
CREATE TABLE dbo.eventAccounts (
    eventName NVARCHAR(100) NOT NULL,
    subGroup NVARCHAR(100) NOT NULL,
    accountNumber NVARCHAR(15) NOT NULL,
    PRIMARY KEY (eventName, subGroup, accountNumber)
);

CREATE INDEX IX_eventAccounts_eventName_subGroup 
ON dbo.eventAccounts(eventName, subGroup) 
INCLUDE (accountNumber);
```

### memberResearch Table
```sql
CREATE TABLE dbo.memberResearch (
    eventName NVARCHAR(100) NOT NULL,
    subGroup NVARCHAR(100) NOT NULL,
    queueName NVARCHAR(100) NOT NULL,
    CallDate DATE NOT NULL,
    CountOfCalls INT NOT NULL,
    AverageTalkTime FLOAT,
    PRIMARY KEY (eventName, subGroup, queueName, CallDate)
);
```

### callHistory Table (Already exists on B2/GenesysDB)
```sql
-- Should have columns:
-- accountNumber NVARCHAR(15)
-- queueName NVARCHAR(100)
-- TalkTime FLOAT
-- CallDate DATE

-- Recommended index for performance:
CREATE INDEX IX_callHistory_accountNumber_CallDate 
ON dbo.callHistory(accountNumber, CallDate) 
INCLUDE (queueName, TalkTime);
```

## Common Issues

### "Module not found" errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "Cannot connect to database"
- Verify ODBC Driver 17 is installed
- Check server names in `.env`
- Ensure Trusted Authentication is configured
- Test SQL Server connection with another tool (SSMS, Azure Data Studio)

### "Query timeout" errors
- Increase timeout values in `.env`
- Check database indexes on account numbers
- Verify network connectivity to SQL Server

### Application won't start
```bash
# Check for syntax errors
python verify.py

# View detailed error messages
python run.py
```

## Production Deployment (IIS)

For production deployment on IIS:

1. Install httpPlatformHandler on IIS
2. Copy application files to IIS directory
3. Create virtual environment and install dependencies
4. Update `web.config` with correct paths
5. Configure IIS site to use the application directory
6. Ensure IIS application pool has database access

See `web.config` for IIS configuration details.

## Support

For issues or questions:
1. Check the main README.md for detailed documentation
2. Review error messages in the console/logs
3. Verify database connectivity and structure
4. Check that all dependencies are installed

## Next Steps

Once the application is running:
- Create sample events to test functionality
- Upload test CSV files with account numbers
- Load data and explore visualizations
- Test queue filtering
- Verify cache performance with multiple loads

Happy analyzing! 🎉

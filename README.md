This script Summerizes a Excel file Company List data , Cleans it and outputs a Summary file into a folder.
# 🤝 HubSpot Expired Quotes → Snowflake ETL Pipeline

## Overview
A Python-based ETL pipeline that extracts expired and closed-lost quotes from **HubSpot CRM** and loads them into **Snowflake** for analytics and reporting. Built to help sales teams analyze deal loss patterns and quote conversion rates.

## Features
- **HubSpot CRM Integration** — pulls deals via HubSpot v3 Search API
- **Expired/Closed-Lost Filter** — targets specific deal stages representing dead quotes
- **Upsert Logic** — MERGE statement prevents duplicates on re-runs
- **Full Payload Storage** — raw JSON stored as Snowflake VARIANT for flexibility
- **Pagination Handling** — automatically handles large deal volumes
- **Secure Credentials** — environment variables via `.env` file

## Architecture
HubSpot CRM (Deals API)
↓
Python ETL Script (hubspot_expired_quotes.py)
↓
Snowflake → CLAUDE_PROJECTS.CRM.HUBSPOT_EXPIRED_QUOTES
## Tech Stack
- **Python** 3.10+
- **HubSpot CRM API** v3
- **Snowflake** — Cloud data warehouse
- **Pandas** — Data manipulation
- **python-dotenv** — Secure credential management

## Project Structure
## Tech Stack
- **Python** 3.10+
- **HubSpot CRM API** v3
- **Snowflake** — Cloud data warehouse
- **Pandas** — Data manipulation
- **python-dotenv** — Secure credential management

## Project Structure
hubspot_quotes(ClosedLost)/
├── hubspot_expired_quotes.py   # Main ETL pipeline script
├── analyze_inc5000.py          # Inc 5000 analysis script
├── requirements.txt            # Python dependencies
└── .gitignore                  # Excludes .env and sensitive files
## Snowflake Table Schema
```sql
CREATE TABLE HUBSPOT_EXPIRED_QUOTES (
    DEAL_ID           VARCHAR(50)    NOT NULL,
    DEAL_NAME         VARCHAR(500),
    AMOUNT            FLOAT,
    DEAL_STAGE        VARCHAR(200),
    PIPELINE          VARCHAR(200),
    CLOSE_DATE        TIMESTAMP_TZ,
    CREATE_DATE       TIMESTAMP_TZ,
    LAST_MODIFIED     TIMESTAMP_TZ,
    OWNER_ID          VARCHAR(100),
    STAGE_PROBABILITY FLOAT,
    DESCRIPTION       VARCHAR(5000),
    RAW_JSON          VARIANT,
    EXTRACTED_AT      TIMESTAMP_TZ  NOT NULL,
    PRIMARY KEY (DEAL_ID)
)
```

## Setup

### Prerequisites
- Python 3.10+
- HubSpot account with Private App access
- Snowflake account

### Installation
```bash
pip install requests snowflake-connector-python python-dotenv
```

### HubSpot Private App Setup
1. Go to HubSpot → Settings → Integrations → Private Apps
2. Click **Create a Private App**
3. Grant `crm.objects.deals.read` permission
4. Copy the token (starts with `pat-na1-...`)

### Configuration
Create a `.env` file in the project root:
## Snowflake Table Schema
```sql
CREATE TABLE HUBSPOT_EXPIRED_QUOTES (
    DEAL_ID           VARCHAR(50)    NOT NULL,
    DEAL_NAME         VARCHAR(500),
    AMOUNT            FLOAT,
    DEAL_STAGE        VARCHAR(200),
    PIPELINE          VARCHAR(200),
    CLOSE_DATE        TIMESTAMP_TZ,
    CREATE_DATE       TIMESTAMP_TZ,
    LAST_MODIFIED     TIMESTAMP_TZ,
    OWNER_ID          VARCHAR(100),
    STAGE_PROBABILITY FLOAT,
    DESCRIPTION       VARCHAR(5000),
    RAW_JSON          VARIANT,
    EXTRACTED_AT      TIMESTAMP_TZ  NOT NULL,
    PRIMARY KEY (DEAL_ID)
)
```

## Setup

### Prerequisites
- Python 3.10+
- HubSpot account with Private App access
- Snowflake account

### Installation
```bash
pip install requests snowflake-connector-python python-dotenv
```

### HubSpot Private App Setup
1. Go to HubSpot → Settings → Integrations → Private Apps
2. Click **Create a Private App**
3. Grant `crm.objects.deals.read` permission
4. Copy the token (starts with `pat-na1-...`)

### Configuration
Create a `.env` file in the project root:

HUBSPOT_TOKEN=pat-na1-your-token-here
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=CRM
SNOWFLAKE_WAREHOUSE=your_warehouse

> **Never commit your `.env` file** — it's excluded via `.gitignore`

### Running the Pipeline
```bash
python hubspot_expired_quotes.py
```

**Expected output:**

HubSpot Expired Quotes → Snowflake Extractor
Fetching deals in stages: ['closedlost']
Fetched 100 deals (total so far: 100)
Total deals retrieved: 243
Upserting 243 rows...
Done. 243 upserted, 0 errors.
### Verify in Snowflake
```sql
SELECT * FROM HUBSPOT_EXPIRED_QUOTES 
ORDER BY EXTRACTED_AT DESC 
LIMIT 20;
```

## How the Upsert Works
The pipeline uses a Snowflake `MERGE` statement:
- **Existing deal_id** → updates all fields with latest HubSpot data
- **New deal_id** → inserts as a new row
- **Result** → safe to re-run without creating duplicates

## Customizing Deal Stages
Update `EXPIRED_STAGES` in the script to match your HubSpot pipeline:
```python
EXPIRED_STAGES = [
    "closedlost",      # standard lost stage
    "your_custom_stage_id",  # add your pipeline stage IDs
]
```
Find your stage IDs in HubSpot → Settings → Objects → Deals → Pipelines.

## License
This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](https://creativecommons.org/licenses/by-nc/4.0/).

© 2026 oping000 (ODell)




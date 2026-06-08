"""
HubSpot Expired Quotes Extractor → Snowflake
=============================================
Pulls deals from HubSpot that represent expired/closed quotes
and loads them into a Snowflake table.

Setup:
  pip install requests snowflake-connector-python python-dotenv

Required .env variables:
  HUBSPOT_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  SNOWFLAKE_ACCOUNT=AMMHYRO-HC82184
  SNOWFLAKE_USER=your_user
  SNOWFLAKE_PASSWORD=your_password
  SNOWFLAKE_DATABASE=CLAUDE_PROJECTS
  SNOWFLAKE_SCHEMA=CRM
  SNOWFLAKE_WAREHOUSE=your_warehouse
"""

import os
import json
import requests
import snowflake.connector
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ── HubSpot Config ──────────────────────────────────────────────────────────

HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
HUBSPOT_BASE  = "https://api.hubapi.com"

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type":  "application/json",
}

# Deal stages that represent expired / dead quotes.
# Go to HubSpot → Settings → Deals → Pipeline to find your exact stage IDs.
# Common defaults listed here — update to match your pipeline.
EXPIRED_STAGES = [
    "closedlost",           # standard lost stage
    "decisionmakerbuyin",   # sometimes used for stalled deals
    # Add your custom stage IDs here, e.g. "expired_quote_stage_id"
]

# Properties to pull for each deal
DEAL_PROPERTIES = [
    "dealname",
    "amount",
    "dealstage",
    "closedate",
    "createdate",
    "hs_lastmodifieddate",
    "hubspot_owner_id",
    "pipeline",
    "hs_deal_stage_probability",
    "description",
]


# ── HubSpot API Helpers ─────────────────────────────────────────────────────

def fetch_all_deals(stages: list[str]) -> list[dict]:
    """
    Pull all deals matching the given stage IDs using the v3 Search API.
    Handles pagination automatically.
    """
    url    = f"{HUBSPOT_BASE}/crm/v3/objects/deals/search"
    deals  = []
    after  = None   # cursor for pagination

    print(f"Fetching deals in stages: {stages}")

    while True:
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "dealstage",
                            "operator":     "IN",
                            "values":       stages,
                        }
                    ]
                }
            ],
            "properties": DEAL_PROPERTIES,
            "limit":      100,  # max per page
        }

        if after:
            payload["after"] = after

        resp = requests.post(url, headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        deals.extend(results)
        print(f"  Fetched {len(results)} deals (total so far: {len(deals)})")

        paging = data.get("paging", {})
        after  = paging.get("next", {}).get("after")
        if not after:
            break

    print(f"Total deals retrieved: {len(deals)}")
    return deals


def get_deal_associations(deal_id: str) -> dict:
    """
    Fetch associated contacts and companies for a deal (optional enrichment).
    """
    url  = f"{HUBSPOT_BASE}/crm/v3/objects/deals/{deal_id}/associations/contacts"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("results", [])
    return []


def normalize_deal(deal: dict) -> dict:
    """
    Flatten a HubSpot deal object into a clean row dict for Snowflake.
    """
    props = deal.get("properties", {})

    def safe_float(val):
        try:
            return float(val) if val else None
        except (ValueError, TypeError):
            return None

    def safe_ts(val):
        """Convert ISO timestamp string to Python datetime."""
        if not val:
            return None
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return None

    return {
        "deal_id":           deal.get("id"),
        "deal_name":         props.get("dealname"),
        "amount":            safe_float(props.get("amount")),
        "deal_stage":        props.get("dealstage"),
        "pipeline":          props.get("pipeline"),
        "close_date":        safe_ts(props.get("closedate")),
        "create_date":       safe_ts(props.get("createdate")),
        "last_modified":     safe_ts(props.get("hs_lastmodifieddate")),
        "owner_id":          props.get("hubspot_owner_id"),
        "stage_probability": safe_float(props.get("hs_deal_stage_probability")),
        "description":       props.get("description"),
        "raw_json":          json.dumps(props),  # keep full payload for reference
        "extracted_at":      datetime.now(timezone.utc),
    }


# ── Snowflake Helpers ───────────────────────────────────────────────────────

def get_snowflake_conn():
    return snowflake.connector.connect(
        account   = os.getenv("SNOWFLAKE_ACCOUNT"),
        user      = os.getenv("SNOWFLAKE_USER"),
        password  = os.getenv("SNOWFLAKE_PASSWORD"),
        database  = os.getenv("SNOWFLAKE_DATABASE"),
        schema    = os.getenv("SNOWFLAKE_SCHEMA"),
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE"),
    )


DDL = """
CREATE TABLE IF NOT EXISTS HUBSPOT_EXPIRED_QUOTES (
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
"""

UPSERT = """
MERGE INTO HUBSPOT_EXPIRED_QUOTES AS target
USING (SELECT %s AS deal_id) AS source
  ON target.DEAL_ID = source.deal_id
WHEN MATCHED THEN UPDATE SET
    DEAL_NAME         = %s,
    AMOUNT            = %s,
    DEAL_STAGE        = %s,
    PIPELINE          = %s,
    CLOSE_DATE        = %s,
    CREATE_DATE       = %s,
    LAST_MODIFIED     = %s,
    OWNER_ID          = %s,
    STAGE_PROBABILITY = %s,
    DESCRIPTION       = %s,
    RAW_JSON          = PARSE_JSON(%s),
    EXTRACTED_AT      = %s
WHEN NOT MATCHED THEN INSERT (
    DEAL_ID, DEAL_NAME, AMOUNT, DEAL_STAGE, PIPELINE,
    CLOSE_DATE, CREATE_DATE, LAST_MODIFIED, OWNER_ID,
    STAGE_PROBABILITY, DESCRIPTION, RAW_JSON, EXTRACTED_AT
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, PARSE_JSON(%s), %s)
"""


def load_to_snowflake(rows: list[dict]):
    """
    Upsert rows into Snowflake. Existing deal_ids are updated; new ones inserted.
    """
    conn = get_snowflake_conn()
    cur  = conn.cursor()

    print("\nConnected to Snowflake. Creating schema and table if needed...")
    cur.execute("CREATE SCHEMA IF NOT EXISTS CRM")
    cur.execute(DDL)

    print(f"Upserting {len(rows)} rows...")
    success = 0
    errors  = 0

    for row in rows:
        try:
            cur.execute(UPSERT, (
                # WHEN MATCHED → UPDATE
                row["deal_id"],
                row["deal_name"], row["amount"], row["deal_stage"],
                row["pipeline"], row["close_date"], row["create_date"],
                row["last_modified"], row["owner_id"],
                row["stage_probability"], row["description"],
                row["raw_json"], row["extracted_at"],
                # WHEN NOT MATCHED → INSERT
                row["deal_id"], row["deal_name"], row["amount"],
                row["deal_stage"], row["pipeline"], row["close_date"],
                row["create_date"], row["last_modified"], row["owner_id"],
                row["stage_probability"], row["description"],
                row["raw_json"], row["extracted_at"],
            ))
            success += 1
        except Exception as e:
            print(f"  ERROR on deal {row.get('deal_id')}: {e}")
            errors += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone. {success} upserted, {errors} errors.")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  HubSpot Expired Quotes → Snowflake Extractor")
    print("=" * 55)

    # 1. Pull deals from HubSpot
    raw_deals = fetch_all_deals(EXPIRED_STAGES)

    if not raw_deals:
        print("No expired deals found. Check your stage IDs in EXPIRED_STAGES.")
        return

    # 2. Normalize
    rows = [normalize_deal(d) for d in raw_deals]

    # 3. Preview first 3
    print("\nSample rows:")
    for r in rows[:3]:
        print(f"  {r['deal_id']} | {r['deal_name']} | ${r['amount']} | {r['deal_stage']}")

    # 4. Load to Snowflake
    load_to_snowflake(rows)

    print("\nQuery to verify:")
    print("  SELECT * FROM HUBSPOT_EXPIRED_QUOTES ORDER BY EXTRACTED_AT DESC LIMIT 20;")


if __name__ == "__main__":
    main()

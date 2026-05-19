import os
import sys

import pandas as pd
from sqlalchemy import create_engine

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import DB_URI


def seed_historic_data():
    csv_path = os.path.join("data", "unusual_query_detection_dataset_1200_rows (1).csv")

    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV not found at {csv_path}")
        return

    print(f"📖 Reading {csv_path}...")
    df = pd.read_csv(csv_path)

    # Standardize column names to match the new MySQL schema
    column_mapping = {
        "unusual_query_flag": "anomaly_flag",
        "table_accessed": "table_accessed",
        "query_type": "query_type",
    }

    # Ensure all required columns exist
    required_cols = [
        "timestamp",
        "user_id",
        "table_accessed",
        "query_type",
        "rows_returned",
        "after_hours_access",
        "sensitive_data_access",
        "failed_login_attempt",
        "total_queries_session",
        "data_exfiltration_pattern",
        "anomaly_flag",
    ]

    # Rename if necessary
    if "unusual_query_flag" in df.columns:
        df = df.rename(columns={"unusual_query_flag": "anomaly_flag"})

    # Add dummy query_text if missing
    if "query_text" not in df.columns:
        df["query_text"] = "HISTORIC DATA IMPORT"

    try:
        engine = create_engine(DB_URI)
        print("🔗 Connecting to MySQL...")

        # We append so we don't delete any live logs already there
        df[required_cols + ["query_text"]].to_sql(
            "query_monitoring", engine, if_exists="append", index=False
        )

        print(f"✅ SUCCESS: {len(df)} rows imported into 'query_monitoring' table.")
        print("🚀 Your dashboard should now show all 40 users!")

    except Exception as e:
        print(f"❌ Database Error: {e}")


if __name__ == "__main__":
    seed_historic_data()

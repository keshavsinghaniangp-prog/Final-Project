import os
import re
import sys
import time
from datetime import datetime, timedelta

import joblib
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    from watchdog.observers.polling import PollingObserver
except ImportError:
    print("Error: 'watchdog' library not found. Please run: pip install watchdog")
    sys.exit(1)

# --- PATH & DB CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "postgresql.log")
MODEL_PATH = os.path.join(BASE_DIR, "..", "model", "unusual_query_detector.pkl")

# --- IMPORTANT: Connect to Dockerized MySQL ---
# The database name is now part of the URI
DB_URI = "mysql+mysqlconnector://root:root_password@localhost:3306/security_monitoring"
# URI for initial connection to create the database
SERVER_URI = "mysql+mysqlconnector://root:root_password@localhost:3306"
DB_NAME = "security_monitoring"
LIVE_TABLE_NAME = "query_monitoring"

LOG_PATTERN = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|UNKNOWN)\s+(.*)"


class LogUpdateHandler(FileSystemEventHandler):
    """Event handler that triggers the pipeline when the log file is modified."""

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def on_modified(self, event):
        if not event.is_directory and os.path.abspath(
            event.src_path
        ) == os.path.abspath(LOG_FILE):
            self.pipeline.process_new_logs()


class MLInferencePipeline:
    """The main class for processing logs, running ML inference, and storing results."""

    def __init__(self):
        print("\n" + "=" * 50)
        print("🛡️  ENTERPRISE DAM SECURITY PIPELINE (MySQL Edition)")
        print("=" * 50)

        self.engine = self.setup_database()
        self.model = self.load_ml_model()
        self.last_position = 0
        self.last_periodic_check = datetime.now()

        # Business Logic Mapping for feature engineering
        self.monitored_tables = [
            "salary",
            "finance",
            "hr_data",
            "transactions",
            "customers",
            "orders",
            "inventory",
            "products",
            "employees",
        ]
        self.sensitive_tables = [
            "salary",
            "finance",
            "hr_data",
            "customers",
            "transactions",
        ]

    def _create_database_if_not_exists(self):
        """Connects to the MySQL server and creates the database if it's missing."""
        try:
            engine = create_engine(SERVER_URI)
            with engine.connect() as connection:
                connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
            print(f"✅ SUCCESS: Database '{DB_NAME}' is present.")
        except OperationalError:
            print(
                "❌ CRITICAL ERROR: Could not connect to MySQL server at localhost:3306."
            )
            print("Please ensure your Docker container is running and accessible.")
            sys.exit(1)

    def _create_table_if_not_exists(self, engine):
        """Creates the live monitoring table in the database if it's missing."""
        try:
            with engine.connect() as connection:
                connection.execute(
                    text(
                        f"""
                    CREATE TABLE IF NOT EXISTS {LIVE_TABLE_NAME} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME,
                        user_id VARCHAR(255),
                        table_accessed VARCHAR(255),
                        query_type VARCHAR(50),
                        rows_returned INT,
                        after_hours_access TINYINT,
                        sensitive_data_access TINYINT,
                        failed_login_attempt TINYINT,
                        total_queries_session INT,
                        data_exfiltration_pattern TINYINT,
                        query_text TEXT,
                        anomaly_flag TINYINT
                    );
                """
                    )
                )
            print(f"✅ SUCCESS: Table '{LIVE_TABLE_NAME}' is present.")
        except Exception as e:
            print(
                f"❌ CRITICAL ERROR: Could not create table '{LIVE_TABLE_NAME}'. Reason: {e}"
            )
            sys.exit(1)

    def setup_database(self):
        """Orchestrates the database and table setup."""
        self._create_database_if_not_exists()
        try:
            engine = create_engine(DB_URI)
            self._create_table_if_not_exists(engine)
            print("✅ SUCCESS: Connection to MySQL database established.")
            return engine
        except OperationalError:
            print(f"❌ CRITICAL ERROR: Could not connect to database at {DB_URI}")
            print(
                "Please check connection details and ensure the Docker container is running."
            )
            sys.exit(1)

    def load_ml_model(self):
        """Loads the pre-trained machine learning model from disk."""
        if not os.path.exists(MODEL_PATH):
            print(f"❌ CRITICAL ERROR: ML Model not found at {MODEL_PATH}")
            print("Please ensure the model training process has been completed.")
            sys.exit(1)
        try:
            model = joblib.load(MODEL_PATH)
            print(f"✅ SUCCESS: Machine Learning model loaded from {MODEL_PATH}")
            return model
        except Exception as e:
            print(f"❌ ERROR: Failed to load model file. Corrupted file? Details: {e}")
            sys.exit(1)

    def extract_features(self, ts_str, user_id, q_type, q_text):
        """Converts a raw log line into a feature vector for the ML model."""
        table_accessed = "unknown"
        for tbl in self.monitored_tables:
            if tbl.lower() in q_text.lower():
                table_accessed = tbl
                break

        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        is_after_hours = 1 if dt.hour < 8 or dt.hour > 18 else 0
        is_sensitive = 1 if table_accessed in self.sensitive_tables else 0
        is_exfil = 1 if ("*" in q_text or "1=1" in q_text) and q_type == "SELECT" else 0
        rows = 1000 if is_exfil else 1

        return {
            "timestamp": dt,
            "user_id": user_id,
            "table_accessed": table_accessed,
            "query_type": q_type,
            "rows_returned": rows,
            "after_hours_access": is_after_hours,
            "sensitive_data_access": is_sensitive,
            "failed_login_attempt": 0,
            "total_queries_session": 1,
            "data_exfiltration_pattern": is_exfil,
            "query_text": q_text,
        }

    def process_new_logs(self):
        """Tails the log file, processes new lines, runs inference, and saves to the database."""
        if not os.path.exists(LOG_FILE):
            return

        new_records = []
        try:
            current_size = os.path.getsize(LOG_FILE)
            if current_size < self.last_position:
                print("ℹ️  Log file was rotated or cleared. Resetting reader position.")
                self.last_position = 0

            with open(LOG_FILE, "r") as f:
                f.seek(self.last_position)
                lines = f.readlines()
                for line in lines:
                    if not line.strip():
                        continue
                    match = re.search(LOG_PATTERN, line)
                    if match:
                        ts, user, q_type, q_text = match.groups()
                        features = self.extract_features(ts, user, q_type, q_text)
                        new_records.append(features)
                self.last_position = f.tell()
        except Exception as e:
            print(f"⚠️ Warning: Error reading log file: {e}")
            return

        if not new_records:
            return

        df = pd.DataFrame(new_records)
        ml_features = [
            "table_accessed",
            "query_type",
            "rows_returned",
            "after_hours_access",
            "sensitive_data_access",
            "failed_login_attempt",
            "total_queries_session",
            "data_exfiltration_pattern",
        ]

        try:
            df["anomaly_flag"] = self.model.predict(df[ml_features])
            df.to_sql(LIVE_TABLE_NAME, self.engine, if_exists="append", index=False)
            anomalies = int(df["anomaly_flag"].sum())
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(
                f"[{timestamp}] Processed {len(df)} new queries. Flags raised: {anomalies}"
            )
        except Exception as e:
            print(
                f"❌ DB/ML Error: Failed during prediction or database write. Reason: {e}"
            )

    def start(self):
        """Starts the real-time file observer to monitor for log changes."""
        self.process_new_logs()  # Process any existing logs on startup

        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        if not os.path.exists(LOG_FILE):
            open(LOG_FILE, "a").close()  # Create the file if it doesn't exist

        if os.name == "nt":
            print("ℹ️  Platform: Windows detected. Using robust PollingObserver.")
            observer = PollingObserver()
        else:
            observer = Observer()

        handler = LogUpdateHandler(self)
        observer.schedule(handler, path=LOG_DIR, recursive=False)
        observer.start()

        print(f"👀 MONITORING: {LOG_FILE}")
        print("🕒 SCHEDULE: 10-minute deep sync active.")
        print("=" * 50)
        print("Press Ctrl+C to stop the pipeline.\n")

        try:
            while True:
                time.sleep(1)
                if datetime.now() - self.last_periodic_check > timedelta(minutes=10):
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Periodic deep sync triggered..."
                    )
                    self.process_new_logs()
                    self.last_periodic_check = datetime.now()
        except KeyboardInterrupt:
            print("\nShutting down pipeline engine...")
        finally:
            observer.stop()
            observer.join()


if __name__ == "__main__":
    pipeline = MLInferencePipeline()
    pipeline.start()

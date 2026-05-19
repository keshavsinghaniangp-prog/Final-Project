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
DB_URI = "mysql+mysqlconnector://root:root_password@localhost:3306/security_monitoring"
SERVER_URI = "mysql+mysqlconnector://root:root_password@localhost:3306"
DB_NAME = "security_monitoring"
LIVE_TABLE_NAME = "query_monitoring"

LOG_PATTERN = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|UNKNOWN)\s+(.*)"


class LogUpdateHandler(FileSystemEventHandler):
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def on_modified(self, event):
        if not event.is_directory and os.path.abspath(
            event.src_path
        ) == os.path.abspath(LOG_FILE):
            self.pipeline.process_new_logs()


class MLInferencePipeline:
    def __init__(self):
        print("\n" + "=" * 50)
        print("🛡️  ENTERPRISE DAM SECURITY PIPELINE (Relational MySQL)")
        print("=" * 50)

        self.engine = self.setup_database()
        self.model = self.load_ml_model()
        self.last_position = 0
        self.last_periodic_check = datetime.now()

        # Feature mapping
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
        try:
            engine = create_engine(SERVER_URI)
            with engine.connect() as connection:
                connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
                connection.commit()
            print(f"✅ SUCCESS: Database '{DB_NAME}' is present.")
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Could not create database. Reason: {e}")
            sys.exit(1)

    def _setup_schema(self, engine):
        try:
            with engine.connect() as connection:
                # 1. Employees Table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS employees (
                        user_id VARCHAR(50) PRIMARY KEY,
                        full_name VARCHAR(100),
                        department VARCHAR(50),
                        job_role VARCHAR(100),
                        risk_tier VARCHAR(20) DEFAULT 'Low'
                    )
                """))

                # 2. Query Monitoring Table with Foreign Key
                connection.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {LIVE_TABLE_NAME} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME,
                        user_id VARCHAR(50),
                        table_accessed VARCHAR(100),
                        query_type VARCHAR(20),
                        rows_returned INT,
                        after_hours_access TINYINT,
                        sensitive_data_access TINYINT,
                        failed_login_attempt TINYINT,
                        total_queries_session INT,
                        data_exfiltration_pattern TINYINT,
                        query_text TEXT,
                        anomaly_flag TINYINT,
                        CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES employees(user_id)
                    )
                """))
                connection.commit()
            print(f"✅ SUCCESS: Relational Schema verified.")
        except Exception as e:
            print(f"❌ SCHEMA ERROR: {e}")
            sys.exit(1)

    def setup_database(self):
        self._create_database_if_not_exists()
        try:
            engine = create_engine(DB_URI)
            self._setup_schema(engine)
            return engine
        except Exception as e:
            print(f"❌ DB CONNECTION ERROR: {e}")
            sys.exit(1)

    def load_ml_model(self):
        if not os.path.exists(MODEL_PATH):
            print(f"❌ CRITICAL ERROR: ML Model not found at {MODEL_PATH}")
            sys.exit(1)
        try:
            model = joblib.load(MODEL_PATH)
            print(f"✅ SUCCESS: Machine Learning model loaded.")
            return model
        except Exception as e:
            print(f"❌ ERROR: Failed to load model file: {e}")
            sys.exit(1)

    def extract_features(self, ts_str, user_id, q_type, q_text):
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
        if not os.path.exists(LOG_FILE):
            return

        new_records = []
        try:
            current_size = os.path.getsize(LOG_FILE)
            if current_size < self.last_position:
                self.last_position = 0

            with open(LOG_FILE, "r") as f:
                f.seek(self.last_position)
                for line in f:
                    if not line.strip(): continue
                    match = re.search(LOG_PATTERN, line)
                    if match:
                        new_records.append(self.extract_features(*match.groups()))
                self.last_position = f.tell()
        except Exception as e:
            print(f"⚠️ Warning: Error reading log file: {e}")
            return

        if not new_records: return

        df = pd.DataFrame(new_records)
        ml_features = ["table_accessed","query_type","rows_returned","after_hours_access",
                       "sensitive_data_access","failed_login_attempt","total_queries_session","data_exfiltration_pattern"]

        try:
            df["anomaly_flag"] = self.model.predict(df[ml_features])
            df.to_sql(LIVE_TABLE_NAME, self.engine, if_exists="append", index=False)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed {len(df)} logs.")
        except Exception as e:
            print(f"❌ DB/ML Error: {e}")

    def start(self):
        self.process_new_logs()
        observer = PollingObserver()
        handler = LogUpdateHandler(self)
        observer.schedule(handler, path=LOG_DIR, recursive=False)
        observer.start()

        print(f"👀 MONITORING: {LOG_FILE}")
        try:
            while True:
                time.sleep(1)
                if datetime.now() - self.last_periodic_check > timedelta(minutes=10):
                    self.process_new_logs()
                    self.last_periodic_check = datetime.now()
        except KeyboardInterrupt:
            print("\nShutting down pipeline...")
        finally:
            observer.stop()
            observer.join()


if __name__ == "__main__":
    MLInferencePipeline().start()

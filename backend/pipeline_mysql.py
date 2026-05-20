import os
import re
import sys
import time
from datetime import datetime, timedelta

import joblib
import pandas as pd
import sqlparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers.polling import PollingObserver
except ImportError:
    print("Error: 'watchdog' library not found. Please run: pip install watchdog")
    sys.exit(1)

# --- CONFIGURATION ---
DB_URI = "mysql+mysqlconnector://root:root_password@localhost:3306/security_monitoring"
SERVER_URI = "mysql+mysqlconnector://root:root_password@localhost:3306"
DB_NAME = "security_monitoring"
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "model", "unusual_query_detector.pkl"
)
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "postgresql.log")
# Updated Pattern to include IP and App
# YYYY-MM-DD HH:MM:SS user_id SOURCE_IP CLIENT_APP QUERY_TYPE QUERY_TEXT
LOG_PATTERN = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(user_\d+)\s+([\d\.]+)\s+(\w+)\s+(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|UNKNOWN)\s+(.*)"


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
        print("🛡️  ENTERPRISE DAM SECURITY PIPELINE (Relational + SQLParse)")
        print("=" * 50)

        self.engine = self.setup_database()
        self.model = self.load_ml_model()
        self.last_position = 0
        self.last_periodic_check = datetime.now()

    def _create_database_if_not_exists(self):
        try:
            engine = create_engine(SERVER_URI)
            with engine.connect() as connection:
                connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
                connection.commit()
            print(f"✅ SUCCESS: Database '{DB_NAME}' is present.")
        except SQLAlchemyError as e:
            print(f"❌ CRITICAL ERROR: Could not create database. Reason: {e}")
            sys.exit(1)

    def _setup_schema(self, engine):
        try:
            with engine.connect() as connection:
                # 1. Employees Table
                connection.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS employees (
                        user_id VARCHAR(50) PRIMARY KEY,
                        full_name VARCHAR(100),
                        department VARCHAR(50),
                        job_role VARCHAR(100),
                        risk_tier VARCHAR(20) DEFAULT 'Low'
                    )
                """)
                )

                # 2. Query Monitoring Table (Updated Schema)
                connection.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS query_monitoring (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME,
                        user_id VARCHAR(50),
                        source_ip VARCHAR(50),
                        client_app VARCHAR(100),
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
                """)
                )

                # 3. Analyst Feedback Table
                connection.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS analyst_feedback (
                        feedback_id INT AUTO_INCREMENT PRIMARY KEY,
                        query_id INT,
                        analyst_label VARCHAR(50),
                        comments TEXT,
                        timestamp DATETIME,
                        FOREIGN KEY (query_id) REFERENCES query_monitoring(id)
                    )
                """)
                )
                connection.commit()
            print("✅ SUCCESS: Relational Schema verified.")
        except SQLAlchemyError as e:
            print(f"❌ SCHEMA ERROR: {e}")
            sys.exit(1)

    def setup_database(self):
        self._create_database_if_not_exists()
        try:
            engine = create_engine(DB_URI)
            self._setup_schema(engine)
            return engine
        except SQLAlchemyError as e:
            print(f"❌ DB CONNECTION ERROR: {e}")
            sys.exit(1)

    def load_ml_model(self):
        if not os.path.exists(MODEL_PATH):
            print(f"❌ CRITICAL ERROR: ML Model not found at {MODEL_PATH}")
            sys.exit(1)
        try:
            model = joblib.load(MODEL_PATH)
            print("✅ SUCCESS: Machine Learning model loaded.")
            return model
        except Exception as e:
            print(f"❌ ERROR: Failed to load model file: {e}")
            sys.exit(1)

    def parse_sql_query(self, query_text):
        """Uses sqlparse to extract metadata from the query."""
        parsed = sqlparse.parse(query_text)[0]

        # 1. Identify Target Tables
        tables = []
        for token in parsed.tokens:
            if isinstance(token, sqlparse.sql.IdentifierList):
                for identifier in token.get_identifiers():
                    tables.append(identifier.get_real_name())
            elif isinstance(token, sqlparse.sql.Identifier):
                tables.append(token.get_real_name())

        # Fallback to simple matching if sqlparse fails to find table
        if not tables or None in tables:
            monitored = [
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
            tables = [t for t in monitored if t in query_text.lower()]

        table = tables[0] if tables else "unknown"

        # 2. Detect Exfiltration Patterns
        is_exfil = 0
        if "1=1" in query_text or "*" in query_text:
            is_exfil = 1

        return table, is_exfil

    def extract_features(self, ts_str, user_id, ip, app, q_type, q_text):
        table, is_exfil = self.parse_sql_query(q_text)

        sensitive_tables = ["salary", "finance", "hr_data", "customers", "transactions"]

        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        is_after_hours = 1 if dt.hour < 8 or dt.hour > 18 else 0
        is_sensitive = 1 if table in sensitive_tables else 0
        rows = 1000 if is_exfil else 1

        return {
            "timestamp": dt,
            "user_id": user_id,
            "source_ip": ip,
            "client_app": app,
            "table_accessed": table,
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
                    if not line.strip():
                        continue
                    match = re.search(LOG_PATTERN, line)
                    if match:
                        new_records.append(self.extract_features(*match.groups()))
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
            df.to_sql("query_monitoring", self.engine, if_exists="append", index=False)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed {len(df)} logs.")
        except Exception as e:
            print(f"❌ DB/ML Error: {e}")

    def start(self):
        self.process_new_logs()
        observer = PollingObserver()
        handler = LogUpdateHandler(self)
        observer.schedule(handler, path=os.path.dirname(LOG_FILE), recursive=False)
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

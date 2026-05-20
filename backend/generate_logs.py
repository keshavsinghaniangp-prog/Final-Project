import os
import random
import time
from datetime import datetime

import pandas as pd
from faker import Faker
from sqlalchemy import create_engine

DB_URI = "mysql+mysqlconnector://root:root_password@localhost:3306/security_monitoring"
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "postgresql.log")

fake = Faker()


class StatefulLogGenerator:
    def __init__(self):
        self.engine = create_engine(DB_URI)
        self.users_df = self.load_users()
        self.parts = [
            "HYD-PUMP-01",
            "TRAN-GEAR-X",
            "AXLE-BRKT-99",
            "VALVE-STEM-04",
            "ENG-FLTR-V8",
        ]
        self.tables = {
            "Warehouse": ["inventory", "products", "orders"],
            "HR": ["hr_data", "employees"],
            "Sales": ["orders", "customers", "products"],
            "Finance": ["finance", "transactions", "salary"],
            "IT": [
                "inventory",
                "hr_data",
                "finance",
                "employees",
            ],  # IT has broad but specific access
        }
        self.apps = [
            "WebUI",
            "DBeaver",
            "Python_Script",
            "Workday_Integration",
            "Tableau_Connector",
        ]

        # Assign a "Home IP" range to each user for identity theft simulation
        self.user_ips = {
            row["user_id"]: f"10.20.{random.randint(10, 50)}.{random.randint(2, 254)}"
            for _, row in self.users_df.iterrows()
        }

    def load_users(self):
        try:
            return pd.read_sql("SELECT user_id, department FROM employees", self.engine)
        except Exception as e:
            print(f"⚠️ Employees table not seeded! Error: {e}")
            exit(1)

    def generate_themed_query(self, dept, is_anomaly=False):
        if is_anomaly:
            target_dept = random.choice([d for d in self.tables.keys() if d != dept])
            table = random.choice(self.tables[target_dept])
        else:
            table = random.choice(self.tables.get(dept, ["products"]))

        part = random.choice(self.parts)

        if table == "inventory":
            if random.random() > 0.5:
                return (
                    "UPDATE",
                    f"UPDATE inventory SET stock = stock - {random.randint(1, 10)} WHERE part_sku = '{part}'",
                )
            return (
                "SELECT",
                "SELECT stock_level FROM inventory WHERE warehouse_zone = 'ZONE-A'",
            )
        elif table == "finance":
            if is_anomaly and random.random() < 0.5:
                return "SELECT", f"SELECT * FROM finance WHERE 1=1 -- exfiltration"
            return (
                "SELECT",
                f"SELECT * FROM finance WHERE transaction_type = 'WIRE_TRANSFER' AND amount > 50000",
            )
        elif table == "hr_data":
            if is_anomaly and random.random() < 0.5:
                return "SELECT", f"SELECT * FROM hr_data"
            return (
                "SELECT",
                f"SELECT ssn, salary_grade FROM hr_data WHERE performance_rating = 'Critical'",
            )
        else:
            return "SELECT", f"SELECT id, name FROM {table} LIMIT 100"

    def run(self):
        print(f"🚀 Generator Started. Identity-aware logs writing to {LOG_FILE}...")
        while True:
            user = self.users_df.sample(n=1).iloc[0]
            uid, dept = user["user_id"], user["department"]

            is_anomaly = random.random() < 0.08  # 8% anomaly rate

            # Identity Theft Simulation: Anomaly uses external IP and unusual app
            if is_anomaly and random.random() < 0.4:
                ip = fake.ipv4_public()  # External Attacker IP
                app = random.choice(
                    ["Unknown_Client", "Python_Script", "PowerShell_Invoke"]
                )
            else:
                ip = self.user_ips[uid]  # Normal Home IP
                app = random.choice(self.apps)

            q_type, q_text = self.generate_themed_query(dept, is_anomaly)

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Format: YYYY-MM-DD HH:MM:SS user_id SOURCE_IP CLIENT_APP QUERY_TYPE QUERY_TEXT
            log_line = f"{ts} {uid} {ip} {app} {q_type} {q_text}\n"

            with open(LOG_FILE, "a") as f:
                f.write(log_line)

            # Randomize sleep to simulate realistic burst traffic
            time.sleep(random.uniform(0.1, 1.5))


if __name__ == "__main__":
    StatefulLogGenerator().run()

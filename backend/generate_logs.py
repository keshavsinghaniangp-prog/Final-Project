import os
import random
import time
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine

DB_URI = "mysql+mysqlconnector://root:root_password@localhost:3306/security_monitoring"
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "postgresql.log")


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
        }

    def load_users(self):
        try:
            return pd.read_sql("SELECT user_id, department FROM employees", self.engine)
        except:
            print("⚠️ Employees table not seeded! Run seed_employees.py first.")
            exit(1)

    def generate_themed_query(self, dept, is_anomaly=False):
        # RBAC Logic: If anomaly, pick a table outside their department
        if is_anomaly:
            target_dept = random.choice([d for d in self.tables.keys() if d != dept])
            table = random.choice(self.tables[target_dept])
        else:
            table = random.choice(self.tables.get(dept, ["products"]))

        part = random.choice(self.parts)

        # Tractor Parts Themed Queries
        if table == "inventory":
            if random.random() > 0.5:
                return (
                    "UPDATE",
                    f"UPDATE inventory SET stock = stock - {random.randint(1, 10)} WHERE part_sku = '{part}'",
                )
            return (
                "SELECT",
                f"SELECT stock_level FROM inventory WHERE warehouse_zone = 'ZONE-A'",
            )
        elif table == "finance":
            return (
                "SELECT",
                f"SELECT * FROM finance WHERE transaction_type = 'WIRE_TRANSFER' AND amount > 50000",
            )
        elif table == "hr_data":
            return (
                "SELECT",
                f"SELECT ssn, salary_grade FROM hr_data WHERE performance_rating = 'Critical'",
            )
        else:
            return "SELECT", f"SELECT id, name FROM {table} LIMIT 100"

    def run(self):
        print(f"🚀 Generator Started. Role-Based logs writing to {LOG_FILE}...")
        while True:
            user = self.users_df.sample(n=1).iloc[0]
            uid, dept = user["user_id"], user["department"]

            # 10% Anomaly Chance
            is_anomaly = random.random() < 0.1
            q_type, q_text = self.generate_themed_query(dept, is_anomaly)

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"{ts} {uid} {q_type} {q_text}\n"

            with open(LOG_FILE, "a") as f:
                f.write(log_line)

            time.sleep(random.uniform(0.5, 2.0))


if __name__ == "__main__":
    StatefulLogGenerator().run()

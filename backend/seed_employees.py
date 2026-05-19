import random

import pandas as pd
from faker import Faker
from sqlalchemy import create_engine, text

DB_URI = "mysql+mysqlconnector://root:root_password@localhost:3306/security_monitoring"


def seed_employees():
    fake = Faker()
    engine = create_engine(DB_URI)

    depts = {
        "IT": ["SysAdmin", "Security Analyst", "DevOps"],
        "HR": ["HR Manager", "Recruiter"],
        "Sales": ["Account Executive", "Sales Lead"],
        "Warehouse": ["Inventory Clerk", "Logistics Coordinator"],
        "Finance": ["Accountant", "Payroll Specialist"],
    }

    employees = []
    print("🌱 Seeding 40 employees...")

    for i in range(1, 41):
        dept = random.choice(list(depts.keys()))
        role = random.choice(depts[dept])
        user_id = f"user_{i:02d}"

        employees.append(
            {
                "user_id": user_id,
                "full_name": fake.name(),
                "department": dept,
                "job_role": role,
                "risk_tier": random.choices(
                    ["Low", "Med", "High"], weights=[80, 15, 5]
                )[0],
            }
        )

    df = pd.DataFrame(employees)

    try:
        with engine.connect() as conn:
            # Clear existing to avoid PK violations during testing
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            conn.execute(text("TRUNCATE TABLE employees;"))
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            conn.commit()

        df.to_sql("employees", engine, if_exists="append", index=False)
        print(f"✅ Successfully seeded 40 employees into MySQL.")
    except Exception as e:
        print(f"❌ Seeding Failed: {e}")


if __name__ == "__main__":
    seed_employees()

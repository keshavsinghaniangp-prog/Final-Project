import os
import random
import time
from datetime import datetime

# Define absolute paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "postgresql.log")


def setup_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    # Clear the file on startup to simulate fresh logs
    try:
        with open(LOG_FILE, "w") as f:
            f.write("")
        print(f"Log file initialized at: {LOG_FILE}")
    except Exception as e:
        print(f"Error initializing log file: {e}")


def generate_log_line():
    users = [f"user_{i:02d}" for i in range(1, 41)]
    all_tables = [
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
    query_types = ["SELECT", "INSERT", "UPDATE", "DELETE", "UNKNOWN"]

    user = random.choice(users)
    table = random.choice(all_tables)
    q_type = random.choice(query_types)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Refined Anomaly & Warning Simulation ---
    # We now decouple after-hours and sensitive access for more realistic scenarios.

    # Scenario 1: High-Risk Anomaly (e.g., Exfiltration)
    if random.random() < 0.1:
        table = random.choice(
            ["salary", "finance", "customers"]
        )  # Target sensitive data
        q_type = "SELECT"
        q_text = f"SELECT * FROM {table} WHERE 1=1"

    # Scenario 2: Medium-Risk Warning (e.g., After-hours access on non-sensitive data)
    elif random.random() < 0.15:
        # Simulate after-hours access on a NON-SENSITIVE table
        table = random.choice(["inventory", "products", "orders"])
        q_type = "UPDATE"
        q_text = f"UPDATE {table} SET stock = 0 WHERE last_updated < '2023-01-01'"
        # Force timestamp to be after hours
        timestamp = (
            datetime.now()
            .replace(hour=random.choice([22, 23, 0, 1]))
            .strftime("%Y-%m-%d %H:%M:%S")
        )

    # Scenario 3: Medium-Risk Warning (e.g., Sensitive access during business hours)
    elif random.random() < 0.15:
        table = "hr_data"
        q_type = "SELECT"
        q_text = f"SELECT ssn, name FROM {table} LIMIT 200"

    # Scenario 4: Normal Behavior (Default)
    else:
        q_text = f"{q_type} id, name FROM {table} WHERE id = {random.randint(1, 1000)}"

    # Format exactly as pipeline expects
    log_line = f"{timestamp} {user} {q_type} {q_text}\n"
    return log_line


def simulate_database_traffic():
    setup_log_dir()
    print(f"Starting simulated database traffic... Writing to {LOG_FILE}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            try:
                with open(LOG_FILE, "a") as f:
                    for _ in range(random.randint(1, 5)):
                        line = generate_log_line()
                        f.write(line)
                        f.flush()

                time.sleep(random.uniform(0.5, 2.0))
            except Exception as e:
                print(f"Error writing to logs: {e}")
                time.sleep(5)

    except KeyboardInterrupt:
        print("\nStopping simulated traffic.")


if __name__ == "__main__":
    simulate_database_traffic()

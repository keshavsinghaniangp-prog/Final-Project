import pandas as pd
import numpy as np

def generate_logs(n=5000):

    users = [f"user_{i}" for i in range(20)]

    data = []

    for _ in range(n):

        user = np.random.choice(users)

        rows = np.random.randint(10,500)

        after_hours = np.random.choice([0,1],p=[0.8,0.2])

        sensitive = np.random.choice([0,1],p=[0.9,0.1])

        failed = np.random.choice([0,1],p=[0.95,0.05])

        data.append([user,rows,after_hours,sensitive,failed])

    df = pd.DataFrame(data,columns=[
        "user",
        "rows_returned",
        "after_hours",
        "sensitive_access",
        "failed_login"
    ])

    df["query"] = 1

    return df
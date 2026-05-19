import pandas as pd

def build_features(logs):

    features = logs.groupby("user").agg({

        "rows_returned":"mean",
        "after_hours":"sum",
        "sensitive_access":"sum",
        "failed_login":"sum",
        "query":"count"

    }).reset_index()

    features.columns = [

        "user",
        "avg_rows",
        "after_hours_count",
        "sensitive_access_count",
        "failed_logins",
        "total_queries"

    ]

    return features
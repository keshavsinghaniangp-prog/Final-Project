import joblib
import pandas as pd

model = joblib.load("models/isolation_model.pkl")
scaler = joblib.load("models/scaler.pkl")

def compute_risk_scores(df):

    features = [
        "avg_rows",
        "after_hours_count",
        "sensitive_access_count",
        "failed_logins",
        "total_queries"
    ]

    X = df[features]

    X_scaled = scaler.transform(X)

    anomaly_scores = model.decision_function(X_scaled)

    df["risk_score"] = (1 - anomaly_scores) * 100

    df["anomaly"] = df["risk_score"].apply(
        lambda x: "anomaly" if x > 60 else "normal"
    )

    return df
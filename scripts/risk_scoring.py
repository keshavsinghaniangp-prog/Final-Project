import os

import joblib
import numpy as np
import pandas as pd

# Path to the models
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model")


def calculate_risk_scores(user_features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the Unsupervised Isolation Forest model to assign a 0-100 risk score.
    """
    if user_features_df.empty:
        return user_features_df

    try:
        # Load the artifacts
        scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        iso_forest = joblib.load(os.path.join(MODEL_DIR, "isolation_model.pkl"))

        # Prepare features for prediction
        cols = [
            "avg_rows",
            "after_hours_count",
            "sensitive_access_count",
            "total_queries",
        ]
        X_scaled = scaler.transform(user_features_df[cols])

        # Capture the raw decision score (lower is more anomalous)
        # Decision function returns values in range [-0.5, 0.5] approx
        raw_scores = iso_forest.decision_function(X_scaled)

        # --- Normalization Logic ---
        # Map raw outlier scores to a 0-100 Corporate Risk Score.
        # We want higher numbers to mean HIGHER RISK.
        # Decision function: most normal is high positive, most anomalous is high negative.

        # Shift and invert to make anomalies high positive numbers
        # We'll use a robust min-max scaling based on the current batch
        s_min, s_max = raw_scores.min(), raw_scores.max()

        if s_max == s_min:
            risk_scores = np.zeros_like(raw_scores)
        else:
            # Invert: 1.0 = outlier, 0.0 = normal
            normalized = (raw_scores - s_min) / (s_max - s_min + 1e-9)
            risk_scores = (1 - normalized) * 100

        user_features_df["risk_score"] = risk_scores.round(1)

        # --- Risk Labeling ---
        user_features_df["risk_level"] = "Low Risk"
        user_features_df.loc[user_features_df["risk_score"] > 40, "risk_level"] = (
            "Medium Risk"
        )
        user_features_df.loc[user_features_df["risk_score"] > 75, "risk_level"] = (
            "High Risk"
        )

        return user_features_df.sort_values("risk_score", ascending=False)

    except Exception as e:
        print(f"⚠️ Risk Scoring Error: {e}")
        user_features_df["risk_score"] = 0
        user_features_df["risk_level"] = "Unknown"
        return user_features_df

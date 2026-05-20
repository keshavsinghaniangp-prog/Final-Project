import os

import joblib
import numpy as np
import pandas as pd
import shap

# Path to the models
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model")


def calculate_risk_scores(user_features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the Unsupervised Isolation Forest model to assign a 0-100 risk score.
    Now includes SHAP for Explainable AI (XAI).
    """
    if user_features_df.empty:
        return user_features_df

    try:
        # 1. Load Artifacts
        scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        iso_forest = joblib.load(os.path.join(MODEL_DIR, "isolation_model.pkl"))

        # 2. Prepare Features (Matching Training Order)
        # Note: We now have more features (velocity, deviation)
        # For simplicity in this upgrade, we stick to the main 4 but we can expand.
        cols = [
            "avg_rows",
            "after_hours_count",
            "sensitive_access_count",
            "total_queries",
        ]
        X = user_features_df[cols]
        X_scaled = scaler.transform(X)

        # 3. Model Prediction
        raw_scores = iso_forest.decision_function(X_scaled)

        # 4. Normalization to 0-100 Corporate Risk Score
        s_min, s_max = raw_scores.min(), raw_scores.max()
        if s_max == s_min:
            risk_scores = np.zeros_like(raw_scores)
        else:
            normalized = (raw_scores - s_min) / (s_max - s_min + 1e-9)
            risk_scores = (1 - normalized) * 100

        user_features_df["risk_score"] = risk_scores.round(1)

        # 5. SHAP Explanations (XAI)
        # Isolation Forest is compatible with TreeExplainer
        explainer = shap.TreeExplainer(iso_forest)
        shap_values = explainer.shap_values(X_scaled)

        # We store the main contributor for each user
        # Identify index of max shap value (highest contribution to anomaly)
        max_idx = np.argmax(np.abs(shap_values), axis=1)
        user_features_df["top_risk_reason"] = [
            cols[i].replace("_", " ").title() for i in max_idx
        ]

        # 6. Risk Labeling
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
        return user_features_df

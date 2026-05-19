import os

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(
    BASE_DIR, "..", "data", "unusual_query_detection_dataset_1200_rows (1).csv"
)
MODEL_DIR = os.path.join(BASE_DIR, "..", "model")


def train_models():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    print(f"📖 Loading training data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)

    # --- MODEL A: Query-Level Supervised Classification ---
    print("🛠️ Training Model A: Supervised Query Detector (Random Forest)...")

    # Ensure column names match the dataset
    # The dataset has 'unusual_query_flag' as target
    X_a = df[
        [
            "table_accessed",
            "query_type",
            "rows_returned",
            "after_hours_access",
            "sensitive_data_access",
            "data_exfiltration_pattern",
        ]
    ]
    y_a = df["unusual_query_flag"]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                ["table_accessed", "query_type"],
            ),
            (
                "num",
                "passthrough",
                [
                    "rows_returned",
                    "after_hours_access",
                    "sensitive_data_access",
                    "data_exfiltration_pattern",
                ],
            ),
        ]
    )

    model_a = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(n_estimators=100, random_state=42)),
        ]
    )

    model_a.fit(X_a, y_a)
    joblib.dump(model_a, os.path.join(MODEL_DIR, "unusual_query_detector.pkl"))
    print("✅ Model A saved.")

    # --- MODEL B: User-Level Unsupervised Behavior Profiling ---
    print("🛠️ Training Model B: Unsupervised User Profiler (Isolation Forest)...")

    # Aggregate behavior by user to create a baseline profile
    user_features = (
        df.groupby("user_id")
        .agg(
            avg_rows=("rows_returned", "mean"),
            after_hours_count=("after_hours_access", "sum"),
            sensitive_access_count=("sensitive_data_access", "sum"),
            total_queries=("user_id", "size"),
        )
        .reset_index()
    )

    X_b = user_features[
        ["avg_rows", "after_hours_count", "sensitive_access_count", "total_queries"]
    ]

    scaler = StandardScaler()
    X_b_scaled = scaler.fit_transform(X_b)

    # We set a small contamination factor for the baseline
    model_b = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model_b.fit(X_b_scaled)

    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
    joblib.dump(model_b, os.path.join(MODEL_DIR, "isolation_model.pkl"))

    print("✅ Model B and Scaler saved.")
    print("\n🚀 All ML models successfully updated and stored in /model/")


if __name__ == "__main__":
    train_models()

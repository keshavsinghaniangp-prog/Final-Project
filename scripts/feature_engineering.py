import numpy as np
import pandas as pd


def engineer_user_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw log activity into user-level behavioral metrics.
    Includes Peer-Group normalization and Query Velocity.
    """
    if df.empty:
        return pd.DataFrame()

    # 1. Sort by time for velocity calculation
    df = df.sort_values(["user_id", "timestamp"])

    # 2. Calculate Query Velocity (Queries per minute)
    # Get time delta between current and previous query for each user
    df["time_delta"] = df.groupby("user_id")["timestamp"].diff().dt.total_seconds()

    # Velocity = 60 / time_delta (Handle division by zero)
    # A low time delta means high velocity
    df["velocity"] = 60.0 / (df["time_delta"].replace(0, 0.1).fillna(60.0))

    # Aggregate by User
    user_profiles = (
        df.groupby(["user_id", "full_name", "department", "job_role"])
        .agg(
            avg_rows=("rows_returned", "mean"),
            after_hours_count=("after_hours_access", "sum"),
            sensitive_access_count=("sensitive_data_access", "sum"),
            total_queries=("user_id", "size"),
            anomaly_events=("unusual_query_flag", "sum"),
            avg_velocity=("velocity", "mean"),
            max_velocity=("velocity", "max"),
        )
        .reset_index()
    )

    # 3. PEER-GROUP NORMALIZATION
    # Calculate department-level averages for peer comparison
    dept_stats = (
        user_profiles.groupby("department")
        .agg(
            dept_avg_queries=("total_queries", "mean"),
            dept_avg_sensitive=("sensitive_access_count", "mean"),
        )
        .reset_index()
    )

    user_profiles = user_profiles.merge(dept_stats, on="department")

    # Create Peer-Deviation metrics
    user_profiles["query_deviation"] = user_profiles["total_queries"] / (
        user_profiles["dept_avg_queries"] + 1e-6
    )
    user_profiles["sensitive_deviation"] = user_profiles["sensitive_access_count"] / (
        user_profiles["dept_avg_sensitive"] + 1e-6
    )

    return user_profiles

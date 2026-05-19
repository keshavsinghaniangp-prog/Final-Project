import pandas as pd


def engineer_user_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw log activity into user-level behavioral metrics.
    Accepts the relational dataframe (including joined employee fields).
    """
    if df.empty:
        return pd.DataFrame()

    # Define required columns for the aggregation
    # We group by ID and identity fields to preserve them in the output
    user_profiles = (
        df.groupby(["user_id", "full_name", "department"])
        .agg(
            avg_rows=("rows_returned", "mean"),
            after_hours_count=("after_hours_access", "sum"),
            sensitive_access_count=("sensitive_data_access", "sum"),
            total_queries=("user_id", "size"),
            anomaly_events=("unusual_query_flag", "sum"),
        )
        .reset_index()
    )

    return user_profiles

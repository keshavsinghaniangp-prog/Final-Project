import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from utils.config import DB_URI


def _read_table() -> pd.DataFrame:
    engine = create_engine(DB_URI)
    # Objective 4: SQL JOIN for role-based identity enrichment
    query = """
        SELECT
            q.*,
            e.full_name,
            e.department,
            e.job_role,
            e.risk_tier as user_baseline_risk
        FROM query_monitoring q
        INNER JOIN employees e ON q.user_id = e.user_id
    """
    return pd.read_sql(query, engine)


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if "anomaly_flag" in df.columns:
        df = df.rename(columns={"anomaly_flag": "unusual_query_flag"})
    if "id" in df.columns and "event_id" not in df.columns:
        df = df.rename(columns={"id": "event_id"})

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(["user_id", "timestamp"])

    # Calculate step per unique user
    df["user_timeline_step"] = df.groupby("user_id").cumcount() + 1
    return df


@st.cache_data(ttl=2)
def get_processed_data() -> pd.DataFrame:
    try:
        return _enrich(_read_table())
    except SQLAlchemyError as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame()

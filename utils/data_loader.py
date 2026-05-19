import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from utils.config import DB_URI


def _read_table() -> pd.DataFrame:
    engine = create_engine(DB_URI)
    # The table created by pipeline_mysql.py is called 'query_monitoring'
    return pd.read_sql("SELECT * FROM query_monitoring", engine)


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    if "anomaly_flag" in df.columns:
        df = df.rename(columns={"anomaly_flag": "unusual_query_flag"})
    if "id" in df.columns and "event_id" not in df.columns:
        df = df.rename(columns={"id": "event_id"})

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values(["user_id", "timestamp"])

    df["user_timeline_step"] = df.groupby("user_id").cumcount() + 1
    return df


@st.cache_data(ttl=2)
def get_processed_data() -> pd.DataFrame:
    try:
        return _enrich(_read_table())
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        return pd.DataFrame()

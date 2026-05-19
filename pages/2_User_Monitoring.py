from typing import cast

import pandas as pd
import plotly.express as px
import streamlit as st

from _bootstrap import ensure_project_root

ensure_project_root()

from utils.data_loader import get_processed_data  # noqa: E402
from utils.ui import (  # noqa: E402
    configure_page,
    metric_card,
    page_header,
    section_title,
    show_empty,
)


@st.cache_data(ttl=5)
def load_page_data():
    return get_processed_data()


configure_page("User Monitoring")

st.sidebar.header("Investigation")
df = load_page_data()

page_header(
    "User Monitoring",
    "Per-user resource access, behavioral indicators, and forensic audit records.",
    "Healthy" if not df.empty else "Awaiting Logs",
)

if df.empty:
    show_empty(
        "No records are available.",
        ["Confirm Docker MySQL is running and the pipeline has inserted rows."],
    )
    st.stop()

users = sorted(df["user_id"].astype(str).unique())
selected_user = st.sidebar.selectbox("User", users)
user_data = cast(
    pd.DataFrame, df[df["user_id"].astype(str) == selected_user]
).sort_values(by=["timestamp", "user_timeline_step"])

cols = st.columns(4)
with cols[0]:
    metric_card("Events", len(user_data), "Total user activity")
with cols[1]:
    metric_card("ML alerts", int(user_data["unusual_query_flag"].sum()))
with cols[2]:
    metric_card("Sensitive access", int(user_data["sensitive_data_access"].sum()))
with cols[3]:
    metric_card("After-hours", int(user_data["after_hours_access"].sum()))

section_title("Resource Profile")
table_counts = user_data["table_accessed"].value_counts().reset_index().head(10)
table_counts.columns = ["Table", "Events"]
fig = px.bar(
    table_counts,
    x="Events",
    y="Table",
    orientation="h",
    text="Events",
)
fig.update_layout(
    height=360,
    showlegend=False,
    margin=dict(t=10, b=10, l=10, r=10),
)
st.plotly_chart(fig, use_container_width=True)

section_title("Forensic Audit Log")
display_cols = [
    "timestamp",
    "user_id",
    "query_type",
    "table_accessed",
    "rows_returned",
    "after_hours_access",
    "sensitive_data_access",
    "unusual_query_flag",
    "query_text",
]
st.dataframe(
    user_data[[col for col in display_cols if col in user_data.columns]],
    hide_index=True,
    use_container_width=True,
)

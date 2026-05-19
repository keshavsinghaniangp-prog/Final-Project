import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import get_processed_data
from utils.ui import configure_page, metric_card, page_header, section_title, show_empty

# 1. Configuration
configure_page("User Monitoring")


# 2. Data Loading
@st.cache_data(ttl=5)
def load_monitoring_data():
    return get_processed_data()


df = load_monitoring_data()

if df.empty:
    page_header("User Monitoring", "Data Source Offline", "Offline")
    show_empty("No live records found in MySQL.", ["Ensure the pipeline is running."])
    st.stop()

# 3. Sidebar Selection (Identity-Based)
st.sidebar.header("Investigation")

# Extract unique users with their metadata
users_meta = (
    df[["user_id", "full_name", "department"]]
    .drop_duplicates()
    .sort_values("full_name")
)
user_options = {
    f"{row['full_name']} ({row['department']})": row["user_id"]
    for _, row in users_meta.iterrows()
}

selected_label = st.sidebar.selectbox("Select Employee", list(user_options.keys()))
selected_uid = user_options[selected_label]

# Filter individual data
user_data = df[df["user_id"] == selected_uid].sort_values("timestamp", ascending=False)

# 4. Header
page_header("Forensic View", f"Detailed activity audit for {selected_label}", "Healthy")

# 5. Metric Summary (Individual)
cols = st.columns(4)
with cols[0]:
    metric_card("Total Events", len(user_data), "Captured queries")
with cols[1]:
    metric_card(
        "ML Flagged", int(user_data["unusual_query_flag"].sum()), "Anomalous actions"
    )
with cols[2]:
    metric_card(
        "Sensitive Access",
        int(user_data["sensitive_data_access"].sum()),
        "High-value tables",
    )
with cols[3]:
    metric_card(
        "Exfil Signals",
        int(user_data["data_exfiltration_pattern"].sum()),
        "Data leak patterns",
    )

st.write("---")

# 6. Interaction Profile
section_title("Database Resource Interaction Profile")
vol_data = user_data["table_accessed"].value_counts().reset_index()
vol_data.columns = ["Resource (Table)", "Query Count"]

fig_vol = px.bar(
    vol_data,
    x="Query Count",
    y="Resource (Table)",
    orientation="h",
    color="Query Count",
    color_continuous_scale="Blues",
)
fig_vol.update_layout(height=400, showlegend=False)
st.plotly_chart(fig_vol, use_container_width=True)

# 7. Forensic Audit Table
section_title("Chronological Forensic Audit Log")

# Select relevant columns for the audit
audit_cols = [
    "timestamp",
    "query_type",
    "table_accessed",
    "rows_returned",
    "after_hours_access",
    "sensitive_data_access",
    "unusual_query_flag",
    "query_text",
]

display_audit = user_data[audit_cols].rename(
    columns={
        "unusual_query_flag": "ML Flag",
        "timestamp": "Time",
        "query_type": "Type",
        "table_accessed": "Target",
        "query_text": "Executed SQL String",
    }
)

st.dataframe(display_audit, use_container_width=True, hide_index=True)

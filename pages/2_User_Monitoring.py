from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

from utils.config import DB_URI
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

users_meta = (
    df[["user_id", "full_name", "department"]]
    .drop_duplicates()
    .sort_values(by="full_name")
)
user_options = {
    f"{row['full_name']} ({row['department']})": row["user_id"]
    for _, row in users_meta.iterrows()
}

selected_label = st.sidebar.selectbox("Select Employee", list(user_options.keys()))
selected_uid = user_options[selected_label]

user_data = df[df["user_id"] == selected_uid].sort_values(
    by="timestamp", ascending=False
)

# 4. Header
page_header("Forensic View", f"Detailed activity audit for {selected_label}", "Healthy")

# 5. Metric Summary
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
    # Add a mock velocity display
    metric_card("Avg Velocity", f"{len(user_data) / 10:.1f} q/m", "Query frequency")

st.write("---")

# 6. Interaction Profile & Metadata
c1, c2 = st.columns([1, 1])

with c1:
    section_title("Database Resource Interaction Profile")
    vol_data = user_data["table_accessed"].value_counts().reset_index()
    vol_data.columns = ["Resource", "Count"]
    fig_vol = px.bar(
        vol_data,
        x="Count",
        y="Resource",
        orientation="h",
        color="Count",
        color_continuous_scale="Blues",
    )
    fig_vol.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_vol, use_container_width=True)

with c2:
    section_title("Connection Metadata")
    # Show unique IPs and Apps used
    meta_df = user_data[["source_ip", "client_app"]].drop_duplicates()
    st.dataframe(
        meta_df.rename(
            columns={"source_ip": "Source IP", "client_app": "Client Application"}
        ),
        use_container_width=True,
        hide_index=True,
    )
    if len(meta_df) > 1:
        st.warning(
            "⚠️ **Security Alert:** Multiple IPs/Apps detected for this user session."
        )

# 7. ANALYST FEEDBACK LOOP
section_title("🛡️ Security Admin Feedback Loop")
st.markdown("Select a flagged incident to verify or dismiss the ML prediction.")

# Get flagged queries only for feedback
flagged_queries = user_data[user_data["unusual_query_flag"] == 1].head(10)

if flagged_queries.empty:
    st.success("No flagged queries pending review for this user.")
else:
    with st.form("feedback_form"):
        target_query_id = st.selectbox(
            "Select Incident ID to Review", flagged_queries["id"].tolist()
        )
        feedback_label = st.radio(
            "Verdict",
            ["Confirm Threat", "False Positive", "Benign Outlier"],
            horizontal=True,
        )
        feedback_comment = st.text_area(
            "Analyst Comments", placeholder="Describe why this is/isn't a threat..."
        )

        submit_btn = st.form_submit_button("Submit Verdict")

        if submit_btn:
            try:
                engine = create_engine(DB_URI)
                with engine.connect() as conn:
                    conn.execute(
                        text("""
                        INSERT INTO analyst_feedback (query_id, analyst_label, comments, timestamp)
                        VALUES (:qid, :label, :comment, :ts)
                    """),
                        {
                            "qid": target_query_id,
                            "label": feedback_label,
                            "comment": feedback_comment,
                            "ts": datetime.now(),
                        },
                    )
                    conn.commit()
                st.success(
                    f"✅ Verdict for ID {target_query_id} saved. This feedback will be used to retrain the ML model."
                )
            except Exception as e:
                st.error(f"Failed to save feedback: {e}")

# 8. Forensic Audit Table
section_title("Chronological Forensic Audit Log")
audit_cols = [
    "timestamp",
    "source_ip",
    "client_app",
    "query_type",
    "table_accessed",
    "unusual_query_flag",
    "query_text",
]
display_audit = user_data[audit_cols].copy()
display_audit = display_audit.rename(
    columns={
        "unusual_query_flag": "ML Flag",
        "timestamp": "Time",
        "query_type": "Type",
        "table_accessed": "Target",
        "query_text": "Executed SQL String",
    }
)
st.dataframe(display_audit, use_container_width=True, hide_index=True)

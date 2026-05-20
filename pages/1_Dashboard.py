import pandas as pd
import plotly.express as px
import streamlit as st

from scripts.feature_engineering import engineer_user_features
from scripts.risk_scoring import calculate_risk_scores
from utils.config import RISK_COLORS
from utils.data_loader import get_processed_data
from utils.ui import configure_page, page_header, section_title, show_empty

# 1. Configuration
configure_page("Risk Posture")


# 2. Data Loading & Dual-Tier Processing
@st.cache_data(ttl=5)
def load_all_metrics():
    # Tier 0: Get Raw Relational Data from MySQL
    df = get_processed_data()
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Tier 2: User-Level Behavioral Profiling + Peer Group Analysis + Velocity
    user_features = engineer_user_features(df)
    risk_df = calculate_risk_scores(user_features)

    return df, risk_df


df, risk_df = load_all_metrics()

# 3. Header
page_header(
    "Risk Posture",
    "Behavioral risk analysis with Explainable AI (XAI) and Peer-Group normalization.",
    "Healthy" if not df.empty else "Awaiting Logs",
)

if df.empty:
    show_empty(
        "No live monitoring data is available.",
        ["Ensure Docker MySQL, the Log Generator, and the Pipeline are running."],
    )
    st.stop()

# 4. Top KPI Metric Cards
m1, m2, m3, m4 = st.columns(4)

total_users = len(risk_df)
high_risk = len(risk_df[risk_df["risk_level"] == "High Risk"])
med_risk = len(risk_df[risk_df["risk_level"] == "Medium Risk"])
low_risk = len(risk_df[risk_df["risk_level"] == "Low Risk"])

with m1:
    st.metric("Users Monitored", total_users)
with m2:
    st.metric("High Risk Profile", high_risk, delta=high_risk, delta_color="inverse")
with m3:
    st.metric("Medium Risk Profile", med_risk)
with m4:
    st.metric("Low Risk Profile", low_risk)

st.write("---")

# 5. Visualizations
c1, c2 = st.columns([1, 1.4])

with c1:
    section_title("Risk Tier Distribution")
    fig_pie = px.pie(
        risk_df,
        names="risk_level",
        hole=0.6,
        color="risk_level",
        color_discrete_map=RISK_COLORS,
    )
    fig_pie.update_layout(
        height=400, showlegend=True, legend=dict(orientation="h", y=-0.1)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    section_title("Risk Contributor Analysis (XAI)")
    # Show summary of SHAP top reasons across the organization
    xai_summary = risk_df["top_risk_reason"].value_counts().reset_index()
    xai_summary.columns = ["Risk Driver", "Impacted Users"]

    fig_xai = px.bar(
        xai_summary,
        x="Impacted Users",
        y="Risk Driver",
        orientation="h",
        color="Impacted Users",
        color_continuous_scale="Reds",
    )
    fig_xai.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_xai, use_container_width=True)

# 6. Critical User Table with XAI Explanations
section_title("Behavioral Risk Profile Audit")
st.info(
    "💡 **XAI Insight:** The 'Primary Risk Driver' is calculated using SHAP values from the behavioral model."
)

display_df = risk_df[
    [
        "full_name",
        "department",
        "risk_score",
        "risk_level",
        "top_risk_reason",
        "total_queries",
    ]
].copy()

display_df = display_df.rename(
    columns={
        "full_name": "Employee Name",
        "department": "Department",
        "risk_score": "Risk Score",
        "risk_level": "Tier",
        "top_risk_reason": "Primary Risk Driver",
        "total_queries": "Event Count",
    }
)

st.dataframe(display_df, use_container_width=True, hide_index=True)

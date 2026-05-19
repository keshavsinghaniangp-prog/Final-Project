from typing import cast

import pandas as pd
import plotly.express as px
import streamlit as st

from _bootstrap import ensure_project_root

ensure_project_root()

from utils.config import RISK_COLORS  # noqa: E402
from utils.data_loader import get_processed_data  # noqa: E402
from utils.risk import summarize_risk  # noqa: E402
from utils.ui import (  # noqa: E402
    configure_page,
    metric_card,
    page_header,
    section_title,
    show_empty,
)


@st.cache_data(ttl=5)
def load_page_data():
    df = get_processed_data()
    return df, summarize_risk(df)


configure_page("Risk Posture")
df, risk = load_page_data()

page_header(
    "Risk Posture",
    "User-level scoring based on ML anomalies, sensitive access, and exfiltration signals.",
    "Healthy" if not df.empty else "Awaiting Logs",
)

if df.empty:
    show_empty(
        "No live monitoring data is available.",
        ["Start the generator and MySQL pipeline, then refresh this page."],
    )
    st.stop()

cols = st.columns(4)
with cols[0]:
    metric_card("Users monitored", risk["total_users"], "Unique users in Docker MySQL")
with cols[1]:
    metric_card("High risk", risk["high_risk_users"], "Top quartile by risk score")
with cols[2]:
    metric_card("Medium risk", risk["medium_risk_users"], "Elevated behavior profile")
with cols[3]:
    metric_card("Low risk", risk["low_risk_users"], "Lowest relative risk group")

chart_cols = st.columns([1, 1.4])
with chart_cols[0]:
    section_title("Risk Tiers")
    fig = px.pie(
        risk["risk_distribution"],
        names="Risk Level",
        values="Count",
        hole=0.58,
        color="Risk Level",
        color_discrete_map=RISK_COLORS,
    )
    fig.update_layout(
        height=390,
        margin=dict(t=10, b=10, l=10, r=10),
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_traces(
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>Users: %{value}<extra></extra>",
    )
    st.plotly_chart(fig, use_container_width=True)

with chart_cols[1]:
    section_title("Risk Contributors")
    fig = px.bar(
        risk["risk_contributors"],
        x="Count",
        y="Factor",
        orientation="h",
        text="Count",
        color="Factor",
    )
    fig.update_layout(
        height=390,
        showlegend=False,
        xaxis_title="Events",
        yaxis_title="",
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

section_title("Highest Risk Users")
profile = risk["user_risk_profile"].copy()
profile["risk_score"] = profile["risk_score"].round(1)
profile["anomaly_rate"] = (profile["anomaly_rate"] * 100).round(1)
profile["sensitive_rate"] = (profile["sensitive_rate"] * 100).round(1)

display_profile = cast(
    pd.DataFrame,
    profile[
        [
            "user_id",
            "risk_level",
            "risk_score",
            "total_events",
            "anomaly_events",
            "anomaly_rate",
            "sensitive_rate",
        ]
    ],
).rename(
    columns={
        "user_id": "User",
        "risk_level": "Risk Level",
        "risk_score": "Risk Score",
        "total_events": "Events",
        "anomaly_events": "ML Alerts",
        "anomaly_rate": "Alert Rate %",
        "sensitive_rate": "Sensitive Access %",
    }
)

st.dataframe(
    display_profile,
    hide_index=True,
    use_container_width=True,
)

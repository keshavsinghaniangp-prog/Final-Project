from datetime import datetime
from typing import cast

import pandas as pd
import streamlit as st

from _bootstrap import ensure_project_root

ensure_project_root()

from utils.data_loader import get_processed_data  # noqa: E402
from utils.pdf_generator import generate_pdf  # noqa: E402
from utils.ui import (  # noqa: E402
    configure_page,
    metric_card,
    page_header,
    section_title,
    show_empty,
)


def _series(df: pd.DataFrame, column: str) -> pd.Series:
    return cast(pd.Series, df[column])


def _frame(df: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    return cast(pd.DataFrame, df[mask]).copy()


@st.cache_data(ttl=5)
def load_alerts() -> pd.DataFrame:
    df = get_processed_data()
    if df.empty:
        return pd.DataFrame()

    critical = _frame(df, _series(df, "unusual_query_flag") == 1)
    critical["severity"] = "High"

    warning_mask = (
        (_series(df, "failed_login_attempt") == 1)
        | (
            (_series(df, "after_hours_access") == 1)
            & (_series(df, "sensitive_data_access") == 1)
        )
    ) & (_series(df, "unusual_query_flag") == 0)
    warning = _frame(df, warning_mask)
    warning["severity"] = "Medium"

    alerts = pd.concat([critical, warning], ignore_index=True)
    if alerts.empty:
        return alerts
    return cast(pd.DataFrame, alerts).sort_values(by=["timestamp"], ascending=False)


configure_page("Alerts Center")
alerts = load_alerts()

page_header(
    "Alerts Center",
    "Prioritized incidents generated from live ML and behavioral rules.",
    "Healthy" if not alerts.empty else "Awaiting Alerts",
)

if alerts.empty:
    show_empty(
        "No high or medium priority alerts are currently active.",
        ["New alerts will appear as the pipeline processes suspicious logs."],
    )
    st.stop()

high_count = int((alerts["severity"] == "High").sum())
medium_count = int((alerts["severity"] == "Medium").sum())

cols = st.columns(4)
with cols[0]:
    metric_card("High alerts", high_count, "ML anomaly predictions")
with cols[1]:
    metric_card("Medium alerts", medium_count, "Behavioral rule matches")
with cols[2]:
    metric_card("After-hours", int(alerts["after_hours_access"].sum()))
with cols[3]:
    metric_card("Sensitive access", int(alerts["sensitive_data_access"].sum()))

section_title("Filters")
f1, f2, f3 = st.columns(3)
with f1:
    severity_filter = st.multiselect(
        "Severity",
        ["High", "Medium"],
        default=["High", "Medium"],
    )
with f2:
    table_filter = st.multiselect(
        "Table",
        sorted(alerts["table_accessed"].astype(str).unique()),
    )
with f3:
    user_search = st.text_input("User contains")

filtered = _frame(alerts, _series(alerts, "severity").isin(severity_filter))
if table_filter:
    filtered = _frame(filtered, _series(filtered, "table_accessed").isin(table_filter))
if user_search:
    filtered = _frame(
        filtered,
        _series(filtered, "user_id").astype(str).str.contains(user_search, case=False),
    )

section_title(f"Active Incidents ({len(filtered)})")
incident_cols = [
    "timestamp",
    "severity",
    "full_name",
    "department",
    "query_type",
    "table_accessed",
    "rows_returned",
]
st.dataframe(
    filtered[incident_cols],
    hide_index=True,
    use_container_width=True,
)

section_title("Export")
st.write(
    f"Last scan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
    "Generate a report from the currently filtered incidents."
)

if st.button("Generate PDF report", type="primary"):
    if filtered.empty:
        st.warning("No incidents match the current filters.")
    else:
        report = cast(pd.DataFrame, filtered[incident_cols].copy())
        report["timestamp"] = _series(report, "timestamp").dt.strftime("%Y-%m-%d %H:%M")
        filename = generate_pdf(
            report,
            filename=f"DAM_Security_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        )
        with open(filename, "rb") as report_file:
            st.download_button(
                "Download report",
                data=report_file,
                file_name=filename,
                mime="application/pdf",
            )

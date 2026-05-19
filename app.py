import streamlit as st

from utils.config import APP_TITLE
from utils.data_loader import get_processed_data
from utils.ui import configure_page, metric_card, page_header, section_title, show_empty


@st.cache_data(ttl=5)
def load_overview() -> dict[str, object]:
    df = get_processed_data()
    if df.empty:
        return {
            "status": "Awaiting Logs",
            "active_users": 0,
            "events": 0,
            "alerts": 0,
            "last_seen": None,
        }

    return {
        "status": "Healthy",
        "active_users": int(df["user_id"].nunique()),
        "events": len(df),
        "alerts": int(df["unusual_query_flag"].sum()),
        "last_seen": df["timestamp"].max() if "timestamp" in df else None,
    }


configure_page("Overview")
overview = load_overview()

page_header(
    APP_TITLE,
    "Live query monitoring, anomaly detection, and user risk assessment.",
    str(overview["status"]),
)

cols = st.columns(4)
with cols[0]:
    metric_card("Active users", overview["active_users"], "Unique users in live logs")
with cols[1]:
    metric_card("Events processed", overview["events"], "Rows stored in Docker MySQL")
with cols[2]:
    metric_card("ML alerts", overview["alerts"], "Queries flagged by the model")
with cols[3]:
    last_seen = overview["last_seen"]
    last_seen_text = "No activity" if last_seen is None else str(last_seen)
    metric_card("Latest event", last_seen_text, "Most recent ingested log")

section_title("Security Workbench")

modules = [
    (
        "Risk Posture",
        "User risk tiers and global risk contributors.",
        "pages/1_Dashboard.py",
    ),
    (
        "User Monitoring",
        "Investigate individual timelines and query behavior.",
        "pages/2_User_Monitoring.py",
    ),
    (
        "Alerts Center",
        "Review critical and warning-level incidents.",
        "pages/3_Alerts.py",
    ),
    (
        "Query Console",
        "Inject test queries into the live log stream.",
        "pages/4_Query_Console.py",
    ),
]

nav_cols = st.columns(4)
for col, (title, description, page) in zip(nav_cols, modules, strict=True):
    with col:
        st.markdown(
            f"""
            <div class="dam-card">
                <div class="dam-card-label">{title}</div>
                <div class="dam-card-note">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Open {title}", key=page, use_container_width=True):
            st.switch_page(page)

if overview["status"] != "Healthy":
    show_empty(
        "The dashboard is running, but no live records are available yet.",
        [
            "Start Docker MySQL, backend/pipeline_mysql.py, and backend/generate_logs.py.",
            "The app reads from the live_query_monitoring table in Docker MySQL.",
        ],
    )

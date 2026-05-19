from datetime import datetime

import streamlit as st

from _bootstrap import ensure_project_root

ensure_project_root()

from utils.config import LOG_FILE, QUERY_TYPES  # noqa: E402
from utils.ui import (  # noqa: E402
    configure_page,
    metric_card,
    page_header,
    section_title,
)

PRESETS = {
    "Normal product lookup": "SELECT id, name FROM products WHERE id = 42",
    "Sensitive finance access": "SELECT account_balance FROM finance WHERE id = 12",
    "Exfiltration pattern": "SELECT * FROM salary WHERE 1=1",
    "Inventory update": "UPDATE inventory SET stock = 0 WHERE id = 55",
}


def normalize_query(query: str) -> tuple[str, str]:
    clean_query = " ".join(query.split())
    query_type = clean_query.split(" ", maxsplit=1)[0].upper()
    if query_type not in QUERY_TYPES:
        query_type = "UNKNOWN"
    return query_type, clean_query


def append_log(user_id: str, query: str) -> str:
    query_type, clean_query = normalize_query(query)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} {user_id.strip()} {query_type} {clean_query}\n"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(log_line)
    return log_line.strip()


configure_page("Query Console")
page_header(
    "Query Console",
    "Manual query injection for validating the live monitoring pipeline.",
    "Connected",
)

left, right = st.columns([0.9, 1.6])
with left:
    section_title("Session")
    user_id = st.text_input("User ID", value="user_99")
    preset_name = st.selectbox("Preset", list(PRESETS))
    metric_card("Log target", str(LOG_FILE), "Pipeline input file")

with right:
    section_title("SQL")
    query_text = st.text_area(
        "Query",
        value=PRESETS[preset_name],
        height=220,
    )

    if st.button("Execute and log query", type="primary", use_container_width=True):
        if not user_id.strip():
            st.error("User ID is required.")
        elif not query_text.strip():
            st.error("Query is required.")
        else:
            log_entry = append_log(user_id, query_text)
            st.success("Query added to the live log stream.")
            st.code(log_entry, language="text")

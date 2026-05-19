import html
from collections.abc import Iterable

import streamlit as st

from utils.config import APP_SHORT_TITLE


BASE_CSS = """
<style>
    :root {
        --dam-text: #172033;
        --dam-muted: #64748b;
        --dam-border: #dbe3ef;
        --dam-soft: #f6f8fb;
        --dam-blue: #2563eb;
        --dam-green: #16a34a;
        --dam-orange: #d97706;
        --dam-red: #dc2626;
    }

    .main .block-container {
        padding: 1.6rem 2.2rem 2.4rem;
        max-width: 1320px;
    }

    h1, h2, h3 {
        color: var(--dam-text);
        letter-spacing: 0;
    }

    .dam-header {
        border-bottom: 1px solid var(--dam-border);
        padding-bottom: 1rem;
        margin-bottom: 1.2rem;
    }

    .dam-title {
        color: var(--dam-text);
        font-size: 2rem;
        font-weight: 750;
        margin: 0;
    }

    .dam-subtitle {
        color: var(--dam-muted);
        font-size: 0.98rem;
        margin-top: 0.35rem;
    }

    .dam-status {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        border: 1px solid var(--dam-border);
        background: #ffffff;
        color: var(--dam-text);
        font-size: 0.82rem;
        font-weight: 650;
        margin-top: 0.75rem;
    }

    .dam-status.healthy { border-color: #bbf7d0; color: var(--dam-green); }
    .dam-status.warning { border-color: #fed7aa; color: var(--dam-orange); }
    .dam-status.offline { border-color: #fecaca; color: var(--dam-red); }

    .dam-card {
        background: #ffffff;
        border: 1px solid var(--dam-border);
        border-radius: 8px;
        padding: 1rem;
        min-height: 112px;
    }

    .dam-card-label {
        color: var(--dam-muted);
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .dam-card-value {
        color: var(--dam-text);
        font-size: 2rem;
        font-weight: 780;
        line-height: 1.1;
        margin-top: 0.45rem;
    }

    .dam-card-note {
        color: var(--dam-muted);
        font-size: 0.82rem;
        margin-top: 0.45rem;
    }

    .dam-section-title {
        color: var(--dam-text);
        font-size: 1.05rem;
        font-weight: 730;
        margin: 1.1rem 0 0.75rem;
    }

    .dam-alert {
        border: 1px solid var(--dam-border);
        border-left-width: 5px;
        border-radius: 8px;
        padding: 0.9rem 1rem;
        background: #ffffff;
    }

    .dam-alert.high { border-left-color: var(--dam-red); }
    .dam-alert.medium { border-left-color: var(--dam-orange); }
    .dam-alert.low { border-left-color: var(--dam-green); }

    div.stButton > button {
        border-radius: 8px;
        border: 1px solid var(--dam-border);
        min-height: 3rem;
        font-weight: 650;
    }
</style>
"""


def configure_page(title: str, icon: str = "shield") -> None:
    st.set_page_config(
        page_title=f"{title} | {APP_SHORT_TITLE}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(BASE_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str, status: str | None = None) -> None:
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    status_html = ""
    if status:
        state = "healthy" if status.lower() == "healthy" else "warning"
        if status.lower() in {"offline", "awaiting logs"}:
            state = "offline"
        status_html = (
            f"<div class='dam-status {state}'>{html.escape(status)}</div>"
        )
    st.markdown(
        f"""
        <div class="dam-header">
            <div class="dam-title">{safe_title}</div>
            <div class="dam-subtitle">{safe_subtitle}</div>
            {status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: object, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="dam-card">
            <div class="dam-card-label">{html.escape(label)}</div>
            <div class="dam-card-value">{html.escape(str(value))}</div>
            <div class="dam-card-note">{html.escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(
        f"<div class='dam-section-title'>{html.escape(text)}</div>",
        unsafe_allow_html=True,
    )


def show_empty(message: str, details: Iterable[str] | None = None) -> None:
    st.info(message)
    if details:
        for detail in details:
            st.caption(detail)

"""NorthStar account dashboard with internal and customer-facing views."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from components import dashboard_header, footer, inject_styles
from data import DataValidationError, load_metrics, period_summary
from external_dashboard import build_customer_dashboard_data, render_external_dashboard
from internal_dashboard import render_internal_dashboard


APP_DIR = Path(__file__).resolve().parent
CSV_PATH = APP_DIR / "northstar_flagship_30_day_metrics.csv"
INTERNAL_AUDIENCE = "Internal Dashboard — Fireworks Team"
EXTERNAL_AUDIENCE = "External Dashboard — Fireworks Team"


st.set_page_config(
    page_title="Northstar Account Intelligence | Fireworks",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_styles()


@st.cache_data(show_spinner=False)
def get_metrics(path: str, modified_at: float) -> pd.DataFrame:
    """Load the runtime CSV and invalidate the cache when it changes."""

    del modified_at
    return load_metrics(path)


try:
    modified_at = CSV_PATH.stat().st_mtime if CSV_PATH.exists() else 0.0
    data = get_metrics(str(CSV_PATH), modified_at)
except DataValidationError as exc:
    st.error("NorthStar data could not be loaded")
    st.markdown(f"**What to fix:** {exc}")
    st.caption(f"Expected file: {CSV_PATH}")
    st.stop()
except Exception as exc:  # Defensive boundary: keep failures useful inside the app.
    st.error("Unexpected dashboard error")
    st.markdown(f"The CSV could not be prepared: `{type(exc).__name__}: {exc}`")
    st.stop()


period = period_summary(data)
audience = dashboard_header(
    period.start,
    period.end,
    period.latest,
    internal_label=INTERNAL_AUDIENCE,
    external_label=EXTERNAL_AUDIENCE,
)

if audience == EXTERNAL_AUDIENCE:
    customer_data = build_customer_dashboard_data(data)
    render_external_dashboard(customer_data)
    footer(
        CSV_PATH.name,
        len(customer_data.daily),
        customer_data.period.latest,
        scope="Customer-facing demo · customer-safe fields only",
    )
else:
    render_internal_dashboard(data)
    footer(CSV_PATH.name, len(data), period.latest)

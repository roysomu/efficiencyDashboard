"""Customer-safe data boundary and presentation for the NorthStar dashboard.

The renderer in this module accepts only ``CustomerDashboardData``. The full
validated source frame, internal health score, general account notes, and
internal commercial or expansion artifacts never cross into the external
presentation. Two explicitly selected operational events are sanitized into
customer-facing expansion evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from types import MappingProxyType
from typing import Mapping

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import GREEN, GRID, MUTED, NAVY, PURPLE, chart_header, display_date, kpi_card, line_chart, section
from data import (
    SUPPLIED_ACCOUNT_OUTCOMES,
    PeriodSummary,
    change_summary,
    dashboard_metrics,
    period_summary,
    safe_mean,
)


# This is the complete set of runtime CSV fields that may enter the external
# daily presentation layer. In particular, deployment names and raw
# operational notes are intentionally excluded.
CUSTOMER_SAFE_DAILY_FIELDS = (
    "date",
    "requests",
    "total_tokens",
    "spend_usd",
    "p50_latency_ms",
    "p95_latency_ms",
    "error_rate_pct",
    "availability_pct",
    "tier1_tickets",
    "automated_tier1_tickets",
    "automation_rate_pct",
    "grounded_answer_rate_pct",
    "quality_eval_pass_rate_pct",
    "escalation_rate_pct",
)

# Document the information classes that must never be added to the external
# model without an explicit product/privacy review.
EXTERNAL_DATA_DENYLIST = (
    "operational_note",
    "account_health_score",
    "relationship_sentiment",
    "renewal_risk",
    "competitive_risk",
    "expansion_stage",
    "expansion_confidence",
    "support_cost",
    "staffing",
    "gross_margin",
    "revenue",
    "internal_owner_notes",
)

CUSTOMER_SAFE_EXPANSION_EVENT_DATES = MappingProxyType(
    {
        "catalog_sync": pd.Timestamp("2026-08-09"),
        "promotion_load": pd.Timestamp("2026-08-21"),
    }
)


@dataclass(frozen=True)
class ExpansionEvidence:
    """Sanitized, dated evidence used only for customer-facing pilot gates."""

    date: pd.Timestamp
    error_rate_pct: float
    p95_latency_ms: float
    grounded_answer_rate_pct: float
    quality_eval_pass_rate_pct: float
    note: str


@dataclass(frozen=True)
class CustomerDashboardData:
    """Sanitized evidence available to customer-facing render functions."""

    daily: pd.DataFrame
    period: PeriodSummary
    metrics: Mapping[str, float]
    averages: Mapping[str, float]
    changes: Mapping[str, Mapping[str, float]]
    supplied_outcomes: Mapping[str, float]
    expansion_evidence: Mapping[str, ExpansionEvidence]


def _safe_event_evidence(source: pd.DataFrame) -> Mapping[str, ExpansionEvidence]:
    """Extract only the dated operational evidence approved for expansion checks."""

    def evidence_for(row: pd.Series) -> ExpansionEvidence:
        note = row.get("operational_note", "")
        return ExpansionEvidence(
            date=pd.Timestamp(row["date"]),
            error_rate_pct=float(row["error_rate_pct"]),
            p95_latency_ms=float(row["p95_latency_ms"]),
            grounded_answer_rate_pct=float(row["grounded_answer_rate_pct"]),
            quality_eval_pass_rate_pct=float(row["quality_eval_pass_rate_pct"]),
            note=str(note).strip() if pd.notna(note) else "Not supplied",
        )

    evidence: dict[str, ExpansionEvidence] = {}
    for event_name, event_date in CUSTOMER_SAFE_EXPANSION_EVENT_DATES.items():
        matching_rows = source.loc[source["date"].eq(event_date)]
        if matching_rows.empty:
            raise ValueError(f"Customer expansion evidence is missing the {event_date.date()} record")
        evidence[event_name] = evidence_for(matching_rows.iloc[0])

    evidence["period_end_quality"] = evidence_for(source.sort_values("date").iloc[-1])
    return MappingProxyType(evidence)


def build_customer_dashboard_data(source: pd.DataFrame) -> CustomerDashboardData:
    """Create a customer-safe model from the validated runtime CSV.

    Daily calculations happen after column allowlisting. Expansion-event
    evidence is separately reduced to three immutable customer-safe records so
    a render function cannot access the raw source frame or general notes.
    """

    missing = sorted(set(CUSTOMER_SAFE_DAILY_FIELDS) - set(source.columns))
    if missing:
        raise ValueError("Customer dashboard is missing safe source fields: " + ", ".join(missing))

    safe_daily = source.loc[:, CUSTOMER_SAFE_DAILY_FIELDS].copy()
    period = period_summary(safe_daily)
    metrics = dashboard_metrics(safe_daily)
    averages = {
        "availability_pct": safe_mean(safe_daily, "availability_pct"),
        "error_rate_pct": safe_mean(safe_daily, "error_rate_pct"),
        "p50_latency_ms": safe_mean(safe_daily, "p50_latency_ms"),
        "p95_latency_ms": safe_mean(safe_daily, "p95_latency_ms"),
        "automation_rate_pct": safe_mean(safe_daily, "automation_rate_pct"),
        "grounded_answer_rate_pct": safe_mean(safe_daily, "grounded_answer_rate_pct"),
        "quality_eval_pass_rate_pct": safe_mean(safe_daily, "quality_eval_pass_rate_pct"),
        "escalation_rate_pct": safe_mean(safe_daily, "escalation_rate_pct"),
    }
    changes = {
        column: change_summary(safe_daily, column)
        for column in (
            "requests",
            "automation_rate_pct",
            "availability_pct",
            "error_rate_pct",
            "p50_latency_ms",
            "p95_latency_ms",
            "grounded_answer_rate_pct",
            "quality_eval_pass_rate_pct",
            "escalation_rate_pct",
            "spend_usd",
        )
    }

    return CustomerDashboardData(
        daily=safe_daily,
        period=period,
        metrics=MappingProxyType(metrics),
        averages=MappingProxyType(averages),
        changes=MappingProxyType({name: MappingProxyType(value) for name, value in changes.items()}),
        supplied_outcomes=MappingProxyType(dict(SUPPLIED_ACCOUNT_OUTCOMES)),
        expansion_evidence=_safe_event_evidence(source),
    )


def _number(value: float, decimals: int = 0) -> str:
    if pd.isna(value):
        return "Not available"
    return f"{value:,.{decimals}f}"


def _compact(value: float) -> str:
    if pd.isna(value):
        return "Not available"
    magnitude = abs(value)
    if magnitude >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if magnitude >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def _change_text(change: Mapping[str, float], *, suffix: str = "", decimals: int = 1) -> str:
    if pd.isna(change["absolute"]):
        return "First-to-last daily change unavailable"
    percent = f" ({change['percent']:+.1f}%)" if pd.notna(change["percent"]) else ""
    return f"{change['absolute']:+,.{decimals}f}{suffix}{percent} from first to last daily observation"


def _plot(
    data: CustomerDashboardData,
    column: str,
    title: str,
    value: str,
    *,
    color: str = PURPLE,
    suffix: str = "",
    prefix: str = "",
    fill: bool = False,
    key: str,
) -> None:
    chart_header(title, value, _change_text(data.changes[column], suffix=suffix))
    st.plotly_chart(
        line_chart(
            data.daily,
            column,
            title,
            color=color,
            y_suffix=suffix,
            y_prefix=prefix,
            fill=fill,
            height=300,
        ),
        width="stretch",
        key=key,
        config={"displayModeBar": False},
        alt=f"{title} over the supplied daily reporting period",
    )


def _executive_metric_card(label: str, value: str, detail: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="ns-exec-kpi">
          <div class="ns-exec-kpi-label">{escape(label)}</div>
          <div class="ns-exec-kpi-value">{escape(value)}</div>
          <div class="ns-exec-kpi-detail">{escape(detail)}</div>
          <span class="ns-exec-kpi-accent" style="background:{escape(accent)}"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _executive_panel_heading(title: str, meta: str) -> None:
    st.markdown(
        f'<div class="ns-exec-panel-head"><span class="ns-exec-panel-title">{escape(title)}</span>'
        f'<span class="ns-exec-panel-meta">{escape(meta)}</span></div>',
        unsafe_allow_html=True,
    )


def _executive_axis_dates(frame: pd.DataFrame) -> list[pd.Timestamp]:
    indices = sorted({0, len(frame) // 4, len(frame) // 2, len(frame) * 3 // 4, len(frame) - 1})
    return [frame.iloc[index]["date"] for index in indices]


def _executive_period_label(period: PeriodSummary) -> str:
    if period.start.year == period.end.year and period.start.month == period.end.month:
        return f"{display_date(period.start, include_year=False)}–{period.end.day}"
    return f"{display_date(period.start, include_year=False)}–{display_date(period.end, include_year=False)}"


def _usage_and_adoption_figure(data: CustomerDashboardData) -> go.Figure:
    frame = data.daily
    date_padding = pd.DateOffset(days=1)
    x_range = [frame["date"].min() - date_padding, frame["date"].max() + date_padding]
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=frame["date"],
            y=frame["tier1_tickets"],
            name="Tier-1 tickets",
            marker={"color": "#DCE6FB"},
            hovertemplate="%{x|%b %d, %Y}<br>Tier-1 tickets: %{y:,.0f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Bar(
            x=frame["date"],
            y=frame["automated_tier1_tickets"],
            name="Automated tickets",
            marker={"color": "#3567E8"},
            hovertemplate="%{x|%b %d, %Y}<br>Automated tickets: %{y:,.0f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["automation_rate_pct"],
            name="Automation rate",
            mode="lines",
            line={"color": "#17966F", "width": 2.4},
            yaxis="y2",
            hovertemplate="%{x|%b %d, %Y}<br>Automation rate: %{y:.1f}%<extra></extra>",
        )
    )
    tick_values = _executive_axis_dates(frame)
    figure.update_layout(
        height=315,
        margin={"l": 8, "r": 8, "t": 48, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        barmode="overlay",
        bargap=0.34,
        hovermode="x unified",
        font={"family": "Inter, sans-serif", "color": NAVY, "size": 11},
        legend={
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": 1.14,
            "yanchor": "top",
            "font": {"color": MUTED, "size": 10},
        },
        xaxis={
            "showgrid": False,
            "showline": False,
            "tickmode": "array",
            "tickvals": tick_values,
            "tickformat": "%b %-d",
            "tickfont": {"color": MUTED, "size": 10},
            "range": x_range,
        },
        yaxis={
            "gridcolor": GRID,
            "gridwidth": 1,
            "zeroline": False,
            "showline": False,
            "showticklabels": False,
            "rangemode": "tozero",
        },
        yaxis2={
            "overlaying": "y",
            "side": "right",
            "range": [0, 100],
            "showgrid": False,
            "showline": False,
            "showticklabels": False,
            "zeroline": False,
        },
    )
    return figure


def _daily_spend_figure(data: CustomerDashboardData) -> go.Figure:
    frame = data.daily
    date_padding = pd.DateOffset(days=1)
    x_range = [frame["date"].min() - date_padding, frame["date"].max() + date_padding]
    figure = go.Figure(
        go.Scatter(
            x=frame["date"],
            y=frame["spend_usd"],
            mode="lines",
            line={"color": "#3567E8", "width": 3},
            hovertemplate="%{x|%b %d, %Y}<br>Spend: $%{y:,.2f}<extra></extra>",
        )
    )
    tick_values = _executive_axis_dates(frame)
    figure.update_layout(
        height=315,
        margin={"l": 8, "r": 8, "t": 48, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="x unified",
        font={"family": "Inter, sans-serif", "color": NAVY, "size": 11},
        xaxis={
            "showgrid": False,
            "showline": False,
            "tickmode": "array",
            "tickvals": tick_values,
            "tickformat": "%b %-d",
            "tickfont": {"color": MUTED, "size": 10},
            "range": x_range,
        },
        yaxis={
            "gridcolor": GRID,
            "gridwidth": 1,
            "zeroline": False,
            "showline": False,
            "showticklabels": False,
        },
    )
    return figure


def _render_executive_overview(data: CustomerDashboardData) -> None:
    st.markdown('<div class="ns-exec-title">Executive Overview</div>', unsafe_allow_html=True)
    cards = st.columns(4, gap="medium")
    executive_cards = (
        (
            "Tier-1 tickets automated",
            f"{data.supplied_outcomes['tier1_automation_rate_pct']:.0f}%",
            "Deployment brief",
            "#3567E8",
        ),
        (
            "Average handle time improvement",
            f"{data.supplied_outcomes['handle_time_reduction_pct']:.0f}% lower",
            "Deployment brief",
            "#17966F",
        ),
        (
            "CSAT movement",
            f"+{data.supplied_outcomes['csat_lift_points']:.0f} points",
            "Deployment brief",
            "#B97618",
        ),
        (
            "Availability",
            f"{_number(data.averages['availability_pct'], 2)}% avg.",
            f"{data.period.days}-day average",
            "#17966F",
        ),
    )
    for column, (label, value, detail, accent) in zip(cards, executive_cards):
        with column:
            _executive_metric_card(label, value, detail, accent)

    period_label = _executive_period_label(data.period)
    usage_column, spend_column = st.columns([5, 3], gap="medium")
    with usage_column:
        with st.container(key="exec_usage_panel"):
            _executive_panel_heading("Usage and Tier-1 adoption", f"Daily · {period_label}")
            st.plotly_chart(
                _usage_and_adoption_figure(data),
                width="stretch",
                key="external_exec_usage_adoption",
                config={"displayModeBar": False},
                alt="Daily Tier-1 tickets, automated tickets, and automation rate",
            )
    with spend_column:
        with st.container(key="exec_spend_panel"):
            _executive_panel_heading("Daily spend", f"USD · {period_label}")
            st.plotly_chart(
                _daily_spend_figure(data),
                width="stretch",
                key="external_exec_spend",
                config={"displayModeBar": False},
                alt="Daily recorded spend across the reporting period",
            )

    steps_column, snapshot_column = st.columns([5, 3], gap="medium")
    with steps_column:
        st.markdown(
            """
            <div class="ns-exec-lower-panel">
              <div class="ns-exec-lower-head"><span class="ns-exec-lower-title">Joint next steps</span><span class="ns-exec-review">Review together</span></div>
              <div class="ns-exec-step"><div class="ns-exec-step-title">Agree on service targets</div><div class="ns-exec-step-owner">CX + Engineering</div><div class="ns-exec-step-status">To agree</div></div>
              <div class="ns-exec-step"><div class="ns-exec-step-title">Review evaluation coverage and escalations</div><div class="ns-exec-step-owner">CX + Engineering</div><div class="ns-exec-step-status">To agree</div></div>
              <div class="ns-exec-step"><div class="ns-exec-step-title">Confirm Everyday Home profile as proposed pilot</div><div class="ns-exec-step-owner">Joint team</div><div class="ns-exec-step-status">To agree</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with snapshot_column:
        st.markdown(
            f"""
            <div class="ns-exec-lower-panel">
              <div class="ns-exec-lower-head"><span class="ns-exec-lower-title">Service and quality snapshot</span></div>
              <div class="ns-exec-snapshot-row"><span class="ns-exec-snapshot-label">P95 latency</span><span class="ns-exec-snapshot-value">{_number(data.averages['p95_latency_ms'], 0)} ms avg.</span></div>
              <div class="ns-exec-snapshot-row"><span class="ns-exec-snapshot-label">Grounded answers</span><span class="ns-exec-snapshot-value">{_number(data.averages['grounded_answer_rate_pct'], 1)}% avg.</span></div>
              <div class="ns-exec-snapshot-row"><span class="ns-exec-snapshot-label">Evaluation pass rate</span><span class="ns-exec-snapshot-value">{_number(data.averages['quality_eval_pass_rate_pct'], 1)}% avg.</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_service_performance(data: CustomerDashboardData) -> None:
    section(
        "Service performance",
        "Observed volume, automation, and reliability",
        "Cards show reporting-period summaries; charts show daily observations from the runtime CSV.",
    )
    cards = st.columns(4)
    service_cards = (
        ("Total requests", _compact(data.metrics["total_requests"]), ""),
        ("Availability", f"{_number(data.averages['availability_pct'], 3)}%", ""),
        ("Error rate", f"{_number(data.averages['error_rate_pct'], 3)}%", ""),
        ("P95 latency", f"{_number(data.averages['p95_latency_ms'], 0)} ms", ""),
    )
    for column, (label, value, status) in zip(cards, service_cards):
        with column:
            kpi_card(label, value, "Calculated from the supplied daily records.", status, "neutral")

    first, second = st.columns(2)
    with first:
        _plot(
            data,
            "requests",
            "Daily requests",
            f"{_compact(data.metrics['total_requests'])} total",
            color=NAVY,
            fill=True,
            key="external_service_requests",
        )
    with second:
        _plot(
            data,
            "automation_rate_pct",
            "Daily automation rate",
            f"{_number(data.averages['automation_rate_pct'], 1)}% mean",
            color=GREEN,
            suffix="%",
            key="external_service_automation",
        )

    first, second = st.columns(2)
    with first:
        _plot(
            data,
            "availability_pct",
            "Daily availability",
            f"{_number(data.averages['availability_pct'], 3)}% mean",
            color=GREEN,
            suffix="%",
            key="external_service_availability",
        )
    with second:
        _plot(
            data,
            "error_rate_pct",
            "Daily error rate",
            f"{_number(data.averages['error_rate_pct'], 3)}% mean",
            suffix="%",
            key="external_service_errors",
        )

    first, second = st.columns(2)
    with first:
        _plot(
            data,
            "p50_latency_ms",
            "Daily P50 latency",
            f"{_number(data.averages['p50_latency_ms'], 0)} ms mean",
            color=NAVY,
            suffix=" ms",
            key="external_service_p50",
        )
    with second:
        _plot(
            data,
            "p95_latency_ms",
            "Daily P95 latency",
            f"{_number(data.averages['p95_latency_ms'], 0)} ms mean",
            suffix=" ms",
            key="external_service_p95",
        )


def _render_answer_quality(data: CustomerDashboardData) -> None:
    section(
        "Answer quality",
        "Observed grounding, evaluation, and escalation signals",
        "Summary cards show period averages; charts show the supplied daily observations.",
    )
    cards = st.columns(3)
    quality_cards = (
        ("Grounded-answer rate", "grounded_answer_rate_pct"),
        ("Evaluation pass rate", "quality_eval_pass_rate_pct"),
        ("Escalation rate", "escalation_rate_pct"),
    )
    for column, (label, field) in zip(cards, quality_cards):
        with column:
            kpi_card(
                label,
                f"{_number(data.averages[field], 1)}%",
                "Observed mean across the supplied daily reporting period.",
                "",
                "neutral",
            )

    first, second = st.columns(2)
    with first:
        _plot(
            data,
            "grounded_answer_rate_pct",
            "Daily grounded-answer rate",
            f"{_number(data.averages['grounded_answer_rate_pct'], 1)}% mean",
            color=GREEN,
            suffix="%",
            key="external_quality_grounding",
        )
    with second:
        _plot(
            data,
            "quality_eval_pass_rate_pct",
            "Daily evaluation pass rate",
            f"{_number(data.averages['quality_eval_pass_rate_pct'], 1)}% mean",
            color=NAVY,
            suffix="%",
            key="external_quality_eval",
        )

    _plot(
        data,
        "escalation_rate_pct",
        "Daily escalation rate",
        f"{_number(data.averages['escalation_rate_pct'], 1)}% mean",
        suffix="%",
        key="external_quality_escalation",
    )



def _risk_gate_card(
    index: int,
    title: str,
    badge: str,
    evidence: str,
    action: str,
    gate: str,
    *,
    tone: str = "amber",
) -> None:
    st.markdown(
        f"""
        <div class="ns-risk-card">
          <div class="ns-risk-card-head">
            <span class="ns-risk-index {escape(tone)}">{index}</span>
            <span class="ns-risk-card-title">{escape(title)}</span>
            <span class="ns-risk-badge {escape(tone)}">{escape(badge)}</span>
          </div>
          <div class="ns-risk-evidence">{escape(evidence)}</div>
          <div class="ns-risk-action-row"><span>Proposed action</span><p>{escape(action)}</p></div>
          <div class="ns-risk-gate-row"><span>Pilot gate</span><p>{escape(gate)}</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_risks_and_expansion(data: CustomerDashboardData) -> None:
    catalog = data.expansion_evidence["catalog_sync"]
    promotion = data.expansion_evidence["promotion_load"]
    quality = data.expansion_evidence["period_end_quality"]
    p95_change_pct = abs(data.changes["p95_latency_ms"]["percent"])

    st.markdown(
        """
        <div class="ns-risk-page-head">
          <div><div class="ns-risk-page-title">Risks &amp; Expansion</div>
          <div class="ns-risk-page-copy">Flagship outcomes support a next step; flagship operating lessons define the pilot gates.</div></div>
          <div class="ns-risk-page-meta">Customer view · joint planning</div>
        </div>
        <div class="ns-recommendation">
          <div class="ns-recommendation-main">
            <span class="ns-recommendation-kicker">Proposed first pilot</span>
            <div><strong>Everyday Home</strong><span>Recommend one controlled pilot, followed by sequential expansion if the agreed service and quality gates pass.</span></div>
          </div>
          <div class="ns-recommendation-side"><span>Illustrative — confirm with NorthStar</span><small>A pilot recommendation, not a four-brand rollout commitment</small></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="ns-risk-section-head"><div><strong>Why expand: flagship success evidence</strong>'
        '<span>Current deployment-brief results</span></div><small>Deployment brief</small></div>',
        unsafe_allow_html=True,
    )
    proof_columns = st.columns(3, gap="medium")
    proof_points = (
        ("Tier-1 automation", f"{data.supplied_outcomes['tier1_automation_rate_pct']:.0f}%", "of Tier-1 support volume"),
        ("Average handle time", f"{data.supplied_outcomes['handle_time_reduction_pct']:.0f}% lower", "reported improvement"),
        ("Customer satisfaction", f"+{data.supplied_outcomes['csat_lift_points']:.0f} points", "reported CSAT movement"),
    )
    for column, (label, value, detail) in zip(proof_columns, proof_points):
        with column:
            st.markdown(
                f'<div class="ns-proof-card"><div class="ns-proof-label">{escape(label)}</div>'
                f'<div class="ns-proof-value">{escape(value)}</div><div class="ns-proof-detail">{escape(detail)}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
        <div class="ns-operating-strip">
          <div><span class="ns-operating-dot"></span><strong>{data.period.days}-day operating evidence:</strong>
          {_number(data.averages['availability_pct'], 3)}% average availability ·
          {_number(data.averages['p95_latency_ms'], 0)} ms average P95 ·
          P95 improved {_number(p95_change_pct, 1)}% first-to-last.</div>
          <small>CSV observations; results describe the flagship only and do not guarantee another brand's results.</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="ns-profile-card">
          <div class="ns-profile-head"><strong>Proposed pilot profile · Everyday Home</strong><span>Illustrative assumptions pending NorthStar confirmation</span></div>
          <div class="ns-profile-grid">
            <div><small>Positioning</small><strong>Value-oriented</strong></div>
            <div><small>Monthly Tier-1 volume</small><strong>About 96K</strong></div>
            <div><small>Catalog</small><strong>About 8K SKUs · medium complexity</strong></div>
            <div><small>Tone</small><strong>Friendly · practical</strong></div>
            <div><small>Returns &amp; team</small><strong>Assumed 30-day standard · maturity 4/5</strong></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="ns-risk-section-head ns-risk-gates-head"><div><strong>Expansion risks and pilot gates</strong>'
        '<span>Flagship events were mitigated or adjusted; each now informs an expansion check.</span></div></div>',
        unsafe_allow_html=True,
    )
    risks_column, context_column = st.columns([2.15, 1], gap="medium")
    with risks_column:
        _risk_gate_card(
            1,
            "Catalog sync resilience",
            f"Flagship event · {display_date(catalog.date, include_year=False)}",
            f"The catalog-sync event recorded {catalog.error_rate_pct:.2f}% errors and {catalog.p95_latency_ms:,.0f} ms P95. Source note: {catalog.note}.",
            "Validate Everyday Home catalog freshness, stale-item handling, alerting, and recovery.",
            "Updates are observable and stale-item or retrieval failures are recoverable.",
        )
        _risk_gate_card(
            2,
            "Promotion-load resilience",
            f"Flagship event · {display_date(promotion.date, include_year=False)}",
            f"The promotion traffic event recorded {promotion.error_rate_pct:.2f}% errors. Source note: {promotion.note}.",
            "Confirm NorthStar's actual peak forecast and load-test against it.",
            "Agree error and latency limits, then validate them under representative load.",
        )
        _risk_gate_card(
            3,
            "Brand-specific answer quality",
            f"Flagship metrics · {display_date(quality.date, include_year=False)}",
            f"The flagship ended at {quality.grounded_answer_rate_pct:.1f}% grounded-answer rate and {quality.quality_eval_pass_rate_pct:.1f}% evaluation pass rate.",
            "Evaluate Everyday Home product questions, returns, policy exceptions, and handoffs before increasing automation.",
            "Meet agreed quality thresholds before raising automation.",
            tone="purple",
        )

    with context_column:
        st.markdown(
            f"""
            <div class="ns-context-card ns-spend-context">
              <div class="ns-context-title">Flagship spend context</div>
              <div class="ns-context-copy">Observed in the supplied {data.period.days}-day period</div>
              <div class="ns-spend-grid">
                <div><small>Period spend</small><strong>${_number(data.metrics['total_spend'], 0)}</strong></div>
                <div><small>Spend / request</small><strong>${_number(data.metrics['spend_per_request'], 4)}</strong></div>
              </div>
              <div class="ns-context-note">No budget target or expansion forecast supplied.</div>
            </div>
            <div class="ns-context-card ns-path-card">
              <div class="ns-context-title">Staged expansion path</div>
              <div class="ns-context-copy">Each step uses evidence from the previous one.</div>
              <div class="ns-path-step"><span>1</span><div>Confirm Everyday Home profile with NorthStar<small>Status: To agree</small></div></div>
              <div class="ns-path-step"><span>2</span><div>Agree service and quality gates<small>Status: To agree</small></div></div>
              <div class="ns-path-step"><span>3</span><div>Run a controlled, monitored pilot<small>Timing: To agree</small></div></div>
              <div class="ns-path-step"><span>4</span><div>Review results before selecting the next brand<small>Next brand: Not supplied</small></div></div>
              <div class="ns-path-foot">Sequential expansion · not a simultaneous rollout</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="ns-expansion-logic">
          <span>✓</span><div><strong>The expansion logic</strong><p>Flagship success supports the next step; its operating lessons set the gates. Expand to another brand only after Everyday Home meets agreed service, answer-quality, and readiness criteria.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_external_dashboard(data: CustomerDashboardData) -> None:
    """Render the four-tab customer-facing dashboard from sanitized data."""

    executive, service, quality, risks = st.tabs(
        ["Executive Overview", "Service Performance", "Answer Quality", "Risks & Expansion"],
        key="external_navigation",
    )
    with executive:
        _render_executive_overview(data)
    with service:
        _render_service_performance(data)
    with quality:
        _render_answer_quality(data)
    with risks:
        _render_risks_and_expansion(data)

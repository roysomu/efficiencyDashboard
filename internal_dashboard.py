"""Internal-only NorthStar account intelligence presentation.

This module intentionally owns planning assumptions, competitive hypotheses,
relationship coverage, staffing equivalents, and commercial scenarios. None of
these objects are imported by the customer-facing dashboard.
"""

from __future__ import annotations

from html import escape
from typing import Mapping

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import (
    AMBER,
    GREEN,
    NAVY,
    PURPLE,
    RED,
    chart_header,
    display_date,
    kpi_card,
    line_chart,
    section,
)
from data import (
    account_health_score,
    change_summary,
    dashboard_metrics,
    event_record,
    expansion_scenario,
)


BRAND_MULTIPLIERS = {
    "Everyday Home": 0.70,
    "Active": 0.55,
    "Luxe": 0.45,
    "Outlet": 0.30,
}


def _number(value: float, decimals: int = 0) -> str:
    if pd.isna(value):
        return "Not available"
    return f"{value:,.{decimals}f}"


def _compact(value: float) -> str:
    if pd.isna(value):
        return "Not available"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def _change(change: Mapping[str, float], *, suffix: str = "", decimals: int = 1) -> str:
    if pd.isna(change["absolute"]):
        return "Change unavailable"
    percent = f" ({change['percent']:+.1f}%)" if pd.notna(change["percent"]) else ""
    return f"{change['absolute']:+,.{decimals}f}{suffix}{percent} first-to-last"


def _notice(title: str, copy: str, *, tone: str = "assumption") -> None:
    st.markdown(
        f'<div class="ns-internal-notice {escape(tone)}"><strong>{escape(title)}</strong>'
        f'<span>{escape(copy)}</span></div>',
        unsafe_allow_html=True,
    )


def _panel(title: str, copy: str, *, meta: str = "", badge: str = "") -> None:
    badge_html = f'<span class="ns-mini-badge">{escape(badge)}</span>' if badge else ""
    meta_html = f'<div class="ns-priority-meta">{escape(meta)}</div>' if meta else ""
    st.markdown(
        f'<div class="ns-panel ns-internal-panel"><div class="ns-panel-title">{escape(title)}{badge_html}</div>'
        f'<p class="ns-panel-copy">{escape(copy)}</p>{meta_html}</div>',
        unsafe_allow_html=True,
    )


def _priority_card(index: str, title: str, copy: str, meta: str) -> None:
    st.markdown(
        f'<div class="ns-panel ns-priority-card"><div class="ns-priority-head">'
        f'<span class="ns-priority-index">{escape(index)}</span>{escape(title)}</div>'
        f'<div class="ns-priority-copy">{escape(copy)}</div>'
        f'<div class="ns-priority-meta">{escape(meta)}</div></div>',
        unsafe_allow_html=True,
    )


def _risk_card(
    code: str,
    title: str,
    evidence: str,
    action: str,
    meta: str,
    *,
    tone: str,
) -> None:
    st.markdown(
        f"""
        <div class="ns-internal-risk {escape(tone)}">
          <div class="ns-internal-risk-head"><span>{escape(code)}</span><strong>{escape(title)}</strong></div>
          <div class="ns-evidence-label">Evidence</div><p>{escape(evidence)}</p>
          <div class="ns-evidence-label">Next action</div><p>{escape(action)}</p>
          <div class="ns-priority-meta">{escape(meta)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _plot(
    frame: pd.DataFrame,
    column: str,
    title: str,
    *,
    color: str,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    fill: bool = False,
    key: str,
) -> None:
    change = change_summary(frame, column)
    chart_header(
        title,
        f"{prefix}{_number(change['last'], decimals)}{suffix}",
        _change(change, suffix=suffix, decimals=decimals),
    )
    st.plotly_chart(
        line_chart(
            frame,
            column,
            title,
            color=color,
            y_prefix=prefix,
            y_suffix=suffix,
            height=275,
            fill=fill,
        ),
        width="stretch",
        key=key,
        config={"displayModeBar": False},
        alt=f"{title} across the 31-day reporting period",
    )


def _render_overview(frame: pd.DataFrame) -> None:
    metrics = dashboard_metrics(frame)
    health = account_health_score(frame)
    p95_change = change_summary(frame, "p95_latency_ms")

    st.markdown(
        """
        <div class="ns-overview-head">
          <div><h2>Account overview</h2><p>Keep the executive summary concise; use links to move into the detailed tabs.</p></div>
          <span>TAB 1 / 5</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    kpi_specs = [
        ("Operational health", f"{health['weighted_total']:.1f} / 100", ""),
        ("Adoption", _compact(metrics["total_requests"]), f"requests · {metrics['request_change_pct']:+.1f}% first-to-last day"),
        ("Availability", f"{metrics['mean_availability']:.3f}%", "31-day mean"),
        ("P95 latency", f"{metrics['mean_p95_latency_ms']:,.0f} ms", f"31-day mean · down {abs(p95_change['percent']):.1f}% first-to-last"),
        ("Tier-1 automation", f"{metrics['weighted_automation_rate_pct']:.1f}%", ""),
    ]
    kpi_cols = st.columns(5, gap="medium")
    for column, (label, value, detail) in zip(kpi_cols, kpi_specs):
        with column:
            st.markdown(
                f'<div class="ns-overview-kpi"><span>{escape(label)}</span><strong>{escape(value)}</strong><small>{escape(detail)}</small></div>',
                unsafe_allow_html=True,
            )

    spend_col, priorities_col = st.columns([1.5, 1], gap="medium")
    with spend_col:
        with st.container(key="overview_spend_card"):
            spend_text, spend_chart = st.columns([1.25, 1], gap="small", vertical_alignment="center")
            with spend_text:
                st.markdown(
                    f"""
                    <div class="ns-overview-spend-copy"><h3>Spend / revenue reference</h3>
                    <strong>Recorded spend: ${metrics['total_spend']:,.2f}</strong>
                    <p>Customer spend; billed revenue proxy only if billable · no budget target</p></div>
                    """,
                    unsafe_allow_html=True,
                )
            with spend_chart:
                figure = go.Figure(
                    go.Scatter(
                        x=frame["date"],
                        y=frame["spend_usd"],
                        mode="lines",
                        line={"color": "#71809A", "width": 2.5, "shape": "spline", "smoothing": 0.35},
                        hovertemplate="%{x|%b %d}<br>$%{y:,.2f}<extra></extra>",
                    )
                )
                figure.update_layout(
                    height=118,
                    margin={"l": 2, "r": 2, "t": 4, "b": 22},
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    xaxis={
                        "tickvals": [frame["date"].iloc[0], frame["date"].iloc[-1]],
                        "ticktext": ["Aug 1", "Aug 31"],
                        "showgrid": False,
                        "showline": True,
                        "linecolor": "#E2E7EF",
                        "tickfont": {"size": 8, "color": "#8791A3"},
                        "fixedrange": True,
                    },
                    yaxis={
                        "showticklabels": False,
                        "gridcolor": "#EEF1F5",
                        "zeroline": False,
                        "fixedrange": True,
                    },
                )
                st.plotly_chart(
                    figure,
                    width="stretch",
                    key="overview_spend_sparkline",
                    config={"displayModeBar": False},
                    alt="Daily recorded spend from August 1 through August 31",
                )
    with priorities_col:
        st.markdown(
            """
            <div class="ns-wire-card ns-overview-main-card ns-overview-priorities-side">
              <h3>Top 3 priorities</h3>
              <p class="ns-wire-sub">Short summary only · evidence, mitigations, and full action log are in Risks &amp; Actions.</p>
              <div class="ns-overview-priority"><span class="technical">R1 · Technical</span><div><strong>Validate catalog-sync and promotion safeguards</strong><small>Engineering Lead · Nov 23</small></div></div>
              <div class="ns-overview-priority"><span>R2 · Relationship</span><div><strong>Confirm sponsor and decision-owner coverage</strong><small>Account Lead · Nov 25</small></div></div>
              <div class="ns-overview-priority"><span>R3 · Execution</span><div><strong>Stage rollout and validate delivery capacity</strong><small>Account + Eng + Support · Nov 30</small></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    decisions_col, expansion_col = st.columns([0.97, 1.03], gap="medium")
    with decisions_col:
        st.markdown(
            """
            <div class="ns-wire-card ns-overview-bottom-card">
              <h3>Leadership decisions needed</h3>
              <p class="ns-wire-sub">Decision requests only; no approvals were supplied.</p>
              <div class="ns-overview-decision"><strong>1&nbsp; Confirm Northstar Home pilot scope and quality gates</strong><small>Account + Engineering leadership · target Dec 4 (illustrative)</small></div>
              <div class="ns-overview-decision"><strong>2&nbsp; Reserve engineering and support capacity</strong><small>Engineering + Support Ops · target Dec 2 (illustrative)</small></div>
              <div class="ns-overview-link">Full decision log and completion evidence → Risks &amp; Actions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with expansion_col:
        st.markdown(
            """
            <div class="ns-wire-card ns-overview-bottom-card ns-overview-expansion-bottom">
              <h3>Expansion at a glance</h3>
              <p class="ns-wire-sub">Illustrative pipeline hypothesis · detailed profiles and gates are on Expansion.</p>
              <div class="ns-overview-pipeline"><strong>Northstar Home</strong><b>Pilot candidate</b><small>Weeks 1–4</small></div>
              <div class="ns-overview-pipeline"><strong>Active</strong><span>Discovery</span><small>Weeks 5–7</small></div>
              <div class="ns-overview-pipeline"><strong>Luxe</strong><span>Discovery</span><small>Weeks 8–10</small></div>
              <div class="ns-overview-pipeline"><strong>Outlet</strong><span>Readiness review</span><small>Weeks 11–13</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_performance(frame: pd.DataFrame) -> None:
    metrics = dashboard_metrics(frame)
    error_peak = frame.loc[frame["error_rate_pct"].idxmax()]
    section(
        "",
        "Performance",
        "",
    )
    _notice(
        "Performance navigation cue",
        "Read the detailed risk interpretation on Risks & Actions. The spend / revenue summary lives on Overview; only the distinct daily spend trend appears here.",
        tone="info",
    )

    pairs = [
        (("requests", "Requests & adoption", PURPLE, "", "", 0, True), ("availability_pct", "Availability", GREEN, "", "%", 3, False)),
        (("error_rate_pct", "Error rate", RED, "", "%", 2, False), ("p95_latency_ms", "P95 latency", AMBER, "", " ms", 0, False)),
        (("p50_latency_ms", "P50 latency", NAVY, "", " ms", 0, False), ("automation_rate_pct", "Tier-1 automation", GREEN, "", "%", 1, False)),
        (("avg_handle_time_min", "Average handle time", PURPLE, "", " min", 2, False), ("grounded_answer_rate_pct", "Grounded answers", PURPLE, "", "%", 1, False)),
        (("quality_eval_pass_rate_pct", "Evaluation pass rate", GREEN, "", "%", 1, False), ("escalation_rate_pct", "Escalation rate", AMBER, "", "%", 1, False)),
        (("spend_usd", "Daily recorded spend", NAVY, "$", "", 2, True), ("csat_score", "CSAT score", GREEN, "", "", 1, False)),
    ]
    for row_index, pair in enumerate(pairs):
        cols = st.columns(2, gap="medium")
        for column, spec in zip(cols, pair):
            metric, title, color, prefix, suffix, decimals, fill = spec
            with column:
                _plot(frame, metric, title, color=color, prefix=prefix, suffix=suffix, decimals=decimals, fill=fill, key=f"internal_perf_{row_index}_{metric}")

    st.caption(
        f"31-day references: {metrics['mean_availability']:.3f}% average availability · "
        f"{metrics['mean_p95_latency_ms']:,.0f} ms average P95 · "
        f"period-high error rate {error_peak['error_rate_pct']:.2f}% on {display_date(error_peak['date'], include_year=False)}."
    )


def _render_risks(frame: pd.DataFrame) -> None:
    catalog = event_record(frame, "2026-08-09")
    promotion = event_record(frame, "2026-08-21")
    section(
        "Internal operating plan",
        "Risks & Actions",
        "Evidence-backed flagship lessons, internal dependencies, and one dated action tracker.",
    )
    _notice(
        "Provisional planning fields",
        "Risk priorities, ratings, role owners, dates, and statuses are illustrative internal assumptions; the dated metrics and operational notes are from the CSV.",
    )

    risk_cols = st.columns(3, gap="medium")
    with risk_cols[0]:
        _risk_card(
            "R1 · P1",
            "Catalog sync and peak-load resilience",
            f"{display_date(catalog['date'], include_year=False)}: {catalog['error_rate_pct']:.2f}% errors and {catalog['p95_latency_ms']:,.0f} ms P95; source note says mitigated the same day. {display_date(promotion['date'], include_year=False)}: {promotion['error_rate_pct']:.2f}% errors; source note says the autoscaling threshold was adjusted.",
            "Verify recovery, catalog freshness, and load behavior before the Everyday Home pilot.",
            "Assumed owner: Engineering Lead · Illustrative target: Nov 23 · Rating: High / High (provisional)",
            tone="risk",
        )
    with risk_cols[1]:
        _risk_card(
            "R2 · P2",
            "Sponsor and decision coverage unverified",
            "No sponsor, economic buyer, policy owner, renewal date, or decision-process record was supplied.",
            "Map customer roles and confirm decision evidence before treating expansion as committed.",
            "Assumed owner: Account Lead · Illustrative target: Nov 25 · Rating: Medium / High (provisional)",
            tone="watch",
        )
    with risk_cols[2]:
        _risk_card(
            "R3 · P3",
            "Four-brand rollout capacity",
            "Engineering, Support, and approval capacity are not supplied for a four-brand sequence.",
            "Stage Everyday Home → Active → Luxe → Outlet and validate capacity at every gate.",
            "Assumed owners: Account + Engineering + Support · Illustrative target: Nov 30 · Rating: Medium / Medium (provisional)",
            tone="watch",
        )

    section("Dependencies", "Dependency register", "Customer roles and dates remain assumptions until NorthStar confirms them.")
    dependencies = pd.DataFrame(
        [
            ["Catalog feed, versioning, freshness", "Everyday Home, then all", "NorthStar Catalog + Engineering", "Nov 30", "Needs validation"],
            ["Policy source of truth and exceptions", "All; Outlet highest", "CX / Policy owner", "Nov 30", "Not confirmed"],
            ["Brand evaluation set and escalation rules", "Everyday Home first", "AI Engineering + CX", "Dec 2", "Not started"],
        ],
        columns=["Dependency", "Applies to", "Assumed owner", "Illustrative target", "Provisional status"],
    )
    st.dataframe(
        dependencies,
        hide_index=True,
        width="stretch",
        height=175,
        alt="Internal expansion dependency register",
    )

    section("Execution", "Action tracker", "Completion evidence is defined now; ownership and timing must be confirmed.")
    actions = pd.DataFrame(
        [
            ["Verify catalog and traffic safeguards", "Engineering Lead", "Nov 23", "In progress", "Follow-up test and mitigation notes"],
            ["Confirm sponsor and policy owners", "Account Lead", "Nov 25", "Not started", "Named roles and decision map"],
            ["Validate four profiles and confirm Everyday Home pilot", "Account + NorthStar", "Nov 30", "Not started", "Approved profile and pilot gates"],
            ["Estimate support coverage and cost", "Support Ops + Finance", "Dec 2", "Not started", "Validated input model"],
        ],
        columns=["Action", "Assumed owner", "Illustrative target", "Provisional status", "Completion evidence"],
    )
    st.dataframe(
        actions,
        hide_index=True,
        width="stretch",
        height=210,
        alt="Internal risk action tracker",
    )


def _render_expansion(frame: pd.DataFrame) -> None:
    section(
        "Internal scenario",
        "Expansion confidence & internal blockers",
        "Stage-gated plan. Flagship inputs are measured; additional-brand operating values are a static synthetic August baseline. Automation, spend, support, and economics remain illustrative.",
    )
    _notice(
        "Illustrative scenario — not a forecast",
        "The new-brand baseline is a one-time calculation from the supplied synthetic August CSVs. Readiness and every projection below require NorthStar and Fireworks validation.",
    )

    confidence, blockers = st.columns([0.75, 2.25], gap="medium")
    with confidence:
        st.markdown(
            """
            <div class="ns-confidence-card"><span>Expansion confidence</span><strong>65<small>/100</small></strong>
            <b>MEDIUM · ASSUMED</b><p>Everyday Home pilot confidence is positive; four-brand rollout confidence remains 40/100 until gates pass.</p></div>
            """,
            unsafe_allow_html=True,
        )
    with blockers:
        bcols = st.columns(2, gap="small")
        blocker_items = [
            ("Engineering burst test", "Validate 2× flagship baseline, autoscaling, concurrency, and P95 headroom."),
            ("RAG isolation and freshness", "Use brand-specific indexes, incremental refresh, stale-catalog alerts, and policy lineage."),
            ("Quality and safety", "Build brand evaluation sets for returns, product facts, tone, escalation, and abstention."),
            ("Delivery capacity", "Confirm Engineering and Support owners, capacity, on-call, rollback, and NorthStar approvers."),
        ]
        for col, (title, copy) in zip(bcols * 2, blocker_items):
            with col:
                _panel(title, copy, badge="Blocker")
        st.caption("Engineering effort assumption: 2 engineers × 3 weeks for platform work + 1 engineer × 1 week per brand.")

    st.markdown(
        '<div class="ns-score-formula"><strong>Assumed confidence inputs</strong><span>30% flagship value · 25% technical readiness · 20% sponsor access · 15% brand readiness · 10% economics. Unknown inputs are scored neutral or low.</span></div>',
        unsafe_allow_html=True,
    )

    section(
        "Workload",
        "Synthetic August operating baseline",
        "Static 31-day values calculated once from the supplied pre-expansion CSVs. These are synthetic planning inputs, not verified NorthStar actuals.",
    )
    operating_baseline = pd.DataFrame(
        [
            ["Everyday Home", 96_000, 9_449, "9.84%", "8.82 min", "78.61", "78.25%", "184.2", 77],
            ["Active", 78_886, 10_063, "12.76%", "10.58 min", "75.57", "71.87%", "290.6", 72],
            ["Luxe", 64_544, 11_629, "18.02%", "13.18 min", "72.67", "66.17%", "453.1", 75],
            ["Outlet", 43_029, 6_403, "14.88%", "9.67 min", "74.56", "69.78%", "380.6", 52],
        ],
        columns=[
            "Brand",
            "Tier-1 tickets",
            "Tier-2 escalations",
            "Escalation rate",
            "Weighted AHT",
            "Weighted CSAT",
            "Weighted FCR",
            "Avg backlog",
            "Active agents",
        ],
    )
    st.dataframe(
        operating_baseline,
        hide_index=True,
        width="stretch",
        height=178,
        alt="Synthetic August operating baseline for the four proposed expansion brands",
    )
    st.caption("Escalation rate uses total Tier-2 escalations ÷ total Tier-1 tickets. AHT, CSAT, and FCR are weighted by daily Tier-1 tickets; backlog is the 31-day daily mean.")

    projection_rows = [
        ["Everyday Home", "0.669×", 96_000, 65_280, 30_720, "$811.96", "Proposed pilot"],
        ["Active", "0.550×", 78_886, 53_642, 25_244, "$667.21", "After Everyday Home gate"],
        ["Luxe", "0.450×", 64_544, 43_890, 20_654, "$545.91", "After Active gate"],
        ["Outlet", "0.300×", 43_029, 29_260, 13_769, "$363.94", "After Luxe gate"],
        ["Four-brand increment", "1.969×", 282_459, 192_072, 90_387, "$2,389.02", "Illustrative total"],
        ["All five steady state", "2.969×", 425_889, 289_605, 136_284, "$3,602.14", "Illustrative run rate"],
    ]
    st.dataframe(
        pd.DataFrame(
            projection_rows,
            columns=[
                "Brand / scenario",
                "Vs. flagship",
                "Tier-1 tickets",
                "Automated @ 68%",
                "Residual tickets",
                "Serving-spend proxy",
                "Stage assumption",
            ],
        ),
        hide_index=True,
        width="stretch",
        height=280,
        alt="Static expansion workload and illustrative automation and serving-spend scenario",
    )
    st.caption("The four-brand baseline is 282,459 tickets, or 1.969× the 143,430-ticket flagship baseline. Automation applies the rounded 68.0% flagship rate. Serving spend scales the flagship's $1,213.12 recorded spend by ticket volume; setup and delivery costs are excluded.")

    section("Capacity", "Illustrative support projection", "Capacity equivalents are not a hiring plan or a Fireworks cost-of-goods estimate.")
    support_rows = [
        ["Flagship", 4_739, 29.6, "$151,662"],
        ["Four-brand increment", 12_579, 78.6, "$402,522"],
        ["All five", 17_318, 108.2, "$554,184"],
    ]
    st.dataframe(
        pd.DataFrame(support_rows, columns=["Scenario", "Support hours", "FTE-month equivalent", "NorthStar support-cost estimate"]),
        hide_index=True,
        width="stretch",
        height=175,
        alt="Illustrative NorthStar support capacity and cost projection",
    )
    st.caption("Assumptions: 68.0% automation · 80% human touch on residual tickets · brand-specific ticket-weighted AHT · $32/hour · 160 hours/FTE-month. New-brand totals use the synthetic baseline; flagship values retain the existing measured baseline.")

    section("Scenario economics", "Illustrative gross-margin case", "This scenario assumes recorded spend is billable revenue. Actual pricing, recognized revenue, and Fireworks COGS are unknown.")
    margin_rows = [
        ["Flagship", "$1,213", "$485", "$728"],
        ["Four-brand increment", "$2,389", "$956", "$1,433"],
        ["All five", "$3,602", "$1,441", "$2,161"],
    ]
    st.dataframe(
        pd.DataFrame(margin_rows, columns=["Scenario", "Billable-spend revenue proxy", "Modeled COGS", "Modeled gross profit"]),
        hide_index=True,
        width="stretch",
        height=175,
        alt="Illustrative gross-margin scenario assuming recorded spend is billable",
    )
    st.caption("Assumed gross-margin target: 60%. NorthStar support labor is separate. Validate actual revenue, COGS, Engineering, and CSM effort before reporting margin.")

    _panel(
        "Stage-gated go / no-go path",
        "Everyday Home pilot → prove P95 and quality under a 2× burst → confirm support coverage and source freshness → Active → Luxe → Outlet.",
        meta="Every gate, owner, timeline, and readiness state: To agree",
        badge="Illustrative",
    )


def _render_commercial_relationships(frame: pd.DataFrame) -> None:
    metrics = dashboard_metrics(frame)
    scenario = expansion_scenario(frame, BRAND_MULTIPLIERS)
    last = frame.sort_values("date").iloc[-1]
    section(
        "Restricted internal planning",
        "Commercial & Relationships",
        "Relationship, renewal, competitive, staffing, support-cost, and margin views are internal-only and are not available to the external renderer.",
    )
    _notice(
        "Assumption notice",
        "Relationship scores, stakeholder coverage, renewal status, competitor activity, billability, and financial scenarios are illustrative pending validation.",
    )

    rel, renewal = st.columns(2, gap="medium")
    with rel:
        _panel(
            "Relationship health · 70/100",
            "Assumed status: Watch / validate. Assumed coverage is 3 of 6 key roles: VP Customer Experience, VP Engineering, and Support Operations. Gaps: economic buyer, Security / AI Governance, and Brand Operations.",
            meta="No stakeholder map or relationship evidence supplied.",
            badge="Assumed",
        )
    with renewal:
        _panel(
            "Renewal and competitive position",
            "Renewal terms are unverified. Competitive risk is assumed medium–high. Illustrative evaluation set: AWS Bedrock, Together AI, and Anthropic direct; no shortlist or active evaluation was confirmed.",
            meta="Cost of waiting: delays readiness evidence and delivery-capacity decisions.",
            badge="Assumed",
        )

    section("Measured baseline", "Flagship account readout", "These values are calculated directly from the 31-day CSV; the brief’s rounded outcome remains separately labeled.")
    measured = st.columns(4, gap="medium")
    with measured[0]:
        kpi_card("Tier-1 tickets", f"{metrics['total_tier1_tickets']:,.0f}", "31-day measured total", "Measured", "good")
    with measured[1]:
        kpi_card("Automated tickets", f"{metrics['total_automated_tier1_tickets']:,.0f}", f"{metrics['weighted_automation_rate_pct']:.1f}% weighted CSV rate", "Measured", "good")
    with measured[2]:
        kpi_card("Recorded spend", f"${metrics['total_spend']:,.2f}", "Spend; not confirmed revenue", "Measured", "neutral")
    with measured[3]:
        kpi_card("Period-end operations", f"{last['automation_rate_pct']:.1f}%", f"Automation · {last['p95_latency_ms']:,.0f} ms P95", "Measured", "good")
    st.caption("Deployment brief outcome: rounded 70% Tier-1 automation. CSV weighted 31-day rate: 68.0%. These are different measures and are intentionally not conflated.")

    section("Illustrative model", "Support economics and staffing equivalent", "This models a NorthStar operating estimate—not Fireworks COGS and not a staffing recommendation.")
    flagship = scenario["flagship"]
    assumptions = scenario["assumptions"]
    econ = st.columns(3, gap="medium")
    with econ[0]:
        kpi_card("Human support hours", f"{flagship['support_hours']:,.0f}", f"{assumptions['human_touch_rate_pct']:.0f}% touch × nonautomated tickets × {assumptions['average_handle_time_min']:.2f} min", "Illustrative", "watch")
    with econ[1]:
        kpi_card("FTE-month equivalent", f"{flagship['fte_month_equivalent']:,.0f}", f"At {assumptions['fte_hours_per_month']:.0f} productive hours/month", "Illustrative", "watch")
    with econ[2]:
        kpi_card("Support-cost estimate", f"${flagship['support_cost']/1000:,.0f}K", f"At assumed ${assumptions['support_hourly_cost']:.0f}/hour", "Illustrative", "watch")

    section("Illustrative model", "Gross-margin assumption", "")
    margin = scenario["margin"]["flagship"]
    margin_cols = st.columns(3, gap="medium")
    labels = [
        ("Billable-spend revenue proxy", margin["revenue_proxy"], "Assumes recorded spend is billable"),
        ("Modeled COGS", margin["modeled_cogs"], "40% of proxy under 60% GM target"),
        ("Modeled gross profit", margin["modeled_gross_profit"], "Proxy less modeled COGS"),
    ]
    for col, (label, value, detail) in zip(margin_cols, labels):
        with col:
            kpi_card(label, f"${value:,.0f}", detail, "Illustrative", "watch")

    _panel(
        "Implementation guardrails",
        "Keep measured CSV values and scenarios separate. Label every state Confirmed, Assumed, Illustrative, To agree, or Not supplied. Require access control before deploying this internal route.",
        meta="Commercial and relationship evidence needed: contract, renewal, stakeholder map, pricing, recognized revenue, COGS, support model, and delivery allocation.",
        badge="Internal only",
    )


def render_internal_dashboard(frame: pd.DataFrame) -> None:
    """Render the five consolidated internal dashboard tabs."""

    overview, performance, risks, expansion, commercial = st.tabs(
        [
            "Overview",
            "Performance",
            "Risks & Actions",
            "Expansion",
            "Commercial & Relationships",
        ],
        key="dashboard_navigation",
    )
    with overview:
        _render_overview(frame)
    with performance:
        _render_performance(frame)
    with risks:
        _render_risks(frame)
    with expansion:
        _render_expansion(frame)
    with commercial:
        _render_commercial_relationships(frame)

"""Reusable presentation components for the NorthStar dashboard."""

from __future__ import annotations

from html import escape
from typing import Sequence

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


NAVY = "#17213A"
PURPLE = "#6D5CE7"
PURPLE_DARK = "#5142C7"
PURPLE_LIGHT = "#EEEAFE"
GREEN = "#14866D"
AMBER = "#B76E00"
RED = "#C24747"
MUTED = "#667085"
GRID = "#E9EAF0"


def inject_styles() -> None:
    st.html(
        """
        <style>
        :root {
            --ns-navy: #17213A;
            --ns-purple: #6D5CE7;
            --ns-purple-dark: #5142C7;
            --ns-purple-soft: #EEEAFE;
            --ns-bg: #F5F6FA;
            --ns-card: #FFFFFF;
            --ns-border: #E7E8EF;
            --ns-muted: #667085;
            --ns-green: #14866D;
            --ns-amber: #B76E00;
            --ns-red: #C24747;
        }
        .stApp { background: var(--ns-bg); color: var(--ns-navy); }
        .block-container { max-width: 1480px; padding: 2rem 2.4rem 4rem; }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"] { right: 1rem; }
        h1, h2, h3, h4, p, label, [data-testid="stMetricValue"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        h1, h2, h3 { color: var(--ns-navy); letter-spacing: -0.02em; }
        .ns-header {
            background: linear-gradient(125deg, #171E36 0%, #25204D 58%, #4A3F9C 100%);
            border: 1px solid rgba(255,255,255,.09); border-radius: 20px;
            color: white; padding: 1.35rem 1.55rem; margin-bottom: 1rem;
            box-shadow: 0 14px 32px rgba(30, 24, 75, .12);
        }
        .ns-header-top { display:flex; justify-content:space-between; gap:2rem; align-items:flex-start; }
        .ns-brand { display:flex; align-items:center; gap:.65rem; font-weight:700; font-size:1rem; color:white; margin-bottom:.8rem; }
        .ns-logo { width:28px; height:28px; border-radius:9px; background:linear-gradient(145deg,#9F8CFF,#6654E8); display:grid; place-items:center; box-shadow:inset 0 0 0 1px rgba(255,255,255,.25); }
        .ns-logo::before { content:"F"; color:#FFFFFF; font-size:.9rem; font-weight:800; line-height:1; }
        .ns-title { font-size:1.72rem; line-height:1.18; font-weight:750; letter-spacing:-.035em; margin:0 0 .35rem; color:white; }
        .ns-subtitle { color:#D7D4F4; font-size:.91rem; line-height:1.5; max-width:760px; margin:0; }
        .ns-meta { min-width:330px; display:grid; grid-template-columns:1fr 1fr; gap:.65rem; }
        .ns-meta-item { background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12); border-radius:12px; padding:.65rem .75rem; }
        .ns-meta-label { display:block; color:#BBB6E5; font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; margin-bottom:.18rem; }
        .ns-meta-value { color:white; font-size:.86rem; font-weight:650; }
        .ns-internal-pill { display:inline-flex; align-items:center; gap:.4rem; color:#E7E4FF; background:rgba(136,118,255,.18); border:1px solid rgba(173,160,255,.28); padding:.3rem .55rem; border-radius:999px; font-size:.72rem; font-weight:650; margin-bottom:.55rem; }
        .ns-internal-pill::before { content:""; width:6px; height:6px; border-radius:50%; background:#A99CFF; }
        .ns-section { margin:1.4rem 0 .75rem; }
        .ns-section-kicker { color:var(--ns-purple-dark); font-size:.72rem; font-weight:750; text-transform:uppercase; letter-spacing:.095em; margin-bottom:.18rem; }
        .ns-section-title { color:var(--ns-navy); font-size:1.18rem; font-weight:750; letter-spacing:-.02em; margin:0; }
        .ns-section-copy { color:var(--ns-muted); font-size:.84rem; margin-top:.24rem; }
        .ns-kpi { background:white; border:1px solid var(--ns-border); border-radius:16px; padding:1rem 1.05rem; min-height:154px; box-shadow:0 5px 18px rgba(24,30,58,.04); }
        .ns-kpi-top { display:flex; align-items:center; justify-content:space-between; gap:.75rem; }
        .ns-kpi-label { color:var(--ns-muted); font-size:.73rem; font-weight:700; text-transform:uppercase; letter-spacing:.075em; }
        .ns-status { font-size:.67rem; font-weight:750; padding:.25rem .46rem; border-radius:999px; white-space:nowrap; }
        .ns-status.good { color:#11725E; background:#E2F5F0; }
        .ns-status.watch { color:#975B00; background:#FFF1D8; }
        .ns-status.neutral { color:#5E6074; background:#EFF0F4; }
        .ns-status.risk { color:#A43B3B; background:#FBE7E7; }
        .ns-kpi-value { color:var(--ns-navy); font-size:1.72rem; line-height:1.2; font-weight:760; letter-spacing:-.035em; margin:.72rem 0 .28rem; }
        .ns-kpi-detail { color:var(--ns-muted); font-size:.78rem; line-height:1.45; }
        .ns-kpi-detail strong { color:var(--ns-navy); font-weight:700; }
        .ns-panel { background:white; border:1px solid var(--ns-border); border-radius:16px; padding:1rem 1.05rem; box-shadow:0 5px 18px rgba(24,30,58,.04); }
        .ns-panel-title { color:var(--ns-navy); font-size:.96rem; font-weight:750; margin:0 0 .25rem; }
        .ns-panel-copy { color:var(--ns-muted); font-size:.78rem; line-height:1.45; margin:0; }
        .ns-priority { border-top:1px solid var(--ns-border); padding:.78rem 0 .15rem; margin-top:.68rem; }
        .ns-priority-head { display:flex; align-items:center; gap:.55rem; color:var(--ns-navy); font-size:.82rem; font-weight:720; }
        .ns-priority-index { flex:0 0 auto; width:23px; height:23px; display:grid; place-items:center; background:var(--ns-purple-soft); color:var(--ns-purple-dark); border-radius:7px; font-size:.7rem; font-weight:800; }
        .ns-priority-copy { color:var(--ns-muted); font-size:.75rem; line-height:1.45; margin:.35rem 0 0 1.8rem; }
        .ns-priority-meta { color:#8A8E9E; font-size:.69rem; margin:.32rem 0 0 1.8rem; }
        .ns-signal { background:white; border:1px solid var(--ns-border); border-radius:15px; padding:.95rem 1rem; min-height:166px; border-top:3px solid var(--ns-purple); }
        .ns-signal-label { color:var(--ns-muted); font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.055em; }
        .ns-signal-value { color:var(--ns-navy); font-size:1.42rem; font-weight:760; margin:.48rem 0 .2rem; }
        .ns-signal-date { color:var(--ns-purple-dark); font-size:.75rem; font-weight:700; }
        .ns-signal-context { color:var(--ns-muted); font-size:.75rem; line-height:1.45; margin-top:.48rem; }
        .ns-unknown-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.75rem; }
        .ns-unknown { background:white; border:1px solid var(--ns-border); border-radius:13px; padding:.85rem .9rem; }
        .ns-unknown-label { color:var(--ns-muted); font-size:.72rem; }
        .ns-unknown-value { color:var(--ns-navy); font-size:.91rem; font-weight:720; margin:.22rem 0; }
        .ns-unknown-action { color:var(--ns-purple-dark); font-size:.72rem; }
        .ns-note { border-left:3px solid var(--ns-purple); background:#F8F7FF; border-radius:0 10px 10px 0; padding:.68rem .78rem; margin:.55rem 0; }
        .ns-note-date { color:var(--ns-purple-dark); font-size:.7rem; font-weight:750; }
        .ns-note-copy { color:var(--ns-navy); font-size:.78rem; line-height:1.42; margin-top:.16rem; }
        .ns-chart-summary { display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; margin-bottom:.25rem; }
        .ns-chart-title { color:var(--ns-navy); font-size:.93rem; font-weight:750; }
        .ns-chart-value { color:var(--ns-navy); font-size:1.2rem; font-weight:760; text-align:right; }
        .ns-chart-compare { color:var(--ns-muted); font-size:.7rem; text-align:right; }
        .ns-exec-title { color:var(--ns-navy); font-size:1.45rem; font-weight:780; letter-spacing:-.025em; margin:1.15rem 0 1rem; }
        .ns-exec-kpi { position:relative; overflow:hidden; background:white; border:1px solid #DEE3EC; border-radius:16px; padding:1rem 1.15rem; min-height:145px; box-shadow:0 4px 15px rgba(24,30,58,.025); }
        .ns-exec-kpi-label { color:#667085; font-size:.78rem; line-height:1.35; font-weight:700; }
        .ns-exec-kpi-value { color:var(--ns-navy); font-size:2rem; line-height:1.12; font-weight:780; letter-spacing:-.04em; margin:1.05rem 0 .55rem; }
        .ns-exec-kpi-detail { color:#667085; font-size:.73rem; }
        .ns-exec-kpi-accent { position:absolute; top:18px; right:5px; bottom:18px; width:4px; border-radius:999px; }
        :is(.st-key-exec_usage_panel, .st-key-exec_spend_panel) { background:white; border:1px solid #DEE3EC; border-radius:16px; padding:1rem 1rem .35rem; margin-top:1rem; box-shadow:0 4px 15px rgba(24,30,58,.025); }
        :is(.st-key-exec_usage_panel, .st-key-exec_spend_panel) .stPlotlyChart { background:transparent; border:0; border-radius:0; padding:0; box-shadow:none; }
        .ns-exec-panel-head { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin:.05rem 0 .15rem; }
        .ns-exec-panel-title { color:var(--ns-navy); font-size:1rem; font-weight:760; }
        .ns-exec-panel-meta { color:#667085; font-size:.7rem; white-space:nowrap; }
        .ns-exec-lower-panel { background:white; border:1px solid #DEE3EC; border-radius:16px; padding:1rem 1.15rem; min-height:272px; box-shadow:0 4px 15px rgba(24,30,58,.025); }
        .ns-exec-lower-head { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:1.15rem; }
        .ns-exec-lower-title { color:var(--ns-navy); font-size:1rem; font-weight:760; }
        .ns-exec-review { color:#3567E8; font-size:.7rem; font-weight:750; }
        .ns-exec-step { display:grid; grid-template-columns:1fr auto; gap:.35rem 1rem; padding:.72rem 0; border-bottom:1px solid #E8EBF1; }
        .ns-exec-step:last-child { border-bottom:0; padding-bottom:0; }
        .ns-exec-step-title { color:#344054; font-size:.77rem; font-weight:720; }
        .ns-exec-step-owner { color:#667085; font-size:.68rem; }
        .ns-exec-step-status { color:#667085; font-size:.68rem; align-self:center; grid-column:2; grid-row:1 / span 2; }
        .ns-exec-snapshot-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.82rem 0; }
        .ns-exec-snapshot-label { color:#667085; font-size:.73rem; }
        .ns-exec-snapshot-value { color:var(--ns-navy); font-size:.75rem; font-weight:760; text-align:right; }
        .ns-risk-page-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:1.15rem 0 .85rem; }
        .ns-risk-page-title { color:var(--ns-navy); font-size:1.45rem; line-height:1.15; font-weight:780; letter-spacing:-.025em; }
        .ns-risk-page-copy { color:var(--ns-muted); font-size:.8rem; margin-top:.28rem; }
        .ns-risk-page-meta { color:#7D8394; font-size:.68rem; white-space:nowrap; }
        .ns-recommendation { display:flex; align-items:center; justify-content:space-between; gap:1.25rem; background:white; border:1px solid #DEE3EC; border-left:5px solid var(--ns-purple); border-radius:14px; padding:.85rem 1rem; box-shadow:0 5px 18px rgba(24,30,58,.04); }
        .ns-recommendation-main { min-width:0; }
        .ns-recommendation-kicker { display:inline-flex; color:var(--ns-purple-dark); background:var(--ns-purple-soft); border-radius:999px; padding:.25rem .52rem; font-size:.62rem; line-height:1; font-weight:800; text-transform:uppercase; letter-spacing:.075em; margin-bottom:.45rem; }
        .ns-recommendation-main > div { display:flex; align-items:baseline; flex-wrap:wrap; gap:.35rem .8rem; }
        .ns-recommendation-main strong { color:var(--ns-navy); font-size:1.08rem; }
        .ns-recommendation-main div span { color:#4D566B; font-size:.76rem; line-height:1.45; }
        .ns-recommendation-side { display:flex; flex-direction:column; align-items:flex-end; gap:.35rem; flex:0 0 auto; }
        .ns-recommendation-side span { color:#93620D; background:#FFF7E4; border:1px solid #F0DBA8; border-radius:999px; padding:.28rem .58rem; font-size:.62rem; font-weight:800; text-transform:uppercase; letter-spacing:.045em; }
        .ns-recommendation-side small { color:#7D8394; font-size:.61rem; text-align:right; }
        .ns-risk-section-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:1.05rem 0 .55rem; }
        .ns-risk-section-head > div { display:flex; flex-direction:column; gap:.18rem; }
        .ns-risk-section-head strong { color:var(--ns-navy); font-size:.92rem; }
        .ns-risk-section-head span { color:var(--ns-muted); font-size:.7rem; }
        .ns-risk-section-head small { color:#7D8394; font-size:.65rem; }
        .ns-proof-card { position:relative; background:white; border:1px solid #DEE3EC; border-radius:13px; padding:.78rem .9rem; min-height:94px; box-shadow:0 4px 13px rgba(24,30,58,.03); }
        .ns-proof-label { color:#667085; font-size:.65rem; font-weight:760; text-transform:uppercase; letter-spacing:.065em; }
        .ns-proof-value { color:var(--ns-navy); font-size:1.38rem; line-height:1.15; font-weight:790; letter-spacing:-.035em; margin:.36rem 0 .1rem; }
        .ns-proof-detail { color:#667085; font-size:.67rem; }
        .ns-operating-strip { display:flex; align-items:center; justify-content:space-between; gap:1rem; background:#F1F4FB; border:1px solid #E2E7F1; border-radius:10px; color:#4E596F; font-size:.69rem; line-height:1.45; padding:.58rem .78rem; margin-top:.62rem; }
        .ns-operating-strip strong { color:#344054; }
        .ns-operating-strip small { color:#7D8394; font-size:.61rem; text-align:right; max-width:330px; }
        .ns-operating-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--ns-purple); margin-right:.48rem; }
        .ns-profile-card { background:white; border:1px solid #DEE3EC; border-radius:14px; margin-top:.85rem; box-shadow:0 4px 13px rgba(24,30,58,.03); }
        .ns-profile-head { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.65rem .9rem .52rem; border-bottom:1px solid #EDF0F5; }
        .ns-profile-head strong { color:#5E687C; font-size:.65rem; text-transform:uppercase; letter-spacing:.075em; }
        .ns-profile-head span { color:#7D8394; font-size:.63rem; }
        .ns-profile-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); padding:.55rem .15rem .68rem; }
        .ns-profile-grid > div { padding:.12rem .75rem; border-right:1px solid #EDF0F5; }
        .ns-profile-grid > div:last-child { border-right:0; }
        .ns-profile-grid small { display:block; color:#7D8394; font-size:.6rem; font-weight:760; text-transform:uppercase; letter-spacing:.06em; margin-bottom:.22rem; }
        .ns-profile-grid strong { display:block; color:var(--ns-navy); font-size:.72rem; line-height:1.35; }
        .ns-risk-gates-head { margin-top:1.15rem; }
        .ns-risk-card { background:white; border:1px solid #DEE3EC; border-radius:14px; padding:.78rem .9rem; margin-bottom:.72rem; box-shadow:0 4px 13px rgba(24,30,58,.035); }
        .ns-risk-card-head { display:grid; grid-template-columns:auto 1fr auto; align-items:center; gap:.55rem; }
        .ns-risk-index { width:24px; height:24px; display:grid; place-items:center; border-radius:50%; font-size:.68rem; font-weight:820; }
        .ns-risk-index.amber { color:#A65B13; background:#FFF1E5; }
        .ns-risk-index.purple { color:var(--ns-purple-dark); background:var(--ns-purple-soft); }
        .ns-risk-card-title { color:var(--ns-navy); font-size:.8rem; font-weight:770; }
        .ns-risk-badge { border-radius:999px; padding:.25rem .55rem; font-size:.57rem; line-height:1; font-weight:800; text-transform:uppercase; letter-spacing:.04em; }
        .ns-risk-badge.amber { color:#98520D; background:#FFF5E9; }
        .ns-risk-badge.purple { color:var(--ns-purple-dark); background:#F3EFFF; }
        .ns-risk-evidence { color:#4F596D; font-size:.7rem; line-height:1.45; margin:.48rem 0 .55rem 1.82rem; }
        .ns-risk-action-row, .ns-risk-gate-row { display:grid; grid-template-columns:92px 1fr; gap:.5rem; align-items:start; border-top:1px solid #EDF0F5; padding:.46rem 0 0 1.82rem; margin-top:.4rem; }
        .ns-risk-action-row span, .ns-risk-gate-row span { color:#667085; font-size:.58rem; font-weight:800; text-transform:uppercase; letter-spacing:.065em; }
        .ns-risk-action-row p, .ns-risk-gate-row p { color:#4F596D; font-size:.67rem; line-height:1.4; margin:0; }
        .ns-context-card { background:white; border:1px solid #DEE3EC; border-radius:14px; padding:.9rem 1rem; margin-bottom:.72rem; box-shadow:0 4px 13px rgba(24,30,58,.035); }
        .ns-context-title { color:var(--ns-navy); font-size:.86rem; font-weight:770; }
        .ns-context-copy { color:#7D8394; font-size:.65rem; line-height:1.4; margin-top:.22rem; }
        .ns-spend-grid { display:grid; grid-template-columns:1fr 1fr; gap:.75rem; border-top:1px solid #EDF0F5; margin-top:.65rem; padding-top:.65rem; }
        .ns-spend-grid small { display:block; color:#7D8394; font-size:.58rem; font-weight:760; text-transform:uppercase; letter-spacing:.06em; }
        .ns-spend-grid strong { display:block; color:var(--ns-navy); font-size:1.25rem; letter-spacing:-.03em; margin-top:.22rem; }
        .ns-context-note { color:#667085; background:#F6F7FA; border-radius:7px; font-size:.61rem; line-height:1.35; padding:.38rem .45rem; margin-top:.62rem; }
        .ns-path-step { display:grid; grid-template-columns:22px 1fr; gap:.52rem; align-items:start; color:#414B60; font-size:.69rem; line-height:1.35; margin-top:.62rem; }
        .ns-path-step > span { width:20px; height:20px; display:grid; place-items:center; color:var(--ns-purple-dark); background:var(--ns-purple-soft); border-radius:50%; font-size:.58rem; font-weight:800; }
        .ns-path-step small { display:block; color:#8A8E9E; font-size:.58rem; margin-top:.08rem; }
        .ns-path-foot { color:var(--ns-purple-dark); background:#F4F1FF; border-radius:7px; font-size:.58rem; font-weight:800; text-align:center; text-transform:uppercase; letter-spacing:.04em; padding:.38rem; margin-top:.7rem; }
        .ns-expansion-logic { display:flex; align-items:flex-start; gap:.7rem; background:#EAF8F3; border:1px solid #CBEBDD; border-radius:12px; padding:.7rem .85rem; margin-top:.1rem; }
        .ns-expansion-logic > span { display:grid; place-items:center; flex:0 0 auto; width:24px; height:24px; border-radius:50%; color:#14795F; background:#D2F1E6; font-weight:850; }
        .ns-expansion-logic strong { color:#14795F; font-size:.68rem; text-transform:uppercase; letter-spacing:.055em; }
        .ns-expansion-logic p { color:#3F5D55; font-size:.68rem; line-height:1.45; margin:.15rem 0 0; }
        .st-key-dashboard_header { background:#111B35; border:1px solid #111B35; border-radius:14px; padding:.38rem .75rem; margin-bottom:.15rem; box-shadow:0 6px 18px rgba(17,27,53,.10); }
        .st-key-dashboard_header > div[data-testid="stVerticalBlock"] { gap:0; }
        .ns-compact-brand { display:flex; align-items:center; gap:.7rem; min-height:40px; color:#FFFFFF; }
        .ns-compact-brand strong { color:#FFFFFF; font-size:.92rem; line-height:1.25; }
        .ns-compact-brand .ns-logo { width:28px; height:28px; border-radius:8px; }
        .ns-mode-label { color:#BFC8DC; font-size:.52rem; font-weight:750; text-transform:uppercase; letter-spacing:.08em; margin:0 0 .1rem; text-align:center; }
        .ns-compact-period { color:#DDE4F2; font-size:.58rem; line-height:1.25; text-align:right; white-space:nowrap; }
        .st-key-dashboard_header .st-key-audience_switch { margin:0; }
        .st-key-dashboard_header .st-key-audience_switch [data-baseweb="button-group"] { background:#202C49; border:1px solid #40506C; border-radius:14px; padding:2px; }
        .st-key-dashboard_header .st-key-audience_switch [role="radiogroup"] { display:flex; background:#202C49; border:1px solid #40506C; border-radius:10px; padding:2px; }
        .st-key-dashboard_header .st-key-audience_switch [role="radio"] { flex:1 1 0; min-height:28px; display:flex; align-items:center; justify-content:center; border-radius:8px; padding:.18rem .45rem; color:#DDE4F2 !important; }
        .st-key-dashboard_header .st-key-audience_switch [role="radio"] * { color:inherit !important; font-size:.58rem !important; line-height:1.1 !important; }
        .st-key-dashboard_header .st-key-audience_switch [role="radio"][aria-checked="true"] { color:#FFFFFF !important; background:#7357E8 !important; }
        .st-key-dashboard_header .st-key-audience_switch button { min-height:28px; padding:.18rem .45rem !important; color:#DDE4F2 !important; background:transparent !important; border:0 !important; font-size:.58rem !important; line-height:1.1 !important; }
        .st-key-dashboard_header .st-key-audience_switch button * { color:inherit !important; font-size:.58rem !important; line-height:1.1 !important; }
        .st-key-dashboard_header .st-key-audience_switch button[aria-pressed="true"] { color:#FFFFFF !important; background:#7357E8 !important; border-radius:11px !important; }
        .ns-overview-head { display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; margin:.8rem .25rem .65rem; }
        .ns-overview-head h2 { color:#172033; font-size:1.35rem; line-height:1.15; font-weight:740; margin:0; }
        .ns-overview-head p { color:#667085; font-size:.68rem; margin:.28rem 0 0; }
        .ns-overview-head > span { color:#6246D8; background:#F4F1FF; border-radius:999px; padding:.3rem 1.35rem; font-size:.58rem; font-weight:750; white-space:nowrap; }
        .ns-overview-kpi { background:#FFFFFF; border:1px solid #E4E8EF; border-radius:12px; padding:.72rem .9rem; min-height:92px; box-shadow:0 3px 12px rgba(20,33,61,.04); }
        .ns-overview-kpi > span { display:block; color:#667085; font-size:.56rem; font-weight:750; text-transform:uppercase; }
        .ns-overview-kpi > strong { display:block; color:#172033; font-size:1.32rem; line-height:1.1; margin:.45rem 0 .22rem; }
        .ns-overview-kpi > small { display:block; color:#667085; font-size:.56rem; line-height:1.25; }
        .ns-wire-card { background:#FFFFFF; border:1px solid #E4E8EF; border-radius:12px; padding:.82rem 1.05rem; box-shadow:0 3px 12px rgba(20,33,61,.04); margin-top:.75rem; }
        .ns-wire-card h3, .ns-overview-spend-copy h3 { color:#172033; font-size:.82rem; line-height:1.2; font-weight:730; margin:0; }
        .ns-wire-sub { color:#667085; font-size:.55rem; line-height:1.35; margin:.24rem 0 .15rem; }
        .ns-overview-main-card { min-height:238px; }
        .ns-overview-bottom-card { min-height:175px; }
        .ns-overview-priority { display:grid; grid-template-columns:112px 1fr; gap:.8rem; align-items:start; border-bottom:1px solid #EDF0F5; padding:.58rem 0; }
        .ns-overview-priority:last-child { border-bottom:0; }
        .ns-overview-priority > span { color:#8B5A08; background:#FFF7E8; border-radius:999px; padding:.28rem .45rem; font-size:.54rem; font-weight:750; text-align:center; }
        .ns-overview-priority > span.technical { color:#A64B17; background:#FFF1E8; }
        .ns-overview-priority strong, .ns-overview-decision strong { display:block; color:#344054; font-size:.66rem; line-height:1.3; }
        .ns-overview-priority small, .ns-overview-decision small { display:block; color:#667085; font-size:.54rem; margin-top:.25rem; }
        .ns-overview-pipeline { display:grid; grid-template-columns:1fr 1.15fr auto; gap:.55rem; align-items:center; border-bottom:1px solid #EDF0F5; min-height:41px; }
        .ns-overview-pipeline:last-child { border-bottom:0; }
        .ns-overview-pipeline strong { color:#172033; font-size:.66rem; }
        .ns-overview-pipeline b { color:#167657; font-size:.6rem; }
        .ns-overview-pipeline span { color:#596579; font-size:.6rem; font-weight:600; }
        .ns-overview-pipeline small { color:#667085; font-size:.54rem; text-align:right; }
        .ns-overview-decision { padding:.34rem 0 .48rem; }
        .ns-overview-link { color:#6246D8; font-size:.54rem; font-weight:650; margin-top:.05rem; }
        .ns-overview-expansion-bottom .ns-overview-pipeline { min-height:30px; }
        .st-key-overview_spend_card { background:#FFFFFF; border:1px solid #DCE2EA; border-radius:12px; padding:.82rem 1.05rem .4rem; min-height:238px; margin-top:.75rem; box-shadow:0 3px 12px rgba(20,33,61,.04); }
        .st-key-overview_spend_card .stPlotlyChart { background:transparent; border:0; border-radius:0; padding:0; box-shadow:none; }
        .ns-overview-spend-copy > strong { display:block; color:#172033; font-size:1.02rem; line-height:1.2; margin:.7rem 0 .3rem; }
        .ns-overview-spend-copy p { color:#667085; font-size:.56rem; line-height:1.35; margin:0; }
        .ns-internal-notice { display:flex; align-items:flex-start; gap:.55rem; border-radius:11px; padding:.62rem .78rem; margin:.45rem 0 .85rem; font-size:.72rem; line-height:1.45; }
        .ns-internal-notice strong { flex:0 0 auto; }
        .ns-internal-notice.assumption { color:#7B550D; background:#FFF8E8; border:1px solid #F0DCA8; }
        .ns-internal-notice.info { color:#40547A; background:#F0F4FC; border:1px solid #DCE4F4; }
        .ns-internal-panel { min-height:128px; }
        .ns-mini-badge { float:right; color:var(--ns-purple-dark); background:var(--ns-purple-soft); border-radius:999px; padding:.22rem .45rem; font-size:.58rem; text-transform:uppercase; letter-spacing:.04em; }
        .ns-priority-card { min-height:175px; }
        .ns-priority-card .ns-priority-copy, .ns-priority-card .ns-priority-meta { margin-left:1.8rem; }
        .ns-health-banner { display:grid; grid-template-columns:auto 1fr auto; align-items:center; gap:1.1rem; color:white; background:linear-gradient(110deg,#27204F,#5142C7); border-radius:16px; padding:.95rem 1.05rem; margin:.25rem 0 1rem; }
        .ns-health-banner > div > span { display:block; color:#D8D3FF; font-size:.66rem; font-weight:750; text-transform:uppercase; letter-spacing:.07em; }
        .ns-health-banner > div > strong { display:block; font-size:1.95rem; line-height:1.1; margin-top:.2rem; }
        .ns-health-banner small { color:#C5BEF5; font-size:.78rem; }
        .ns-health-banner p { color:#ECEAFE; font-size:.72rem; line-height:1.45; margin:0; }
        .ns-health-banner p b { color:white; }
        .ns-internal-risk { background:white; border:1px solid var(--ns-border); border-top:4px solid var(--ns-amber); border-radius:15px; padding:.9rem 1rem; min-height:330px; box-shadow:0 5px 18px rgba(24,30,58,.035); }
        .ns-internal-risk.risk { border-top-color:var(--ns-red); }
        .ns-internal-risk-head { display:flex; align-items:center; gap:.55rem; margin-bottom:.72rem; }
        .ns-internal-risk-head span { color:var(--ns-purple-dark); background:var(--ns-purple-soft); border-radius:7px; padding:.28rem .42rem; font-size:.62rem; font-weight:800; }
        .ns-internal-risk-head strong { color:var(--ns-navy); font-size:.84rem; }
        .ns-internal-risk p { color:#596276; font-size:.7rem; line-height:1.48; margin:.2rem 0 .68rem; }
        .ns-internal-risk .ns-priority-meta { margin:.2rem 0 0; padding-top:.55rem; border-top:1px solid var(--ns-border); }
        .ns-evidence-label { color:#7D8394; font-size:.57rem; font-weight:800; text-transform:uppercase; letter-spacing:.07em; }
        .ns-confidence-card { height:100%; min-height:245px; color:white; background:linear-gradient(150deg,#2A2457,#6D5CE7); border-radius:16px; padding:1rem 1.05rem; box-shadow:0 10px 24px rgba(76,62,172,.18); }
        .ns-confidence-card > span { display:block; color:#D8D3FF; font-size:.68rem; font-weight:750; text-transform:uppercase; letter-spacing:.07em; }
        .ns-confidence-card > strong { display:block; font-size:3rem; line-height:1; margin:.8rem 0 .45rem; }
        .ns-confidence-card small { color:#D8D3FF; font-size:1rem; }
        .ns-confidence-card b { display:inline-block; color:#2B215B; background:#DCD6FF; border-radius:999px; padding:.26rem .5rem; font-size:.6rem; }
        .ns-confidence-card p { color:#E5E1FF; font-size:.7rem; line-height:1.45; margin:.75rem 0 0; }
        .ns-score-formula { display:flex; align-items:center; gap:.75rem; color:#4E596F; background:#F0F3FA; border:1px solid #E0E5F0; border-radius:11px; padding:.6rem .75rem; margin-top:.75rem; font-size:.68rem; }
        .ns-score-formula strong { color:#344054; flex:0 0 auto; }
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) div[data-baseweb="tab-list"],
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) [role="tablist"] { gap:8px; flex-wrap:wrap; border-bottom:none !important; background:transparent; padding:.25rem 0 .5rem; box-shadow:none; }
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) [data-baseweb="tab-highlight"],
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) [data-baseweb="tab-border"] { display:none !important; }
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[data-baseweb="tab"],
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[role="tab"] { min-height:40px; height:auto; border-radius:999px !important; padding:6px 18px !important; background-color:#F3F4F6 !important; border:1px solid #E5E7EB !important; box-shadow:0 2px 5px rgba(23,33,58,.06); color:#374151 !important; opacity:1 !important; transition:all .15s ease; }
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[data-baseweb="tab"] p,
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[role="tab"] p,
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[role="tab"] span { color:#374151 !important; font-weight:500 !important; opacity:1 !important; }
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[data-baseweb="tab"]:hover,
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[role="tab"]:hover { background-color:#E5E7EB !important; border-color:#D1D5DB !important; transform:translateY(-1px); }
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[data-baseweb="tab"][aria-selected="true"],
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[role="tab"][aria-selected="true"] { background-color:#4F46E5 !important; border-color:#4F46E5 !important; box-shadow:0 5px 12px rgba(79,70,229,.24); }
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[data-baseweb="tab"][aria-selected="true"] p,
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[role="tab"][aria-selected="true"] p,
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[role="tab"][aria-selected="true"] span { color:#FFFFFF !important; font-weight:650 !important; }
        :is(.st-key-dashboard_navigation, .st-key-external_navigation) button[role="tab"]:focus-visible { outline:3px solid rgba(79,70,229,.25); outline-offset:2px; }
        .st-key-audience_switch { margin-bottom:.7rem; }
        [data-testid="stDataFrame"] { border:1px solid var(--ns-border); border-radius:14px; overflow:hidden; }
        .stPlotlyChart { background:white; border:1px solid var(--ns-border); border-radius:15px; padding:.45rem .55rem .2rem; box-shadow:0 5px 18px rgba(24,30,58,.035); }
        .ns-footer { color:#85899A; font-size:.7rem; margin-top:2rem; padding-top:1rem; border-top:1px solid var(--ns-border); }
        @media (max-width: 900px) {
            .block-container { padding:1rem; }
            .ns-header-top { flex-direction:column; }
            .ns-meta { min-width:0; width:100%; }
            .st-key-dashboard_header .ns-meta { grid-template-columns:1fr 1fr; }
            .st-key-dashboard_header .ns-compact-brand { min-height:38px; }
            .ns-compact-period { text-align:left; }
            .ns-overview-head { margin-top:.65rem; }
            .ns-overview-priority { grid-template-columns:1fr; gap:.35rem; }
            .ns-overview-priority > span { justify-self:start; }
            .ns-overview-pipeline { grid-template-columns:1fr auto; }
            .ns-overview-pipeline small { grid-column:2; grid-row:1; }
            .ns-overview-pipeline :is(span,b) { grid-column:1 / span 2; }
            .ns-health-banner { grid-template-columns:1fr; align-items:flex-start; }
            .ns-internal-risk { min-height:0; }
            .ns-score-formula, .ns-internal-notice { flex-direction:column; }
            .ns-unknown-grid { grid-template-columns:1fr; }
            .ns-exec-kpi { min-height:132px; }
            .ns-risk-page-head, .ns-recommendation, .ns-operating-strip, .ns-profile-head { align-items:flex-start; flex-direction:column; }
            .ns-recommendation-side { align-items:flex-start; }
            .ns-operating-strip small { text-align:left; max-width:none; }
            .ns-profile-grid { grid-template-columns:1fr 1fr; }
            .ns-profile-grid > div { border-right:0; border-bottom:1px solid #EDF0F5; padding:.55rem .75rem; }
            .ns-profile-grid > div:last-child { border-bottom:0; }
            .ns-risk-card-head { grid-template-columns:auto 1fr; }
            .ns-risk-badge { grid-column:2; justify-self:start; }
            .ns-risk-evidence { margin-left:0; }
            .ns-risk-action-row, .ns-risk-gate-row { grid-template-columns:1fr; padding-left:0; }
        }
        </style>
        """,
    )


def display_date(value: pd.Timestamp, *, include_year: bool = True) -> str:
    """Format a date without platform-specific strftime flags."""

    text = value.strftime("%b %d, %Y" if include_year else "%b %d")
    return text.replace(" 0", " ")


def dashboard_header(
    start: pd.Timestamp,
    end: pd.Timestamp,
    latest: pd.Timestamp,
    *,
    internal_label: str,
    external_label: str,
) -> str:
    """Render the title and dashboard-mode switch as one responsive header."""

    current = st.session_state.get("audience_switch", internal_label)
    with st.container(key="dashboard_header"):
        identity_col, mode_col, period_col = st.columns([1.15, 1.35, 0.38], gap="medium", vertical_alignment="center")
        with mode_col:
            st.markdown('<div class="ns-mode-label">Dashboard mode</div>', unsafe_allow_html=True)
            audience = st.segmented_control(
                "Dashboard mode",
                [internal_label, external_label],
                default=internal_label,
                key="audience_switch",
                label_visibility="collapsed",
                width="stretch",
                wrap=True,
            )
        audience = audience or current or internal_label
        customer_facing = audience == external_label
        with identity_col:
            title = "Fireworks / NorthStar Customer Outcomes" if customer_facing else "Fireworks / NorthStar Internal Account Intelligence"
            st.markdown(
                f"""
                <div class="ns-compact-brand"><span class="ns-logo"></span><strong>{escape(title)}</strong></div>
                """,
                unsafe_allow_html=True,
            )

        period = f"{display_date(start, include_year=False)} – {display_date(end)}"
        with period_col:
            st.markdown(
                f'<div class="ns-compact-period">Reporting period<br><strong>{period}</strong></div>',
                unsafe_allow_html=True,
            )
    return audience


def header(
    start: pd.Timestamp,
    end: pd.Timestamp,
    latest: pd.Timestamp,
    *,
    audience_label: str = "Internal Dashboard — Fireworks Team",
    customer_facing: bool = False,
) -> None:
    period = f"{display_date(start, include_year=False)} – {display_date(end)}"
    freshness = f"Through {display_date(latest)}"
    if customer_facing:
        title = "Northstar Customer Outcomes Dashboard"
        subtitle = (
            "A shared view of supplied business outcomes and observed Flagship Support "
            "performance for the reporting period."
        )
        third_label, third_value = "Account", "NorthStar Retail Group"
        fourth_label, fourth_value = "Deployment", "Flagship Support"
    else:
        title = "Northstar Account Intelligence Dashboard"
        subtitle = (
            "A shared operating view for account, engineering, and leadership teams—"
            "grounded in supplied account evidence and explicit about what still needs validation."
        )
        third_label, third_value = "Account owner", "Not provided"
        fourth_label, fourth_value = "View", "Internal only"
    st.markdown(
        f"""
        <div class="ns-header">
          <div class="ns-header-top">
            <div>
              <div class="ns-brand"><span class="ns-logo"></span><span>Fireworks</span></div>
              <div class="ns-internal-pill">{escape(audience_label)}</div>
              <h1 class="ns-title">{escape(title)}</h1>
              <p class="ns-subtitle">{escape(subtitle)}</p>
            </div>
            <div class="ns-meta">
              <div class="ns-meta-item"><span class="ns-meta-label">Reporting period</span><span class="ns-meta-value">{period}</span></div>
              <div class="ns-meta-item"><span class="ns-meta-label">Evidence freshness</span><span class="ns-meta-value">{freshness}</span></div>
              <div class="ns-meta-item"><span class="ns-meta-label">{escape(third_label)}</span><span class="ns-meta-value">{escape(third_value)}</span></div>
              <div class="ns-meta-item"><span class="ns-meta-label">{escape(fourth_label)}</span><span class="ns-meta-value">{escape(fourth_value)}</span></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(kicker: str, title: str, copy: str = "") -> None:
    copy_html = f'<div class="ns-section-copy">{escape(copy)}</div>' if copy else ""
    st.markdown(
        f'<div class="ns-section"><div class="ns-section-kicker">{escape(kicker)}</div>'
        f'<h2 class="ns-section-title">{escape(title)}</h2>{copy_html}</div>',
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, detail: str, status: str, tone: str = "neutral") -> None:
    st.markdown(
        f"""
        <div class="ns-kpi">
          <div class="ns-kpi-top"><span class="ns-kpi-label">{escape(label)}</span><span class="ns-status {escape(tone)}">{escape(status)}</span></div>
          <div class="ns-kpi-value">{escape(value)}</div>
          <div class="ns-kpi-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def priority_panel(items: Sequence[dict[str, str]]) -> None:
    blocks = []
    for index, item in enumerate(items, 1):
        blocks.append(
            f'<div class="ns-priority"><div class="ns-priority-head"><span class="ns-priority-index">{index}</span>{escape(item["title"])}</div>'
            f'<div class="ns-priority-copy">{escape(item["copy"])}</div>'
            f'<div class="ns-priority-meta">{escape(item.get("meta", "Owner/date not provided"))}</div></div>'
        )
    st.markdown(
        '<div class="ns-panel"><div class="ns-panel-title">Top 3 Priorities (Internal)</div>'
        '<p class="ns-panel-copy">Proposed focus areas based on supplied evidence and known information gaps.</p>'
        + "".join(blocks)
        + "</div>",
        unsafe_allow_html=True,
    )


def leadership_panel() -> None:
    st.markdown(
        """
        <div class="ns-panel">
          <div class="ns-panel-title">Leadership decisions</div>
          <p class="ns-panel-copy">No decision or approval records were supplied. These are information-gathering asks, not recorded decisions.</p>
          <div class="ns-priority"><div class="ns-priority-head"><span class="ns-priority-index">A</span>Assign accountable account owner</div><div class="ns-priority-copy">Confirm the person responsible for coordinating health, renewal, and expansion evidence.</div><div class="ns-priority-meta">Decision status: Not provided</div></div>
          <div class="ns-priority"><div class="ns-priority-head"><span class="ns-priority-index">B</span>Define expansion assessment criteria</div><div class="ns-priority-copy">Approve required evidence and review cadence before scoring any brand.</div><div class="ns-priority-meta">Decision status: Not provided</div></div>
          <div class="ns-priority"><div class="ns-priority-head"><span class="ns-priority-index">C</span>Complete commercial evidence</div><div class="ns-priority-copy">Provide revenue, renewal, support-cost, staffing, margin, and competitive context.</div><div class="ns-priority-meta">Decision status: Not provided</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def line_chart(
    frame: pd.DataFrame,
    column: str,
    title: str,
    *,
    color: str = PURPLE,
    y_suffix: str = "",
    y_prefix: str = "",
    height: int = 300,
    fill: bool = False,
) -> go.Figure:
    hover_template = "%{x|%b %d, %Y}<br>" + title + ": " + y_prefix + "%{y:,.2f}" + y_suffix + "<extra></extra>"
    trace = go.Scatter(
        x=frame["date"],
        y=frame[column],
        mode="lines",
        line={"color": color, "width": 2.5, "shape": "spline", "smoothing": 0.45},
        fill="tozeroy" if fill else None,
        fillcolor="rgba(109, 92, 231, 0.08)" if fill else None,
        hovertemplate=hover_template,
        connectgaps=False,
    )
    figure = go.Figure(trace)
    figure.update_layout(
        height=height,
        margin={"l": 12, "r": 12, "t": 12, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="x unified",
        font={"family": "Inter, sans-serif", "color": NAVY, "size": 12},
        xaxis={
            "showgrid": False,
            "showline": False,
            "tickformat": "%b %d",
            "tickfont": {"color": MUTED, "size": 10},
            "nticks": 7,
        },
        yaxis={
            "gridcolor": GRID,
            "gridwidth": 1,
            "zeroline": False,
            "showline": False,
            "tickfont": {"color": MUTED, "size": 10},
            "ticksuffix": y_suffix,
            "tickprefix": y_prefix,
        },
    )
    return figure


def chart_header(title: str, value: str, comparison: str) -> None:
    st.markdown(
        f'<div class="ns-chart-summary"><div class="ns-chart-title">{escape(title)}</div>'
        f'<div><div class="ns-chart-value">{escape(value)}</div><div class="ns-chart-compare">{escape(comparison)}</div></div></div>',
        unsafe_allow_html=True,
    )


def signal_card(signal: dict[str, object]) -> None:
    date = signal["date"]
    date_text = display_date(date) if pd.notna(date) else "Date unavailable"
    st.markdown(
        f"""
        <div class="ns-signal">
          <div class="ns-signal-label">{escape(str(signal['label']))}</div>
          <div class="ns-signal-value">{escape(str(signal['display']))}</div>
          <div class="ns-signal-date">{escape(date_text)}</div>
          <div class="ns-signal-context">{escape(str(signal['context']))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def notes_panel(notes: pd.DataFrame) -> None:
    if notes.empty:
        st.markdown('<div class="ns-panel"><div class="ns-panel-title">Operational notes</div><p class="ns-panel-copy">No operational notes were supplied.</p></div>', unsafe_allow_html=True)
        return
    blocks = []
    for row in notes.itertuples(index=False):
        blocks.append(
            f'<div class="ns-note"><div class="ns-note-date">{display_date(row.date)}</div>'
            f'<div class="ns-note-copy">{escape(str(row.operational_note))}</div></div>'
        )
    st.markdown(
        '<div class="ns-panel"><div class="ns-panel-title">Operational notes from source</div>'
        '<p class="ns-panel-copy">Recorded context from the CSV; wording is shown as supplied.</p>'
        + "".join(blocks)
        + "</div>",
        unsafe_allow_html=True,
    )


def unknown_grid(items: Sequence[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="ns-unknown"><div class="ns-unknown-label">{escape(label)}</div>'
        f'<div class="ns-unknown-value">Not provided</div><div class="ns-unknown-action">{escape(action)}</div></div>'
        for label, action in items
    )
    st.markdown(f'<div class="ns-unknown-grid">{cards}</div>', unsafe_allow_html=True)


def footer(
    source_name: str,
    row_count: int,
    latest: pd.Timestamp,
    *,
    scope: str = "Internal use only",
) -> None:
    st.markdown(
        f'<div class="ns-footer">Source: {escape(source_name)} · {row_count:,} daily records · Latest evidence {display_date(latest)} · {escape(scope)}</div>',
        unsafe_allow_html=True,
    )

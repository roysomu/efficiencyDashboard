"""Data loading and calculation helpers for the NorthStar dashboard.

This module deliberately contains no Streamlit code.  Keeping the data layer
separate makes it possible to build a future customer-safe presentation layer
without exposing internal account-management fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "date",
    "deployment",
    "requests",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "spend_usd",
    "p50_latency_ms",
    "p95_latency_ms",
    "error_rate_pct",
    "availability_pct",
    "tier1_tickets",
    "automated_tier1_tickets",
    "automation_rate_pct",
    "avg_handle_time_min",
    "csat_score",
    "grounded_answer_rate_pct",
    "quality_eval_pass_rate_pct",
    "escalation_rate_pct",
    "operational_note",
]

NUMERIC_COLUMNS = [column for column in REQUIRED_COLUMNS if column not in {"date", "deployment", "operational_note"}]

# Account outcomes supplied directly by the user on 2026-11-18. These are kept
# separate from CSV-derived operational evidence so their provenance is clear.
SUPPLIED_ACCOUNT_OUTCOMES = {
    "tier1_automation_rate_pct": 70.0,
    "handle_time_reduction_pct": 35.0,
    "csat_lift_points": 12.0,
}

# The source CSV does not contain contractual targets. These values come from
# the requested score methodology and are therefore labeled illustrative in UI.
HEALTH_GUARDRAILS = {
    "automation_rate_pct": 70.0,
    "handle_time_reduction_pct": 30.0,
    "csat_lift_points": 10.0,
    "availability_pct": 99.9,
    "error_rate_pct": 1.0,
    "p95_latency_ms": 2_000.0,
    "grounding_rate_pct": 95.0,
    "evaluation_pass_rate_pct": 95.0,
    "period_spend_budget_usd": 1_300.0,
}

HEALTH_WEIGHTS = {
    "Adoption": 0.25,
    "Business outcomes": 0.25,
    "Reliability": 0.20,
    "Quality": 0.20,
    "Spend efficiency": 0.10,
}


class DataValidationError(ValueError):
    """Raised when the operational CSV cannot safely power the dashboard."""


@dataclass(frozen=True)
class PeriodSummary:
    start: pd.Timestamp
    end: pd.Timestamp
    latest: pd.Timestamp
    days: int


def load_metrics(csv_path: str | Path) -> pd.DataFrame:
    """Load, validate, clean, and sort the NorthStar daily metrics CSV."""

    path = Path(csv_path)
    if not path.exists():
        raise DataValidationError(
            f"Operational data file not found at {path}. Place "
            "northstar_flagship_30_day_metrics.csv in the project root."
        )

    try:
        frame = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise DataValidationError("The operational CSV is empty.") from exc
    except (OSError, pd.errors.ParserError) as exc:
        raise DataValidationError(f"The operational CSV could not be read: {exc}") from exc

    if frame.empty:
        raise DataValidationError("The operational CSV has headers but no data rows.")

    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise DataValidationError("The operational CSV is missing required columns: " + ", ".join(missing))

    frame = frame.loc[:, REQUIRED_COLUMNS].copy()
    parsed_dates = pd.to_datetime(frame["date"], format="mixed", errors="coerce")
    malformed_count = int(parsed_dates.isna().sum())
    if malformed_count:
        raise DataValidationError(
            f"The operational CSV contains {malformed_count} malformed date value(s). "
            "Correct them before reloading the dashboard."
        )
    frame["date"] = parsed_dates

    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan)

    completely_empty = [column for column in NUMERIC_COLUMNS if frame[column].notna().sum() == 0]
    if completely_empty:
        raise DataValidationError(
            "These required metric columns contain no usable numeric values: " + ", ".join(completely_empty)
        )

    frame["deployment"] = frame["deployment"].fillna("Not provided").astype(str)
    frame["operational_note"] = frame["operational_note"].replace(r"^\s*$", np.nan, regex=True)
    return frame.sort_values("date", kind="stable").reset_index(drop=True)


def period_summary(frame: pd.DataFrame) -> PeriodSummary:
    return PeriodSummary(
        start=frame["date"].min(),
        end=frame["date"].max(),
        latest=frame["date"].max(),
        days=int(frame["date"].nunique()),
    )


def first_last(frame: pd.DataFrame, column: str) -> tuple[float, float]:
    """Return the first and last non-null values of a daily metric."""

    values = frame.loc[frame[column].notna(), column]
    if values.empty:
        return np.nan, np.nan
    return float(values.iloc[0]), float(values.iloc[-1])


def change_summary(frame: pd.DataFrame, column: str) -> dict[str, float]:
    first, last = first_last(frame, column)
    absolute = last - first
    percent = (absolute / first * 100) if pd.notna(first) and first != 0 else np.nan
    return {"first": first, "last": last, "absolute": absolute, "percent": percent}


def safe_sum(frame: pd.DataFrame, column: str) -> float:
    values = frame[column].dropna()
    return float(values.sum()) if not values.empty else np.nan


def safe_mean(frame: pd.DataFrame, column: str) -> float:
    values = frame[column].dropna()
    return float(values.mean()) if not values.empty else np.nan


def safe_ratio(numerator: float, denominator: float, multiplier: float = 1.0) -> float:
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return np.nan
    return numerator / denominator * multiplier


def capped_score(numerator: float, denominator: float) -> float:
    """Return a 0–100 attainment score, capped at 100."""

    if pd.isna(numerator) or pd.isna(denominator) or denominator <= 0:
        return np.nan
    return float(np.clip(numerator / denominator * 100, 0, 100))


def account_health_score(
    frame: pd.DataFrame,
    outcomes: dict[str, float] | None = None,
) -> dict[str, object]:
    """Calculate the requested five-dimension account-health score.

    Adoption and business outcomes use explicitly supplied account evidence.
    Reliability, quality, spend, and automated-ticket volume are calculated
    from the CSV. All requested targets are treated as illustrative guardrails.
    """

    evidence = outcomes or SUPPLIED_ACCOUNT_OUTCOMES
    guardrails = HEALTH_GUARDRAILS

    automation_rate = float(evidence["tier1_automation_rate_pct"])
    handle_time_reduction = float(evidence["handle_time_reduction_pct"])
    csat_lift = float(evidence["csat_lift_points"])

    availability = safe_mean(frame, "availability_pct")
    error_rate = safe_mean(frame, "error_rate_pct")
    p95_latency = safe_mean(frame, "p95_latency_ms")
    grounding = safe_mean(frame, "grounded_answer_rate_pct")
    evaluation = safe_mean(frame, "quality_eval_pass_rate_pct")
    spend = safe_sum(frame, "spend_usd")
    automated_tickets = safe_sum(frame, "automated_tier1_tickets")

    adoption_score = capped_score(automation_rate, guardrails["automation_rate_pct"])
    handle_time_score = capped_score(handle_time_reduction, guardrails["handle_time_reduction_pct"])
    csat_score = capped_score(csat_lift, guardrails["csat_lift_points"])
    business_score = safe_mean(pd.DataFrame({"value": [handle_time_score, csat_score]}), "value")

    availability_score = capped_score(availability, guardrails["availability_pct"])
    error_score = capped_score(guardrails["error_rate_pct"], error_rate)
    latency_score = capped_score(guardrails["p95_latency_ms"], p95_latency)
    reliability_score = safe_mean(
        pd.DataFrame({"value": [availability_score, error_score, latency_score]}), "value"
    )

    grounding_score = capped_score(grounding, guardrails["grounding_rate_pct"])
    evaluation_score = capped_score(evaluation, guardrails["evaluation_pass_rate_pct"])
    quality_score = safe_mean(pd.DataFrame({"value": [grounding_score, evaluation_score]}), "value")

    actual_spend_per_ticket = safe_ratio(spend, automated_tickets)
    target_spend_per_ticket = safe_ratio(guardrails["period_spend_budget_usd"], automated_tickets)
    spend_score = capped_score(target_spend_per_ticket, actual_spend_per_ticket)

    dimensions = [
        {
            "dimension": "Adoption",
            "weight": HEALTH_WEIGHTS["Adoption"],
            "score": adoption_score,
            "evidence": f"{automation_rate:.1f}% Tier-1 automation",
            "calculation": f"{automation_rate:.1f}% ÷ {guardrails['automation_rate_pct']:.0f}% × 100",
            "source": "User-provided account outcome",
        },
        {
            "dimension": "Business outcomes",
            "weight": HEALTH_WEIGHTS["Business outcomes"],
            "score": business_score,
            "evidence": f"{handle_time_reduction:.1f}% handle-time reduction; +{csat_lift:.1f} CSAT pts",
            "calculation": (
                f"Average of {handle_time_reduction:.1f}% ÷ {guardrails['handle_time_reduction_pct']:.0f}% "
                f"and {csat_lift:.1f} ÷ {guardrails['csat_lift_points']:.0f}; each capped at 100"
            ),
            "source": "User-provided account outcomes",
        },
        {
            "dimension": "Reliability",
            "weight": HEALTH_WEIGHTS["Reliability"],
            "score": reliability_score,
            "evidence": f"{availability:.3f}% availability; {error_rate:.3f}% errors; {p95_latency:,.0f} ms P95",
            "calculation": "Average of availability ÷ 99.9%, 1.0% ÷ errors, and 2,000 ms ÷ P95; capped at 100",
            "source": "CSV period averages",
        },
        {
            "dimension": "Quality",
            "weight": HEALTH_WEIGHTS["Quality"],
            "score": quality_score,
            "evidence": f"{grounding:.1f}% grounded; {evaluation:.1f}% evaluation pass",
            "calculation": "Average of grounding ÷ 95% and evaluation pass ÷ 95%; capped at 100",
            "source": "CSV period averages",
        },
        {
            "dimension": "Spend efficiency",
            "weight": HEALTH_WEIGHTS["Spend efficiency"],
            "score": spend_score,
            "evidence": f"${actual_spend_per_ticket:.4f} per automated ticket",
            "calculation": (
                f"${target_spend_per_ticket:.4f} guardrail ÷ ${actual_spend_per_ticket:.4f} actual; "
                f"${guardrails['period_spend_budget_usd']:,.0f} period budget equivalent"
            ),
            "source": "CSV spend and automated tickets",
        },
    ]

    for dimension in dimensions:
        dimension["weighted_contribution"] = float(dimension["score"] * dimension["weight"])

    weighted_total = float(sum(dimension["weighted_contribution"] for dimension in dimensions))
    return {
        "weighted_total": weighted_total,
        "dimensions": dimensions,
        "guardrail_label": "Illustrative guardrail",
    }


def dashboard_metrics(frame: pd.DataFrame) -> dict[str, float]:
    requests = safe_sum(frame, "requests")
    tokens = safe_sum(frame, "total_tokens")
    spend = safe_sum(frame, "spend_usd")
    tier1_tickets = safe_sum(frame, "tier1_tickets")
    automated_tier1_tickets = safe_sum(frame, "automated_tier1_tickets")
    request_change = change_summary(frame, "requests")
    return {
        "total_requests": requests,
        "request_first": request_change["first"],
        "request_last": request_change["last"],
        "request_change_pct": request_change["percent"],
        "mean_availability": safe_mean(frame, "availability_pct"),
        "total_spend": spend,
        "total_tokens": tokens,
        "total_tier1_tickets": tier1_tickets,
        "total_automated_tier1_tickets": automated_tier1_tickets,
        "weighted_automation_rate_pct": safe_ratio(
            automated_tier1_tickets, tier1_tickets, 100
        ),
        "mean_p50_latency_ms": safe_mean(frame, "p50_latency_ms"),
        "mean_p95_latency_ms": safe_mean(frame, "p95_latency_ms"),
        "mean_error_rate_pct": safe_mean(frame, "error_rate_pct"),
        "mean_grounded_answer_rate_pct": safe_mean(
            frame, "grounded_answer_rate_pct"
        ),
        "mean_quality_eval_pass_rate_pct": safe_mean(
            frame, "quality_eval_pass_rate_pct"
        ),
        "mean_escalation_rate_pct": safe_mean(frame, "escalation_rate_pct"),
        "mean_handle_time_min": (
            safe_mean(frame, "avg_handle_time_min")
            if "avg_handle_time_min" in frame.columns
            else np.nan
        ),
        "spend_per_request": safe_ratio(spend, requests),
        "spend_per_million_tokens": safe_ratio(spend, tokens, 1_000_000),
    }


def event_record(frame: pd.DataFrame, event_date: str | pd.Timestamp) -> dict[str, object]:
    """Return one dated CSV record for evidence-backed internal risk cards."""

    date = pd.Timestamp(event_date)
    matching = frame.loc[frame["date"].eq(date)]
    if matching.empty:
        raise DataValidationError(f"The operational CSV is missing the {date.date()} record")
    row = matching.iloc[0]
    return {
        "date": pd.Timestamp(row["date"]),
        "error_rate_pct": float(row["error_rate_pct"]),
        "p95_latency_ms": float(row["p95_latency_ms"]),
        "grounded_answer_rate_pct": float(row["grounded_answer_rate_pct"]),
        "quality_eval_pass_rate_pct": float(row["quality_eval_pass_rate_pct"]),
        "operational_note": (
            str(row["operational_note"]).strip()
            if pd.notna(row["operational_note"])
            else "Not supplied"
        ),
    }


def expansion_scenario(
    frame: pd.DataFrame,
    brand_multipliers: dict[str, float],
    *,
    human_touch_rate: float = 0.80,
    support_hourly_cost: float = 32.0,
    fte_hours_per_month: float = 160.0,
    gross_margin_target: float = 0.60,
) -> dict[str, object]:
    """Calculate an explicitly illustrative internal expansion scenario.

    CSV totals remain measured inputs. Brand multipliers, support behavior,
    hourly cost, FTE conversion, billability, and margin target are assumptions
    supplied by the consolidated internal wireframe.
    """

    metrics = dashboard_metrics(frame)
    # The wireframe uses the visibly rounded weighted rate for scenario rows.
    rounded_automation_rate = round(metrics["weighted_automation_rate_pct"], 1) / 100
    average_handle_time = metrics["mean_handle_time_min"]
    measured_nonautomated_tickets = (
        metrics["total_tier1_tickets"] - metrics["total_automated_tier1_tickets"]
    )

    def workload(multiplier: float) -> dict[str, float]:
        tickets = metrics["total_tier1_tickets"] * multiplier
        automated = tickets * rounded_automation_rate
        spend = metrics["total_spend"] * multiplier
        # Support capacity follows the measured flagship nonautomated count,
        # scaled by the visible volume multiplier. Projected automated tickets
        # separately use the displayed 68.0% rounded rate.
        nonautomated = measured_nonautomated_tickets * multiplier
        support_hours = nonautomated * human_touch_rate * average_handle_time / 60
        return {
            "multiplier": multiplier,
            "tickets": tickets,
            "automated_tickets": automated,
            "recorded_spend_proxy": spend,
            "support_hours": support_hours,
            "fte_month_equivalent": support_hours / fte_hours_per_month,
            "support_cost": support_hours * support_hourly_cost,
        }

    brands = {brand: workload(multiplier) for brand, multiplier in brand_multipliers.items()}
    incremental_multiplier = sum(brand_multipliers.values())
    flagship = workload(1.0)
    incremental = workload(incremental_multiplier)
    all_five = workload(1.0 + incremental_multiplier)

    def margin_case(model: dict[str, float]) -> dict[str, float]:
        revenue_proxy = model["recorded_spend_proxy"]
        modeled_cogs = revenue_proxy * (1 - gross_margin_target)
        return {
            "revenue_proxy": revenue_proxy,
            "modeled_cogs": modeled_cogs,
            "modeled_gross_profit": revenue_proxy - modeled_cogs,
        }

    return {
        "measured_inputs": metrics,
        "assumptions": {
            "brand_multipliers": dict(brand_multipliers),
            "automation_rate_pct": rounded_automation_rate * 100,
            "human_touch_rate_pct": human_touch_rate * 100,
            "average_handle_time_min": average_handle_time,
            "support_hourly_cost": support_hourly_cost,
            "fte_hours_per_month": fte_hours_per_month,
            "gross_margin_target_pct": gross_margin_target * 100,
            "assumed_recorded_spend_is_billable_revenue": True,
        },
        "brands": brands,
        "flagship": flagship,
        "incremental": incremental,
        "all_five": all_five,
        "margin": {
            "flagship": margin_case(flagship),
            "incremental": margin_case(incremental),
            "all_five": margin_case(all_five),
        },
    }


def dated_extreme(frame: pd.DataFrame, column: str, mode: str) -> tuple[pd.Timestamp, float]:
    valid = frame.loc[frame[column].notna(), ["date", column]]
    if valid.empty:
        return pd.NaT, np.nan
    index = valid[column].idxmax() if mode == "max" else valid[column].idxmin()
    return frame.loc[index, "date"], float(frame.loc[index, column])


def largest_daily_regression(
    frame: pd.DataFrame,
    column: str,
    *,
    higher_is_better: bool,
) -> tuple[pd.Timestamp, float, float]:
    """Return date, one-day change, and value for the largest adverse move."""

    values = frame[["date", column]].dropna().copy()
    if len(values) < 2:
        return pd.NaT, np.nan, np.nan
    values["change"] = values[column].diff()
    index = values["change"].idxmin() if higher_is_better else values["change"].idxmax()
    return frame.loc[index, "date"], float(values.loc[index, "change"]), float(frame.loc[index, column])


def observed_signals(frame: pd.DataFrame) -> list[dict[str, object]]:
    """Produce transparent, data-backed observations for Risks & Actions."""

    error_date, error_value = dated_extreme(frame, "error_rate_pct", "max")
    latency_date, latency_value = dated_extreme(frame, "p95_latency_ms", "max")
    availability_date, availability_value = dated_extreme(frame, "availability_pct", "min")
    regression_date, regression_change, regression_value = largest_daily_regression(
        frame, "availability_pct", higher_is_better=True
    )

    return [
        {
            "label": "Error-rate period high",
            "date": error_date,
            "value": error_value,
            "display": f"{error_value:.2f}%" if pd.notna(error_value) else "Not available",
            "context": "Observed maximum in the supplied reporting period; validate root cause and prevention steps.",
        },
        {
            "label": "P95 latency period high",
            "date": latency_date,
            "value": latency_value,
            "display": f"{latency_value:,.0f} ms" if pd.notna(latency_value) else "Not available",
            "context": "Observed maximum in the supplied reporting period; review capacity and dependency behavior.",
        },
        {
            "label": "Availability period low",
            "date": availability_date,
            "value": availability_value,
            "display": f"{availability_value:.3f}%" if pd.notna(availability_value) else "Not available",
            "context": "Observed minimum in the supplied reporting period; confirm incident and follow-up records.",
        },
        {
            "label": "Largest one-day availability regression",
            "date": regression_date,
            "value": regression_value,
            "display": f"{regression_change:+.3f} pts" if pd.notna(regression_change) else "Not available",
            "context": (
                f"Availability reached {regression_value:.3f}% that day. Proposed action: validate the driver and safeguards."
                if pd.notna(regression_value)
                else "Not enough data to calculate a daily regression."
            ),
        },
    ]


def available_notes(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[frame["operational_note"].notna(), ["date", "operational_note"]].copy()


def deployments(frame: pd.DataFrame) -> list[str]:
    return sorted(value for value in frame["deployment"].dropna().astype(str).unique() if value)


def missing_value_counts(frame: pd.DataFrame, columns: Iterable[str] = NUMERIC_COLUMNS) -> dict[str, int]:
    return {column: int(frame[column].isna().sum()) for column in columns}

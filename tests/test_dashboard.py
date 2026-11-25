"""Regression checks for the audience routes and customer-safe data boundary."""

from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from data import dashboard_metrics, expansion_scenario, load_metrics
from external_dashboard import (
    CUSTOMER_SAFE_DAILY_FIELDS,
    EXTERNAL_DATA_DENYLIST,
    build_customer_dashboard_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "northstar_flagship_30_day_metrics.csv"
APP_PATH = PROJECT_ROOT / "app.py"
INTERNAL_AUDIENCE = "Internal Dashboard — Fireworks Team"
EXTERNAL_AUDIENCE = "External Dashboard — Fireworks Team"


class CustomerDataBoundaryTest(unittest.TestCase):
    def test_external_model_contains_only_allowlisted_daily_fields(self) -> None:
        source = load_metrics(CSV_PATH)
        customer = build_customer_dashboard_data(source)

        self.assertEqual(tuple(customer.daily.columns), CUSTOMER_SAFE_DAILY_FIELDS)
        self.assertFalse(set(customer.daily.columns) & set(EXTERNAL_DATA_DENYLIST))
        self.assertNotIn("deployment", customer.daily.columns)
        self.assertNotIn("operational_note", customer.daily.columns)
        self.assertEqual(len(customer.daily), len(source))
        self.assertEqual(customer.expansion_evidence["catalog_sync"].error_rate_pct, 2.18)
        self.assertEqual(customer.expansion_evidence["promotion_load"].error_rate_pct, 1.41)
        self.assertEqual(customer.expansion_evidence["period_end_quality"].grounded_answer_rate_pct, 96.5)


class SharedMetricsTest(unittest.TestCase):
    def test_weighted_automation_and_scenarios_trace_to_csv(self) -> None:
        source = load_metrics(CSV_PATH)
        metrics = dashboard_metrics(source)
        scenario = expansion_scenario(
            source,
            {"Everyday Home": 0.70, "Active": 0.55, "Luxe": 0.45, "Outlet": 0.30},
        )

        self.assertAlmostEqual(metrics["weighted_automation_rate_pct"], 67.9690, places=3)
        self.assertAlmostEqual(metrics["total_spend"], 1213.12, places=2)
        self.assertAlmostEqual(scenario["incremental"]["recorded_spend_proxy"], 2426.24, places=2)
        self.assertEqual(scenario["assumptions"]["automation_rate_pct"], 68.0)


class AudienceRoutingTest(unittest.TestCase):
    def test_internal_view_remains_the_default(self) -> None:
        app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()

        self.assertFalse(app.exception)
        self.assertEqual(app.segmented_control[0].value, INTERNAL_AUDIENCE)
        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["Overview", "Performance", "Risks & Actions", "Expansion", "Commercial & Relationships"],
        )
        rendered_markdown = "\n".join(str(element.value) for element in app.markdown)
        for expected_label in (
            "Operational health",
            "Spend / revenue reference",
            "Top 3 priorities",
            "Expansion at a glance",
            "Leadership decisions needed",
            "Performance navigation cue",
            "Expansion confidence",
            "Commercial",
            "68.0% weighted CSV rate",
            "Illustrative scenario — not a forecast",
        ):
            self.assertIn(expected_label, rendered_markdown)
        self.assertLess(rendered_markdown.index("Operational health"), rendered_markdown.index("Adoption"))
        self.assertLess(rendered_markdown.index("Spend / revenue reference"), rendered_markdown.index("Top 3 priorities"))
        self.assertLess(rendered_markdown.index("Top 3 priorities"), rendered_markdown.index("Leadership decisions needed"))
        self.assertLess(rendered_markdown.index("Leadership decisions needed"), rendered_markdown.index("Expansion at a glance"))

    def test_external_view_uses_customer_tabs_without_internal_content(self) -> None:
        app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
        app.segmented_control[0].set_value(EXTERNAL_AUDIENCE).run()

        self.assertFalse(app.exception)
        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["Executive Overview", "Service Performance", "Answer Quality", "Risks & Expansion"],
        )
        rendered_markdown = "\n".join(str(element.value) for element in app.markdown)
        self.assertNotIn("Service reliability and answer quality", rendered_markdown)
        self.assertNotIn("Usage, adoption, and spend trends", rendered_markdown)
        for expected_label in (
            "Tier-1 tickets automated",
            "Average handle time improvement",
            "CSAT movement",
            "Usage and Tier-1 adoption",
            "Daily spend",
            "Joint next steps",
            "Service and quality snapshot",
            "Proposed first pilot",
            "Everyday Home",
            "Expansion risks and pilot gates",
            "Catalog sync resilience",
            "Promotion-load resilience",
            "Brand-specific answer quality",
            "Flagship spend context",
            "Staged expansion path",
        ):
            self.assertIn(expected_label, rendered_markdown)
        self.assertIn("Confirm Everyday Home profile as proposed pilot", rendered_markdown)
        self.assertIn("2.18% errors and 2,168 ms P95", rendered_markdown)
        self.assertIn("autoscaling threshold adjusted", rendered_markdown)
        self.assertIn("96.5% grounded-answer rate", rendered_markdown)
        self.assertIn("No budget target or expansion forecast supplied", rendered_markdown)
        self.assertEqual(len(app.get("plotly_chart")), 11)
        for internal_label in (
            "Account health score",
            "Top 3 Priorities (Internal)",
            "Operational notes from source",
            "Competitive status",
            "Gross margin",
        ):
            self.assertNotIn(internal_label, rendered_markdown)


if __name__ == "__main__":
    unittest.main()

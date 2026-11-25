# NorthStar Account Intelligence Dashboard

Fireworks account dashboard built with Streamlit, pandas, and Plotly. It is one application with a compact Fireworks header, a mode switch beside the title, and separate internal and customer-facing dashboard modules. Both modes reuse the same validated CSV loader and metric calculations, while the external renderer receives only an explicitly sanitized customer-safe data model.

The current implementation includes:

- **Internal Dashboard — Fireworks Team:** five tabs for account overview, performance, risks and actions, expansion planning, and internal commercial/relationship analysis.
- **External Dashboard — Fireworks Team:** four customer-safe tabs for outcomes, service performance, answer quality, and a proposed Everyday Home expansion pilot.
- A responsive wide-screen layout that preserves the current Fireworks/NorthStar colors, typography, card treatments, navigation behavior, and reporting-period context.
- Clear separation between CSV-derived measurements, supplied deployment-brief outcomes, and values labeled **Assumed**, **Illustrative**, **To agree**, **Not supplied**, or **Not assessed**.
- Regression tests for the audience routes, external-data allowlist, shared calculations, and the current Overview panel order.

## Requirements

- Python 3.10 or newer
- Dependencies in `requirements.txt`: Streamlit, pandas, Plotly, and NumPy

## Setup

From the `NorthStar_Chat_helper` project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

## Start the dashboard

```bash
streamlit run app.py
```

Streamlit will print the local dashboard URL, normally `http://localhost:8501`.

## Run the regression checks

The checks use Python's standard-library test runner and Streamlit's in-process app tester. They verify both audience routes, the customer-safe data boundary, shared metric calculations, and the Overview hierarchy:

```bash
python -m unittest discover -s tests -v
```

## Operational data

The application expects this file at the project root, next to `app.py`:

```text
northstar_flagship_30_day_metrics.csv
```

The CSV is the sole source of operational evidence. It is read at runtime, dates are parsed and sorted ascending, and numeric fields are safely coerced so missing values appear as gaps instead of invented replacements. The app shows a useful error if the file is missing, empty, malformed, or lacks required columns.

Required columns:

```text
date
deployment
requests
input_tokens
output_tokens
total_tokens
spend_usd
p50_latency_ms
p95_latency_ms
error_rate_pct
availability_pct
tier1_tickets
automated_tier1_tickets
automation_rate_pct
avg_handle_time_min
csat_score
grounded_answer_rate_pct
quality_eval_pass_rate_pct
escalation_rate_pct
operational_note
```

## Audience views

The compact header places the mode selector beside the dashboard title and shows the reporting period on the right. The selector changes presentation only; it is not authentication or a security boundary.

- **Internal Dashboard — Fireworks Team** renders the five internal tabs from `internal_dashboard.py`.
- **External Dashboard — Fireworks Team** renders the four customer-facing tabs from `external_dashboard.py`.

The external renderer accepts only a sanitized `CustomerDashboardData` object produced after applying the explicit `CUSTOMER_SAFE_DAILY_FIELDS` allowlist. Raw operational notes remain outside the customer daily model. Only the Aug 9 catalog-sync event and Aug 21 promotion-load event are reduced to immutable, customer-safe expansion evidence. Health-score objects, relationship or renewal assessments, competitor details, internal expansion confidence, support-cost assumptions, staffing equivalents, provider-margin scenarios, internal blockers, and internal owner notes are not available to the external renderer.

## Internal navigation

- **Overview** — the wireframe-aligned executive summary with five matching KPI cards for operational health, adoption, availability, P95 latency, and weighted Tier-1 automation, followed by two responsive rows of planning cards. The current order is:
  1. **Spend / revenue reference** on the upper left, using recorded CSV spend and a compact daily sparkline.
  2. **Top 3 priorities** on the upper right.
  3. **Leadership decisions needed** on the lower left.
  4. **Expansion at a glance** on the lower right.
- **Performance** — separately scaled daily charts for requests, availability, error rate, P50/P95 latency, automation, handle time, grounding, evaluation pass rate, escalations, CSAT, and recorded spend. The spend/revenue summary remains on Overview and is not duplicated here; only the distinct daily spend trend is retained.
- **Risks & Actions** — three evidence-backed flagship risks, a dependency register, and an action tracker. Dated event metrics come from the CSV; priorities, owners, dates, ratings, and statuses are visibly provisional internal assumptions.
- **Expansion** — stage-gated internal planning with illustrative confidence, blockers, brand-volume multipliers, four-brand workload, serving-spend proxies, support-capacity equivalents, and gross-margin scenarios. These are labeled assumptions rather than forecasts.
- **Commercial & Relationships** — restricted internal relationship, renewal, competitive, staffing, support-cost, and margin analysis, alongside a measured flagship baseline and implementation guardrails.

## External navigation

- **Executive Overview** — preserves the KPI-card and chart layout for the supplied 70% Tier-1 automation, 35% lower average handle time, +12 CSAT points, average availability, usage/adoption trends, daily spend, service/quality snapshot, and joint next steps. The proposed pilot step reads: “Confirm Everyday Home profile as proposed pilot.”
- **Service Performance** — customer-safe request volume, weighted automation, availability, error rate, and P50/P95 latency with daily trends and period summaries.
- **Answer Quality** — grounding, evaluation-pass, and escalation trends with an explicit evaluation-coverage caveat.
- **Risks & Expansion** — a customer-safe expansion page containing:
  - a recommendation banner for **Proposed first pilot: Everyday Home**;
  - flagship deployment-brief evidence: 70% Tier-1 automation, 35% lower average handle time, and +12 CSAT points;
  - a CSV-derived operating strip for 31-day average availability, average P95 latency, and first-to-last P95 change;
  - an **Illustrative — confirm with NorthStar** Everyday Home profile covering value-oriented positioning, approximately 96K monthly Tier-1 tickets, approximately 8K medium-complexity SKUs, a friendly/practical tone, assumed 30-day standard returns, and team maturity 4/5;
  - separate catalog-sync resilience, promotion-load resilience, and brand-specific answer-quality cards, each distinguishing flagship evidence from the proposed action and pilot gate. Their CSV evidence includes the Aug 9 catalog event (2.18% errors and 2,168 ms P95), the Aug 21 promotion event (1.41% errors), and the period-end 96.5% grounding and 95.3% evaluation-pass rates;
  - compact flagship spend context for period spend and spend per request, with no invented budget target or expansion forecast; and
  - a sequential path: confirm the profile → agree service and quality gates → run a controlled monitored pilot → review results before selecting the next brand.

The external risks are presented as lessons that inform expansion checks, not as unresolved flagship-release blockers. Flagship results are also explicitly described as evidence from the current deployment rather than guaranteed outcomes for another brand.

## Metric provenance

Shared calculations live in `data.py` and are reused by both renderers. The app keeps provenance visible:

- **CSV-derived:** requests, tickets, weighted automation, availability, errors, latency, handle time, CSAT, grounding, evaluation pass rate, escalations, tokens, recorded spend, unit-spend calculations, dated extrema, and dated event evidence.
- **Deployment-brief outcomes:** rounded 70% Tier-1 automation, 35% lower average handle time, and +12 CSAT points.
- **Illustrative internal planning:** health guardrails, brand-volume multipliers, support-cost and staffing equivalents, expansion confidence, readiness states, billability, and gross-margin scenarios.
- **Illustrative external profile:** Everyday Home positioning, ticket volume, SKU complexity, tone, assumed returns policy, and team maturity pending NorthStar confirmation.

The brief's rounded 70% automation outcome is intentionally kept separate from the CSV's 68.0% weighted 31-day rate. Recorded spend is never presented as confirmed revenue; it is labeled a revenue proxy only inside scenarios that explicitly assume the spend is billable.

## Assumptions and limitations

- First-to-last-day comparisons compare the first and last valid daily observations in the supplied reporting period. They are not prior-period comparisons.
- The audience selector changes presentation only. It does not implement access control; deploy the external view behind appropriate authentication before using it as a security boundary.
- Account Health is calculated as 25% Adoption + 25% Business Outcomes + 20% Reliability + 20% Quality + 10% Spend Efficiency. Adoption (70% Tier-1 automation) and Business Outcomes (35% handle-time reduction and +12 CSAT points) use account evidence supplied directly by the user; Reliability, Quality, spend, and automated-ticket counts are calculated from the CSV.
- Health-score targets—including the $1,300 period-spend equivalent—are labeled **Illustrative guardrails** because contractual targets are not present in the CSV.
- Relationship coverage, renewal, support cost, staffing, gross margin, brand stage/readiness, estimated value, owner, decision approval, deadlines, and competitive status are not present in the CSV. They are displayed as **Not provided** or **Not assessed**, with proposed validation actions.
- The Everyday Home profile is an illustrative planning assumption pending NorthStar confirmation; it is not presented as verified customer data.
- Spend per request and spend per million tokens are transparent calculations from recorded CSV spend and usage. They are not margin, revenue, or cost-to-serve estimates.
- Internal operational notes are displayed as provided in the CSV. The external data model exposes only the two reduced, customer-safe event notes used for the expansion gates.
- The external outcome cards (70% Tier-1 automation, 35% handle-time reduction, and +12 CSAT points) are explicitly labeled as supplied account outcomes. External service, quality, usage, and spend metrics are calculated from the runtime CSV.
- The external view does not show budget variance because no validated budget or contractual spend target is present in the source. Its pilot path assigns no invented owner, deadline, readiness status, budget target, expansion cost, or confidence.

## Structure

- `app.py` — single Streamlit entry point, cached CSV loading, compact shared header, audience routing, and footer composition.
- `data.py` — Streamlit-independent loading, validation, shared metric calculations, health scoring, observed signals, dated event records, and illustrative internal scenarios.
- `components.py` — shared Fireworks/NorthStar styling, responsive card treatments, header/mode selector, reusable KPI and panel components, and Plotly configuration.
- `internal_dashboard.py` — five-tab internal renderer: Overview, Performance, Risks & Actions, Expansion, and Commercial & Relationships.
- `external_dashboard.py` — customer-safe allowlist, immutable sanitized data model, safe event evidence, and four-tab external renderer.
- `.streamlit/config.toml` — persistent light theme and Fireworks/NorthStar color tokens.
- `tests/test_dashboard.py` — shared-calculation, audience-routing, external-data-boundary, tab-label, customer-content, and Overview-order regression checks.
- `northstar_flagship_30_day_metrics.csv` — runtime operational source.

# MVD US XBRL Country Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the first complete MVD-owned weekly country valuation index for the United States using point-in-time SEC XBRL fundamentals, a replaceable development price adapter, stable cohorts, weekly medians, coverage diagnostics, and explicit warnings.

**Architecture:** Add a new MVD-calculated data path beside the legacy ETF snapshot path. Immutable source observations feed canonical point-in-time company facts, versioned country cohorts, daily aggregate valuations, and atomically published weekly observations. Provider protocols isolate SEC, universe, and price acquisition from reusable calculation code.

**Tech Stack:** Python 3.13, Prefect 3, psycopg/PostgreSQL, pytest, Fastify 5, TypeScript, Next.js 15, React 19, Chakra UI 3, Recharts, Vitest.

**Spec:** `docs/superpowers/specs/2026-09-13-mvd-xbrl-country-indices-design.md`

## Global Constraints

- Assign companies to the country of their primary equity listing.
- Target 75–80% market coverage at cohort formation and warn outside the 72.5–82.5% operating tolerance.
- Keep membership and constituent count stable inside a cohort version.
- Use only facts public by each valuation day's cutoff.
- Calculate daily country aggregates before taking the weekly median; never average company multiples.
- Retain reported, carried-forward, and imputed coverage separately.
- Exact P/FCF is TTM operating cash flow minus TTM cash capital expenditure.
- Never expose development-only raw prices as commercially licensed production data.
- Preserve the previous complete publication if a run is partial or failed.
- Keep the legacy ETF series separate until the MVD series passes acceptance checks.
- Use atomic commits; each task below is one independently reviewable commit.

---

## File map

### Pipeline foundation

- `apps/pipelines/src/sql/schema/040_mvd_country_indices.sql`: normalized source, cohort, calculation, publication, warning, and lineage tables.
- `apps/pipelines/src/lib/source/country_index_types.py`: immutable provider and canonical source types.
- `apps/pipelines/src/lib/source/country_index_protocols.py`: filing, universe, price, and FX provider protocols.
- `apps/pipelines/src/lib/source/adapters/sec_xbrl.py`: SEC submissions/companyfacts discovery and immutable retrieval.
- `apps/pipelines/src/lib/source/adapters/sec_universe.py`: US primary-listing universe from SEC exchange/ticker metadata.
- `apps/pipelines/src/lib/source/adapters/development_prices.py`: explicitly development-only daily-price implementation.
- `apps/pipelines/src/lib/pipeline/canonical_facts.py`: taxonomy mapping and cumulative-period derivation.
- `apps/pipelines/src/lib/pipeline/point_in_time.py`: latest-public-fact selection and TTM construction.
- `apps/pipelines/src/lib/pipeline/country_cohorts.py`: stable 75–80% cohort selection and versioning.
- `apps/pipelines/src/lib/pipeline/country_valuation.py`: aggregate daily metric calculations and coverage.
- `apps/pipelines/src/lib/pipeline/weekly_valuation.py`: weekly medians, ranges, status, and warning rules.
- `apps/pipelines/src/lib/pipeline/uncertainty.py`: seeded initial sensitivity model and effective-count diagnostics.
- `apps/pipelines/src/lib/db/country_indices.py`: idempotent writes and atomic publication pointer.
- `apps/pipelines/src/tasks/run_us_country_index_etl.py`: restartable stage orchestration.
- `apps/pipelines/src/flows/us_country_index_flow.py`: Prefect entry point.

### Product boundaries

- `packages/shared/src/contracts/equity-market-valuation.ts`: overview and country-history contracts for MVD metrics and quality metadata.
- `apps/api/src/routes/equity-market-valuations.ts`: latest weekly overview from the publication mart.
- `apps/api/src/routes/equity-market-valuation-history.ts`: versioned country history and methodology endpoint.
- `apps/web/src/app/equity-markets/market-valuation/page.tsx`: overview rows, coverage, and warning state.
- `apps/web/src/app/equity-markets/market-valuation/[marketId]/page.tsx`: historical country page.
- `apps/web/src/features/equity/market-valuation-methodology.tsx`: reusable methodology and sources.

---

### Task 1: Add the normalized country-index schema

**Files:**
- Create: `apps/pipelines/src/sql/schema/040_mvd_country_indices.sql`
- Modify: `apps/pipelines/src/lib/db/schema.py`
- Test: `apps/pipelines/tests/test_country_index_schema.py`

**Interfaces:**
- Produces: immutable tables under `raw`/`staging`, versioned tables under `core`, and read models under `marts` used by every later task.

- [ ] **Step 1: Write a failing schema registration test**

```python
from src.lib.db.schema import SCHEMA_FILES


def test_country_index_schema_runs_after_legacy_valuation_schema():
    assert SCHEMA_FILES[-1] == "040_mvd_country_indices.sql"
```

Add assertions that the SQL contains primary keys for filings, facts, prices, cohort memberships, daily values, weekly values, publication runs, and warning rows; foreign keys must prevent memberships or metric rows without their parent version.

- [ ] **Step 2: Run the focused test and confirm it fails**

Run: `cd apps/pipelines; python -m pytest tests/test_country_index_schema.py -q`

Expected: failure because `040_mvd_country_indices.sql` is not registered.

- [ ] **Step 3: Define the schema**

Create tables for:

```text
raw.regulatory_filings
raw.regulatory_facts
raw.security_prices
core.securities
core.security_listings
core.canonical_facts
core.country_cohorts
core.country_cohort_members
core.point_in_time_fundamentals
core.country_daily_metrics
core.country_weekly_metrics
core.country_metric_warnings
core.country_index_runs
marts.country_index_publications
```

Use `(provider, external_id, content_hash)` for immutable documents, `(security_id, trading_date, provider)` for prices, `(market_id, cohort_version, security_id)` for memberships, and `(run_id, market_id, metric_key, valuation_date)` / `(run_id, market_id, metric_key, week_id)` for daily and weekly values. Store `methodology_version`, source coverage components, interval bounds, status, and structured reasons on metric observations.

- [ ] **Step 4: Run schema tests**

Run: `cd apps/pipelines; python -m pytest tests/test_country_index_schema.py tests/test_db_load_foundations.py -q`

Expected: all pass.

- [ ] **Step 5: Commit atomically**

```bash
git add apps/pipelines/src/sql/schema/040_mvd_country_indices.sql apps/pipelines/src/lib/db/schema.py apps/pipelines/tests/test_country_index_schema.py
git commit -m "feat: add country index data model"
```

### Task 2: Define provider and canonical domain contracts

**Files:**
- Create: `apps/pipelines/src/lib/source/country_index_types.py`
- Create: `apps/pipelines/src/lib/source/country_index_protocols.py`
- Test: `apps/pipelines/tests/test_country_index_contracts.py`

**Interfaces:**
- Produces: `RegulatoryFiling`, `RawXbrlFact`, `SecurityListing`, `DailyPrice`, `FxRate`, `ProviderLicense`, `FilingProvider`, `UniverseProvider`, `PriceProvider`, and `FxProvider`.

- [ ] **Step 1: Write failing contract tests**

```python
def test_price_license_blocks_development_provider_in_production():
    license_info = ProviderLicense(provider="fixture", usage="development_only")
    with pytest.raises(ValueError, match="commercial production"):
        license_info.assert_publishable(environment="production")


def test_raw_fact_keeps_point_in_time_lineage():
    fact = RawXbrlFact(..., published_at="2026-05-01T12:00:00Z")
    assert fact.filing_id
    assert fact.taxonomy
    assert fact.context_id
```

- [ ] **Step 2: Verify failure**

Run: `cd apps/pipelines; python -m pytest tests/test_country_index_contracts.py -q`

- [ ] **Step 3: Implement frozen dataclasses and protocols**

Use explicit signatures:

```python
class FilingProvider(Protocol):
    def discover(self, accepted_from: datetime, accepted_to: datetime) -> list[RegulatoryFiling]: ...
    def fetch_facts(self, filing: RegulatoryFiling) -> list[RawXbrlFact]: ...

class UniverseProvider(Protocol):
    def listings_as_of(self, market_id: str, as_of: date) -> list[SecurityListing]: ...

class PriceProvider(Protocol):
    license: ProviderLicense
    def daily_prices(self, security: SecurityListing, start: date, end: date) -> list[DailyPrice]: ...
```

Reject naive datetimes and non-positive prices at construction.

- [ ] **Step 4: Run tests**

Run: `cd apps/pipelines; python -m pytest tests/test_country_index_contracts.py -q`

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/source/country_index_types.py apps/pipelines/src/lib/source/country_index_protocols.py apps/pipelines/tests/test_country_index_contracts.py
git commit -m "feat: define country index provider contracts"
```

### Task 3: Implement immutable SEC XBRL acquisition

**Files:**
- Create: `apps/pipelines/src/lib/source/adapters/sec_xbrl.py`
- Create: `apps/pipelines/tests/fixtures/sec/company_tickers_exchange.json`
- Create: `apps/pipelines/tests/fixtures/sec/companyfacts_aapl.json`
- Test: `apps/pipelines/tests/test_sec_xbrl_adapter.py`

**Interfaces:**
- Consumes: `FilingProvider`, `RegulatoryFiling`, `RawXbrlFact`.
- Produces: `SecXbrlAdapter.discover_company(cik: str)`, `fetch_companyfacts(cik: str)`, and parsed facts retaining accession, filing date, period, form, frame, unit, and source URL.

- [ ] **Step 1: Write fixture-based failing tests**

Test that amended facts retain separate accession/publication timestamps, custom concepts are preserved in raw facts, supported forms include `10-K`, `10-Q`, `20-F`, and `40-F`, and requests set an identifiable SEC-compliant user agent.

- [ ] **Step 2: Verify failure without network access**

Run: `cd apps/pipelines; python -m pytest tests/test_sec_xbrl_adapter.py -q`

- [ ] **Step 3: Implement the adapter using standard-library HTTP**

Use injectable `fetch_json(url, headers)` so tests never call SEC. Prefer SEC bulk archives for backfill and companyfacts for incremental updates. Return failures as typed source errors; never disable TLS verification.

- [ ] **Step 4: Run adapter and existing source tests**

Run: `cd apps/pipelines; python -m pytest tests/test_sec_xbrl_adapter.py tests/test_source_fetch.py tests/test_error_handling.py -q`

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/source/adapters/sec_xbrl.py apps/pipelines/tests/fixtures/sec apps/pipelines/tests/test_sec_xbrl_adapter.py
git commit -m "feat: ingest SEC XBRL facts"
```

### Task 4: Build the US listing universe and development price adapter

**Files:**
- Create: `apps/pipelines/src/lib/source/adapters/sec_universe.py`
- Create: `apps/pipelines/src/lib/source/adapters/development_prices.py`
- Test: `apps/pipelines/tests/test_sec_universe_adapter.py`
- Test: `apps/pipelines/tests/test_development_price_adapter.py`

**Interfaces:**
- Produces: primary common-stock `SecurityListing` rows and split-aware `DailyPrice` rows.

- [ ] **Step 1: Write failing tests for filtering and licensing**

Cover duplicate share classes, ETFs, funds, preferred shares, ADR duplication, inactive dates, zero prices, split metadata, missing dates, and this hard guard:

```python
with pytest.raises(ValueError, match="development-only"):
    adapter.assert_publishable(environment="production")
```

- [ ] **Step 2: Verify failure**

Run: `cd apps/pipelines; python -m pytest tests/test_sec_universe_adapter.py tests/test_development_price_adapter.py -q`

- [ ] **Step 3: Implement adapters behind injected transports**

Use SEC `company_tickers_exchange.json` as discovery input, then deterministic security-type rules. Reuse no ETF-fundamental code. The price adapter may use a free development endpoint only when `MVD_ENV != production`; persist provider and license class with every price.

- [ ] **Step 4: Run focused tests**

Run: `cd apps/pipelines; python -m pytest tests/test_sec_universe_adapter.py tests/test_development_price_adapter.py -q`

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/source/adapters/sec_universe.py apps/pipelines/src/lib/source/adapters/development_prices.py apps/pipelines/tests/test_sec_universe_adapter.py apps/pipelines/tests/test_development_price_adapter.py
git commit -m "feat: add US universe and development prices"
```

### Task 5: Normalize SEC facts and construct point-in-time TTM values

**Files:**
- Create: `apps/pipelines/src/lib/pipeline/canonical_facts.py`
- Create: `apps/pipelines/src/lib/pipeline/point_in_time.py`
- Test: `apps/pipelines/tests/test_canonical_facts.py`
- Test: `apps/pipelines/tests/test_point_in_time_fundamentals.py`

**Interfaces:**
- Produces: `normalize_facts(facts, taxonomy_version) -> list[CanonicalFact]` and `fundamentals_as_of(security_id, valuation_at, facts) -> PointInTimeFundamentals`.

- [ ] **Step 1: Write failing tests**

Cover direct quarters, `Q2 = H1 - Q1`, `Q4 = FY - 9M`, amendments visible only after acceptance, consolidated facts preferred over parent-only facts, unit conversion, latest equity instant, TTM dividends, and exact FCF.

```python
assert result.ttm_free_cash_flow == result.ttm_operating_cash_flow - result.ttm_capex
assert result.net_income.lineage.publication_times <= (valuation_at,)
```

- [ ] **Step 2: Verify failure**

Run: `cd apps/pipelines; python -m pytest tests/test_canonical_facts.py tests/test_point_in_time_fundamentals.py -q`

- [ ] **Step 3: Implement versioned concept mapping and selection**

Map standard US GAAP/IFRS concepts to canonical revenue, attributable net income, common equity, operating cash flow, cash capex, common dividends, weighted-average shares, and period-end shares. Preserve candidate facts and rejection reasons instead of overwriting conflicts.

- [ ] **Step 4: Run tests**

Run: `cd apps/pipelines; python -m pytest tests/test_canonical_facts.py tests/test_point_in_time_fundamentals.py -q`

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/pipeline/canonical_facts.py apps/pipelines/src/lib/pipeline/point_in_time.py apps/pipelines/tests/test_canonical_facts.py apps/pipelines/tests/test_point_in_time_fundamentals.py
git commit -m "feat: calculate point-in-time SEC fundamentals"
```

### Task 6: Construct stable country cohorts

**Files:**
- Create: `apps/pipelines/src/lib/pipeline/country_cohorts.py`
- Test: `apps/pipelines/tests/test_country_cohorts.py`

**Interfaces:**
- Produces: `form_cohort(market_id, effective_date, candidates, target=(0.75, 0.80)) -> CountryCohort` and `evaluate_cohort_coverage(cohort, market_caps) -> CohortCoverage`.

- [ ] **Step 1: Write failing deterministic-selection tests**

Test the smallest stable count in band, deterministic tie breaking by security ID, closest-above-75% fallback, 72.5–82.5% warnings, two-week exceptional reconstitution trigger, forced replacement, and unchanged count.

- [ ] **Step 2: Verify failure**

Run: `cd apps/pipelines; python -m pytest tests/test_country_cohorts.py -q`

- [ ] **Step 3: Implement pure cohort functions**

Keep database and network access out of this module. Return structured `coverage_band_unreachable`, `coverage_below_tolerance`, and `coverage_above_tolerance` reasons.

- [ ] **Step 4: Run tests**

Run: `cd apps/pipelines; python -m pytest tests/test_country_cohorts.py -q`

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/pipeline/country_cohorts.py apps/pipelines/tests/test_country_cohorts.py
git commit -m "feat: build stable country index cohorts"
```

### Task 7: Calculate daily aggregate valuation metrics

**Files:**
- Create: `apps/pipelines/src/lib/pipeline/country_valuation.py`
- Test: `apps/pipelines/tests/test_country_valuation.py`

**Interfaces:**
- Produces: `calculate_daily_country_metrics(cohort, prices, fundamentals, fx, methodology_version) -> list[DailyCountryMetric]`.

- [ ] **Step 1: Write failing numeric tests**

Use a three-company fixture proving aggregate P/E differs from mean company P/E. Cover P/B, P/S, P/CF, exact P/FCF, dividend yield, negative aggregate denominators, finance-sector eligibility, reported/carried/imputed weights, concentration, and effective count.

```python
expected_pe = sum(row.market_cap for row in rows) / sum(row.ttm_net_income for row in rows)
assert metrics["pe"].value == Decimal(str(expected_pe))
```

- [ ] **Step 2: Verify failure**

Run: `cd apps/pipelines; python -m pytest tests/test_country_valuation.py -q`

- [ ] **Step 3: Implement Decimal-based aggregation**

Calculate market caps in a common currency, keep losses in denominators, and return unavailable with `non_positive_denominator` instead of emitting a misleading multiple. Never renormalize away a fixed-cohort constituent with missing data.

- [ ] **Step 4: Run tests**

Run: `cd apps/pipelines; python -m pytest tests/test_country_valuation.py -q`

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/pipeline/country_valuation.py apps/pipelines/tests/test_country_valuation.py
git commit -m "feat: calculate aggregate country valuations"
```

### Task 8: Add weekly medians and initial uncertainty reporting

**Files:**
- Create: `apps/pipelines/src/lib/pipeline/weekly_valuation.py`
- Create: `apps/pipelines/src/lib/pipeline/uncertainty.py`
- Test: `apps/pipelines/tests/test_weekly_valuation.py`
- Test: `apps/pipelines/tests/test_country_index_uncertainty.py`

**Interfaces:**
- Produces: `summarize_week(daily_metrics) -> WeeklyCountryMetric` and `estimate_sensitivity(metric, cohort, seed, draws=1000) -> SensitivityResult`.

- [ ] **Step 1: Write failing tests**

Test median-of-five behavior, four-day holiday weeks, rejection below three days, min/max range, midweek filing cutoff, deterministic seeded intervals, leave-one-out impact, effective count, warning ordering, and `experimental` status before calibration.

- [ ] **Step 2: Verify failure**

Run: `cd apps/pipelines; python -m pytest tests/test_weekly_valuation.py tests/test_country_index_uncertainty.py -q`

- [ ] **Step 3: Implement weekly and sensitivity summaries**

Use the median imputation result as the point estimate when fixed-cohort facts are missing. Store imputed weight separately, derive interval percentiles from all draws, and expose component contributions. Do not describe this interval as a confidence interval.

- [ ] **Step 4: Run tests**

Run: `cd apps/pipelines; python -m pytest tests/test_weekly_valuation.py tests/test_country_index_uncertainty.py -q`

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/pipeline/weekly_valuation.py apps/pipelines/src/lib/pipeline/uncertainty.py apps/pipelines/tests/test_weekly_valuation.py apps/pipelines/tests/test_country_index_uncertainty.py
git commit -m "feat: summarize weekly valuation uncertainty"
```

### Task 9: Persist stages and publish atomically

**Files:**
- Create: `apps/pipelines/src/lib/db/country_indices.py`
- Test: `apps/pipelines/tests/test_country_index_db.py`

**Interfaces:**
- Produces idempotent `upsert_*` functions and `publish_completed_run(connection, run_id)`.

- [ ] **Step 1: Write failing transaction tests**

Assert immutable raw inserts use conflict-ignore, derived rows upsert only inside the same methodology/run key, failed runs cannot publish, and publication pointer replacement happens in one transaction after all expected market/metric rows validate.

- [ ] **Step 2: Verify failure**

Run: `cd apps/pipelines; python -m pytest tests/test_country_index_db.py -q`

- [ ] **Step 3: Implement parameterized psycopg writes**

Do not delete history by `market_id`. Roll back the transaction on invariant failure and retain the prior row in `marts.country_index_publications`.

- [ ] **Step 4: Run tests**

Run: `cd apps/pipelines; python -m pytest tests/test_country_index_db.py tests/test_db_load_foundations.py -q`

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/db/country_indices.py apps/pipelines/tests/test_country_index_db.py
git commit -m "feat: publish country indices atomically"
```

### Task 10: Orchestrate the US vertical slice

**Files:**
- Create: `apps/pipelines/src/tasks/run_us_country_index_etl.py`
- Create: `apps/pipelines/src/flows/us_country_index_flow.py`
- Modify: `apps/pipelines/src/flows/all_flows.py`
- Test: `apps/pipelines/tests/test_us_country_index_flow.py`
- Modify: `apps/pipelines/tests/test_all_flows.py`

**Interfaces:**
- Produces: `run_us_country_index_flow() -> dict[str, object]` with stage counts, publication status, source errors, warning counts, and previous-publication preservation.

- [ ] **Step 1: Write a failing orchestration test with fake providers**

Prove stage order, checkpoint reuse, one failed symbol becoming a structured warning, production license guard, minimum-three-day rule, and atomic publication only after validation.

- [ ] **Step 2: Verify failure**

Run: `cd apps/pipelines; python -m pytest tests/test_us_country_index_flow.py tests/test_all_flows.py -q`

- [ ] **Step 3: Implement the task and Prefect flow**

Run immutable ingestion, normalization, cohort evaluation, five daily calculations, weekly summary, sensitivity, validation, and publication as named restartable stages. Keep historical backfill out of the weekend incremental flow.

- [ ] **Step 4: Run the complete pipeline suite**

Run: `cd apps/pipelines; python -m pytest -q`

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/tasks/run_us_country_index_etl.py apps/pipelines/src/flows/us_country_index_flow.py apps/pipelines/src/flows/all_flows.py apps/pipelines/tests/test_us_country_index_flow.py apps/pipelines/tests/test_all_flows.py
git commit -m "feat: orchestrate the US country index flow"
```

### Task 11: Expose versioned overview and history contracts

**Files:**
- Modify: `packages/shared/src/contracts/equity-market-valuation.ts`
- Modify: `apps/api/src/routes/equity-market-valuations.ts`
- Create: `apps/api/src/routes/equity-market-valuation-history.ts`
- Modify: `apps/api/src/server.ts`
- Modify: `apps/api/tests/equity-market-valuations-route.test.ts`
- Create: `apps/api/tests/equity-market-valuation-history-route.test.ts`

**Interfaces:**
- Produces: `GET /equity-markets/valuations` and `GET /equity-markets/valuations/:marketId?from=&to=` using only atomically published runs.

- [ ] **Step 1: Write failing API tests**

Require fields for value, weekly range, sensitivity interval, method, status, coverage components, actual/effective counts, concentration, cohort version, valuation week/dates, warning codes, methodology version, and references. Verify unknown market returns 404 and invalid dates return 400.

- [ ] **Step 2: Verify failure**

Run: `npm run test --workspace @mvd/api -- equity-market-valuations-route.test.ts equity-market-valuation-history-route.test.ts`

- [ ] **Step 3: Update shared types and SQL mapping**

Query the publication mart, never raw/staging tables. Return structured references once per source/methodology and connect metric claims to reference IDs.

- [ ] **Step 4: Run API tests**

Run: `npm run test --workspace @mvd/api`

- [ ] **Step 5: Commit**

```bash
git add packages/shared/src/contracts/equity-market-valuation.ts apps/api/src/routes/equity-market-valuations.ts apps/api/src/routes/equity-market-valuation-history.ts apps/api/src/server.ts apps/api/tests/equity-market-valuations-route.test.ts apps/api/tests/equity-market-valuation-history-route.test.ts
git commit -m "feat: expose MVD country valuation history"
```

### Task 12: Build the overview and US history page

**Files:**
- Modify: `apps/web/src/app/equity-markets/market-valuation/page.tsx`
- Create: `apps/web/src/app/equity-markets/market-valuation/[marketId]/page.tsx`
- Create: `apps/web/src/features/equity/market-valuation-methodology.tsx`
- Modify: `apps/web/tests/market-valuation-page.test.tsx`
- Create: `apps/web/tests/market-valuation-history-page.test.tsx`

**Interfaces:**
- Consumes the contracts from Task 11.
- Produces a clickable country row and country page with weekly charts and methodology.

- [ ] **Step 1: Write failing UI tests**

Test that the overview shows company count, effective count, market/fundamental coverage, warning icon/reason, and no ETF identity; the country page shows weekly median methodology, range, sensitivity band, cohort boundary, freshness, formulas, exact source citations, and an unavailable state. Verify columns absent for all visible countries remain hidden.

- [ ] **Step 2: Verify failure**

Run: `npm run test --workspace @mvd/web -- market-valuation-page.test.tsx market-valuation-history-page.test.tsx`

- [ ] **Step 3: Implement responsive Chakra UI pages**

Use the existing theme and analysis citation components. Make the entire overview row and country title link to the history page. Use Recharts for weekly value/range/sensitivity display, with an accessible table fallback. Explain that the headline is the median of daily aggregate country values and show development-price methodology visibly while applicable.

- [ ] **Step 4: Run web tests**

Run: `npm run test --workspace @mvd/web`

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/app/equity-markets/market-valuation/page.tsx apps/web/src/app/equity-markets/market-valuation/[marketId]/page.tsx apps/web/src/features/equity/market-valuation-methodology.tsx apps/web/tests/market-valuation-page.test.tsx apps/web/tests/market-valuation-history-page.test.tsx
git commit -m "feat: show MVD country valuation history"
```

### Task 13: Run the US feasibility and reconciliation gate

**Files:**
- Create: `apps/pipelines/src/flows/us_country_index_backfill.py`
- Create: `apps/pipelines/tests/test_us_country_index_backfill.py`
- Create: `docs/validation/mvd-us-country-index-feasibility.md`

**Interfaces:**
- Produces a bounded backfill command and an evidence report that decides whether the architecture is ready for additional jurisdictions.

- [ ] **Step 1: Write the backfill acceptance test**

Test a fixture backfill across a filing amendment, split, missing price day, cohort transition, and holiday week. Assert rerunning is idempotent and produces identical methodology-versioned weekly rows.

- [ ] **Step 2: Implement bounded backfill parameters**

Expose `--from`, `--to`, `--market us`, `--resume`, and `--development-prices`. Refuse an unbounded backfill and refuse production publication with development prices.

- [ ] **Step 3: Run fixture verification**

Run: `cd apps/pipelines; python -m pytest tests/test_us_country_index_backfill.py -q`

- [ ] **Step 4: Run a live development sample**

Run one recent complete week, then one historical quarter. Record runtime, eligible-universe count, price coverage, XBRL mapping coverage, market coverage, metric coverage, warning distribution, and unresolved identifier/corporate-action cases in the validation document. Do not claim commercial readiness.

- [ ] **Step 5: Run repository verification**

Run:

```bash
cd apps/pipelines && python -m pytest -q
npm run test --workspace @mvd/api
npm run test --workspace @mvd/web
```

Expected: all pass; the feasibility document contains measured results rather than placeholders.

- [ ] **Step 6: Commit**

```bash
git add apps/pipelines/src/flows/us_country_index_backfill.py apps/pipelines/tests/test_us_country_index_backfill.py docs/validation/mvd-us-country-index-feasibility.md
git commit -m "test: validate US country index feasibility"
```

## Post-plan jurisdiction sequence

Do not implement additional jurisdictions inside this plan. If the US feasibility gate passes, write one adapter plan per source family in this order:

1. EDINET/Japan to prove the canonical model outside SEC and US GAAP.
2. OpenDART/South Korea.
3. MOPS/Taiwan.
4. ESEF EU/EEA discovery plus country-by-country promotion gates.
5. UKSEF/FCA and Companies House reconciliation.

Each later plan reuses the schema, protocols, point-in-time engine, cohort engine, daily aggregation, weekly aggregation, uncertainty model, API, and UI from this plan. A jurisdiction task may add taxonomy mappings and source metadata but may not fork metric definitions silently.

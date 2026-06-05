# Currency Analysis Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real `Currency Analysis` end to end on top of the existing MVD architecture, covering relative PPP and IRP for `EUR/USD` from source layer to UI.

**Architecture:** Implementation should extend the current Taylor-driven foundations instead of creating a second parallel stack. Public serving stays `mart`-first, ETL stays `domain-first`, and the page remains one coherent analysis surface even though `PPP` and `IRP` are prepared through separate analytical transforms and honest availability checks.

**Tech Stack:** Python, Prefect, PostgreSQL, Fastify, Next.js, TypeScript, Chakra UI, pytest, Vitest

---

## File Map

### Existing files likely to modify

- `apps/pipelines/src/lib/source/registry.py`
- `apps/pipelines/src/lib/source/types.py`
- `apps/pipelines/src/lib/source/fetch.py`
- `apps/pipelines/src/lib/db.py`
- `apps/pipelines/src/lib/pipeline/transforms/staging.py`
- `apps/pipelines/src/lib/pipeline/transforms/reference_metrics.py`
- `apps/pipelines/src/sql/taylor_rule_schema.sql`
- `apps/pipelines/src/flows/all_flows.py`
- `apps/api/src/server.ts`
- `apps/api/src/lib/db.ts`
- `apps/web/src/features/site-shell/mvd-data.ts`
- `apps/web/src/app/macro/page.tsx`
- `apps/web/src/app/macro/[driver]/page.tsx`

### New files likely to create

#### Shared contracts
- `packages/shared/src/contracts/currency-analysis.ts`

#### Pipelines
- `apps/pipelines/src/lib/pipeline/transforms/currency_ppp.py`
- `apps/pipelines/src/lib/pipeline/transforms/currency_irp.py`
- `apps/pipelines/src/tasks/run_currency_market_etl.py`
- `apps/pipelines/src/tasks/load_currency_analysis_layers.py`
- `apps/pipelines/src/flows/currency_analysis_flow.py`
- `apps/pipelines/tests/test_currency_ppp_transform.py`
- `apps/pipelines/tests/test_currency_irp_transform.py`
- `apps/pipelines/tests/test_currency_analysis_flow.py`

#### API
- `apps/api/src/routes/currency-analysis.ts`
- `apps/api/tests/currency-analysis-route.test.ts`

#### Web
- `apps/web/src/app/macro/currency-analysis/page.tsx`
- `apps/web/src/features/macro/currency-analysis-client.tsx`
- `apps/web/src/features/macro/currency-analysis-types.ts`
- `apps/web/tests/currency-analysis-page.test.tsx`

---

## Phase 1: Extend Source Coverage For Currency Inputs

**Objective:** Add the raw source coverage needed for `EUR/USD` spot, monthly CPI index levels, tenor-specific money-market / gov-bill proxies, and observed forward quotes where a reliable provider path exists.

**Target internal series keys**
- `eurusd_spot_monthly`
- `eurusd_spot_daily`
- `us_cpi_index`
- `ea_cpi_index`
- `eur_3m_rate`
- `eur_6m_rate`
- `eur_12m_rate`
- `usd_3m_rate`
- `usd_6m_rate`
- `usd_12m_rate`
- `eurusd_forward_3m`
- `eurusd_forward_6m`
- `eurusd_forward_12m`

**Files**
- Modify: `apps/pipelines/src/lib/source/registry.py`
- Modify: `apps/pipelines/src/lib/source/types.py`
- Modify: `apps/pipelines/src/lib/source/fetch.py`
- Test: `apps/pipelines/tests/test_source_registry.py`
- Test: `apps/pipelines/tests/test_source_fetch.py`
- Test: `apps/pipelines/tests/test_fred_adapter.py`
- Test: `apps/pipelines/tests/test_ecb_adapter.py`
- Test: `apps/pipelines/tests/test_dbnomics_adapter.py`

- [ ] Add failing registry tests for the new currency series keys, asserting provider, frequency, unit, region, and source URL metadata are present.

- [ ] Run the registry tests to confirm they fail because the currency series are not registered yet.

Run: `pytest apps/pipelines/tests/test_source_registry.py -v`
Expected: FAIL with missing currency-analysis series keys.

- [ ] Extend `registry.py` with `EUR/USD`, CPI index, and tenor-rate series definitions using the existing `SeriesDefinition` model and only real provider paths.

- [ ] If observed forward data needs metadata beyond the current source types, extend `types.py` minimally so forward series can declare tenor and asset metadata without breaking the Taylor path.

- [ ] Update `fetch.py` only if needed so the dispatcher can handle any newly required provider metadata without hardcoding currency-analysis logic into fetch orchestration.

- [ ] Add tests that verify:
  - CPI index series use index-level units rather than inflation-rate units
  - tenor-rate series are frequency- and tenor-tagged correctly
  - forward series either map to a real provider path or are omitted from the registry entirely

- [ ] Run the focused source tests again.

Run: `pytest apps/pipelines/tests/test_source_registry.py apps/pipelines/tests/test_source_fetch.py apps/pipelines/tests/test_fred_adapter.py apps/pipelines/tests/test_ecb_adapter.py apps/pipelines/tests/test_dbnomics_adapter.py -v`
Expected: PASS with the new currency series definitions loading cleanly.

- [ ] Commit:

```bash
git add apps/pipelines/src/lib/source/registry.py apps/pipelines/src/lib/source/types.py apps/pipelines/src/lib/source/fetch.py apps/pipelines/tests/test_source_registry.py apps/pipelines/tests/test_source_fetch.py apps/pipelines/tests/test_fred_adapter.py apps/pipelines/tests/test_ecb_adapter.py apps/pipelines/tests/test_dbnomics_adapter.py
git commit -m "feat: extend source coverage for currency analysis"
```

---

## Phase 2: Expand Database And Load Layer For Currency Marts

**Objective:** Add mart storage for `PPP`, `IRP`, and honest availability metadata while reusing the current raw and staging layer structure.

**Files**
- Modify: `apps/pipelines/src/sql/taylor_rule_schema.sql`
- Modify: `apps/pipelines/src/lib/db.py`
- Test: `apps/pipelines/tests/test_db_load_foundations.py`

- [ ] Add failing DB-load tests for new mart tables and helper functions:
  - `mart.currency_ppp_snapshots`
  - `mart.currency_ppp_paths`
  - `mart.currency_irp_snapshots`
  - `mart.currency_data_availability`

- [ ] Run the DB-load tests to verify the new schema objects do not yet exist.

Run: `pytest apps/pipelines/tests/test_db_load_foundations.py -v`
Expected: FAIL with missing currency-analysis tables or helper expectations.

- [ ] Extend `taylor_rule_schema.sql` with the currency mart tables:
  - `mart.currency_ppp_snapshots` for base-month-specific current fair value / deviation outputs
  - `mart.currency_ppp_paths` for monthly PPP path points
  - `mart.currency_irp_snapshots` for tenor-specific `CIP` / `UIP` outputs
  - `mart.currency_data_availability` for no-fallback display control

- [ ] Keep the existing `raw.series_observations` and `staging.series_observations` tables as the canonical storage for currency source observations instead of inventing a second raw model.

- [ ] Add DB helper functions to `db.py` for:
  - replacing PPP snapshot rows
  - replacing PPP path rows
  - replacing IRP snapshot rows
  - replacing currency availability rows

- [ ] Ensure the new helpers accept complete prepared rows and do not recreate transform logic inside the load layer.

- [ ] Run the DB-load tests again.

Run: `pytest apps/pipelines/tests/test_db_load_foundations.py -v`
Expected: PASS with schema bootstrap and load helpers supporting currency mart tables.

- [ ] Commit:

```bash
git add apps/pipelines/src/sql/taylor_rule_schema.sql apps/pipelines/src/lib/db.py apps/pipelines/tests/test_db_load_foundations.py
git commit -m "feat: add currency analysis mart load foundations"
```

---

## Phase 3: Build Currency Analytical Transforms And Flow

**Objective:** Implement the reusable analytical transforms and one composed flow that produces `PPP`, `IRP`, and availability outputs from staged data.

**Files**
- Create: `apps/pipelines/src/lib/pipeline/transforms/currency_ppp.py`
- Create: `apps/pipelines/src/lib/pipeline/transforms/currency_irp.py`
- Modify: `apps/pipelines/src/lib/pipeline/transforms/staging.py`
- Modify: `apps/pipelines/src/lib/pipeline/transforms/reference_metrics.py`
- Create: `apps/pipelines/src/tasks/run_currency_market_etl.py`
- Create: `apps/pipelines/src/tasks/load_currency_analysis_layers.py`
- Create: `apps/pipelines/src/flows/currency_analysis_flow.py`
- Modify: `apps/pipelines/src/flows/all_flows.py`
- Test: `apps/pipelines/tests/test_currency_ppp_transform.py`
- Test: `apps/pipelines/tests/test_currency_irp_transform.py`
- Test: `apps/pipelines/tests/test_currency_analysis_flow.py`

- [ ] Add a failing `PPP` transform test that feeds staged monthly `EUR/USD`, `US CPI`, and `Euro Area CPI` rows into a transform and asserts:
  - base-month anchoring uses the chosen month’s observed spot
  - the output path is built from index levels, not YoY rates
  - the current snapshot includes implied fair value and percent deviation

- [ ] Add a failing `IRP` transform test that feeds staged spot, tenor rates, and optional forward rows into a transform and asserts:
  - `3M`, `6M`, and `12M` rows are produced independently
  - `CIP` implied forward is computed per tenor
  - observed-forward comparisons are omitted when forward data is unavailable
  - `UIP` is emitted as a smaller theoretical companion output, not merged into the main `CIP` row shape

- [ ] Run the new transform tests to verify both fail before implementation.

Run: `pytest apps/pipelines/tests/test_currency_ppp_transform.py apps/pipelines/tests/test_currency_irp_transform.py -v`
Expected: FAIL with missing currency transform modules.

- [ ] Implement `currency_ppp.py` with pure analytical helpers that:
  - accept staged monthly index and spot rows
  - generate monthly PPP path points across all available base months
  - generate current snapshot rows for the API to filter by user-selected base month later

- [ ] Implement `currency_irp.py` with helpers that:
  - accept latest staged spot, tenor-rate, and optional forward rows
  - compute tenor spreads, `CIP` implied forwards, optional basis gaps, and `UIP` expectation fields
  - emit explicit availability flags so missing forward rows suppress only the affected tenor comparison

- [ ] Extend `staging.py` only where needed to normalize FX and rate series cleanly into the existing staged-observation shape.

- [ ] Extend `reference_metrics.py` only if it is the cleanest place to expose already-built real-rate reference context to the later `Currency Analysis` API without turning it into a third analytical section.

- [ ] Implement `run_currency_market_etl.py` so one domain ETL run:
  - fetches currency source series
  - writes raw rows
  - stages observations
  - runs both analytical transforms
  - writes mart outputs
  - records availability metadata honestly

- [ ] Implement `load_currency_analysis_layers.py` with thin load orchestration over the new DB helper functions.

- [ ] Implement `currency_analysis_flow.py` and register it in `all_flows.py`.

- [ ] Add a flow test that covers:
  - successful PPP + IRP mart writes
  - missing-forward behavior that suppresses only the affected observed-forward comparison
  - failed required-PPP-input behavior that records unavailable PPP output rather than fabricating fallback values

- [ ] Run the focused pipeline tests again.

Run: `pytest apps/pipelines/tests/test_currency_ppp_transform.py apps/pipelines/tests/test_currency_irp_transform.py apps/pipelines/tests/test_currency_analysis_flow.py apps/pipelines/tests/test_all_flows.py -v`
Expected: PASS with the currency flow producing mart-ready outputs and honest availability metadata.

- [ ] Commit:

```bash
git add apps/pipelines/src/lib/pipeline/transforms/currency_ppp.py apps/pipelines/src/lib/pipeline/transforms/currency_irp.py apps/pipelines/src/lib/pipeline/transforms/staging.py apps/pipelines/src/lib/pipeline/transforms/reference_metrics.py apps/pipelines/src/tasks/run_currency_market_etl.py apps/pipelines/src/tasks/load_currency_analysis_layers.py apps/pipelines/src/flows/currency_analysis_flow.py apps/pipelines/src/flows/all_flows.py apps/pipelines/tests/test_currency_ppp_transform.py apps/pipelines/tests/test_currency_irp_transform.py apps/pipelines/tests/test_currency_analysis_flow.py
git commit -m "feat: add currency analysis pipeline flow"
```

---

## Phase 4: Add Shared Contract And API Route

**Objective:** Expose a stable, mart-first API contract for the new currency analysis page, including user-selectable PPP base month and honest IRP availability.

**Files**
- Create: `packages/shared/src/contracts/currency-analysis.ts`
- Create: `apps/api/src/routes/currency-analysis.ts`
- Modify: `apps/api/src/server.ts`
- Test: `apps/api/tests/currency-analysis-route.test.ts`

- [ ] Add a failing shared-contract + route test that expects `/macro/currency-analysis` to return:
  - top-level `asOf`
  - `ppp` block with available base months, selected base month, summary snapshot, path points, and references
  - `irp` block with `3M`, `6M`, `12M` rows, a distinct `uip` sub-section, and availability-aware references

- [ ] Run the API route test to confirm the route is missing.

Run: `npm --prefix apps/api test -- currency-analysis-route.test.ts`
Expected: FAIL with route not found or missing contract file.

- [ ] Define `CurrencyAnalysisResponse` in `packages/shared/src/contracts/currency-analysis.ts` so web and API share one explicit response shape.

- [ ] Implement `currency-analysis.ts` route logic that:
  - reads only mart tables
  - accepts an optional `baseMonth` query parameter
  - validates the requested base month against available snapshot rows
  - returns the selected PPP snapshot plus the full path for that base month
  - returns `IRP` tenor rows only when their required data exists
  - returns `UIP` as a separate sub-block under the IRP section

- [ ] Keep API behavior honest:
  - if no valid PPP base month exists, return an empty PPP block rather than fabricated output
  - if a tenor lacks observed forward data, omit the observed-forward comparison fields for that tenor
  - if a tenor lacks required rate inputs entirely, omit that tenor row

- [ ] Register the route in `server.ts`.

- [ ] Run the API tests again.

Run: `npm --prefix apps/api test -- currency-analysis-route.test.ts`
Expected: PASS with the route returning mart-first currency-analysis data and correct empty-state behavior.

- [ ] Commit:

```bash
git add packages/shared/src/contracts/currency-analysis.ts apps/api/src/routes/currency-analysis.ts apps/api/src/server.ts apps/api/tests/currency-analysis-route.test.ts
git commit -m "feat: add currency analysis api route"
```

---

## Phase 5: Build The Currency Analysis Page

**Objective:** Create the first product-facing `Currency Analysis` page with theory-first sections, a user-selectable PPP base month, and a side-by-side IRP tenor table.

**Files**
- Modify: `apps/web/src/features/site-shell/mvd-data.ts`
- Modify: `apps/web/src/app/macro/page.tsx`
- Modify: `apps/web/src/app/macro/[driver]/page.tsx`
- Create: `apps/web/src/app/macro/currency-analysis/page.tsx`
- Create: `apps/web/src/features/macro/currency-analysis-types.ts`
- Create: `apps/web/src/features/macro/currency-analysis-client.tsx`
- Test: `apps/web/tests/currency-analysis-page.test.tsx`

- [ ] Add a failing page test that expects `/macro/currency-analysis` to render:
  - a `Relative Purchasing Power Parity` section with theory text, formula, base-month control, summary view, chart shell, takeaway, and references
  - an `Interest Rate Parity` section with theory text, formula, `CIP` tenor table, separate `UIP` sub-section, takeaway, and references
  - no placeholder text and no fake “fallback” values when data is missing

- [ ] Run the web test to confirm the route and client components do not exist yet.

Run: `npm --prefix apps/web test -- currency-analysis-page.test.tsx`
Expected: FAIL with missing page or missing rendered sections.

- [ ] Add `currency-analysis` to `mvd-data.ts` with a summary that matches the master plan and does not hardcode this page as the only future FX analysis forever.

- [ ] Create `currency-analysis-types.ts` as the local frontend type wrapper around `CurrencyAnalysisResponse`.

- [ ] Implement `page.tsx` as a server component that fetches `/macro/currency-analysis`, passes through search params for `baseMonth`, and keeps provider-specific logic out of the UI.

- [ ] Implement `currency-analysis-client.tsx` with:
  - `PPP` theory-first block
  - explicit PPP formula block
  - month-level base selector
  - summary card for current spot vs implied fair value
  - chart component shell for spot vs PPP path
  - short takeaway text block
  - `IRP` theory-first block
  - formula block for `CIP` and `UIP`
  - `3M / 6M / 12M` `CIP` table
  - separate `UIP` sub-section
  - references per section

- [ ] Keep rendering honest:
  - missing PPP output should suppress the PPP analysis body rather than fill it with dummy numbers
  - missing observed forwards should leave only the affected table cells or labels absent, not replaced by fake values

- [ ] Run the web tests again.

Run: `npm --prefix apps/web test -- currency-analysis-page.test.tsx`
Expected: PASS with the page rendering theory-first PPP and IRP sections and honest partial-data handling.

- [ ] Commit:

```bash
git add apps/web/src/features/site-shell/mvd-data.ts apps/web/src/app/macro/page.tsx apps/web/src/app/macro/[driver]/page.tsx apps/web/src/app/macro/currency-analysis/page.tsx apps/web/src/features/macro/currency-analysis-types.ts apps/web/src/features/macro/currency-analysis-client.tsx apps/web/tests/currency-analysis-page.test.tsx
git commit -m "feat: add currency analysis page"
```

---

## Final Verification

- [ ] Run pipeline tests:

```bash
pytest apps/pipelines/tests -v
```

- [ ] Run API tests:

```bash
npm --prefix apps/api test
```

- [ ] Run web tests:

```bash
npm --prefix apps/web test
```

- [ ] Run typecheck:

```bash
npx.cmd tsc -p apps/api/tsconfig.json --noEmit
npx.cmd tsc -p apps/web/tsconfig.json --noEmit
```

- [ ] If local runtime is available, run one end-to-end sanity path:
  - execute `currency_analysis_flow`
  - confirm currency mart rows exist
  - confirm `/macro/currency-analysis` returns real data
  - confirm the page renders real PPP and IRP sections without placeholder fallbacks

---

## Self-Review Notes

- Spec coverage:
  - `PPP` base-month-relative analysis is implemented in Phase 3 and served in Phases 4-5.
  - `IRP` `CIP` + `UIP` with `3M / 6M / 12M` tenor handling is implemented in Phase 3 and served in Phases 4-5.
  - no-fallback behavior is enforced in Phases 2-5.
  - full-stack `source -> pipeline -> postgres -> api -> web` alignment is preserved throughout.

- Placeholder scan:
  - no `TBD`, `TODO`, or “implement later” markers remain in the plan tasks.
  - each phase points to concrete files and verification commands.

- Type consistency:
  - the route contract, frontend types, and mart output naming all revolve around `ppp`, `irp`, `uip`, `baseMonth`, and tenor rows to avoid later rename drift.

---

## Execution Notes For The Next Chat

- Start from `docs/analysis/currency-analysis-master-plan.md`.
- Reuse the existing Taylor foundations instead of rebuilding source, DB, or route infrastructure from scratch.
- Preserve the analysis `theory first` rule in the final page.
- Treat missing observed-forward data as an honest omission, not as a cue to invent substitute values.

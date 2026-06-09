# PPP Anchor Methodology Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the `Currency Analysis` PPP methodology so long-run `average` / `median` anchoring aggregates completed PPP outputs instead of averaging CPI base levels, and update the UI so the open methodology stays fully aligned with the new calculation.

**Architecture:** Keep the `source -> pipeline -> postgres -> api -> web` split intact. The key correction happens in the PPP transform: each eligible base month remains a complete spot+CPI base package, a current PPP fair value is calculated for each base month, and only then are those current outputs aggregated into the user-facing `average` / `median` anchor result. API and UI must expose this logic explicitly so the methodology shown on the page is never stale or misleading.

**Tech Stack:** Python, PostgreSQL, Fastify, Next.js, TypeScript, Chakra UI, pytest, Vitest

---

## File Map

### Existing files to modify

- `apps/pipelines/src/lib/pipeline/transforms/currency_ppp.py`
- `apps/pipelines/tests/test_currency_ppp_transform.py`
- `apps/api/src/routes/currency-analysis.ts`
- `apps/api/tests/currency-analysis-route.test.ts`
- `packages/shared/src/contracts/currency-analysis.ts`
- `apps/web/src/features/macro/currency-analysis-client.tsx`
- `apps/web/src/features/macro/components/currency-ppp-formula-block.tsx`
- `apps/web/src/features/macro/components/currency-ppp-data-inputs-block.tsx`
- `apps/web/src/features/macro/components/currency-ppp-readout-block.tsx`
- `apps/web/src/features/macro/components/currency-ppp-path-table-block.tsx`
- `apps/web/tests/currency-analysis-page.test.tsx`

### Optional files to modify only if needed

- `apps/web/src/features/macro/currency-analysis-types.ts`
- `docs/analysis/currency-analysis-master-plan.md`
- `docs/analysis/FOR-AGENTS-UI-BUILD-INSTRUCTIONS.md`

---

## Phase 1: Lock The Correct PPP Methodology In Tests

**Objective:** Define the intended methodology in tests before changing implementation.

**Files**
- Modify: `apps/pipelines/tests/test_currency_ppp_transform.py`

- [ ] Add a failing transform test for the new long-run anchor behavior:
  - choose a small synthetic monthly dataset
  - compute `PPP_t` separately for each eligible base month
  - assert that the final `average` anchor snapshot equals the average of those completed PPP outputs
  - assert that it does **not** equal the old behavior of averaging `base_us_cpi` / `base_ea_cpi` first

- [ ] Add a failing transform test for `median` anchor behavior:
  - compute `PPP_t` separately for each eligible base month
  - assert that the final `median` anchor snapshot equals the median of those completed PPP outputs

- [ ] Add a failing transform test that proves the base-month package stays internally coherent:
  - each eligible base month must use its own `spot_base`, `US_CPI_base`, and `EA_CPI_base`
  - no synthetic averaged CPI base level is allowed for window anchors

- [ ] Run the focused PPP transform tests to confirm the current implementation fails them.

Run: `pytest apps/pipelines/tests/test_currency_ppp_transform.py -v`
Expected: FAIL on the new long-run anchor methodology assertions.

---

## Phase 2: Correct The PPP Transform

**Objective:** Replace “aggregate inputs first” with “calculate PPP per base month first, aggregate outputs last”.

**Files**
- Modify: `apps/pipelines/src/lib/pipeline/transforms/currency_ppp.py`
- Modify: `apps/pipelines/tests/test_currency_ppp_transform.py`

- [ ] Refactor the window-anchor branch so it no longer computes:
  - `base_spot = aggregate(anchor spot values)`
  - `base_us_cpi = aggregate(anchor CPI values)`
  - `base_ea_cpi = aggregate(anchor CPI values)`
  for long-run window anchors.

- [ ] Implement the corrected logic for each window anchor:
  - enumerate every eligible base month in the chosen consecutive window
  - for each base month, calculate a current-month PPP fair value using that month’s own:
    - base spot
    - base US CPI
    - base euro-area CPI
  - aggregate those completed current PPP fair values using the requested `average` or `median`

- [ ] Decide and encode the same rule for `current valuation gap`:
  - compute a gap for each eligible base month against the latest observed spot
  - aggregate those completed gaps using the requested `average` or `median`
  - do not back-solve gap from a synthetic aggregated CPI base

- [ ] Preserve the existing “single-year anchor” logic, but make sure it is still internally coherent:
  - the year anchor should only use that year’s own monthly base points
  - no synthetic CPI base outside the selected year

- [ ] Preserve existing requirements that are still correct:
  - month-end normalization for spot if that remains current policy
  - consecutive-month requirements
  - honest `trailing_12m_average_gap_pct` behavior
  - imputation metadata

- [ ] Run the PPP transform tests again.

Run: `pytest apps/pipelines/tests/test_currency_ppp_transform.py -v`
Expected: PASS with the corrected window-anchor methodology.

---

## Phase 3: Expose The New Methodology Through API Metadata

**Objective:** Make the corrected methodology explicit in the API so the frontend can explain it accurately.

**Files**
- Modify: `packages/shared/src/contracts/currency-analysis.ts`
- Modify: `apps/api/src/routes/currency-analysis.ts`
- Modify: `apps/api/tests/currency-analysis-route.test.ts`

- [ ] Add failing API tests for new PPP methodology metadata, for example:
  - anchor calculation mode is `aggregate_ppp_outputs`
  - base-month sample count is returned
  - methodology summary text or flags distinguish:
    - `single-year anchor`
    - `window anchor built from per-base-month PPP outputs`

- [ ] Extend the shared PPP response shape with explicit methodology metadata, such as:
  - `anchorMethodology`
  - `anchorObservationCount`
  - `anchorAggregationTarget`
  - `baseMonthsUsed` or a count if that is all the UI needs

- [ ] Fix the existing API label bug for yearly `median` anchors so the label no longer says `base-year-average anchor`.

- [ ] Update the route to map the corrected pipeline outputs into the new response shape without reintroducing model logic in the API layer.

- [ ] Run the API route test.

Run: `npm.cmd --prefix apps/api test -- currency-analysis-route.test.ts`
Expected: PASS with the corrected metadata and label behavior.

---

## Phase 4: Update The Currency Analysis UI For Open Methodology

**Objective:** Update the page so the UI explains the corrected methodology clearly and does not keep any stale language from the old CPI-averaging model.

**Files**
- Modify: `apps/web/src/features/macro/currency-analysis-client.tsx`
- Modify: `apps/web/src/features/macro/components/currency-ppp-formula-block.tsx`
- Modify: `apps/web/src/features/macro/components/currency-ppp-data-inputs-block.tsx`
- Modify: `apps/web/src/features/macro/components/currency-ppp-readout-block.tsx`
- Modify: `apps/web/src/features/macro/components/currency-ppp-path-table-block.tsx`
- Modify: `apps/web/tests/currency-analysis-page.test.tsx`

- [ ] Add a failing UI test that checks the methodology copy does **not** claim or imply that CPI base levels are averaged across the window.

- [ ] Update the `Model Inputs And Anchor Method` block so it says clearly:
  - the spot source supplies observed base spots
  - CPI sources supply observed base CPI values and latest CPI values
  - the long-run `average` / `median` window works by calculating a PPP current fair value for each eligible base month and aggregating those results

- [ ] Update the formula or nearby explanation so it stays truthful:
  - the formula itself remains the standard relative PPP identity
  - the window-anchor explanation must clarify that the page aggregates completed `PPP_t` outputs across many base months
  - do not imply that `P_h,0` and `P_f,0` are themselves averaged into one synthetic base level

- [ ] Update the readout labels/notes so the user can see:
  - which values are observed
  - which values are calculated
  - that the long-run window fair value is a summary across many base months rather than one guessed “normal year”

- [ ] Update the path table heading/caption if needed so it remains truthful under the new method.

- [ ] Run the currency page test.

Run: `npm.cmd --prefix apps/web test -- currency-analysis-page.test.tsx`
Expected: PASS with open-methodology copy aligned to the corrected pipeline logic.

---

## Phase 5: Full Regression Check

**Objective:** Make sure the correction does not break route typing, Taylor UI refactors, or current PPP rendering.

**Files**
- Modify only if regressions require it

- [ ] Run focused pipeline verification:

Run: `pytest apps/pipelines/tests/test_currency_ppp_transform.py apps/pipelines/tests/test_db_load_foundations.py -v`
Expected: PASS

- [ ] Run focused API verification:

Run: `npm.cmd --prefix apps/api test -- currency-analysis-route.test.ts`
Expected: PASS

- [ ] Run focused web verification:

Run: `npm.cmd --prefix apps/web test -- currency-analysis-page.test.tsx taylor-rule-page.test.tsx`
Expected: PASS

- [ ] Run web typecheck:

Run: `npx.cmd tsc -p apps/web/tsconfig.json --noEmit`
Expected: PASS

---

## Recommended Commit Strategy

- Commit 1: `fix: correct PPP window anchor methodology`
  - pipeline transform
  - PPP transform tests

- Commit 2: `fix: expose corrected PPP methodology in api`
  - shared contract
  - API route
  - API tests

- Commit 3: `fix: align currency PPP UI with corrected methodology`
  - currency PPP UI blocks
  - currency page test

Do not include:
- `apps/web/tsconfig.tsbuildinfo`

---

## Methodology Note

This correction is specifically intended to preserve the original product goal:

- the user should **not** need to remember one exact month or year that had a “normal” EUR/USD level
- but the model should still respect relative PPP mechanics
- therefore the robust window should aggregate completed PPP outputs across eligible base months, not average CPI base levels into a synthetic pseudo-base

---

## Self-Review Notes

- The main methodological error is explicitly captured: CPI base levels must not be averaged across the long-run window for the primary PPP anchor.
- The UI update is part of the plan, not optional, so open methodology stays synchronized with the code.
- The commit strategy is intentionally small and low-friction.

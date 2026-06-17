# Highest P/S USA Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first production-grade backend/pipeline slice for `Highest P/S Stocks` by shipping the USA section (`S&P 500`) with a real ranking, benchmark context, unavailable handling, and a contract that can later be extended cleanly to Europe.

**Architecture:** Keep the existing `source -> pipeline -> postgres -> api -> web` boundary. The pipeline owns constituent eligibility, liquidity/size filtering, sector-relative P/S ranking, and benchmark calculation; Postgres stores page-ready outputs; the API only serves a stable shape with explicit unavailable semantics and no placeholder rows.

**Tech Stack:** Python, Prefect, PostgreSQL, Fastify, TypeScript, pytest, Vitest

---

## Scope Boundary

This plan covers only the **USA section** of the new two-section Highest P/S analysis.

It should ship:
- `S&P 500` constituent universe only
- one benchmark card set for the USA section
- one ranking table payload for the USA section
- explicit unavailable handling

It should **not** ship yet:
- `STOXX Europe 600` live data ingestion
- merged USA+EU ranking logic
- frontend layout refactors beyond the contract needed for a second section later

## Target Contract Direction

The eventual feature should expose two sections (`usa` and `europe`). For the USA slice, the backend should already shape the response as section-based rather than as one flat legacy ranking.

Recommended response shape for the first slice:

```ts
type HighestPsMarketSection = {
  key: "usa";
  label: "USA High P/S Leaders";
  universeKey: "sp500";
  asOf: string | null;
  unavailable: boolean;
  benchmark: {
    key: "sp500";
    label: "S&P 500 Average P/S";
    averagePsRatio: string | null;
    topBasketAveragePsRatio: string | null;
    topBasketIndexWeightPct: string | null;
    eligibleConstituentCount: number;
  };
  ranking: Array<{
    rank: number;
    ticker: string;
    company: string;
    countryCode: string;
    countryName: string;
    sector: string;
    psRatio: string;
    sectorAveragePsRatio: string;
    relativeToSectorMultiple: string;
    indexWeightPct: string;
  }>;
};

type HighestPsRankingResponse = {
  asOf: string | null;
  sections: HighestPsMarketSection[];
  references: Array<{ label: string; url?: string }>;
};
```

For the USA-only slice, `sections` contains exactly one item. The Europe section can be added later without contract churn.

## Ranking Methodology (USA Slice)

The USA ranking should not be raw “highest P/S among all constituents”. It should be:

1. Start from real `S&P 500` constituents
2. Require valid inputs:
   - market cap present and `> 0`
   - trailing 12M revenue present and `> 0`
   - P/S present and `> 0`
   - sector present
   - index weight present and `> 0`
3. Apply an **eligibility gate** for “large and traded enough” names using both:
   - market cap rank inside `S&P 500`
   - average daily traded value rank inside `S&P 500`
4. Keep only the eligible subset
5. Compute **sector average P/S** inside the eligible subset
6. Compute `relative_to_sector_multiple = company_ps / sector_average_ps`
7. Rank by `relative_to_sector_multiple` descending
8. Return `Top 25`

This is the first shipping methodology. It intentionally avoids tiny outliers and avoids raw-sector bias.

## File Map

### Modify

- `packages/shared/src/contracts/highest-ps-ranking.ts`
- `apps/api/src/routes/...` (new route registration or existing equity route index)
- `apps/api/tests/...` (new highest-P/S route tests)
- `apps/pipelines/src/lib/db.py`
- `apps/pipelines/src/sql/taylor_rule_schema.sql`
- `apps/pipelines/tests/test_db_load_foundations.py`
- `apps/web/src/features/equity/highest-ps-ranking-types.ts`

### Create

- `apps/pipelines/src/lib/pipeline/transforms/highest_ps_ranking.py`
- `apps/pipelines/src/tasks/load_highest_ps_ranking_layers.py`
- `apps/pipelines/src/flows/highest_ps_ranking_flow.py`
- `apps/pipelines/tests/test_highest_ps_ranking_transform.py`
- `apps/pipelines/tests/test_highest_ps_ranking_flow.py`
- `apps/api/src/routes/highest-ps-ranking.ts`
- `apps/api/tests/highest-ps-ranking-route.test.ts`

### Reuse / Inspect Before Implementing

- existing mart-loading patterns in `apps/pipelines/src/lib/db.py`
- existing unavailable-state route patterns in:
  - `apps/api/src/routes/currency-analysis.ts`
  - `apps/web/src/app/equity-markets/highest-ps-ranking/page.tsx`

---

### Task 1: Lock the USA-first contract

**Files:**
- Modify: `packages/shared/src/contracts/highest-ps-ranking.ts`
- Modify: `apps/web/src/features/equity/highest-ps-ranking-types.ts`
- Test: `apps/api/tests/highest-ps-ranking-route.test.ts`

- [ ] **Step 1: Write the failing route-contract test**

Create `apps/api/tests/highest-ps-ranking-route.test.ts` with a minimal contract assertion:

```ts
expect(response.json()).toEqual({
  asOf: "2026-06-15",
  sections: [
    {
      key: "usa",
      label: "USA High P/S Leaders",
      universeKey: "sp500",
      asOf: "2026-06-15",
      unavailable: false,
      benchmark: {
        key: "sp500",
        label: "S&P 500 Average P/S",
        averagePsRatio: "3.80",
        topBasketAveragePsRatio: "11.40",
        topBasketIndexWeightPct: "18.20",
        eligibleConstituentCount: 182,
      },
      ranking: [
        {
          rank: 1,
          ticker: "NVDA",
          company: "NVIDIA",
          countryCode: "US",
          countryName: "United States",
          sector: "Information Technology",
          psRatio: "24.10",
          sectorAveragePsRatio: "8.00",
          relativeToSectorMultiple: "3.01",
          indexWeightPct: "6.10",
        },
      ],
    },
  ],
  references: [],
});
```

- [ ] **Step 2: Run the route test to verify it fails**

Run:

```bash
npm.cmd --prefix apps/api test -- highest-ps-ranking-route.test.ts
```

Expected: FAIL because the route or contract shape does not exist yet.

- [ ] **Step 3: Update the shared contract**

Replace the flat legacy contract in `packages/shared/src/contracts/highest-ps-ranking.ts` with a section-based contract that supports:
- `asOf`
- `sections`
- `references`
- per-section `benchmark`
- per-section `ranking`
- per-section `unavailable`

- [ ] **Step 4: Update the web-side shared type alias**

Keep `apps/web/src/features/equity/highest-ps-ranking-types.ts` as a thin alias to the shared contract and update the empty shape accordingly:

```ts
export const emptyHighestPsRankingPageData: HighestPsRankingPageData = {
  asOf: null,
  sections: [],
  references: [],
};
```

- [ ] **Step 5: Commit**

```bash
git add packages/shared/src/contracts/highest-ps-ranking.ts apps/web/src/features/equity/highest-ps-ranking-types.ts apps/api/tests/highest-ps-ranking-route.test.ts
git commit -m "feat: define section-based highest ps contract"
```

### Task 2: Build the USA ranking transform

**Files:**
- Create: `apps/pipelines/src/lib/pipeline/transforms/highest_ps_ranking.py`
- Create: `apps/pipelines/tests/test_highest_ps_ranking_transform.py`

- [ ] **Step 1: Write the failing transform test for eligibility and sector-relative ranking**

Create `apps/pipelines/tests/test_highest_ps_ranking_transform.py` with a test that feeds simplified constituent rows and asserts:
- invalid rows are excluded
- sector averages are computed from eligible rows
- `relative_to_sector_multiple` drives rank order
- `Top 25` truncation is applied

Use this core assertion style:

```python
assert outputs["sections"][0]["ranking"][0] == {
    "rank": 1,
    "ticker": "AAA",
    "company": "Alpha",
    "country_code": "US",
    "country_name": "United States",
    "sector": "Information Technology",
    "ps_ratio": 24.1,
    "sector_average_ps_ratio": 8.0,
    "relative_to_sector_multiple": 3.0125,
    "index_weight_pct": 6.1,
}
```

- [ ] **Step 2: Run the transform test to verify it fails**

Run:

```bash
pytest apps/pipelines/tests/test_highest_ps_ranking_transform.py -v
```

Expected: FAIL because the transform module does not exist yet.

- [ ] **Step 3: Write the minimal transform**

Create `apps/pipelines/src/lib/pipeline/transforms/highest_ps_ranking.py` with focused helpers:
- `_eligible_rows(...)`
- `_sector_average_ps(...)`
- `_relative_multiple(...)`
- `build_highest_ps_outputs(...)`

The transform should return:
- `sections`
- per-section benchmark summary
- `as_of`

It should return an empty section with `unavailable=True` when no eligible rows survive.

- [ ] **Step 4: Run the transform test to verify it passes**

Run:

```bash
pytest apps/pipelines/tests/test_highest_ps_ranking_transform.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/pipeline/transforms/highest_ps_ranking.py apps/pipelines/tests/test_highest_ps_ranking_transform.py
git commit -m "feat: add usa highest ps ranking transform"
```

### Task 3: Add mart storage for the USA section

**Files:**
- Modify: `apps/pipelines/src/sql/taylor_rule_schema.sql`
- Modify: `apps/pipelines/src/lib/db.py`
- Modify: `apps/pipelines/tests/test_db_load_foundations.py`

- [ ] **Step 1: Write the failing DB helper test**

Extend `apps/pipelines/tests/test_db_load_foundations.py` with assertions that new helpers write:
- one benchmark summary table
- one ranking rows table

Suggested helper names:
- `replace_highest_ps_section_summaries`
- `replace_highest_ps_section_rankings`

- [ ] **Step 2: Run the DB helper test to verify it fails**

Run:

```bash
pytest apps/pipelines/tests/test_db_load_foundations.py -v
```

Expected: FAIL because the helper functions and schema tables do not exist.

- [ ] **Step 3: Add schema tables**

Add two mart tables:

```sql
create table if not exists mart.highest_ps_section_summaries (
    section_key text not null,
    as_of_date date,
    universe_key text not null,
    universe_label text not null,
    benchmark_label text not null,
    average_ps_ratio numeric,
    top_basket_average_ps_ratio numeric,
    top_basket_index_weight_pct numeric,
    eligible_constituent_count integer not null,
    unavailable boolean not null default false,
    primary key (section_key)
);

create table if not exists mart.highest_ps_section_rankings (
    section_key text not null,
    rank integer not null,
    ticker text not null,
    company text not null,
    country_code text not null,
    country_name text not null,
    sector text not null,
    ps_ratio numeric not null,
    sector_average_ps_ratio numeric not null,
    relative_to_sector_multiple numeric not null,
    index_weight_pct numeric not null,
    primary key (section_key, rank)
);
```

- [ ] **Step 4: Add DB replace helpers**

Implement corresponding replace helpers in `apps/pipelines/src/lib/db.py` following the mart replace pattern already used elsewhere.

- [ ] **Step 5: Re-run the DB helper test**

Run:

```bash
pytest apps/pipelines/tests/test_db_load_foundations.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/pipelines/src/sql/taylor_rule_schema.sql apps/pipelines/src/lib/db.py apps/pipelines/tests/test_db_load_foundations.py
git commit -m "feat: add highest ps mart storage"
```

### Task 4: Wire the USA flow and load task

**Files:**
- Create: `apps/pipelines/src/tasks/load_highest_ps_ranking_layers.py`
- Create: `apps/pipelines/src/flows/highest_ps_ranking_flow.py`
- Create: `apps/pipelines/tests/test_highest_ps_ranking_flow.py`

- [ ] **Step 1: Write the failing flow test**

Create `apps/pipelines/tests/test_highest_ps_ranking_flow.py` asserting that:
- the flow reads the upstream constituent dataset
- runs the transform
- writes section summary + ranking rows
- reports success counts

- [ ] **Step 2: Run the flow test to verify it fails**

Run:

```bash
pytest apps/pipelines/tests/test_highest_ps_ranking_flow.py -v
```

Expected: FAIL because the flow and task do not exist.

- [ ] **Step 3: Implement the minimal load task and flow**

Keep the first slice simple:
- accept already-prepared constituent rows from the source/mart stub used by tests
- transform them
- write outputs to the new mart tables

The flow result should include:
- `status`
- `section_count`
- `ranking_row_count`

- [ ] **Step 4: Re-run the flow test**

Run:

```bash
pytest apps/pipelines/tests/test_highest_ps_ranking_flow.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/tasks/load_highest_ps_ranking_layers.py apps/pipelines/src/flows/highest_ps_ranking_flow.py apps/pipelines/tests/test_highest_ps_ranking_flow.py
git commit -m "feat: wire usa highest ps ranking flow"
```

### Task 5: Serve the USA section from the API

**Files:**
- Create: `apps/api/src/routes/highest-ps-ranking.ts`
- Modify: existing API route registration file if needed
- Modify: `apps/api/tests/highest-ps-ranking-route.test.ts`

- [ ] **Step 1: Expand the failing route test to include unavailable handling**

Add a second test asserting:
- `sections[0].unavailable === true`
- `sections[0].ranking === []`
- numeric benchmark fields are `null`
when the mart summary exists but indicates unavailable or ranking rows are absent

- [ ] **Step 2: Run the route tests to verify red**

Run:

```bash
npm.cmd --prefix apps/api test -- highest-ps-ranking-route.test.ts
```

Expected: FAIL until the route is implemented.

- [ ] **Step 3: Implement the route**

Create `apps/api/src/routes/highest-ps-ranking.ts` that:
- reads `mart.highest_ps_section_summaries`
- reads `mart.highest_ps_section_rankings`
- groups ranking rows by `section_key`
- emits the section-based response
- never fabricates empty benchmark numbers

- [ ] **Step 4: Re-run the route tests**

Run:

```bash
npm.cmd --prefix apps/api test -- highest-ps-ranking-route.test.ts
```

Expected: PASS.

- [ ] **Step 5: Run the API typecheck**

Run:

```bash
npx.cmd tsc -p apps/api/tsconfig.json --noEmit
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/api/src/routes/highest-ps-ranking.ts apps/api/tests/highest-ps-ranking-route.test.ts
git commit -m "feat: serve usa highest ps ranking section"
```

### Task 6: Final USA slice verification

**Files:**
- Verify only

- [ ] **Step 1: Run pipeline tests**

Run:

```bash
pytest apps/pipelines/tests/test_highest_ps_ranking_transform.py apps/pipelines/tests/test_highest_ps_ranking_flow.py apps/pipelines/tests/test_db_load_foundations.py -v
```

Expected: PASS.

- [ ] **Step 2: Run API tests**

Run:

```bash
npm.cmd --prefix apps/api test -- highest-ps-ranking-route.test.ts
```

Expected: PASS.

- [ ] **Step 3: Run API typecheck**

Run:

```bash
npx.cmd tsc -p apps/api/tsconfig.json --noEmit
```

Expected: PASS.

- [ ] **Step 4: Report actual shipped boundary**

State explicitly that this slice ships:
- USA section only
- section-based contract
- unavailable-safe backend

And does not yet ship:
- Europe section
- live frontend rendering updates for the new two-section shape

---

## Self-Review Notes

- Spec coverage: covers USA section, benchmark card data, cleaned ranking, unavailable semantics, and a contract ready for Europe.
- Scope control: keeps Europe out of this first slice while avoiding a dead-end flat contract.
- No placeholder leak: benchmark fields can be `null` only under explicit `unavailable`, and ranking rows are omitted rather than half-filled.
- Architecture fit: follows existing MVD mart/API patterns rather than moving ranking logic into the web layer.

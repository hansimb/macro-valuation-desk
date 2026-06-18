# Taylor Rule Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real Taylor Rule analysis end to end on top of the reusable MVD architecture, from source layer to UI.

**Architecture:** Implementation proceeds bottom-up but is driven by one concrete use case: Taylor Rule for `US` and `EU`. Each phase should leave behind reusable architecture, not Taylor-specific shortcuts. Public serving stays `mart`-first; ETL remains `domain-first`.

**Tech Stack:** Python, Prefect, PostgreSQL, Fastify, Next.js, TypeScript, Chakra UI, pytest, Vitest

---

## File Map

### Existing files likely to modify

- `apps/pipelines/src/lib/db.py`
- `apps/pipelines/src/flows/macro_seed_flow.py`
- `apps/pipelines/src/tasks/fetch_seed_data.py`
- `apps/pipelines/src/tasks/load_macro_seed.py`
- `apps/pipelines/tests/test_macro_seed_flow.py`
- `apps/api/src/lib/db.ts`
- `apps/api/src/server.ts`
- `apps/web/src/features/site-shell/mvd-data.ts`
- `apps/web/src/app/macro/page.tsx`
- `apps/web/src/app/macro/[driver]/page.tsx`

### New files likely to create

#### Pipelines
- `apps/pipelines/src/lib/source/types.py`
- `apps/pipelines/src/lib/source/registry.py`
- `apps/pipelines/src/lib/source/adapters/base.py`
- `apps/pipelines/src/lib/source/adapters/fred.py`
- `apps/pipelines/src/lib/source/adapters/ecb.py`
- `apps/pipelines/src/lib/source/fetch.py`
- `apps/pipelines/src/lib/pipeline/checkpoints.py`
- `apps/pipelines/src/lib/pipeline/transforms/staging.py`
- `apps/pipelines/src/lib/pipeline/transforms/taylor_rule.py`
- `apps/pipelines/src/tasks/run_us_macro_core_etl.py`
- `apps/pipelines/src/tasks/run_eu_macro_core_etl.py`
- `apps/pipelines/src/tasks/load_taylor_layers.py`
- `apps/pipelines/src/flows/taylor_rule_flow.py`
- `apps/pipelines/tests/test_source_registry.py`
- `apps/pipelines/tests/test_fred_adapter.py`
- `apps/pipelines/tests/test_ecb_adapter.py`
- `apps/pipelines/tests/test_staging_transform.py`
- `apps/pipelines/tests/test_taylor_rule_transform.py`
- `apps/pipelines/tests/test_taylor_rule_flow.py`

#### API
- `apps/api/src/routes/taylor-rule.ts`
- `apps/api/tests/taylor-rule-route.test.ts`

#### Web
- `apps/web/src/app/macro/taylor-rule/page.tsx`
- `apps/web/src/features/macro/taylor-rule-client.tsx`
- `apps/web/src/features/macro/taylor-rule-types.ts`
- `apps/web/tests/taylor-rule-page.test.tsx`

#### SQL / docs
- `apps/pipelines/src/sql/pipeline_schema.sql`
- `docs/analysis/taylor-rule-master-plan.md` (small implementation notes only if needed)

---

## Phase 1: Source Layer Implementation For Taylor Inputs

**Objective:** Build the first real reusable source-layer implementation with enough coverage for Taylor Rule inputs.

**Target internal series keys**
- `us_policy_rate`
- `us_cpi_headline`
- `eu_policy_rate`
- `eu_hicp_headline`

**Files**
- Create: `apps/pipelines/src/lib/source/types.py`
- Create: `apps/pipelines/src/lib/source/registry.py`
- Create: `apps/pipelines/src/lib/source/adapters/base.py`
- Create: `apps/pipelines/src/lib/source/adapters/fred.py`
- Create: `apps/pipelines/src/lib/source/adapters/ecb.py`
- Create: `apps/pipelines/src/lib/source/fetch.py`
- Test: `apps/pipelines/tests/test_source_registry.py`
- Test: `apps/pipelines/tests/test_fred_adapter.py`
- Test: `apps/pipelines/tests/test_ecb_adapter.py`

- [ ] Define source-layer Python types for:
  - series definition
  - fetch options
  - standardized series
  - result object / structured error

- [ ] Create one central registry with Taylor Rule v1 series entries for:
  - US policy rate
  - US inflation
  - EU policy rate
  - EU inflation

- [ ] Implement shared adapter interface in `base.py` with conceptual method:
  - `fetch_series(series_definition, fetch_options) -> result`

- [ ] Implement `FredAdapter` for US series.

- [ ] Implement `EcbAdapter` for EU series.

- [ ] Implement a small adapter dispatcher in `fetch.py` that:
  - receives a registry entry
  - chooses provider adapter
  - returns a standardized result object

- [ ] Test registry integrity:
  - keys exist
  - providers map correctly
  - required metadata fields are present

- [ ] Test one successful US fetch path and one successful EU fetch path.

- [ ] Test one structured failure path from an adapter.

- [ ] Commit:

```bash
git add apps/pipelines/src/lib/source apps/pipelines/tests/test_source_registry.py apps/pipelines/tests/test_fred_adapter.py apps/pipelines/tests/test_ecb_adapter.py
git commit -m "feat: add Taylor Rule source layer foundations"
```

---

## Phase 2: Database / Load Foundations

**Objective:** Create the first real database layout and load structures that match the approved architecture.

**Files**
- Create: `apps/pipelines/src/sql/pipeline_schema.sql`
- Modify: `apps/pipelines/src/lib/db.py`
- Create: `apps/pipelines/src/lib/pipeline/checkpoints.py`

- [ ] Add schema creation SQL for:
  - `core`
  - `etl`
  - `raw`
  - `staging`
  - `mart`

- [ ] Add table creation SQL for:
  - `core.series_metadata`
  - `etl.series_checkpoints`
  - `etl.pipeline_runs`
  - `raw.series_observations`
  - `staging.series_observations`
  - `mart.taylor_rule_inputs`

- [ ] Implement lightweight schema bootstrap helper in `db.py`.

- [ ] Implement helpers for:
  - upserting `core.series_metadata`
  - upserting `raw.series_observations`
  - upserting `staging.series_observations`
  - replacing or upserting `mart.taylor_rule_inputs`

- [ ] Implement checkpoint helpers for:
  - reading latest checkpoint by `series_id`
  - writing successful checkpoint updates
  - recording basic pipeline run state

- [ ] Ensure raw retention is not fully implemented yet, but schema and comments leave space for scheduled cleanup later.

- [ ] Smoke-test locally by creating schema bootstrap path from Python.

- [ ] Commit:

```bash
git add apps/pipelines/src/sql/pipeline_schema.sql apps/pipelines/src/lib/db.py apps/pipelines/src/lib/pipeline/checkpoints.py
git commit -m "feat: add Taylor Rule database and load foundations"
```

---

## Phase 3: Taylor Rule ETL Domain Flow

**Objective:** Implement the first domain ETL flow end to end for Taylor Rule inputs.

**Files**
- Create: `apps/pipelines/src/lib/pipeline/transforms/staging.py`
- Create: `apps/pipelines/src/lib/pipeline/transforms/taylor_rule.py`
- Create: `apps/pipelines/src/tasks/run_us_macro_core_etl.py`
- Create: `apps/pipelines/src/tasks/run_eu_macro_core_etl.py`
- Create: `apps/pipelines/src/tasks/load_taylor_layers.py`
- Create: `apps/pipelines/src/flows/taylor_rule_flow.py`
- Test: `apps/pipelines/tests/test_staging_transform.py`
- Test: `apps/pipelines/tests/test_taylor_rule_transform.py`
- Test: `apps/pipelines/tests/test_taylor_rule_flow.py`

- [ ] Implement staging transform logic that:
  - validates raw observations
  - normalizes dates
  - converts values to numeric form
  - yields `staging-ready` observations

- [ ] Implement Taylor Rule analytical transform that builds `mart.taylor_rule_inputs` rows for:
  - `US`
  - `EU`

- [ ] Keep assumptions explicit in transform code:
  - default `r*`
  - inflation target
  - slack proxy handling

- [ ] Implement domain ETL tasks:
  - one for US macro core
  - one for EU macro core

- [ ] Implement one composed Prefect flow:
  - run source fetch
  - write raw
  - stage transform
  - write staging
  - analytical transform
  - write mart

- [ ] Make checkpoints active:
  - read checkpoint before fetching
  - use fetch window logic
  - update checkpoint only on successful progression

- [ ] Add at least one reprocessing window policy for recent observations.

- [ ] Test:
  - staging transform correctness
  - analytical transform correctness
  - successful ETL flow output
  - checkpoint update on success
  - safe handling of adapter failure

- [ ] Commit:

```bash
git add apps/pipelines/src/lib/pipeline apps/pipelines/src/tasks/run_us_macro_core_etl.py apps/pipelines/src/tasks/run_eu_macro_core_etl.py apps/pipelines/src/tasks/load_taylor_layers.py apps/pipelines/src/flows/taylor_rule_flow.py apps/pipelines/tests/test_staging_transform.py apps/pipelines/tests/test_taylor_rule_transform.py apps/pipelines/tests/test_taylor_rule_flow.py
git commit -m "feat: add Taylor Rule ETL flow"
```

---

## Phase 4: API Route For Taylor Rule

**Objective:** Expose a clean mart-first API contract for the Taylor Rule page.

**Files**
- Create: `apps/api/src/routes/taylor-rule.ts`
- Modify: `apps/api/src/server.ts`
- Test: `apps/api/tests/taylor-rule-route.test.ts`

- [ ] Add a DB query layer in the API that reads from `mart.taylor_rule_inputs`.

- [ ] Include required serving fields for the page:
  - region
  - as-of date
  - policy rate
  - inflation
  - target
  - slack proxy
  - implied rate
  - source references needed by the page

- [ ] Keep route mart-first:
  - no direct raw access
  - no ETL logic in route handler

- [ ] Return a response shape that is easy for the frontend to consume:
  - two-region comparison
  - default assumptions
  - references block

- [ ] Register the route in `server.ts`.

- [ ] Test:
  - route success
  - empty-data behavior
  - response contract shape

- [ ] Commit:

```bash
git add apps/api/src/routes/taylor-rule.ts apps/api/src/server.ts apps/api/tests/taylor-rule-route.test.ts
git commit -m "feat: add Taylor Rule API route"
```

---

## Phase 5: Taylor Rule Web Page

**Objective:** Build the first real analysis page and calculator on top of the prepared API data.

**Files**
- Modify: `apps/web/src/features/site-shell/mvd-data.ts`
- Modify: `apps/web/src/app/macro/page.tsx`
- Modify: `apps/web/src/app/macro/[driver]/page.tsx` or replace with explicit route usage
- Create: `apps/web/src/app/macro/taylor-rule/page.tsx`
- Create: `apps/web/src/features/macro/taylor-rule-client.tsx`
- Create: `apps/web/src/features/macro/taylor-rule-types.ts`
- Test: `apps/web/tests/taylor-rule-page.test.tsx`

- [ ] Add the first real macro analysis entry for Taylor Rule to the macro registry.

- [ ] Build the page route under `/macro/taylor-rule`.

- [ ] Render:
  - page heading
  - formula block
  - USA/EU comparison
  - minimal assumption controls
  - scenario presets
  - short interpretation
  - references

- [ ] Keep the page aligned with the agreed product direction:
  - data-first
  - short text
  - no placeholder dashboards

- [ ] Keep controls limited to assumption-driven values only.

- [ ] Make sure references render clearly from API-provided metadata.

- [ ] Test:
  - page renders without placeholder content
  - references appear
  - formula appears
  - region comparison appears

- [ ] Commit:

```bash
git add apps/web/src/features/site-shell/mvd-data.ts apps/web/src/app/macro/page.tsx apps/web/src/app/macro/taylor-rule/page.tsx apps/web/src/features/macro/taylor-rule-client.tsx apps/web/src/features/macro/taylor-rule-types.ts apps/web/tests/taylor-rule-page.test.tsx
git commit -m "feat: add Taylor Rule analysis page"
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
npx.cmd tsc -p apps/web/tsconfig.json --noEmit
npx.cmd tsc -p apps/api/tsconfig.json --noEmit
```

- [ ] If local runtime is available, run one end-to-end manual sanity path:
  - execute Taylor Rule ETL
  - confirm mart rows exist
  - confirm API route returns data
  - confirm page renders real data

---

## Execution Notes For The Next Chat

- Start from `docs/analysis/taylor-rule-master-plan.md`
- Use architecture docs under `docs/architecture/`
- Implement bottom-up, but keep each phase reusable
- Do not turn Taylor Rule into a special-case shortcut
- Prefer one small working flow over broad partial scaffolding

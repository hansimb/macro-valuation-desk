# Macro Overview

## Feature Name
- Macro Overview / macro landing seed metrics

## Product Route / API Route
- Product route: `apps/web/src/app/macro/page.tsx` (`/macro`)
- API route: `apps/api/src/routes/macro-overview.ts` (`GET /macro/overview`)

## Shared Contract File
- `packages/shared/src/contracts/macro-overview.ts`

## Pipeline Transform Files
- No feature-specific transform found.
- Seed rows are produced directly by `apps/pipelines/src/tasks/fetch_seed_data.py` and loaded by `apps/pipelines/src/tasks/load_macro_seed.py`.

## Pipeline Flow / Task / Load Files
- Flow: `apps/pipelines/src/flows/macro_seed_flow.py`
- Fetch task: `apps/pipelines/src/tasks/fetch_seed_data.py`
- Load task: `apps/pipelines/src/tasks/load_macro_seed.py`
- Full runner includes it: `apps/pipelines/src/flows/all_flows.py`

## DB Schema / Mart Tables
- Seed table: `raw.macro_series`
- Table is created inside `apps/pipelines/src/tasks/load_macro_seed.py`, not in `apps/pipelines/src/sql/pipeline_schema.sql`.
- API reads `raw.macro_series` and falls back to hard-coded seed metrics if the table/query is unavailable.

## Web Page / Components / Types
- Macro landing page: `apps/web/src/app/macro/page.tsx`
- Macro analysis registry: `apps/web/src/features/site-shell/mvd-data.ts`
- Generic macro driver placeholder: `apps/web/src/app/macro/[driver]/page.tsx`
- Site navigation context: `apps/web/src/features/site-shell/navigation-items.ts`, `apps/web/src/features/site-shell/navigation.tsx`

## API Route / Query Files
- Route/query: `apps/api/src/routes/macro-overview.ts`
- API DB helper: `apps/api/src/lib/db.ts`

## Tests
- API: `apps/api/tests/macro-overview-route.test.ts`
- Web macro page: `apps/web/tests/macro-page.test.tsx`
- Navigation shell coverage: `apps/web/tests/navigation-shell.test.tsx`
- Pipeline flow: `apps/pipelines/tests/test_macro_seed_flow.py`
- All-flows order/status: `apps/pipelines/tests/test_all_flows.py`

## Data Availability / Unavailable-State Rules
- API tries `raw.macro_series` ordered by latest `as_of` and returns up to three metrics.
- If the DB query throws or returns no rows, API returns a stable fallback dated `2026-05-01`.
- The `/macro` web page is registry-driven and does not currently call `/macro/overview` directly.

## Start Here
1. `packages/shared/src/contracts/macro-overview.ts`
2. `apps/api/src/routes/macro-overview.ts`
3. `apps/pipelines/src/flows/macro_seed_flow.py`
4. `apps/pipelines/src/tasks/fetch_seed_data.py`
5. `apps/pipelines/src/tasks/load_macro_seed.py`
6. `apps/web/src/app/macro/page.tsx`
7. Feature tests listed above

## Do Not Read First
- `apps/web/src/app/macro/currency-analysis/page.tsx` and `apps/web/src/app/macro/taylor-rule/page.tsx` - live child features, not overview data.
- `apps/web/src/app/macro/[driver]/page.tsx` - generic placeholder for registry slugs.
- `apps/pipelines/src/sql/pipeline_schema.sql` - does not define `raw.macro_series`; read `load_macro_seed.py` instead.
- Source adapters under `apps/pipelines/src/lib/source/adapters/` - not used by the seed flow.

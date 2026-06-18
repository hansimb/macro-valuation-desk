# Taylor Rule

## Feature Name
- Taylor Rule / rule-based policy benchmark

## Product Route / API Route
- Product route: `apps/web/src/app/macro/taylor-rule/page.tsx` (`/macro/taylor-rule`)
- API route: `apps/api/src/routes/taylor-rule.ts` (`GET /macro/taylor-rule`)

## Shared Contract File
- `packages/shared/src/contracts/taylor-rule.ts`

## Pipeline Transform Files
- `apps/pipelines/src/lib/pipeline/transforms/taylor_rule.py`
- `apps/pipelines/src/lib/pipeline/transforms/reference_metrics.py`
- Shared staging normalization: `apps/pipelines/src/lib/pipeline/transforms/staging.py`

## Pipeline Flow / Task / Load Files
- Flow: `apps/pipelines/src/flows/taylor_rule_flow.py`
- Fetch tasks: `apps/pipelines/src/tasks/run_us_macro_core_etl.py`, `apps/pipelines/src/tasks/run_eu_macro_core_etl.py`
- Load task: `apps/pipelines/src/tasks/load_taylor_layers.py`
- Source registry: `apps/pipelines/src/lib/source/registry.py`
- Shared DB helpers: `apps/pipelines/src/lib/db.py`
- Full runner includes it: `apps/pipelines/src/flows/all_flows.py`

## DB Schema / Mart Tables
- Schema DDL: `apps/pipelines/src/sql/pipeline_schema.sql`
- Raw/staging: `raw.series_observations`, `staging.series_observations`
- Mart tables: `mart.taylor_rule_inputs`, `mart.macro_reference_metrics`
- Metadata/checkpoints: `core.series_metadata`, `etl.series_checkpoints`, `etl.pipeline_runs`
- Pipeline run key: `taylor_rule`

## Web Page / Components / Types
- Page: `apps/web/src/app/macro/taylor-rule/page.tsx`
- Client: `apps/web/src/features/macro/taylor-rule-client.tsx`
- Types/default data: `apps/web/src/features/macro/taylor-rule-types.ts`
- Components: `apps/web/src/features/macro/components/taylor-formula-block.tsx`, `taylor-assumptions-panels.tsx`, `taylor-reference-panels.tsx`, `taylor-scenario-panels.tsx`
- Shared analysis components: `analysis-references-block.tsx`, `analysis-citation-links.tsx`, `analysis-formula-terms.tsx`
- Registry entry: `apps/web/src/features/site-shell/mvd-data.ts`

## API Route / Query Files
- Route/query: `apps/api/src/routes/taylor-rule.ts`
- API DB helper: `apps/api/src/lib/db.ts`

## Tests
- API: `apps/api/tests/taylor-rule-route.test.ts`
- Web: `apps/web/tests/taylor-rule-page.test.tsx`
- Pipeline transform: `apps/pipelines/tests/test_taylor_rule_transform.py`
- Reference metrics transform: `apps/pipelines/tests/test_reference_metrics_transform.py`
- Pipeline flow: `apps/pipelines/tests/test_taylor_rule_flow.py`
- Load task: `apps/pipelines/tests/test_load_taylor_layers.py`
- Macro core ETL/source: `apps/pipelines/tests/test_macro_core_etl_tasks.py`, `apps/pipelines/tests/test_source_registry.py`

## Data Availability / Unavailable-State Rules
- Flow returns `status: "failed"` if fetch error collection is non-empty.
- API returns stable empty Taylor Rule data with default assumptions when `mart.taylor_rule_inputs` has no rows.
- Web treats the page as unavailable when the API fetch fails/non-OK or `data.regions.length === 0`.
- Client stores local assumption overrides under `taylor-rule-assumptions-v1`.

## Start Here
1. `packages/shared/src/contracts/taylor-rule.ts`
2. `apps/api/src/routes/taylor-rule.ts`
3. `apps/web/src/app/macro/taylor-rule/page.tsx`
4. `apps/web/src/features/macro/taylor-rule-client.tsx`
5. `apps/pipelines/src/flows/taylor_rule_flow.py`
6. `apps/pipelines/src/lib/pipeline/transforms/taylor_rule.py`
7. `apps/pipelines/src/lib/pipeline/transforms/reference_metrics.py`
8. `apps/pipelines/src/sql/pipeline_schema.sql`
9. Feature tests listed above

## Do Not Read First
- `apps/web/src/app/macro/[driver]/page.tsx` - generic placeholder route, not the live Taylor Rule page.
- `apps/pipelines/src/lib/db.py` - large shared DB helper; jump to `replace_taylor_rule_inputs` and `replace_macro_reference_metrics` only after reading the flow.
- Source adapters under `apps/pipelines/src/lib/source/adapters/` - provider plumbing, not feature behavior.
- `apps/pipelines/src/flows/all_flows.py` - orchestration only, not Taylor Rule logic.

# Currency Analysis

## Feature Name
- Currency Analysis / EUR/USD PPP and IRP analysis

## Product Route / API Route
- Product route: `apps/web/src/app/macro/currency-analysis/page.tsx` (`/macro/currency-analysis`)
- API route: `apps/api/src/routes/currency-analysis.ts` (`GET /macro/currency-analysis`)
- Query params: `anchorKind`, `anchorStatistic`, `windowCode`, `baseYear`

## Shared Contract File
- `packages/shared/src/contracts/currency-analysis.ts`

## Pipeline Transform Files
- `apps/pipelines/src/lib/pipeline/transforms/currency_ppp.py`
- `apps/pipelines/src/lib/pipeline/transforms/currency_irp.py`
- Shared staging normalization: `apps/pipelines/src/lib/pipeline/transforms/staging.py`

## Pipeline Flow / Task / Load Files
- Flow: `apps/pipelines/src/flows/currency_analysis_flow.py`
- Fetch task: `apps/pipelines/src/tasks/run_currency_market_etl.py`
- Load task: `apps/pipelines/src/tasks/load_currency_analysis_layers.py`
- Source registry: `apps/pipelines/src/lib/source/registry.py`
- Shared DB helpers: `apps/pipelines/src/lib/db.py`
- Full runner includes it: `apps/pipelines/src/flows/all_flows.py`

## DB Schema / Mart Tables
- Schema DDL: `apps/pipelines/src/sql/pipeline_schema.sql`
- Raw/staging: `raw.series_observations`, `staging.series_observations`
- Mart tables: `mart.currency_ppp_snapshots`, `mart.currency_ppp_paths`, `mart.currency_irp_snapshots`, `mart.currency_data_availability`
- Metadata/checkpoints: `core.series_metadata`, `etl.series_checkpoints`, `etl.pipeline_runs`
- Pipeline run key: `currency_analysis`

## Web Page / Components / Types
- Page: `apps/web/src/app/macro/currency-analysis/page.tsx`
- Client: `apps/web/src/features/macro/currency-analysis-client.tsx`
- Types/default data: `apps/web/src/features/macro/currency-analysis-types.ts`
- PPP components: `apps/web/src/features/macro/components/currency-ppp-readout-block.tsx`, `currency-ppp-path-table-block.tsx`, `currency-ppp-historical-spot-context-block.tsx`, `currency-ppp-formula-block.tsx`, `currency-ppp-data-inputs-block.tsx`
- IRP components: `apps/web/src/features/macro/components/currency-irp-tenor-table-block.tsx`, `currency-irp-formula-block.tsx`, `currency-irp-data-inputs-block.tsx`, `currency-irp-uip-block.tsx`
- Shared analysis components: `analysis-references-block.tsx`, `analysis-citation-links.tsx`, `analysis-formula-terms.tsx`
- Registry entry: `apps/web/src/features/site-shell/mvd-data.ts`

## API Route / Query Files
- Route/query: `apps/api/src/routes/currency-analysis.ts`
- API DB helper: `apps/api/src/lib/db.ts`

## Tests
- API: `apps/api/tests/currency-analysis-route.test.ts`
- Web: `apps/web/tests/currency-analysis-page.test.tsx`
- Web component: `apps/web/tests/currency-ppp-historical-spot-context-block.test.tsx`
- Pipeline PPP transform: `apps/pipelines/tests/test_currency_ppp_transform.py`
- Pipeline IRP transform: `apps/pipelines/tests/test_currency_irp_transform.py`
- Pipeline flow: `apps/pipelines/tests/test_currency_analysis_flow.py`
- Source registry/staging: `apps/pipelines/tests/test_source_registry.py`, `apps/pipelines/tests/test_staging_transform.py`
- DB foundations: `apps/pipelines/tests/test_db_load_foundations.py`

## Data Availability / Unavailable-State Rules
- PPP transform emits unavailable availability rows when required spot or CPI inputs are missing.
- IRP transform emits unavailable availability rows when spot or tenor rate inputs are missing.
- Flow fails only when both PPP and IRP produce no snapshot rows; partial PPP/IRP availability can still be loaded.
- API returns empty PPP/IRP blocks plus `availability` rows when marts are sparse.
- Web treats the whole page as unavailable when PPP summary is null, CIP rows are empty, and UIP rows are empty, or when fetch fails/non-OK.

## Start Here
1. `packages/shared/src/contracts/currency-analysis.ts`
2. `apps/api/src/routes/currency-analysis.ts`
3. `apps/web/src/app/macro/currency-analysis/page.tsx`
4. `apps/web/src/features/macro/currency-analysis-client.tsx`
5. `apps/pipelines/src/flows/currency_analysis_flow.py`
6. `apps/pipelines/src/lib/pipeline/transforms/currency_ppp.py`
7. `apps/pipelines/src/lib/pipeline/transforms/currency_irp.py`
8. `apps/pipelines/src/sql/pipeline_schema.sql`
9. Feature tests listed above

## Do Not Read First
- `apps/web/src/app/macro/[driver]/page.tsx` - generic placeholder route, not the live feature page.
- `apps/web/src/features/macro/components/currency-ppp-historical-spot-context-block.tsx` - chart-heavy; read after the page/client/types.
- `apps/pipelines/src/lib/db.py` - large shared DB helper; jump to `replace_currency_*` only after reading the flow.
- Source adapters under `apps/pipelines/src/lib/source/adapters/` - provider plumbing, not feature behavior.

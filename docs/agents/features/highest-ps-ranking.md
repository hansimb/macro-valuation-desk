# Highest P/S Ranking

## Feature Name
- Highest P/S Ranking / Highest P/S Stocks

## Product Route / API Route
- Product route: `apps/web/src/app/equity-markets/highest-ps-ranking/page.tsx` (`/equity-markets/highest-ps-ranking`)
- API route: `apps/api/src/routes/highest-ps-ranking.ts` (`GET /equity/highest-ps-ranking`)

## Shared Contract File
- `packages/shared/src/contracts/highest-ps-ranking.ts`

## Pipeline Transform Files
- `apps/pipelines/src/lib/pipeline/transforms/highest_ps_ranking.py`

## Pipeline Flow / Task / Load Files
- Flow: `apps/pipelines/src/flows/highest_ps_ranking_flow.py`
- Load task: `apps/pipelines/src/tasks/load_highest_ps_ranking_layers.py`
- Shared DB helpers: `apps/pipelines/src/lib/db.py`
- Full runner includes it: `apps/pipelines/src/flows/all_flows.py`

## DB Schema / Mart Tables
- Schema DDL: `apps/pipelines/src/sql/pipeline_schema.sql`
- Source/staging table read by flow: `staging.equity_index_constituent_snapshots`
- Mart tables: `mart.highest_ps_section_summaries`, `mart.highest_ps_section_rankings`
- Pipeline run key: `highest_ps_ranking`

## Web Page / Components / Types
- Page: `apps/web/src/app/equity-markets/highest-ps-ranking/page.tsx`
- Page types/helpers: `apps/web/src/features/equity/highest-ps-ranking-types.ts`
- Shared card component: `apps/web/src/features/macro/components/analysis-metric-card.tsx`
- Registry entry: `apps/web/src/features/site-shell/mvd-data.ts`

## API Route / Query Files
- Route/query: `apps/api/src/routes/highest-ps-ranking.ts`
- API DB helper: `apps/api/src/lib/db.ts`

## Tests
- API: `apps/api/tests/highest-ps-ranking-route.test.ts`
- Web: `apps/web/tests/highest-ps-ranking-page.test.tsx`
- Pipeline transform: `apps/pipelines/tests/test_highest_ps_ranking_transform.py`
- Pipeline flow: `apps/pipelines/tests/test_highest_ps_ranking_flow.py`
- DB foundations: `apps/pipelines/tests/test_db_load_foundations.py`
- All-flows order/status: `apps/pipelines/tests/test_all_flows.py`

## Data Availability / Unavailable-State Rules
- Pipeline returns `status: "unavailable"` and writes an unavailable USA summary row when no section outputs exist.
- Section rows carry `unavailable`; web renders a section only when `unavailable` is false, ranking is non-empty, benchmark metrics are present, and eligible count is positive.
- Page fetch failure, non-OK response, or empty sections falls back to `emptyHighestPsRankingPageData` and shows the live-data unavailable message.

## Start Here
1. `packages/shared/src/contracts/highest-ps-ranking.ts`
2. `apps/api/src/routes/highest-ps-ranking.ts`
3. `apps/web/src/app/equity-markets/highest-ps-ranking/page.tsx`
4. `apps/pipelines/src/flows/highest_ps_ranking_flow.py`
5. `apps/pipelines/src/lib/pipeline/transforms/highest_ps_ranking.py`
6. `apps/pipelines/src/sql/pipeline_schema.sql`
7. Feature tests listed above

## Do Not Read First
- `apps/web/src/app/equity-markets/[market]/page.tsx` - market pages are separate from this ranking.
- `apps/web/src/app/stock-markets/page.tsx` - landing/registry page only.
- `apps/pipelines/src/lib/db.py` - large shared DB helper; jump to `read_highest_ps_candidate_rows` and `replace_highest_ps_*` only after reading the flow.
- `apps/pipelines/src/flows/all_flows.py` - orchestration only, not feature logic.

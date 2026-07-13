# Backend Agent Prompt: Market Valuation Data Availability

You are the backend/data agent for Macro Valuation Desk. The frontend market valuation page is integrated and calls:

```text
GET /equity-markets/valuations
```

The UI currently renders:

```text
Live market valuation data is unavailable right now.
Run the market valuation pipeline to populate ETF and index valuation snapshots.
```

This is not a frontend rendering bug. The UI is correctly showing the empty-data state returned by the API.

## Evidence From Local Debugging

`GET http://127.0.0.1:4000/health` returns OK.

`GET http://127.0.0.1:4000/equity-markets/valuations` returns:

```json
{
  "asOf": null,
  "markets": [],
  "references": []
}
```

The local Postgres tables are present but empty:

```text
marts.equity_market_valuation_snapshot count = 0
raw.equity_market_valuation_payloads count = 0
```

Running the ETL function directly returns:

```json
{
  "status": "failed",
  "mart_rows": 0,
  "raw_payload_rows": 0,
  "errors": [
    "us_total_market: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "us_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "europe_developed: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "germany_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "france_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "uk_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "finland_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "sweden_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "norway_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "denmark_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "china_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "japan_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "south_korea_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests.",
    "taiwan_large_cap: EODHD_API_TOKEN is required for EODHD fundamentals requests."
  ]
}
```

The project `.env` has `DATABASE_URL`, but no `EODHD_API_TOKEN`. `infra/compose/.env` was not present during the debug session.

## Goal

Make the backend/data path for market valuation snapshots operational and diagnosable in local development without adding fake fallback valuation data.

## Required Investigation

Start with:

- `apps/pipelines/src/lib/source/adapters/eodhd.py`
- `apps/pipelines/src/tasks/run_equity_market_valuation_etl.py`
- `apps/pipelines/src/flows/equity_market_valuation_flow.py`
- `apps/pipelines/src/lib/db/equity_market_valuation.py`
- `apps/api/src/routes/equity-market-valuations.ts`
- `docs/agents/prompts/2026-07-07-market-valuation-frontend-integration.md`

Confirm:

- how `EODHD_API_TOKEN` should be supplied for local development;
- whether `.env.example`, README, or agent docs should mention it;
- whether the pipeline command should print or persist a clearer failure summary when all providers fail;
- whether the API should remain `{ asOf: null, markets: [], references: [] }` for empty marts or expose a separate diagnostics route/status for operators.

## Constraints

- Do not add fake market valuation rows.
- Do not commit secrets or real provider tokens.
- Keep the shared frontend contract stable unless the API contract is intentionally changed and frontend tests are updated in the same task.
- Preserve the current UI behavior for empty `markets` unless product direction changes.

## Suggested Fix Scope

Prefer a small backend/ops fix:

1. Add or update env documentation for `EODHD_API_TOKEN`.
2. Make the market valuation pipeline failure mode easier to see from CLI/all-flows output.
3. Optionally add a focused test proving missing `EODHD_API_TOKEN` produces a useful failure summary and does not write empty/fake mart rows.

## Verification

Run focused backend/data checks:

```powershell
cd apps/pipelines
python -m pytest tests/test_eodhd_adapter.py tests/test_equity_market_valuation_flow.py -q
```

If API behavior changes, also run:

```powershell
npm.cmd run test --workspace @mvd/api -- equity-market-valuations-route.test.ts
```

For local live data verification, after setting a real token outside git:

```powershell
$env:EODHD_API_TOKEN="<real token>"
cd apps/pipelines
python -m src.flows.equity_market_valuation_flow
```

Then verify:

```text
GET /equity-markets/valuations
```

returns non-empty `markets`.

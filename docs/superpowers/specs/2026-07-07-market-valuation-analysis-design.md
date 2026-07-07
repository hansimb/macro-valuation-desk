# Market Valuation Analysis Design

## Goal

Add a backend-ready global market valuation analysis foundation for broad equity markets. The first version will ingest ETF or index-proxy valuation snapshots, store prepared market valuation rows in PostgreSQL, and expose a stable API for frontend integration.

## Product Scope

The feature covers broad market valuation snapshots for major equity markets such as the United States, Europe, Germany, France, the United Kingdom, Finland, Sweden, Norway, Denmark, China, Japan, South Korea, and Taiwan.

The first implementation is a backend foundation. It does not build the frontend UI, historical percentile model, or a complete bottom-up P/FCF engine.

## Data Source Choice

Use EODHD as the first provider because it offers ETF fundamentals, ETF holdings, and index constituent data under one API family. The first implementation should use ETF or index-proxy snapshot fields when they are available.

The provider fields should be stored with explicit methodology metadata:

- `trailing_pe`: EODHD ETF valuation field for price to earnings.
- `price_to_book`: EODHD ETF valuation field for price to book.
- `price_to_sales`: EODHD ETF valuation field for price to sales.
- `price_to_cash_flow`: EODHD ETF valuation field for price to cash flow.
- `dividend_yield_pct`: EODHD ETF dividend yield field converted to percent when needed.

The product request includes P/FCF, but the first EODHD ETF snapshot field is usually price to cash flow, not exact price to free cash flow. The first version must expose this as `price_to_cash_flow` and set `price_to_free_cash_flow` to unavailable unless a reliable exact field is present. The API and frontend metadata must label `price_to_cash_flow` as a proxy, not as exact P/FCF.

## Architecture

Follow the existing project flow:

```text
source -> pipeline -> postgres -> api -> web
```

The API must not call EODHD directly. Provider fetches belong in `apps/pipelines/src/lib/source`, transformation and loading belong in `apps/pipelines`, prepared data belongs in `marts`, and `apps/api` only serves the prepared mart rows.

## Phase 1: Source

Add a source-layer model for equity market valuation snapshots and an EODHD adapter that can parse a representative ETF fundamentals response into a standardized internal shape.

The adapter must:

- accept a provider symbol such as `VTI.US`;
- read an API token from `EODHD_API_TOKEN`;
- use `demo` only in tests or explicit local sample commands;
- return structured failures rather than silent empty data;
- preserve provider metadata, source URL, and as-of date;
- parse missing valuation fields as `None` without treating the whole response as failed.

## Phase 2: Pipeline

Add a market universe registry and a pipeline flow that turns source snapshots into prepared mart rows.

The pipeline must:

- maintain internal market IDs such as `us_total_market`, `europe_developed`, and `germany_large_cap`;
- associate each market with one measured object, such as an ETF proxy ticker;
- normalize ratios to decimal numbers and dividend yield to percentage points;
- store field-level availability and proxy notes;
- load the latest snapshot into `marts.equity_market_valuation_snapshot`;
- preserve enough raw provider payload data for debugging and future reprocessing.

## Phase 3: API

Add a shared TypeScript contract and Fastify route for the frontend.

The API must:

- expose `GET /equity-markets/valuations`;
- read from `marts.equity_market_valuation_snapshot`;
- return a list of market valuation rows plus references;
- make unavailable P/FCF explicit with `value: null` and a method note;
- include `asOf`, `provider`, `sourceUrl`, and measured object metadata;
- avoid fallback fake valuation data when the mart is empty.

When the mart is empty, the route should return an empty list with a valid response envelope. The frontend can then render an explicit missing-data state.

## Frontend Handoff

After the backend phases are complete, provide a separate frontend-agent prompt. The prompt should tell the frontend agent to integrate the route into the existing Equity Markets section, render missing data honestly, and label `price_to_cash_flow` as a P/CF proxy rather than exact P/FCF.

## Testing Requirements

Each phase must have a focused test command:

- Source: adapter parse and failure tests.
- Pipeline: transform/load tests against sample payloads and SQL contract checks.
- API: route contract tests against mocked database rows and empty mart responses.

End-to-end local verification should be possible with:

```powershell
npm.cmd test
cd apps/pipelines
python -m pytest tests/test_eodhd_adapter.py tests/test_equity_market_valuation_transform.py tests/test_equity_market_valuation_flow.py -q
```

## Atomic Commit Policy

Use one commit per completed phase:

- `feat: add eodhd market valuation source`
- `feat: add market valuation pipeline mart`
- `feat: expose market valuation api`
- `docs: add market valuation frontend handoff`

Each commit must include its relevant tests and only the files needed for that phase.

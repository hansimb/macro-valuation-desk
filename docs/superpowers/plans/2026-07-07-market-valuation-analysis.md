# Market Valuation Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a backend foundation for global equity market valuation snapshots using an EODHD-first source, a pipeline-loaded Postgres mart, and a stable API route for frontend consumption.

**Architecture:** Keep the current `source -> pipeline -> postgres -> api -> web` boundary. Source code fetches and parses EODHD payloads, pipeline code normalizes and loads market valuation snapshots into `marts`, and API code serves prepared mart rows without performing ETL or provider calls.

**Tech Stack:** Python 3.13, pytest, Prefect-compatible pipeline modules, psycopg, PostgreSQL schemas, Fastify, TypeScript, Vitest, shared TypeScript contracts.

---

## Recommended Agent Model

Use subagents for implementation. The work splits cleanly into independent architecture layers:

- Source agent owns EODHD adapter, source models, sample payload parsing, and source tests.
- Pipeline agent owns market universe, transforms, SQL schema, load function, flow task, and pipeline tests.
- API agent owns shared contracts, API route, route registration, and API tests.
- Frontend agent runs after backend is merged and consumes the finished API contract.

Each agent must make atomic commits only for its layer. Agents should not modify another layer unless their task explicitly says to.

## File Structure

Source phase:

- Create `apps/pipelines/src/lib/source/adapters/eodhd.py`: provider adapter for EODHD fundamentals payloads.
- Create `apps/pipelines/src/lib/source/equity_market_valuation.py`: internal source models and parse helpers for valuation snapshots.
- Modify `apps/pipelines/src/lib/source/adapters/__init__.py`: export `EodhdAdapter`.
- Test `apps/pipelines/tests/test_eodhd_adapter.py`: parse representative payloads, missing fields, and structured failures.

Pipeline phase:

- Create `apps/pipelines/src/lib/pipeline/equity_market_universe.py`: internal market universe and measured ETF/index proxies.
- Create `apps/pipelines/src/lib/pipeline/transforms/equity_market_valuation.py`: normalize source snapshots into mart rows.
- Create `apps/pipelines/src/lib/db/equity_market_valuation.py`: create/load mart records.
- Create `apps/pipelines/src/tasks/run_equity_market_valuation_etl.py`: task entrypoint for this pipeline.
- Modify `apps/pipelines/src/flows/all_flows.py`: include the equity valuation ETL in the all-flows entrypoint.
- Create `apps/pipelines/src/sql/schema/030_equity_market_valuation.sql`: raw/staging/mart schema.
- Test `apps/pipelines/tests/test_equity_market_valuation_transform.py`: transform rules and proxy notes.
- Test `apps/pipelines/tests/test_equity_market_valuation_flow.py`: sample end-to-end pipeline path without live network.

API phase:

- Create `packages/shared/src/contracts/equity-market-valuation.ts`: frontend-facing response contract.
- Create `apps/api/src/routes/equity-market-valuations.ts`: Fastify route that reads the mart.
- Modify `apps/api/src/server.ts`: register the route.
- Test `apps/api/tests/equity-market-valuations-route.test.ts`: populated and empty mart responses.

Frontend handoff phase:

- Create `docs/agents/prompts/2026-07-07-market-valuation-frontend-integration.md`: prompt for the frontend agent.

---

### Task 1: Commit Planning Documents

**Files:**
- Create: `docs/superpowers/specs/2026-07-07-market-valuation-analysis-design.md`
- Create: `docs/superpowers/plans/2026-07-07-market-valuation-analysis.md`

- [ ] **Step 1: Commit design and plan**

Run:

```powershell
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add docs/superpowers/specs/2026-07-07-market-valuation-analysis-design.md docs/superpowers/plans/2026-07-07-market-valuation-analysis.md
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "docs: plan market valuation analysis"
```

Expected: commit succeeds with only the two planning files.

### Task 2: Source Layer

**Files:**
- Create: `apps/pipelines/src/lib/source/equity_market_valuation.py`
- Create: `apps/pipelines/src/lib/source/adapters/eodhd.py`
- Modify: `apps/pipelines/src/lib/source/adapters/__init__.py`
- Test: `apps/pipelines/tests/test_eodhd_adapter.py`

- [ ] **Step 1: Write source tests**

Create `apps/pipelines/tests/test_eodhd_adapter.py` with tests for:

```python
from src.lib.source.adapters.eodhd import EodhdAdapter
from src.lib.source.equity_market_valuation import parse_eodhd_fundamentals_snapshot


def test_parse_eodhd_etf_valuation_snapshot():
    payload = {
        "General": {
            "Code": "VTI",
            "Exchange": "US",
            "Name": "Vanguard Total Stock Market ETF",
            "Type": "ETF",
        },
        "ETF_Data": {
            "Valuations_Growth": {
                "Price/Prospective Earnings": 22.1,
                "Price/Book": 3.8,
                "Price/Sales": 2.6,
                "Price/Cash Flow": 14.4,
                "Dividend-Yield Factor": 1.35,
            }
        },
    }

    snapshot = parse_eodhd_fundamentals_snapshot(
        market_id="us_total_market",
        provider_symbol="VTI.US",
        payload=payload,
        source_url="https://eodhd.com/api/fundamentals/VTI.US",
        as_of="2026-07-07",
    )

    assert snapshot.market_id == "us_total_market"
    assert snapshot.provider_symbol == "VTI.US"
    assert snapshot.trailing_pe == 22.1
    assert snapshot.price_to_book == 3.8
    assert snapshot.price_to_sales == 2.6
    assert snapshot.price_to_cash_flow == 14.4
    assert snapshot.price_to_free_cash_flow is None
    assert snapshot.dividend_yield_pct == 1.35
    assert snapshot.price_to_cash_flow_method == "provider_price_to_cash_flow_proxy"


def test_parse_eodhd_snapshot_allows_missing_valuation_fields():
    payload = {"General": {"Code": "EWG", "Exchange": "US", "Name": "iShares MSCI Germany ETF", "Type": "ETF"}}

    snapshot = parse_eodhd_fundamentals_snapshot(
        market_id="germany_large_cap",
        provider_symbol="EWG.US",
        payload=payload,
        source_url="https://eodhd.com/api/fundamentals/EWG.US",
        as_of="2026-07-07",
    )

    assert snapshot.trailing_pe is None
    assert snapshot.price_to_book is None
    assert snapshot.price_to_free_cash_flow is None
    assert snapshot.missing_fields == [
        "trailing_pe",
        "price_to_book",
        "price_to_sales",
        "price_to_cash_flow",
        "dividend_yield_pct",
    ]
```

- [ ] **Step 2: Run source tests and verify RED**

Run:

```powershell
cd apps/pipelines
python -m pytest tests/test_eodhd_adapter.py -q
```

Expected: tests fail because the EODHD adapter and parser do not exist.

- [ ] **Step 3: Implement source models and parser**

Create `apps/pipelines/src/lib/source/equity_market_valuation.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EquityMarketValuationSnapshot:
    market_id: str
    provider: str
    provider_symbol: str
    measured_name: str
    measured_type: str
    source_url: str
    as_of: str
    trailing_pe: float | None
    price_to_book: float | None
    price_to_sales: float | None
    price_to_cash_flow: float | None
    price_to_free_cash_flow: float | None
    dividend_yield_pct: float | None
    price_to_cash_flow_method: str
    price_to_free_cash_flow_method: str
    missing_fields: list[str]


def _number(value: Any) -> float | None:
    if value in (None, "", "NA", "N/A"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_eodhd_fundamentals_snapshot(
    *,
    market_id: str,
    provider_symbol: str,
    payload: dict[str, Any],
    source_url: str,
    as_of: str,
) -> EquityMarketValuationSnapshot:
    general = payload.get("General") or {}
    etf_data = payload.get("ETF_Data") or {}
    valuations = etf_data.get("Valuations_Growth") or {}

    values = {
        "trailing_pe": _number(valuations.get("Price/Prospective Earnings")),
        "price_to_book": _number(valuations.get("Price/Book")),
        "price_to_sales": _number(valuations.get("Price/Sales")),
        "price_to_cash_flow": _number(valuations.get("Price/Cash Flow")),
        "dividend_yield_pct": _number(valuations.get("Dividend-Yield Factor")),
    }

    return EquityMarketValuationSnapshot(
        market_id=market_id,
        provider="eodhd",
        provider_symbol=provider_symbol,
        measured_name=str(general.get("Name") or provider_symbol),
        measured_type=str(general.get("Type") or "ETF"),
        source_url=source_url,
        as_of=as_of,
        trailing_pe=values["trailing_pe"],
        price_to_book=values["price_to_book"],
        price_to_sales=values["price_to_sales"],
        price_to_cash_flow=values["price_to_cash_flow"],
        price_to_free_cash_flow=None,
        dividend_yield_pct=values["dividend_yield_pct"],
        price_to_cash_flow_method="provider_price_to_cash_flow_proxy",
        price_to_free_cash_flow_method="unavailable_exact_pfcf_not_in_provider_snapshot",
        missing_fields=[key for key, value in values.items() if value is None],
    )
```

- [ ] **Step 4: Implement EODHD adapter**

Create `apps/pipelines/src/lib/source/adapters/eodhd.py` with a small `urllib.request` adapter that:

- builds `https://eodhd.com/api/fundamentals/{symbol}?api_token={token}&fmt=json`;
- reads `EODHD_API_TOKEN`;
- returns `FetchResult.failure(...)` when the token is missing, the response is invalid JSON, or the request fails;
- calls `parse_eodhd_fundamentals_snapshot(...)` on success.

- [ ] **Step 5: Export the adapter**

Modify `apps/pipelines/src/lib/source/adapters/__init__.py` to export `EodhdAdapter`.

- [ ] **Step 6: Run source tests and verify GREEN**

Run:

```powershell
cd apps/pipelines
python -m pytest tests/test_eodhd_adapter.py -q
```

Expected: source tests pass.

- [ ] **Step 7: Commit source layer**

Run:

```powershell
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add apps/pipelines/src/lib/source/equity_market_valuation.py apps/pipelines/src/lib/source/adapters/eodhd.py apps/pipelines/src/lib/source/adapters/__init__.py apps/pipelines/tests/test_eodhd_adapter.py
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "feat: add eodhd market valuation source"
```

Expected: commit succeeds with only source-layer files and tests.

### Task 3: Pipeline Layer

**Files:**
- Create: `apps/pipelines/src/lib/pipeline/equity_market_universe.py`
- Create: `apps/pipelines/src/lib/pipeline/transforms/equity_market_valuation.py`
- Create: `apps/pipelines/src/lib/db/equity_market_valuation.py`
- Create: `apps/pipelines/src/tasks/run_equity_market_valuation_etl.py`
- Create: `apps/pipelines/src/sql/schema/030_equity_market_valuation.sql`
- Modify: `apps/pipelines/src/flows/all_flows.py`
- Test: `apps/pipelines/tests/test_equity_market_valuation_transform.py`
- Test: `apps/pipelines/tests/test_equity_market_valuation_flow.py`

- [ ] **Step 1: Write transform tests**

Create `apps/pipelines/tests/test_equity_market_valuation_transform.py` to assert that a source snapshot becomes a mart row with:

- stable `market_id`;
- provider and measured-object metadata;
- numeric valuation fields;
- `price_to_free_cash_flow` as `None`;
- `price_to_cash_flow_method` as `provider_price_to_cash_flow_proxy`.

- [ ] **Step 2: Run transform tests and verify RED**

Run:

```powershell
cd apps/pipelines
python -m pytest tests/test_equity_market_valuation_transform.py -q
```

Expected: tests fail because the transform module does not exist.

- [ ] **Step 3: Create market universe**

Create `apps/pipelines/src/lib/pipeline/equity_market_universe.py` with an initial universe:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EquityMarketDefinition:
    market_id: str
    region: str
    market_name: str
    measured_symbol: str
    measured_name: str
    measured_type: str
    provider: str


EQUITY_MARKET_UNIVERSE: tuple[EquityMarketDefinition, ...] = (
    EquityMarketDefinition("us_total_market", "US", "United States broad market", "VTI.US", "Vanguard Total Stock Market ETF", "ETF", "eodhd"),
    EquityMarketDefinition("us_large_cap", "US", "United States large cap", "SPY.US", "SPDR S&P 500 ETF Trust", "ETF", "eodhd"),
    EquityMarketDefinition("europe_developed", "EU", "Europe developed market", "VGK.US", "Vanguard FTSE Europe ETF", "ETF", "eodhd"),
    EquityMarketDefinition("germany_large_cap", "DE", "Germany large cap", "EWG.US", "iShares MSCI Germany ETF", "ETF", "eodhd"),
    EquityMarketDefinition("france_large_cap", "FR", "France large cap", "EWQ.US", "iShares MSCI France ETF", "ETF", "eodhd"),
    EquityMarketDefinition("uk_large_cap", "GB", "United Kingdom large cap", "EWU.US", "iShares MSCI United Kingdom ETF", "ETF", "eodhd"),
    EquityMarketDefinition("finland_large_cap", "FI", "Finland large cap", "EFNL.US", "iShares MSCI Finland ETF", "ETF", "eodhd"),
    EquityMarketDefinition("sweden_large_cap", "SE", "Sweden large cap", "EWD.US", "iShares MSCI Sweden ETF", "ETF", "eodhd"),
    EquityMarketDefinition("norway_large_cap", "NO", "Norway large cap", "ENOR.US", "iShares MSCI Norway ETF", "ETF", "eodhd"),
    EquityMarketDefinition("denmark_large_cap", "DK", "Denmark large cap", "EDEN.US", "iShares MSCI Denmark ETF", "ETF", "eodhd"),
    EquityMarketDefinition("china_large_cap", "CN", "China large cap", "MCHI.US", "iShares MSCI China ETF", "ETF", "eodhd"),
    EquityMarketDefinition("japan_large_cap", "JP", "Japan large cap", "EWJ.US", "iShares MSCI Japan ETF", "ETF", "eodhd"),
    EquityMarketDefinition("south_korea_large_cap", "KR", "South Korea large cap", "EWY.US", "iShares MSCI South Korea ETF", "ETF", "eodhd"),
    EquityMarketDefinition("taiwan_large_cap", "TW", "Taiwan large cap", "EWT.US", "iShares MSCI Taiwan ETF", "ETF", "eodhd"),
)
```

- [ ] **Step 4: Implement transform**

Create `apps/pipelines/src/lib/pipeline/transforms/equity_market_valuation.py` with a `to_equity_market_valuation_row(snapshot, definition)` function returning a dictionary keyed to the mart columns.

- [ ] **Step 5: Create SQL schema**

Create `apps/pipelines/src/sql/schema/030_equity_market_valuation.sql` with:

```sql
create table if not exists raw.equity_market_valuation_payloads (
    market_id text not null,
    provider text not null,
    provider_symbol text not null,
    as_of date not null,
    payload_json jsonb not null,
    source_url text not null,
    loaded_at timestamptz not null default now(),
    primary key (market_id, provider, provider_symbol, as_of)
);

create table if not exists marts.equity_market_valuation_snapshot (
    market_id text primary key,
    region text not null,
    market_name text not null,
    measured_symbol text not null,
    measured_name text not null,
    measured_type text not null,
    provider text not null,
    source_url text not null,
    as_of date not null,
    trailing_pe numeric,
    price_to_book numeric,
    price_to_sales numeric,
    price_to_cash_flow numeric,
    price_to_free_cash_flow numeric,
    dividend_yield_pct numeric,
    price_to_cash_flow_method text not null,
    price_to_free_cash_flow_method text not null,
    missing_fields jsonb not null default '[]'::jsonb,
    updated_at timestamptz not null default now()
);
```

- [ ] **Step 6: Implement DB loader**

Create `apps/pipelines/src/lib/db/equity_market_valuation.py` with functions to load raw payloads and upsert mart rows using `psycopg` parameterized SQL.

- [ ] **Step 7: Implement ETL task**

Create `apps/pipelines/src/tasks/run_equity_market_valuation_etl.py` that iterates `EQUITY_MARKET_UNIVERSE`, calls `EodhdAdapter`, transforms successful snapshots, and loads mart rows.

- [ ] **Step 8: Add all-flows registration**

Modify `apps/pipelines/src/flows/all_flows.py` to call the equity market valuation ETL after existing macro and currency flows.

- [ ] **Step 9: Run pipeline tests**

Run:

```powershell
cd apps/pipelines
python -m pytest tests/test_equity_market_valuation_transform.py tests/test_equity_market_valuation_flow.py -q
```

Expected: pipeline tests pass without live network access.

- [ ] **Step 10: Commit pipeline layer**

Run:

```powershell
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add apps/pipelines/src/lib/pipeline/equity_market_universe.py apps/pipelines/src/lib/pipeline/transforms/equity_market_valuation.py apps/pipelines/src/lib/db/equity_market_valuation.py apps/pipelines/src/tasks/run_equity_market_valuation_etl.py apps/pipelines/src/sql/schema/030_equity_market_valuation.sql apps/pipelines/src/flows/all_flows.py apps/pipelines/tests/test_equity_market_valuation_transform.py apps/pipelines/tests/test_equity_market_valuation_flow.py
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "feat: add market valuation pipeline mart"
```

Expected: commit succeeds with only pipeline-layer files and tests.

### Task 4: API Layer

**Files:**
- Create: `packages/shared/src/contracts/equity-market-valuation.ts`
- Create: `apps/api/src/routes/equity-market-valuations.ts`
- Modify: `apps/api/src/server.ts`
- Test: `apps/api/tests/equity-market-valuations-route.test.ts`

- [ ] **Step 1: Write API route tests**

Create `apps/api/tests/equity-market-valuations-route.test.ts` with:

- one test for populated database rows;
- one test for an empty mart returning `{ asOf: null, markets: [], references: [] }`;
- one assertion that `priceToFreeCashFlow.value` is `null` when exact P/FCF is unavailable.

- [ ] **Step 2: Run API tests and verify RED**

Run:

```powershell
npm.cmd run test --workspace @mvd/api -- equity-market-valuations-route.test.ts
```

Expected: tests fail because the route and contract do not exist.

- [ ] **Step 3: Add shared contract**

Create `packages/shared/src/contracts/equity-market-valuation.ts` with exported types:

```ts
export type EquityMarketValuationMetric = {
  value: string | null;
  method: string;
};

export type EquityMarketValuationRow = {
  marketId: string;
  region: string;
  marketName: string;
  measuredSymbol: string;
  measuredName: string;
  measuredType: string;
  provider: string;
  sourceUrl: string;
  asOf: string;
  metrics: {
    trailingPe: EquityMarketValuationMetric;
    priceToBook: EquityMarketValuationMetric;
    priceToSales: EquityMarketValuationMetric;
    priceToCashFlow: EquityMarketValuationMetric;
    priceToFreeCashFlow: EquityMarketValuationMetric;
    dividendYieldPct: EquityMarketValuationMetric;
  };
  missingFields: string[];
};

export type EquityMarketValuationReference = {
  label: string;
  url: string;
};

export type EquityMarketValuationsResponse = {
  asOf: string | null;
  markets: EquityMarketValuationRow[];
  references: EquityMarketValuationReference[];
};
```

- [ ] **Step 4: Implement route**

Create `apps/api/src/routes/equity-market-valuations.ts` that queries `marts.equity_market_valuation_snapshot order by region, market_name` and maps database rows to `EquityMarketValuationsResponse`.

- [ ] **Step 5: Register route**

Modify `apps/api/src/server.ts` to import and call `registerEquityMarketValuationsRoute(app)`.

- [ ] **Step 6: Run API tests**

Run:

```powershell
npm.cmd run test --workspace @mvd/api -- equity-market-valuations-route.test.ts
```

Expected: API route tests pass.

- [ ] **Step 7: Run shared backend contract tests**

Run:

```powershell
npm.cmd test
```

Expected: repository TypeScript/Vitest tests pass.

- [ ] **Step 8: Commit API layer**

Run:

```powershell
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add packages/shared/src/contracts/equity-market-valuation.ts apps/api/src/routes/equity-market-valuations.ts apps/api/src/server.ts apps/api/tests/equity-market-valuations-route.test.ts
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "feat: expose market valuation api"
```

Expected: commit succeeds with only API and shared-contract files.

### Task 5: Frontend Agent Handoff

**Files:**
- Create: `docs/agents/prompts/2026-07-07-market-valuation-frontend-integration.md`

- [ ] **Step 1: Create frontend handoff prompt**

Create a prompt that instructs the frontend agent to:

- use `GET /equity-markets/valuations`;
- integrate into the existing Equity Markets route;
- render an empty-data state when `markets` is empty;
- display P/E, P/B, P/S, P/CF proxy, exact P/FCF when available, and dividend yield;
- label P/CF as a proxy and exact P/FCF as unavailable when null;
- avoid fake fallback data;
- add web tests for populated and empty API responses.

- [ ] **Step 2: Commit frontend handoff**

Run:

```powershell
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add docs/agents/prompts/2026-07-07-market-valuation-frontend-integration.md
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "docs: add market valuation frontend handoff"
```

Expected: commit succeeds with only the frontend handoff prompt.

---

## Manual Verification Commands For You

After source phase:

```powershell
cd apps/pipelines
python -m pytest tests/test_eodhd_adapter.py -q
```

After pipeline phase:

```powershell
cd apps/pipelines
python -m pytest tests/test_eodhd_adapter.py tests/test_equity_market_valuation_transform.py tests/test_equity_market_valuation_flow.py -q
```

After API phase:

```powershell
npm.cmd run test --workspace @mvd/api -- equity-market-valuations-route.test.ts
npm.cmd test
```

Optional local live fetch smoke test after adding an EODHD token:

```powershell
$env:EODHD_API_TOKEN="<your-token>"
cd apps/pipelines
python -m src.tasks.run_equity_market_valuation_etl
```

The live smoke test should load current provider snapshots into PostgreSQL when the local database is running. It should fail explicitly if the token or database is unavailable.

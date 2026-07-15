from src.flows.equity_market_valuation_flow import run_equity_market_valuation_flow
from src.lib.db import equity_market_valuation as db_module
from src.lib.source.equity_market_valuation import (
    EquityMarketValuationResult,
    EquityMarketValuationSnapshot,
)
from src.tasks import run_equity_market_valuation_etl as etl_module


def _snapshot(symbol: str) -> EquityMarketValuationSnapshot:
    snapshot = EquityMarketValuationSnapshot(
        provider="eodhd",
        symbol=symbol.split(".")[0],
        exchange="US",
        name=f"{symbol} Fund",
        instrument_type="ETF",
        trailing_pe=20.0,
        price_to_book=4.0,
        price_to_sales=3.0,
        price_to_cash_flow=15.0,
        dividend_yield_pct=1.2,
        price_to_free_cash_flow=None,
        price_to_cash_flow_method="provider_price_to_cash_flow_proxy",
        price_to_free_cash_flow_method="provider_exact_price_to_free_cash_flow_unavailable",
        missing_fields=[],
    )
    object.__setattr__(
        snapshot,
        "source_url",
        f"https://eodhd.com/api/fundamentals/{symbol}?fmt=json",
    )
    object.__setattr__(snapshot, "as_of", "2026-07-06")
    return snapshot


def _payload(symbol: str) -> dict:
    return {
        "General": {
            "Code": symbol.split(".")[0],
            "Exchange": "US",
        },
        "ETF_Data": {
            "Valuations_Growth": {
                "Price/Prospective Earnings": "20.0",
            }
        },
    }


class _FakeAdapter:
    def __init__(self):
        self.fetched_symbols: list[str] = []

    def fetch_fundamentals_snapshot(self, symbol: str):
        self.fetched_symbols.append(symbol)
        if symbol == "VGK.US":
            return EquityMarketValuationResult.failure(
                provider="eodhd",
                key=symbol,
                external_series_id=symbol,
                error_type="fetch_error",
                message="provider unavailable",
            )

        return EquityMarketValuationResult.success(_snapshot(symbol), payload_json=_payload(symbol))


class _ConfigFailureAdapter:
    def fetch_fundamentals_snapshot(self, symbol: str):
        return EquityMarketValuationResult.failure(
            provider="eodhd",
            key=symbol,
            external_series_id=symbol,
            error_type="config_error",
            message="EODHD_API_TOKEN is required for EODHD fundamentals requests.",
        )


def test_run_equity_market_valuation_flow_fetches_transforms_loads_and_reports_failures(monkeypatch):
    adapter = _FakeAdapter()
    loaded_payload_rows = []
    loaded_rows = []
    definitions = [
        definition
        for definition in run_equity_market_valuation_flow.__globals__["EQUITY_MARKET_UNIVERSE"]
        if definition.market_id in {"us_total_market", "europe_developed"}
    ]

    monkeypatch.setattr("src.flows.equity_market_valuation_flow.get_connection", lambda: None)
    monkeypatch.setattr(
        "src.flows.equity_market_valuation_flow.EQUITY_MARKET_UNIVERSE",
        definitions,
    )
    monkeypatch.setattr(
        "src.flows.equity_market_valuation_flow.YahooFinanceAdapter",
        lambda: adapter,
    )
    monkeypatch.setattr(
        "src.tasks.run_equity_market_valuation_etl.upsert_equity_market_valuation_payloads",
        lambda _connection, rows: loaded_payload_rows.extend(rows),
    )
    monkeypatch.setattr(
        "src.tasks.run_equity_market_valuation_etl.replace_equity_market_valuation_snapshots",
        lambda _connection, rows: loaded_rows.extend(rows),
    )

    result = run_equity_market_valuation_flow()

    assert adapter.fetched_symbols == ["VTI.US", "VGK.US"]
    assert result["status"] == "failed"
    assert result["mart_rows"] == 1
    assert result["raw_payload_rows"] == 1
    assert result["errors"] == ["europe_developed: provider unavailable"]
    assert loaded_payload_rows == [
        {
            "provider": "eodhd",
            "external_symbol": "VTI.US",
            "fetched_at": result["fetched_at"],
            "payload_json": _payload("VTI.US"),
        }
    ]
    assert len(loaded_rows) == 1
    assert loaded_rows[0]["market_id"] == "us_total_market"
    assert loaded_rows[0]["measured_symbol"] == "VTI.US"


def test_run_equity_market_valuation_etl_reports_clear_summary_when_all_markets_fail():
    connection = _FakeConnection()
    definitions = [
        type(definition)(
            market_id=definition.market_id,
            region=definition.region,
            market_name=definition.market_name,
            measured_symbol=definition.measured_symbol,
            measured_name=definition.measured_name,
            measured_type=definition.measured_type,
            provider="eodhd",
        )
        for definition in run_equity_market_valuation_flow.__globals__["EQUITY_MARKET_UNIVERSE"]
        if definition.market_id in {"us_total_market", "europe_developed"}
    ]

    result = etl_module.run_equity_market_valuation_etl.fn(
        connection,
        definitions=definitions,
        adapter_factories={"eodhd": _ConfigFailureAdapter},
    )

    assert result["status"] == "failed"
    assert result["mart_rows"] == 0
    assert result["raw_payload_rows"] == 0
    assert result["failure_summary"] == (
        "Equity market valuation ETL failed for all 2 markets; wrote 0 mart rows and "
        "0 raw payload rows. First error: us_total_market: EODHD_API_TOKEN is required "
        "for EODHD fundamentals requests."
    )
    assert connection.cursor_instance.commands == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


class _FakeCursor:
    def __init__(self):
        self.commands = []

    def execute(self, query, params=None):
        self.commands.append((str(query), params))

    def executemany(self, query, rows):
        self.commands.append((str(query), list(rows)))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self):
        self.cursor_instance = _FakeCursor()
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


def test_upsert_equity_market_valuation_payloads_inserts_raw_payload_rows():
    connection = _FakeConnection()

    db_module.upsert_equity_market_valuation_payloads(
        connection,
        [
            {
                "provider": "eodhd",
                "external_symbol": "VTI.US",
                "fetched_at": "2026-07-07T12:00:00Z",
                "payload_json": {"General": {"Code": "VTI"}},
            }
        ],
    )

    commands = connection.cursor_instance.commands
    assert any("insert into raw.equity_market_valuation_payloads" in query.lower() for query, _ in commands)
    assert commands[0][1][0]["payload_json"] == '{"General": {"Code": "VTI"}}'
    assert connection.commit_count == 0


def test_run_equity_market_valuation_flow_bootstraps_schema_before_etl(monkeypatch):
    connection = object()
    calls = []

    monkeypatch.setattr("src.flows.equity_market_valuation_flow.get_connection", lambda: connection)
    monkeypatch.setattr(
        "src.flows.equity_market_valuation_flow.bootstrap_taylor_rule_schema",
        lambda received_connection: calls.append(("bootstrap", received_connection)),
    )
    monkeypatch.setattr(
        "src.tasks.run_equity_market_valuation_etl.run_equity_market_valuation_etl",
        lambda received_connection, **_kwargs: calls.append(("etl", received_connection)) or {"status": "success"},
    )

    result = run_equity_market_valuation_flow()

    assert result == {"status": "success"}
    assert calls == [("bootstrap", connection), ("etl", connection)]


def test_run_equity_market_valuation_etl_commits_raw_and_mart_writes_once(monkeypatch):
    adapter = _FakeAdapter()
    connection = _FakeConnection()
    definitions = [
        definition
        for definition in run_equity_market_valuation_flow.__globals__["EQUITY_MARKET_UNIVERSE"]
        if definition.market_id == "us_total_market"
    ]

    result = etl_module.run_equity_market_valuation_etl.fn(
        connection,
        definitions=definitions,
        adapter_factories={"yahoo_finance": lambda: adapter},
    )

    commands = connection.cursor_instance.commands
    assert result["status"] == "success"
    assert any("insert into raw.equity_market_valuation_payloads" in query.lower() for query, _ in commands)
    assert any("insert into marts.equity_market_valuation_snapshot" in query.lower() for query, _ in commands)
    assert connection.commit_count == 1
    assert connection.rollback_count == 0


def test_run_equity_market_valuation_etl_supports_yahoo_finance_provider(monkeypatch):
    adapter = _FakeAdapter()
    connection = _FakeConnection()
    definition = run_equity_market_valuation_flow.__globals__["EQUITY_MARKET_UNIVERSE"][0]
    yahoo_definition = type(definition)(
        market_id=definition.market_id,
        region=definition.region,
        market_name=definition.market_name,
        measured_symbol=definition.measured_symbol,
        measured_name=definition.measured_name,
        measured_type=definition.measured_type,
        provider="yahoo_finance",
    )

    result = etl_module.run_equity_market_valuation_etl.fn(
        connection,
        definitions=[yahoo_definition],
        adapter_factories={"yahoo_finance": lambda: adapter},
    )

    assert result["status"] == "success"
    assert adapter.fetched_symbols == ["VTI.US"]

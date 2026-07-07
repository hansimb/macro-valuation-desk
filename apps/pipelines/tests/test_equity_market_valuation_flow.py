from src.flows.equity_market_valuation_flow import run_equity_market_valuation_flow
from src.lib.db import equity_market_valuation as db_module
from src.lib.source.equity_market_valuation import (
    EquityMarketValuationResult,
    EquityMarketValuationSnapshot,
)


def _snapshot(symbol: str) -> EquityMarketValuationSnapshot:
    return EquityMarketValuationSnapshot(
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
        "src.flows.equity_market_valuation_flow.EodhdAdapter",
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


class _FakeCursor:
    def __init__(self):
        self.commands = []

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

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commit_count += 1


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
    assert connection.commit_count == 1

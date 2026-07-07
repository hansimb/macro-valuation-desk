import json

from src.lib.source.adapters.eodhd import EodhdAdapter
from src.lib.source.equity_market_valuation import parse_eodhd_fundamentals_snapshot


class _FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _representative_payload() -> dict:
    return {
        "General": {
            "Code": "SPY",
            "Exchange": "US",
            "Name": "SPDR S&P 500 ETF Trust",
            "Type": "ETF",
        },
        "ETF_Data": {
            "Valuations_Growth": {
                "Price/Prospective Earnings": "22.38",
                "Price/Book": 4.76,
                "Price/Sales": "2.91",
                "Price/Cash Flow": "15.64",
                "Dividend-Yield Factor": "1.23",
            }
        },
    }


def test_parse_eodhd_fundamentals_snapshot_returns_market_valuation_snapshot():
    snapshot = parse_eodhd_fundamentals_snapshot(_representative_payload())

    assert snapshot.provider == "eodhd"
    assert snapshot.symbol == "SPY"
    assert snapshot.exchange == "US"
    assert snapshot.name == "SPDR S&P 500 ETF Trust"
    assert snapshot.instrument_type == "ETF"
    assert snapshot.trailing_pe == 22.38
    assert snapshot.price_to_book == 4.76
    assert snapshot.price_to_sales == 2.91
    assert snapshot.price_to_cash_flow == 15.64
    assert snapshot.dividend_yield_pct == 1.23
    assert snapshot.price_to_free_cash_flow is None
    assert snapshot.price_to_cash_flow_method == "provider_price_to_cash_flow_proxy"
    assert (
        snapshot.price_to_free_cash_flow_method
        == "provider_exact_price_to_free_cash_flow_unavailable"
    )
    assert snapshot.missing_fields == []


def test_parse_eodhd_fundamentals_snapshot_records_missing_valuation_fields():
    payload = _representative_payload()
    valuations = payload["ETF_Data"]["Valuations_Growth"]
    del valuations["Price/Book"]
    del valuations["Dividend-Yield Factor"]

    snapshot = parse_eodhd_fundamentals_snapshot(payload)

    assert snapshot.price_to_book is None
    assert snapshot.dividend_yield_pct is None
    assert snapshot.price_to_cash_flow == 15.64
    assert snapshot.missing_fields == [
        "ETF_Data.Valuations_Growth.Price/Book",
        "ETF_Data.Valuations_Growth.Dividend-Yield Factor",
    ]


def test_parse_eodhd_fundamentals_snapshot_treats_malformed_numbers_as_missing():
    payload = _representative_payload()
    valuations = payload["ETF_Data"]["Valuations_Growth"]
    valuations["Price/Prospective Earnings"] = "N/A"
    valuations["Price/Sales"] = "--"

    snapshot = parse_eodhd_fundamentals_snapshot(payload)

    assert snapshot.trailing_pe is None
    assert snapshot.price_to_sales is None
    assert snapshot.price_to_book == 4.76
    assert snapshot.missing_fields == [
        "ETF_Data.Valuations_Growth.Price/Prospective Earnings",
        "ETF_Data.Valuations_Growth.Price/Sales",
    ]


def test_eodhd_adapter_returns_config_failure_when_api_token_is_missing(monkeypatch):
    monkeypatch.delenv("EODHD_API_TOKEN", raising=False)
    monkeypatch.setattr("src.lib.source.adapters.eodhd.load_project_env", lambda: None)

    result = EodhdAdapter().fetch_fundamentals_snapshot("SPY")

    assert result.ok is False
    assert result.snapshot is None
    assert result.error is not None
    assert result.error.provider == "eodhd"
    assert result.error.key == "SPY"
    assert result.error.external_series_id == "SPY"
    assert result.error.error_type == "config_error"
    assert "EODHD_API_TOKEN" in result.error.message


def test_eodhd_adapter_fetches_and_parses_snapshot(monkeypatch):
    monkeypatch.setenv("EODHD_API_TOKEN", "test-token")
    payload = json.dumps(_representative_payload()).encode("utf-8")

    def fake_urlopen(request):
        assert request.full_url == (
            "https://eodhd.com/api/fundamentals/SPY?api_token=test-token&fmt=json"
        )
        return _FakeResponse(payload)

    monkeypatch.setattr("src.lib.source.adapters.eodhd.urlopen", fake_urlopen)

    result = EodhdAdapter().fetch_fundamentals_snapshot("SPY")

    assert result.ok is True
    assert result.error is None
    assert result.payload_json == _representative_payload()
    assert result.snapshot is not None
    assert result.snapshot.symbol == "SPY"
    assert result.snapshot.trailing_pe == 22.38

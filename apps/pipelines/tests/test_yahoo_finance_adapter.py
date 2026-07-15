import json

from src.lib.source.adapters.yahoo_finance import (
    YahooFinanceAdapter,
    parse_yahoo_quote_summary_snapshot,
)


class _FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _raw(value: float) -> dict:
    return {"raw": value, "fmt": str(value)}


def _representative_payload() -> dict:
    return {
        "quoteSummary": {
            "result": [
                {
                    "price": {
                        "symbol": "SPY",
                        "exchangeName": "NYSEArca",
                        "shortName": "SPDR S&P 500 ETF Trust",
                        "quoteType": "ETF",
                        "regularMarketTime": {"raw": 1784102400},
                    },
                    "defaultKeyStatistics": {
                        "trailingPE": _raw(24.2),
                        "priceToBook": _raw(5.1),
                    },
                    "summaryDetail": {
                        "priceToSalesTrailing12Months": _raw(3.2),
                        "dividendYield": {"raw": 0.0124, "fmt": "1.24%"},
                    },
                }
            ],
            "error": None,
        }
    }


def test_parse_yahoo_quote_summary_snapshot_returns_market_valuation_snapshot():
    snapshot = parse_yahoo_quote_summary_snapshot(
        _representative_payload(),
        symbol="SPY",
        source_url="https://query1.finance.yahoo.com/v10/finance/quoteSummary/SPY",
    )

    assert snapshot.provider == "yahoo_finance"
    assert snapshot.symbol == "SPY"
    assert snapshot.exchange == "NYSEArca"
    assert snapshot.name == "SPDR S&P 500 ETF Trust"
    assert snapshot.instrument_type == "ETF"
    assert snapshot.trailing_pe == 24.2
    assert snapshot.price_to_book == 5.1
    assert snapshot.price_to_sales == 3.2
    assert snapshot.price_to_cash_flow is None
    assert snapshot.dividend_yield_pct == 1.24
    assert snapshot.price_to_free_cash_flow is None
    assert snapshot.price_to_cash_flow_method == "provider_price_to_cash_flow_unavailable"
    assert snapshot.price_to_free_cash_flow_method == "provider_exact_price_to_free_cash_flow_unavailable"
    assert snapshot.missing_fields == [
        "quoteSummary.result[0].defaultKeyStatistics.priceToCashFlow"
    ]
    assert snapshot.source_url == "https://query1.finance.yahoo.com/v10/finance/quoteSummary/SPY"
    assert snapshot.as_of == "2026-07-15"


def test_yahoo_finance_adapter_fetches_without_api_token(monkeypatch):
    payload = json.dumps(_representative_payload()).encode("utf-8")

    def fake_urlopen(request):
        assert request.full_url == (
            "https://query1.finance.yahoo.com/v10/finance/quoteSummary/SPY"
            "?modules=price%2CdefaultKeyStatistics%2CsummaryDetail"
        )
        assert request.headers["User-agent"] == "macro-valuation-desk/0.1"
        return _FakeResponse(payload)

    monkeypatch.setattr("src.lib.source.adapters.yahoo_finance.urlopen", fake_urlopen)

    result = YahooFinanceAdapter().fetch_fundamentals_snapshot("SPY.US")

    assert result.ok is True
    assert result.error is None
    assert result.payload_json == _representative_payload()
    assert result.snapshot is not None
    assert result.snapshot.symbol == "SPY"

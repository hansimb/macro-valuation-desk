from __future__ import annotations

from datetime import date

import pytest

from src.lib.source.adapters.development_prices import DevelopmentPriceAdapter
from src.lib.source.country_index_types import SecurityListing


def _security() -> SecurityListing:
    return SecurityListing(
        listing_id="security-master:aapl",
        security_id="security-master:aapl",
        issuer_id="issuer:aapl",
        issuer_name="Apple Inc.",
        security_type="common_stock",
        market_id="us",
        exchange_code="NASDAQ",
        ticker="AAPL",
        trading_currency="USD",
        valid_from=date(1980, 12, 12),
        listing_status="active",
        source_provider="security_master",
        source_external_id="master:aapl",
    )


def _payload(
    *,
    closes: object = (100.0, 102.0),
    timestamps: object = (1735689600, 1735776000),
    splits: object | None = None,
    adjclose: object = (-999.0, float("nan")),
) -> dict[str, object]:
    split_events = splits
    if split_events is None:
        split_events = {
            "1735776000": {
                "date": 1735776000,
                "numerator": 2,
                "denominator": 1,
                "splitRatio": "2:1",
            }
        }
    return {
        "chart": {
            "result": [
                {
                    "timestamp": timestamps,
                    "indicators": {
                        "quote": [{"close": closes}],
                        "adjclose": [{"adjclose": adjclose}],
                    },
                    "events": {"splits": split_events},
                }
            ]
        }
    }


def test_daily_prices_calculate_split_only_adjustments_and_ignore_dividend_adjusted_close():
    requests: list[str] = []

    def fetch_json(url: str) -> dict[str, object]:
        requests.append(url)
        return _payload()

    adapter = DevelopmentPriceAdapter(fetch_json=fetch_json)
    prices = adapter.daily_prices(_security(), date(2025, 1, 1), date(2025, 1, 2))

    assert [price.trading_date for price in prices] == [date(2025, 1, 1), date(2025, 1, 2)]
    assert [price.close_price for price in prices] == [100.0, 102.0]
    assert [price.split_adjusted_close_price for price in prices] == [50.0, 102.0]
    assert all(price.provider == "yahoo_finance_development" for price in prices)
    assert all(price.license_class == "development_only" for price in prices)
    assert prices[1].adjustment_metadata == {
        "split": {"date": "2025-01-02", "ratio": "2:1"}
    }
    assert prices[0].provider_timestamp.tzinfo is not None
    assert adapter.license.usage == "development_only"
    assert requests == [
        "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&period1=1735689600&period2=1735862400"
    ]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (_payload(closes=(0, 102.0)), "close price"),
        (_payload(closes=(-1, 102.0)), "close price"),
        (_payload(closes=(float("nan"), 102.0)), "close price"),
        (_payload(closes=(float("inf"), 102.0)), "close price"),
        (_payload(timestamps=(None, 1735776000)), "missing trading dates"),
        (_payload(timestamps=(1735689600, 1735689600)), "duplicate trading date"),
        (
            _payload(
                splits={
                    "1735776000": {
                        "date": 1735776000,
                        "numerator": 0,
                        "denominator": 1,
                    }
                }
            ),
            "split ratio",
        ),
    ],
)
def test_daily_prices_reject_invalid_prices_dates_and_split_ratios(payload, message):
    adapter = DevelopmentPriceAdapter(fetch_json=lambda _url: payload)

    with pytest.raises(ValueError, match=message):
        adapter.daily_prices(_security(), date(2025, 1, 1), date(2025, 1, 2))


def test_development_price_adapter_hard_blocks_production(monkeypatch):
    monkeypatch.setenv("MVD_ENV", "production")
    requests: list[str] = []

    def fetch_json(url: str) -> dict[str, object]:
        requests.append(url)
        return _payload()

    adapter = DevelopmentPriceAdapter(fetch_json=fetch_json)

    with pytest.raises(ValueError, match="development-only"):
        adapter.assert_publishable(environment="production")
    with pytest.raises(ValueError, match="development-only"):
        adapter.daily_prices(_security(), date(2025, 1, 1), date(2025, 1, 2))
    assert requests == []

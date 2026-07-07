from src.lib.source.equity_market_valuation import EquityMarketValuationSnapshot
from src.lib.pipeline.equity_market_universe import MarketDefinition
from src.lib.pipeline.transforms import equity_market_valuation as transform_module


def test_snapshot_becomes_equity_market_valuation_mart_row():
    definition = MarketDefinition(
        market_id="us_large_cap",
        region="US",
        market_name="United States Large Cap",
        measured_symbol="SPY.US",
        measured_name="SPDR S&P 500 ETF Trust",
        measured_type="etf",
        provider="eodhd",
    )
    snapshot = EquityMarketValuationSnapshot(
        provider="eodhd",
        symbol="SPY",
        exchange="US",
        name="SPDR S&P 500 ETF Trust",
        instrument_type="ETF",
        trailing_pe=22.38,
        price_to_book=4.76,
        price_to_sales=2.91,
        price_to_cash_flow=15.64,
        dividend_yield_pct=1.23,
        price_to_free_cash_flow=None,
        price_to_cash_flow_method="provider_price_to_cash_flow_proxy",
        price_to_free_cash_flow_method="provider_exact_price_to_free_cash_flow_unavailable",
        missing_fields=["ETF_Data.Valuations_Growth.Price/Book"],
    )
    object.__setattr__(
        snapshot,
        "source_url",
        "https://eodhd.com/api/fundamentals/SPY.US?fmt=json",
    )
    object.__setattr__(snapshot, "as_of", "2026-07-06")

    row = transform_module.to_equity_market_valuation_row(snapshot, definition)

    assert row == {
        "market_id": "us_large_cap",
        "region": "US",
        "market_name": "United States Large Cap",
        "measured_symbol": "SPY.US",
        "measured_name": "SPDR S&P 500 ETF Trust",
        "measured_type": "etf",
        "provider": "eodhd",
        "source_url": "https://eodhd.com/api/fundamentals/SPY.US?fmt=json",
        "as_of": "2026-07-06",
        "trailing_pe": 22.38,
        "price_to_book": 4.76,
        "price_to_sales": 2.91,
        "price_to_cash_flow": 15.64,
        "dividend_yield_pct": 1.23,
        "price_to_free_cash_flow": None,
        "price_to_cash_flow_method": "provider_price_to_cash_flow_proxy",
        "price_to_free_cash_flow_method": "provider_exact_price_to_free_cash_flow_unavailable",
        "missing_fields": ["ETF_Data.Valuations_Growth.Price/Book"],
    }

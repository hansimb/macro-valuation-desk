from __future__ import annotations

from src.lib.pipeline.equity_market_universe import MarketDefinition
from src.lib.source.equity_market_valuation import EquityMarketValuationSnapshot


def to_equity_market_valuation_row(
    snapshot: EquityMarketValuationSnapshot,
    definition: MarketDefinition,
) -> dict[str, object]:
    return {
        "market_id": definition.market_id,
        "region": definition.region,
        "market_name": definition.market_name,
        "measured_symbol": definition.measured_symbol,
        "measured_name": definition.measured_name,
        "measured_type": definition.measured_type,
        "provider": snapshot.provider,
        "source_url": snapshot.source_url,
        "as_of": snapshot.as_of,
        "trailing_pe": snapshot.trailing_pe,
        "price_to_book": snapshot.price_to_book,
        "price_to_sales": snapshot.price_to_sales,
        "price_to_cash_flow": snapshot.price_to_cash_flow,
        "dividend_yield_pct": snapshot.dividend_yield_pct,
        "price_to_free_cash_flow": snapshot.price_to_free_cash_flow,
        "price_to_cash_flow_method": snapshot.price_to_cash_flow_method,
        "price_to_free_cash_flow_method": snapshot.price_to_free_cash_flow_method,
        "missing_fields": snapshot.missing_fields,
    }

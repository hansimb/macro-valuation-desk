from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketDefinition:
    market_id: str
    region: str
    market_name: str
    measured_symbol: str
    measured_name: str
    measured_type: str
    provider: str


EQUITY_MARKET_UNIVERSE = [
    MarketDefinition("us_total_market", "US", "United States Total Market", "VTI.US", "Vanguard Total Stock Market ETF", "etf", "eodhd"),
    MarketDefinition("us_large_cap", "US", "United States Large Cap", "SPY.US", "SPDR S&P 500 ETF Trust", "etf", "eodhd"),
    MarketDefinition("europe_developed", "Europe", "Europe Developed", "VGK.US", "Vanguard FTSE Europe ETF", "etf", "eodhd"),
    MarketDefinition("germany_large_cap", "Germany", "Germany Large Cap", "EWG.US", "iShares MSCI Germany ETF", "etf", "eodhd"),
    MarketDefinition("france_large_cap", "France", "France Large Cap", "EWQ.US", "iShares MSCI France ETF", "etf", "eodhd"),
    MarketDefinition("uk_large_cap", "United Kingdom", "United Kingdom Large Cap", "EWU.US", "iShares MSCI United Kingdom ETF", "etf", "eodhd"),
    MarketDefinition("finland_large_cap", "Finland", "Finland Large Cap", "EFNL.US", "iShares MSCI Finland ETF", "etf", "eodhd"),
    MarketDefinition("sweden_large_cap", "Sweden", "Sweden Large Cap", "EWD.US", "iShares MSCI Sweden ETF", "etf", "eodhd"),
    MarketDefinition("norway_large_cap", "Norway", "Norway Large Cap", "ENOR.US", "iShares MSCI Norway ETF", "etf", "eodhd"),
    MarketDefinition("denmark_large_cap", "Denmark", "Denmark Large Cap", "EDEN.US", "iShares MSCI Denmark ETF", "etf", "eodhd"),
    MarketDefinition("china_large_cap", "China", "China Large Cap", "MCHI.US", "iShares MSCI China ETF", "etf", "eodhd"),
    MarketDefinition("japan_large_cap", "Japan", "Japan Large Cap", "EWJ.US", "iShares MSCI Japan ETF", "etf", "eodhd"),
    MarketDefinition("south_korea_large_cap", "South Korea", "South Korea Large Cap", "EWY.US", "iShares MSCI South Korea ETF", "etf", "eodhd"),
    MarketDefinition("taiwan_large_cap", "Taiwan", "Taiwan Large Cap", "EWT.US", "iShares MSCI Taiwan ETF", "etf", "eodhd"),
]

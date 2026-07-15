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
    MarketDefinition("us_total_market", "US", "United States Total Market", "ITOT.US", "iShares Core S&P Total U.S. Stock Market ETF", "etf", "issuer_pages"),
    MarketDefinition("us_large_cap", "US", "United States Large Cap", "SPY.US", "SPDR S&P 500 ETF Trust", "etf", "issuer_pages"),
    MarketDefinition("europe_developed", "Europe", "Europe Developed", "IEUR.US", "iShares Core MSCI Europe ETF", "etf", "issuer_pages"),
    MarketDefinition("germany_large_cap", "Germany", "Germany Large Cap", "EWG.US", "iShares MSCI Germany ETF", "etf", "issuer_pages"),
    MarketDefinition("france_large_cap", "France", "France Large Cap", "EWQ.US", "iShares MSCI France ETF", "etf", "issuer_pages"),
    MarketDefinition("uk_large_cap", "United Kingdom", "United Kingdom Large Cap", "EWU.US", "iShares MSCI United Kingdom ETF", "etf", "issuer_pages"),
    MarketDefinition("finland_large_cap", "Finland", "Finland Large Cap", "EFNL.US", "iShares MSCI Finland ETF", "etf", "issuer_pages"),
    MarketDefinition("sweden_large_cap", "Sweden", "Sweden Large Cap", "EWD.US", "iShares MSCI Sweden ETF", "etf", "issuer_pages"),
    MarketDefinition("norway_large_cap", "Norway", "Norway Large Cap", "ENOR.US", "iShares MSCI Norway ETF", "etf", "issuer_pages"),
    MarketDefinition("denmark_large_cap", "Denmark", "Denmark Large Cap", "EDEN.US", "iShares MSCI Denmark ETF", "etf", "issuer_pages"),
    MarketDefinition("china_large_cap", "China", "China Large Cap", "MCHI.US", "iShares MSCI China ETF", "etf", "issuer_pages"),
    MarketDefinition("japan_large_cap", "Japan", "Japan Large Cap", "EWJ.US", "iShares MSCI Japan ETF", "etf", "issuer_pages"),
    MarketDefinition("south_korea_large_cap", "South Korea", "South Korea Large Cap", "EWY.US", "iShares MSCI South Korea ETF", "etf", "issuer_pages"),
    MarketDefinition("taiwan_large_cap", "Taiwan", "Taiwan Large Cap", "EWT.US", "iShares MSCI Taiwan ETF", "etf", "issuer_pages"),
]

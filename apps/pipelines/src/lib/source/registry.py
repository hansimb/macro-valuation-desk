from __future__ import annotations

from src.lib.source.types import SeriesDefinition


SERIES_REGISTRY: dict[str, SeriesDefinition] = {
    "us_policy_rate": SeriesDefinition(
        key="us_policy_rate",
        category="policy_rate",
        provider="fred",
        external_series_id="DFEDTARU",
        label="Federal Funds Target Range - Upper Limit",
        region="US",
        frequency="daily",
        unit="percent",
        source_url="https://fred.stlouisfed.org/series/DFEDTARU",
    ),
    "us_cpi_headline": SeriesDefinition(
        key="us_cpi_headline",
        category="inflation",
        provider="fred",
        external_series_id="CPIAUCSL",
        label="Consumer Price Index for All Urban Consumers: All Items in U.S. City Average",
        region="US",
        frequency="monthly",
        unit="index",
        source_url="https://fred.stlouisfed.org/series/CPIAUCSL",
    ),
    "us_cpi_core": SeriesDefinition(
        key="us_cpi_core",
        category="inflation",
        provider="fred",
        external_series_id="CPILFESL",
        label="Consumer Price Index for All Urban Consumers: All Items Less Food and Energy in U.S. City Average",
        region="US",
        frequency="monthly",
        unit="index",
        source_url="https://fred.stlouisfed.org/series/CPILFESL",
    ),
    "us_market_real_rate": SeriesDefinition(
        key="us_market_real_rate",
        category="market_rate",
        provider="fred",
        external_series_id="DFII10",
        label="10-Year Treasury Inflation-Indexed Security, Constant Maturity",
        region="US",
        frequency="daily",
        unit="percent",
        source_url="https://fred.stlouisfed.org/series/DFII10",
    ),
    "us_real_gdp": SeriesDefinition(
        key="us_real_gdp",
        category="growth",
        provider="fred",
        external_series_id="GDPC1",
        label="Real Gross Domestic Product",
        region="US",
        frequency="quarterly",
        unit="level",
        source_url="https://fred.stlouisfed.org/series/GDPC1",
    ),
    "eu_policy_rate": SeriesDefinition(
        key="eu_policy_rate",
        category="policy_rate",
        provider="fred",
        external_series_id="ECBDFR",
        label="ECB Deposit Facility Rate",
        region="EU",
        frequency="daily",
        unit="percent",
        source_url="https://fred.stlouisfed.org/series/ECBDFR",
    ),
    "eu_hicp_headline": SeriesDefinition(
        key="eu_hicp_headline",
        category="inflation",
        provider="fred",
        external_series_id="CP00MI15EA20M086NEST",
        label="Harmonized Index of Consumer Prices: Total for Euro Area (20 Countries)",
        region="EU",
        frequency="monthly",
        unit="index",
        source_url="https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
    ),
    "eu_hicp_core": SeriesDefinition(
        key="eu_hicp_core",
        category="inflation",
        provider="fred",
        external_series_id="CPHPLA01EZM661N",
        label="Consumer Price Index: Harmonised Prices: All Items Less Food, Energy, Tobacco, Alcohol: Total for the Euro Area (19 Countries)",
        region="EU",
        frequency="monthly",
        unit="index",
        source_url="https://fred.stlouisfed.org/series/CPHPLA01EZM661N",
    ),
    "eu_market_real_rate": SeriesDefinition(
        key="eu_market_real_rate",
        category="market_rate",
        provider="fred",
        external_series_id="IRLTLT01EZM156N",
        label="10-Year Government Bond Yield for Euro Area (19 Countries)",
        region="EU",
        frequency="monthly",
        unit="percent",
        source_url="https://fred.stlouisfed.org/series/IRLTLT01EZM156N",
    ),
    "eu_real_gdp": SeriesDefinition(
        key="eu_real_gdp",
        category="growth",
        provider="fred",
        external_series_id="CLV10MNACB1GQSCAEA20Q",
        label="Real Gross Domestic Product for Euro Area (20 Countries)",
        region="EU",
        frequency="quarterly",
        unit="level",
        source_url="https://fred.stlouisfed.org/series/CLV10MNACB1GQSCAEA20Q",
    ),
}


def get_series_definition(key: str) -> SeriesDefinition:
    return SERIES_REGISTRY[key]


def get_series_definitions(keys: list[str]) -> list[SeriesDefinition]:
    return [get_series_definition(key) for key in keys]

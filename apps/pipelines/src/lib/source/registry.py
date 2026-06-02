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
        provider="ecb",
        external_series_id="FM.M.US.USD.4F.BB.R_US10YT_RR.YLDA",
        label="Real USA 10-year Government Benchmark bond yield",
        region="US",
        frequency="monthly",
        unit="percent",
        source_url="https://data.ecb.europa.eu/data/datasets/FM/FM.M.US.USD.4F.BB.R_US10YT_RR.YLDA",
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
        provider="ecb",
        external_series_id="FM.D.U2.EUR.4F.KR.DFR.LEV",
        label="ECB Deposit Facility Rate",
        region="EU",
        frequency="daily",
        unit="percent",
        source_url="https://data.ecb.europa.eu/data/datasets/FM/FM.D.U2.EUR.4F.KR.DFR.LEV",
    ),
    "eu_hicp_headline": SeriesDefinition(
        key="eu_hicp_headline",
        category="inflation",
        provider="ecb",
        external_series_id="HICP.M.U2.N.000000.4D0.ANR",
        label="HICP Inflation rate - Total - Annual rate of change, Euro area, Monthly",
        region="EU",
        frequency="monthly",
        unit="percentage_change",
        source_url="https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR",
    ),
    "eu_hicp_core": SeriesDefinition(
        key="eu_hicp_core",
        category="inflation",
        provider="ecb",
        external_series_id="HICP.M.U2.N.XEFUN0.4D0.ANR",
        label="HICP Inflation rate - Total excluding energy and unprocessed food - Annual rate of change, Euro area, Monthly",
        region="EU",
        frequency="monthly",
        unit="percentage_change",
        source_url="https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.XEFUN0.4D0.ANR",
    ),
    "eu_market_real_rate": SeriesDefinition(
        key="eu_market_real_rate",
        category="market_rate",
        provider="ecb",
        external_series_id="FM.M.U2.EUR.4F.BB.R_U2_10Y.YLDA",
        label="Real Euro area 10-year Government Benchmark bond yield",
        region="EU",
        frequency="monthly",
        unit="percent",
        source_url="https://data.ecb.europa.eu/data/datasets/FM/FM.M.U2.EUR.4F.BB.R_U2_10Y.YLDA",
    ),
    "eu_real_gdp": SeriesDefinition(
        key="eu_real_gdp",
        category="growth",
        provider="ecb",
        external_series_id="MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
        label="Gross domestic product at market prices, volume, Euro area 20, Quarterly",
        region="EU",
        frequency="quarterly",
        unit="level",
        source_url="https://data.ecb.europa.eu/data/datasets/MNA/MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
    ),
}


def get_series_definition(key: str) -> SeriesDefinition:
    return SERIES_REGISTRY[key]


def get_series_definitions(keys: list[str]) -> list[SeriesDefinition]:
    return [get_series_definition(key) for key in keys]

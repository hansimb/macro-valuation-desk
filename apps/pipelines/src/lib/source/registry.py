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
}


def get_series_definition(key: str) -> SeriesDefinition:
    return SERIES_REGISTRY[key]

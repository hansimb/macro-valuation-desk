from src.lib.pipeline.transforms.staging import stage_standardized_series
from src.lib.source.types import Observation, StandardizedSeries


def test_stage_standardized_series_normalizes_dates_and_numeric_values():
    series = StandardizedSeries(
        key="us_policy_rate",
        category="policy_rate",
        provider="fred",
        series_id="DFEDTARU",
        label="Federal Funds Target Range - Upper Limit",
        region="US",
        frequency="daily",
        unit="percent",
        source_url="https://fred.stlouisfed.org/series/DFEDTARU",
        observations=[
            Observation(date="2026-05-01", value="4.50"),
            Observation(date="2026-05-02", value="4.75"),
        ],
    )

    rows = stage_standardized_series(series)

    assert rows == [
        {
            "series_id": "us_policy_rate",
            "observation_date": "2026-05-01",
            "numeric_value": 4.5,
            "category": "policy_rate",
            "region": "US",
            "frequency": "daily",
            "unit": "percent",
            "provider": "fred",
            "is_valid": True,
        },
        {
            "series_id": "us_policy_rate",
            "observation_date": "2026-05-02",
            "numeric_value": 4.75,
            "category": "policy_rate",
            "region": "US",
            "frequency": "daily",
            "unit": "percent",
            "provider": "fred",
            "is_valid": True,
        },
    ]


def test_stage_standardized_series_skips_non_numeric_values():
    series = StandardizedSeries(
        key="eu_hicp_headline",
        category="inflation",
        provider="ecb",
        series_id="HICP.M.U2.N.000000.4D0.ANR",
        label="HICP",
        region="EU",
        frequency="monthly",
        unit="percentage_change",
        source_url="https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR",
        observations=[
            Observation(date="2026-04", value="."),
            Observation(date="2026-05", value="2.10"),
        ],
    )

    rows = stage_standardized_series(series)

    assert rows == [
        {
            "series_id": "eu_hicp_headline",
            "observation_date": "2026-05-01",
            "numeric_value": 2.1,
            "category": "inflation",
            "region": "EU",
            "frequency": "monthly",
            "unit": "percentage_change",
            "provider": "ecb",
            "is_valid": True,
        }
    ]


def test_stage_standardized_series_normalizes_quarterly_dates():
    series = StandardizedSeries(
        key="eu_real_gdp",
        category="growth",
        provider="ecb",
        series_id="MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
        label="Real GDP",
        region="EU",
        frequency="quarterly",
        unit="level",
        source_url="https://data.ecb.europa.eu/data/datasets/MNA/MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
        observations=[Observation(date="2026-Q1", value="3309009.58")],
    )

    rows = stage_standardized_series(series)

    assert rows == [
        {
            "series_id": "eu_real_gdp",
            "observation_date": "2026-01-01",
            "numeric_value": 3309009.58,
            "category": "growth",
            "region": "EU",
            "frequency": "quarterly",
            "unit": "level",
            "provider": "ecb",
            "is_valid": True,
        }
    ]

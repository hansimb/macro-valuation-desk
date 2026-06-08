from src.lib.pipeline.transforms.staging import fill_series_gaps, stage_standardized_series
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
            "source_url": "https://fred.stlouisfed.org/series/DFEDTARU",
            "is_valid": True,
            "is_imputed": False,
            "imputation_method": None,
            "imputation_note": None,
            "imputation_source_window": None,
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
            "source_url": "https://fred.stlouisfed.org/series/DFEDTARU",
            "is_valid": True,
            "is_imputed": False,
            "imputation_method": None,
            "imputation_note": None,
            "imputation_source_window": None,
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
            "source_url": "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR",
            "is_valid": True,
            "is_imputed": False,
            "imputation_method": None,
            "imputation_note": None,
            "imputation_source_window": None,
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
            "source_url": "https://data.ecb.europa.eu/data/datasets/MNA/MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
            "is_valid": True,
            "is_imputed": False,
            "imputation_method": None,
            "imputation_note": None,
            "imputation_source_window": None,
        }
    ]


def test_stage_standardized_series_collapses_monthly_fallback_daily_inputs_to_latest_month_value():
    series = StandardizedSeries(
        key="eurusd_spot_monthly",
        category="fx_spot",
        provider="ecb",
        series_id="EXR.M.USD.EUR.SP00.A",
        label="EUR/USD monthly",
        region="FX",
        frequency="monthly",
        unit="usd_per_eur",
        source_url="https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
        observations=[
            Observation(date="2025-10-01", value="1.1723"),
            Observation(date="2025-10-31", value="1.1541"),
        ],
    )

    rows = stage_standardized_series(series)

    assert rows == [
        {
            "series_id": "eurusd_spot_monthly",
            "observation_date": "2025-10-01",
            "numeric_value": 1.1541,
            "category": "fx_spot",
            "region": "FX",
            "frequency": "monthly",
            "unit": "usd_per_eur",
            "provider": "ecb",
            "source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            "is_valid": True,
            "is_imputed": False,
            "imputation_method": None,
            "imputation_note": None,
            "imputation_source_window": None,
        }
    ]


def test_fill_series_gaps_inserts_monthly_imputed_row_with_metadata():
    rows = [
        {
            "series_id": "us_cpi_index",
            "observation_date": month,
            "numeric_value": value,
            "category": "inflation",
            "region": "US",
            "frequency": "monthly",
            "unit": "index",
            "provider": "fred",
            "source_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
            "is_valid": True,
            "is_imputed": False,
            "imputation_method": None,
            "imputation_note": None,
            "imputation_source_window": None,
        }
        for month, value in [
            ("2025-01-01", 100.0),
            ("2025-02-01", 101.0),
            ("2025-03-01", 102.0),
            ("2025-04-01", 103.0),
            ("2025-05-01", 104.0),
            ("2025-06-01", 105.0),
            ("2025-08-01", 107.0),
            ("2025-09-01", 108.0),
            ("2025-10-01", 109.0),
            ("2025-11-01", 110.0),
            ("2025-12-01", 111.0),
        ]
    ]

    filled = fill_series_gaps(rows)
    july_row = next(row for row in filled if row["observation_date"] == "2025-07-01")

    assert july_row["is_imputed"] is True
    assert july_row["imputation_method"] == "median_pm_6_periods"
    assert july_row["imputation_note"] == "Filled using +/- 6 month median assumption."

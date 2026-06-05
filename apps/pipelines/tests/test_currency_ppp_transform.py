from src.lib.pipeline.transforms.currency_ppp import build_currency_ppp_outputs


def test_build_currency_ppp_outputs_creates_paths_and_snapshots_for_all_base_months():
    staging_rows = [
        {
            "series_id": "eurusd_spot_monthly",
            "observation_date": "2026-01-01",
            "numeric_value": 1.1,
            "category": "fx_spot",
            "region": "FX",
            "frequency": "monthly",
            "unit": "usd_per_eur",
            "provider": "ecb",
            "source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            "is_valid": True,
        },
        {
            "series_id": "eurusd_spot_monthly",
            "observation_date": "2026-02-01",
            "numeric_value": 1.2,
            "category": "fx_spot",
            "region": "FX",
            "frequency": "monthly",
            "unit": "usd_per_eur",
            "provider": "ecb",
            "source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            "is_valid": True,
        },
        {
            "series_id": "us_cpi_index",
            "observation_date": "2026-01-01",
            "numeric_value": 100.0,
            "category": "inflation",
            "region": "US",
            "frequency": "monthly",
            "unit": "index",
            "provider": "fred",
            "source_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
            "is_valid": True,
        },
        {
            "series_id": "us_cpi_index",
            "observation_date": "2026-02-01",
            "numeric_value": 102.0,
            "category": "inflation",
            "region": "US",
            "frequency": "monthly",
            "unit": "index",
            "provider": "fred",
            "source_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
            "is_valid": True,
        },
        {
            "series_id": "ea_cpi_index",
            "observation_date": "2026-01-01",
            "numeric_value": 100.0,
            "category": "inflation",
            "region": "EU",
            "frequency": "monthly",
            "unit": "index",
            "provider": "fred",
            "source_url": "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
            "is_valid": True,
        },
        {
            "series_id": "ea_cpi_index",
            "observation_date": "2026-02-01",
            "numeric_value": 101.0,
            "category": "inflation",
            "region": "EU",
            "frequency": "monthly",
            "unit": "index",
            "provider": "fred",
            "source_url": "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
            "is_valid": True,
        },
    ]

    outputs = build_currency_ppp_outputs(staging_rows)

    assert outputs["availability_rows"] == [
        {
            "pair_key": "eurusd",
            "section_key": "ppp",
            "item_key": "relative_ppp",
            "status": "available",
            "detail": "PPP snapshots and paths available.",
            "as_of_date": "2026-02-01",
        }
    ]
    assert outputs["snapshot_rows"] == [
        {
            "pair_key": "eurusd",
            "base_month": "2026-01-01",
            "as_of_month": "2026-02-01",
            "base_spot": 1.1,
            "current_spot": 1.2,
            "implied_ppp": 1.1109,
                "deviation_pct": 8.02,
            "spot_series_key": "eurusd_spot_monthly",
            "spot_source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            "us_cpi_series_key": "us_cpi_index",
            "us_cpi_source_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
            "ea_cpi_series_key": "ea_cpi_index",
            "ea_cpi_source_url": "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
        },
        {
            "pair_key": "eurusd",
            "base_month": "2026-02-01",
            "as_of_month": "2026-02-01",
            "base_spot": 1.2,
            "current_spot": 1.2,
            "implied_ppp": 1.2,
            "deviation_pct": 0.0,
            "spot_series_key": "eurusd_spot_monthly",
            "spot_source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            "us_cpi_series_key": "us_cpi_index",
            "us_cpi_source_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
            "ea_cpi_series_key": "ea_cpi_index",
            "ea_cpi_source_url": "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
        },
    ]
    assert outputs["path_rows"] == [
        {
            "pair_key": "eurusd",
            "base_month": "2026-01-01",
            "observation_month": "2026-01-01",
            "actual_spot": 1.1,
            "implied_ppp": 1.1,
        },
        {
            "pair_key": "eurusd",
            "base_month": "2026-01-01",
            "observation_month": "2026-02-01",
            "actual_spot": 1.2,
            "implied_ppp": 1.1109,
        },
        {
            "pair_key": "eurusd",
            "base_month": "2026-02-01",
            "observation_month": "2026-02-01",
            "actual_spot": 1.2,
            "implied_ppp": 1.2,
        },
    ]


def test_build_currency_ppp_outputs_marks_series_unavailable_when_required_inputs_are_missing():
    outputs = build_currency_ppp_outputs([])

    assert outputs["snapshot_rows"] == []
    assert outputs["path_rows"] == []
    assert outputs["availability_rows"] == [
        {
            "pair_key": "eurusd",
            "section_key": "ppp",
            "item_key": "relative_ppp",
            "status": "unavailable",
            "detail": "Required spot or CPI index inputs are unavailable.",
            "as_of_date": None,
        }
    ]

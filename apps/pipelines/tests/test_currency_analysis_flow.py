from src.flows.currency_analysis_flow import run_currency_analysis_flow
from src.lib.source.types import FetchResult, Observation, StandardizedSeries


def _build_series(
    *,
    key: str,
    category: str,
    region: str,
    frequency: str,
    unit: str,
    provider: str,
    series_id: str,
    source_url: str,
    observations: list[tuple[str, str]],
):
    return StandardizedSeries(
        key=key,
        category=category,
        provider=provider,
        series_id=series_id,
        label=key,
        region=region,
        frequency=frequency,
        unit=unit,
        source_url=source_url,
        observations=[Observation(date=observed_at, value=value) for observed_at, value in observations],
    )


def test_run_currency_analysis_flow_reports_success_and_writes_checkpoints(monkeypatch):
    fetch_results = [
        FetchResult.success(
            _build_series(
                key="eurusd_spot_monthly",
                category="fx_spot",
                region="FX",
                frequency="monthly",
                unit="usd_per_eur",
                provider="ecb",
                series_id="EXR.M.USD.EUR.SP00.A",
                source_url="https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
                observations=[("2026-01", "1.10"), ("2026-02", "1.20")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="eurusd_spot_daily",
                category="fx_spot",
                region="FX",
                frequency="daily",
                unit="usd_per_eur",
                provider="ecb",
                series_id="EXR.D.USD.EUR.SP00.A",
                source_url="https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
                observations=[("2026-05-30", "1.14")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="us_cpi_index",
                category="inflation",
                region="US",
                frequency="monthly",
                unit="index",
                provider="fred",
                series_id="CPIAUCSL",
                source_url="https://fred.stlouisfed.org/series/CPIAUCSL",
                observations=[("2026-01", "100.0"), ("2026-02", "102.0")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="ea_cpi_index",
                category="inflation",
                region="EU",
                frequency="monthly",
                unit="index",
                provider="fred",
                series_id="CP00MI15EA20M086NEST",
                source_url="https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
                observations=[("2026-01", "100.0"), ("2026-02", "101.0")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="eur_3m_rate",
                category="market_rate",
                region="EU",
                frequency="daily",
                unit="percent",
                provider="ecb",
                series_id="EST.B.EU000A2QQF32.CR",
                source_url="https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR",
                observations=[("2026-05-30", "2.0")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="eur_6m_rate",
                category="market_rate",
                region="EU",
                frequency="daily",
                unit="percent",
                provider="ecb",
                series_id="EST.B.EU000A2QQF40.CR",
                source_url="https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF40.CR",
                observations=[("2026-05-30", "2.1")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="eur_12m_rate",
                category="market_rate",
                region="EU",
                frequency="daily",
                unit="percent",
                provider="ecb",
                series_id="EST.B.EU000A2QQF57.CR",
                source_url="https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF57.CR",
                observations=[("2026-05-30", "2.2")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="usd_3m_rate",
                category="market_rate",
                region="US",
                frequency="daily",
                unit="percent",
                provider="fred",
                series_id="DTB3",
                source_url="https://fred.stlouisfed.org/series/DTB3",
                observations=[("2026-05-30", "4.0")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="usd_6m_rate",
                category="market_rate",
                region="US",
                frequency="daily",
                unit="percent",
                provider="fred",
                series_id="DTB6",
                source_url="https://fred.stlouisfed.org/series/DTB6",
                observations=[("2026-05-30", "4.1")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="usd_12m_rate",
                category="market_rate",
                region="US",
                frequency="daily",
                unit="percent",
                provider="fred",
                series_id="DTB1YR",
                source_url="https://fred.stlouisfed.org/series/DTB1YR",
                observations=[("2026-05-30", "4.2")],
            )
        ),
    ]

    written_checkpoints = []

    monkeypatch.setattr("src.flows.currency_analysis_flow.get_connection", lambda: None)
    monkeypatch.setattr("src.tasks.run_currency_market_etl.run_currency_market_etl", lambda connection=None: fetch_results)
    monkeypatch.setattr(
        "src.tasks.load_currency_analysis_layers.write_successful_checkpoint",
        lambda _connection, series_id, last_successful_observation_date, last_run_at: written_checkpoints.append(
            (series_id, last_successful_observation_date)
        ),
    )

    result = run_currency_analysis_flow()

    assert result["status"] == "success"
    assert result["series_fetched"] == 10
    assert result["ppp_snapshot_rows"] == 2
    assert result["ppp_path_rows"] == 4
    assert result["irp_snapshot_rows"] == 3
    assert result["availability_rows"] == 4
    assert ("eurusd_spot_monthly", "2026-02-01") in written_checkpoints
    assert ("eurusd_spot_daily", "2026-05-30") in written_checkpoints


def test_run_currency_analysis_flow_handles_required_input_failure_without_checkpoint_write(monkeypatch):
    failure = FetchResult.failure(
        provider="ecb",
        key="eurusd_spot_monthly",
        external_series_id="EXR.M.USD.EUR.SP00.A",
        error_type="fetch_error",
        message="boom",
    )
    written_checkpoints = []

    monkeypatch.setattr("src.flows.currency_analysis_flow.get_connection", lambda: None)
    monkeypatch.setattr("src.tasks.run_currency_market_etl.run_currency_market_etl", lambda connection=None: [failure])
    monkeypatch.setattr(
        "src.tasks.load_currency_analysis_layers.write_successful_checkpoint",
        lambda _connection, series_id, last_successful_observation_date, last_run_at: written_checkpoints.append(
            (series_id, last_successful_observation_date)
        ),
    )

    result = run_currency_analysis_flow()

    assert result["status"] == "failed"
    assert result["errors"] == ["eurusd_spot_monthly: boom"]
    assert written_checkpoints == []


def test_run_currency_analysis_flow_tolerates_optional_irp_fetch_failures_when_ppp_still_builds(monkeypatch):
    fetch_results = [
        FetchResult.success(
            _build_series(
                key="eurusd_spot_monthly",
                category="fx_spot",
                region="FX",
                frequency="monthly",
                unit="usd_per_eur",
                provider="ecb",
                series_id="EXR.M.USD.EUR.SP00.A",
                source_url="https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
                observations=[("2026-01", "1.10"), ("2026-02", "1.20")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="eurusd_spot_daily",
                category="fx_spot",
                region="FX",
                frequency="daily",
                unit="usd_per_eur",
                provider="ecb",
                series_id="EXR.D.USD.EUR.SP00.A",
                source_url="https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
                observations=[("2026-05-30", "1.14")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="us_cpi_index",
                category="inflation",
                region="US",
                frequency="monthly",
                unit="index",
                provider="fred",
                series_id="CPIAUCSL",
                source_url="https://fred.stlouisfed.org/series/CPIAUCSL",
                observations=[("2026-01", "100.0"), ("2026-02", "102.0")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="ea_cpi_index",
                category="inflation",
                region="EU",
                frequency="monthly",
                unit="index",
                provider="fred",
                series_id="CP00MI15EA20M086NEST",
                source_url="https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
                observations=[("2026-01", "100.0"), ("2026-02", "101.0")],
            )
        ),
        FetchResult.failure(
            provider="ecb",
            key="eur_3m_rate",
            external_series_id="EST.B.EU000A2QQF32.CR",
            error_type="fetch_error",
            message="blocked",
        ),
        FetchResult.failure(
            provider="ecb",
            key="eur_6m_rate",
            external_series_id="EST.B.EU000A2QQF40.CR",
            error_type="fetch_error",
            message="blocked",
        ),
        FetchResult.failure(
            provider="ecb",
            key="eur_12m_rate",
            external_series_id="EST.B.EU000A2QQF57.CR",
            error_type="fetch_error",
            message="blocked",
        ),
        FetchResult.success(
            _build_series(
                key="usd_3m_rate",
                category="market_rate",
                region="US",
                frequency="daily",
                unit="percent",
                provider="fred",
                series_id="DTB3",
                source_url="https://fred.stlouisfed.org/series/DTB3",
                observations=[("2026-05-30", "4.0")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="usd_6m_rate",
                category="market_rate",
                region="US",
                frequency="daily",
                unit="percent",
                provider="fred",
                series_id="DTB6",
                source_url="https://fred.stlouisfed.org/series/DTB6",
                observations=[("2026-05-30", "4.1")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="usd_12m_rate",
                category="market_rate",
                region="US",
                frequency="daily",
                unit="percent",
                provider="fred",
                series_id="DTB1YR",
                source_url="https://fred.stlouisfed.org/series/DTB1YR",
                observations=[("2026-05-30", "4.2")],
            )
        ),
    ]

    written_checkpoints = []

    monkeypatch.setattr("src.flows.currency_analysis_flow.get_connection", lambda: None)
    monkeypatch.setattr("src.tasks.run_currency_market_etl.run_currency_market_etl", lambda connection=None: fetch_results)
    monkeypatch.setattr(
        "src.tasks.load_currency_analysis_layers.write_successful_checkpoint",
        lambda _connection, series_id, last_successful_observation_date, last_run_at: written_checkpoints.append(
            (series_id, last_successful_observation_date)
        ),
    )

    result = run_currency_analysis_flow()

    assert result["status"] == "success"
    assert result["ppp_snapshot_rows"] == 2
    assert result["irp_snapshot_rows"] == 0
    assert result["availability_rows"] == 4
    assert result["fetch_errors"] == [
        "eur_3m_rate: blocked",
        "eur_6m_rate: blocked",
        "eur_12m_rate: blocked",
    ]
    assert ("eur_3m_rate", "2026-05-30") not in written_checkpoints


def test_run_currency_analysis_flow_uses_historical_staging_rows_for_ppp_base_years(monkeypatch):
    fetch_results = [
        FetchResult.success(
            _build_series(
                key="eurusd_spot_monthly",
                category="fx_spot",
                region="FX",
                frequency="monthly",
                unit="usd_per_eur",
                provider="ecb",
                series_id="EXR.M.USD.EUR.SP00.A",
                source_url="https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
                observations=[("2026-01", "1.30"), ("2026-02", "1.40")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="eurusd_spot_daily",
                category="fx_spot",
                region="FX",
                frequency="daily",
                unit="usd_per_eur",
                provider="ecb",
                series_id="EXR.D.USD.EUR.SP00.A",
                source_url="https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
                observations=[("2026-05-30", "1.14")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="us_cpi_index",
                category="inflation",
                region="US",
                frequency="monthly",
                unit="index",
                provider="fred",
                series_id="CPIAUCSL",
                source_url="https://fred.stlouisfed.org/series/CPIAUCSL",
                observations=[("2026-01", "104.0"), ("2026-02", "106.0")],
            )
        ),
        FetchResult.success(
            _build_series(
                key="ea_cpi_index",
                category="inflation",
                region="EU",
                frequency="monthly",
                unit="index",
                provider="fred",
                series_id="CP00MI15EA20M086NEST",
                source_url="https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
                observations=[("2026-01", "102.0"), ("2026-02", "103.0")],
            )
        ),
    ]

    historical_staging_rows = [
        {
            "series_id": "eurusd_spot_monthly",
            "observation_date": "2025-01-01",
            "numeric_value": 1.0,
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
        },
        {
            "series_id": "eurusd_spot_monthly",
            "observation_date": "2025-02-01",
            "numeric_value": 1.2,
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
        },
        {
            "series_id": "us_cpi_index",
            "observation_date": "2025-01-01",
            "numeric_value": 100.0,
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
        },
        {
            "series_id": "us_cpi_index",
            "observation_date": "2025-02-01",
            "numeric_value": 102.0,
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
        },
        {
            "series_id": "ea_cpi_index",
            "observation_date": "2025-01-01",
            "numeric_value": 100.0,
            "category": "inflation",
            "region": "EU",
            "frequency": "monthly",
            "unit": "index",
            "provider": "fred",
            "source_url": "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
            "is_valid": True,
            "is_imputed": False,
            "imputation_method": None,
            "imputation_note": None,
            "imputation_source_window": None,
        },
        {
            "series_id": "ea_cpi_index",
            "observation_date": "2025-02-01",
            "numeric_value": 101.0,
            "category": "inflation",
            "region": "EU",
            "frequency": "monthly",
            "unit": "index",
            "provider": "fred",
            "source_url": "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
            "is_valid": True,
            "is_imputed": False,
            "imputation_method": None,
            "imputation_note": None,
            "imputation_source_window": None,
        },
    ]

    captured = {}

    monkeypatch.setattr("src.flows.currency_analysis_flow.get_connection", lambda: object())
    monkeypatch.setattr("src.flows.currency_analysis_flow.bootstrap_taylor_rule_schema", lambda _connection: None)
    monkeypatch.setattr("src.tasks.run_currency_market_etl.run_currency_market_etl", lambda connection=None: fetch_results)
    monkeypatch.setattr(
        "src.flows.currency_analysis_flow.read_staging_rows_for_series",
        lambda _connection, _series_ids: historical_staging_rows,
        raising=False,
    )
    monkeypatch.setattr(
        "src.tasks.load_currency_analysis_layers.load_currency_analysis_layers",
        lambda connection, **kwargs: captured.setdefault("ppp_snapshot_rows", kwargs["ppp_snapshot_rows"]) or {},
    )

    result = run_currency_analysis_flow()

    assert result["status"] == "success"
    assert result["ppp_snapshot_rows"] == 4
    assert len(captured["ppp_snapshot_rows"]) == 4

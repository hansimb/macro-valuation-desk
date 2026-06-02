from src.flows.taylor_rule_flow import run_taylor_rule_flow
from src.lib.source.types import FetchResult, Observation, StandardizedSeries


def _build_series(key: str, region: str, provider: str, series_id: str, source_url: str, value: str):
    return StandardizedSeries(
        key=key,
        category="policy_rate" if "policy" in key else "inflation",
        provider=provider,
        series_id=series_id,
        label=key,
        region=region,
        frequency="daily" if "policy" in key else "monthly",
        unit="percent" if "policy" in key else "percentage_change",
        source_url=source_url,
        observations=[Observation(date="2026-05-01", value=value)],
    )


def test_run_taylor_rule_flow_updates_checkpoints_on_success(monkeypatch):
    fetched_series = {
        "us_policy_rate": FetchResult.success(
            _build_series(
                "us_policy_rate",
                "US",
                "fred",
                "DFEDTARU",
                "https://fred.stlouisfed.org/series/DFEDTARU",
                "4.50",
            )
        ),
        "us_cpi_headline": FetchResult.success(
            _build_series(
                "us_cpi_headline",
                "US",
                "fred",
                "CPIAUCSL",
                "https://fred.stlouisfed.org/series/CPIAUCSL",
                "2.90",
            )
        ),
        "eu_policy_rate": FetchResult.success(
            _build_series(
                "eu_policy_rate",
                "EU",
                "ecb",
                "FM.D.U2.EUR.4F.KR.DFR.LEV",
                "https://data.ecb.europa.eu/data/datasets/FM/FM.D.U2.EUR.4F.KR.DFR.LEV",
                "2.25",
            )
        ),
        "eu_hicp_headline": FetchResult.success(
            _build_series(
                "eu_hicp_headline",
                "EU",
                "ecb",
                "HICP.M.U2.N.000000.4D0.ANR",
                "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR",
                "2.10",
            )
        ),
    }

    written_checkpoints = []

    monkeypatch.setattr("src.flows.taylor_rule_flow.get_connection", lambda: None)
    monkeypatch.setattr("src.tasks.run_us_macro_core_etl.run_us_macro_core_etl", lambda: [fetched_series["us_policy_rate"], fetched_series["us_cpi_headline"]])
    monkeypatch.setattr("src.tasks.run_eu_macro_core_etl.run_eu_macro_core_etl", lambda: [fetched_series["eu_policy_rate"], fetched_series["eu_hicp_headline"]])
    monkeypatch.setattr(
        "src.tasks.load_taylor_layers.write_successful_checkpoint",
        lambda _connection, series_id, last_successful_observation_date, last_run_at: written_checkpoints.append(
            (series_id, last_successful_observation_date)
        ),
    )

    result = run_taylor_rule_flow()

    assert result["status"] == "success"
    assert result["series_fetched"] == 4
    assert result["mart_rows"] == 2
    assert sorted(written_checkpoints) == [
        ("eu_hicp_headline", "2026-05-01"),
        ("eu_policy_rate", "2026-05-01"),
        ("us_cpi_headline", "2026-05-01"),
        ("us_policy_rate", "2026-05-01"),
    ]


def test_run_taylor_rule_flow_handles_adapter_failure_without_checkpoint_write(monkeypatch):
    failure = FetchResult.failure(
        provider="fred",
        key="us_policy_rate",
        external_series_id="DFEDTARU",
        error_type="fetch_error",
        message="boom",
    )

    written_checkpoints = []

    monkeypatch.setattr("src.flows.taylor_rule_flow.get_connection", lambda: None)
    monkeypatch.setattr("src.tasks.run_us_macro_core_etl.run_us_macro_core_etl", lambda: [failure])
    monkeypatch.setattr("src.tasks.run_eu_macro_core_etl.run_eu_macro_core_etl", lambda: [])
    monkeypatch.setattr(
        "src.tasks.load_taylor_layers.write_successful_checkpoint",
        lambda _connection, series_id, last_successful_observation_date, last_run_at: written_checkpoints.append(
            (series_id, last_successful_observation_date)
        ),
    )

    result = run_taylor_rule_flow()

    assert result["status"] == "failed"
    assert result["errors"] == ["us_policy_rate: boom"]
    assert written_checkpoints == []

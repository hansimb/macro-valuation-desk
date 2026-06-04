from src.flows.taylor_rule_flow import run_taylor_rule_flow
from src.lib.source.types import FetchResult, Observation, StandardizedSeries


def _build_series(key: str, region: str, provider: str, series_id: str, source_url: str, value: str):
    if "policy" in key:
        category = "policy_rate"
        frequency = "daily"
        unit = "percent"
    elif "market_real_rate" in key:
        category = "market_rate"
        frequency = "monthly"
        unit = "percent"
    elif "output_gap" in key:
        category = "output_gap"
        frequency = "monthly"
        unit = "ratio_to_trend_index"
    elif "real_gdp" in key:
        category = "growth"
        frequency = "quarterly"
        unit = "level"
    else:
        category = "inflation"
        frequency = "monthly"
        unit = "index" if key.startswith("us_cpi") else "percentage_change"

    observations = [Observation(date="2026-05-01", value=value)]
    if key == "us_cpi_headline":
        observations = [
            Observation(date="2025-04-01", value="100.0"),
            Observation(date="2026-04-01", value=value),
        ]
    elif key == "us_cpi_core":
        observations = [
            Observation(date="2025-04-01", value="200.0"),
            Observation(date="2026-04-01", value=value),
        ]
    elif key in {"us_real_gdp", "eu_real_gdp"}:
        observations = [
            Observation(date="2025-01-01", value="100.0"),
            Observation(date="2025-04-01", value="101.0"),
            Observation(date="2025-07-01", value="102.01"),
            Observation(date="2025-10-01", value="103.03"),
            Observation(date="2026-01-01", value=value),
        ]
    elif key in {
        "us_market_real_rate",
        "eu_market_real_rate",
        "eu_hicp_headline",
        "eu_hicp_core",
        "us_policy_rate",
        "eu_policy_rate",
        "us_output_gap",
        "eu_output_gap",
    }:
        observations = [Observation(date="2026-04-01", value=value)]

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
        observations=observations,
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
                "103.00",
            )
        ),
        "us_cpi_core": FetchResult.success(
            _build_series(
                "us_cpi_core",
                "US",
                "fred",
                "CPILFESL",
                "https://fred.stlouisfed.org/series/CPILFESL",
                "206.00",
            )
        ),
        "us_market_real_rate": FetchResult.success(
            _build_series(
                "us_market_real_rate",
                "US",
                "ecb",
                "FM.M.US.USD.4F.BB.R_US10YT_RR.YLDA",
                "https://data.ecb.europa.eu/data/datasets/FM/FM.M.US.USD.4F.BB.R_US10YT_RR.YLDA",
                "2.10",
            )
        ),
        "us_real_gdp": FetchResult.success(
            _build_series(
                "us_real_gdp",
                "US",
                "fred",
                "GDPC1",
                "https://fred.stlouisfed.org/series/GDPC1",
                "104.06",
            )
        ),
        "us_output_gap": FetchResult.success(
            _build_series(
                "us_output_gap",
                "US",
                "fred",
                "USALORSGPRTSTSAM",
                "https://fred.stlouisfed.org/series/USALORSGPRTSTSAM",
                "100.80",
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
        "eu_hicp_core": FetchResult.success(
            _build_series(
                "eu_hicp_core",
                "EU",
                "ecb",
                "HICP.M.U2.N.XEFUN0.4D0.ANR",
                "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.XEFUN0.4D0.ANR",
                "2.30",
            )
        ),
        "eu_market_real_rate": FetchResult.success(
            _build_series(
                "eu_market_real_rate",
                "EU",
                "ecb",
                "FM.M.U2.EUR.4F.BB.R_U2_10Y.YLDA",
                "https://data.ecb.europa.eu/data/datasets/FM/FM.M.U2.EUR.4F.BB.R_U2_10Y.YLDA",
                "0.46",
            )
        ),
        "eu_real_gdp": FetchResult.success(
            _build_series(
                "eu_real_gdp",
                "EU",
                "ecb",
                "MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
                "https://data.ecb.europa.eu/data/datasets/MNA/MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
                "104.06",
            )
        ),
        "eu_output_gap": FetchResult.success(
            _build_series(
                "eu_output_gap",
                "EU",
                "fred",
                "EA19LORSGPRTSTSAM",
                "https://fred.stlouisfed.org/series/EA19LORSGPRTSTSAM",
                "99.40",
            )
        ),
    }

    written_checkpoints = []

    monkeypatch.setattr("src.flows.taylor_rule_flow.get_connection", lambda: None)
    monkeypatch.setattr("src.tasks.run_us_macro_core_etl.run_us_macro_core_etl", lambda: [
        fetched_series["us_policy_rate"],
        fetched_series["us_cpi_headline"],
        fetched_series["us_cpi_core"],
        fetched_series["us_market_real_rate"],
        fetched_series["us_real_gdp"],
        fetched_series["us_output_gap"],
    ])
    monkeypatch.setattr("src.tasks.run_eu_macro_core_etl.run_eu_macro_core_etl", lambda: [
        fetched_series["eu_policy_rate"],
        fetched_series["eu_hicp_headline"],
        fetched_series["eu_hicp_core"],
        fetched_series["eu_market_real_rate"],
        fetched_series["eu_real_gdp"],
        fetched_series["eu_output_gap"],
    ])
    monkeypatch.setattr(
        "src.tasks.load_taylor_layers.write_successful_checkpoint",
        lambda _connection, series_id, last_successful_observation_date, last_run_at: written_checkpoints.append(
            (series_id, last_successful_observation_date)
        ),
    )

    result = run_taylor_rule_flow()

    assert result["status"] == "success"
    assert result["series_fetched"] == 12
    assert result["mart_rows"] == 2
    assert sorted(written_checkpoints) == [
        ("eu_hicp_core", "2026-04-01"),
        ("eu_hicp_headline", "2026-04-01"),
        ("eu_market_real_rate", "2026-04-01"),
        ("eu_output_gap", "2026-04-01"),
        ("eu_policy_rate", "2026-04-01"),
        ("eu_real_gdp", "2026-01-01"),
        ("us_cpi_core", "2026-04-01"),
        ("us_cpi_headline", "2026-04-01"),
        ("us_market_real_rate", "2026-04-01"),
        ("us_output_gap", "2026-04-01"),
        ("us_policy_rate", "2026-04-01"),
        ("us_real_gdp", "2026-01-01"),
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


def test_run_taylor_rule_flow_bootstraps_schema_before_checkpoint_reads(monkeypatch):
    calls: list[str] = []
    fake_connection = object()

    monkeypatch.setattr("src.flows.taylor_rule_flow.get_connection", lambda: fake_connection)
    monkeypatch.setattr(
        "src.flows.taylor_rule_flow.bootstrap_taylor_rule_schema",
        lambda connection: calls.append(f"bootstrap:{connection is fake_connection}"),
    )
    monkeypatch.setattr(
        "src.tasks.run_us_macro_core_etl.run_us_macro_core_etl",
        lambda connection=None: calls.append(f"us:{connection is fake_connection}") or [],
    )
    monkeypatch.setattr(
        "src.tasks.run_eu_macro_core_etl.run_eu_macro_core_etl",
        lambda connection=None: calls.append(f"eu:{connection is fake_connection}") or [],
    )
    monkeypatch.setattr(
        "src.tasks.load_taylor_layers.load_taylor_layers",
        lambda connection, **kwargs: {"mart_rows": len(kwargs["mart_rows"])},
    )
    monkeypatch.setattr("src.flows.taylor_rule_flow.build_taylor_rule_inputs", lambda staging_rows: [])
    monkeypatch.setattr("src.flows.taylor_rule_flow.build_macro_reference_metrics", lambda staging_rows: [])

    result = run_taylor_rule_flow()

    assert calls == ["bootstrap:True", "us:True", "eu:True"]
    assert result["status"] == "success"

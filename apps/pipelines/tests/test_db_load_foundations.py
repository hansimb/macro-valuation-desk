from __future__ import annotations

from datetime import date

from psycopg.rows import dict_row

from src.lib.db import (
    bootstrap_taylor_rule_schema,
    get_connection,
    replace_currency_data_availability,
    replace_currency_irp_snapshots,
    replace_currency_ppp_paths,
    replace_currency_ppp_snapshots,
    replace_taylor_rule_inputs,
    upsert_raw_observations,
    upsert_series_metadata,
    upsert_staging_observations,
)
from src.lib.pipeline.checkpoints import (
    build_fetch_options_for_series,
    build_fetch_options_from_checkpoint,
    read_latest_checkpoint,
    record_pipeline_run,
    write_successful_checkpoint,
)
from src.lib.source.registry import get_series_definition


class FakeCursor:
    def __init__(self, fetchone_result=None):
        self.commands: list[tuple[str, object | None]] = []
        self.fetchone_result = fetchone_result

    def execute(self, query, params=None):
        self.commands.append((str(query), params))

    def executemany(self, query, params_seq):
        self.commands.append((str(query), list(params_seq)))

    def fetchone(self):
        return self.fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, fetchone_result=None):
        self.cursor_instance = FakeCursor(fetchone_result=fetchone_result)
        self.commit_count = 0

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commit_count += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_connection_uses_dict_row_factory(monkeypatch):
    captured_kwargs = {}

    def fake_connect(connection_string, **kwargs):
        captured_kwargs["connection_string"] = connection_string
        captured_kwargs.update(kwargs)
        return object()

    monkeypatch.setattr("src.lib.db.get_database_url", lambda: "postgresql://example")
    monkeypatch.setattr("src.lib.db.psycopg.connect", fake_connect)

    connection = get_connection()

    assert connection is not None
    assert captured_kwargs["connection_string"] == "postgresql://example"
    assert captured_kwargs["row_factory"] is dict_row


def test_bootstrap_taylor_rule_schema_creates_required_schemas_and_tables():
    connection = FakeConnection()

    bootstrap_taylor_rule_schema(connection)

    executed_sql = "\n".join(command for command, _ in connection.cursor_instance.commands)

    assert "create schema if not exists core" in executed_sql.lower()
    assert "create schema if not exists etl" in executed_sql.lower()
    assert "create schema if not exists raw" in executed_sql.lower()
    assert "create schema if not exists staging" in executed_sql.lower()
    assert "create schema if not exists mart" in executed_sql.lower()
    assert "create table if not exists core.series_metadata" in executed_sql.lower()
    assert "create table if not exists etl.series_checkpoints" in executed_sql.lower()
    assert "create table if not exists etl.pipeline_runs" in executed_sql.lower()
    assert "create table if not exists raw.series_observations" in executed_sql.lower()
    assert "create table if not exists staging.series_observations" in executed_sql.lower()
    assert "create table if not exists mart.taylor_rule_inputs" in executed_sql.lower()
    assert "create table if not exists mart.currency_ppp_snapshots" in executed_sql.lower()
    assert "create table if not exists mart.currency_ppp_paths" in executed_sql.lower()
    assert "create table if not exists mart.currency_irp_snapshots" in executed_sql.lower()
    assert "create table if not exists mart.currency_data_availability" in executed_sql.lower()


def test_upsert_helpers_write_expected_row_shapes():
    connection = FakeConnection()
    definition = get_series_definition("us_policy_rate")

    upsert_series_metadata(connection, [definition])
    upsert_raw_observations(
        connection,
        [
            {
                "series_id": "us_policy_rate",
                "observation_date": "2026-05-01",
                "value": "4.50",
                "fetched_at": "2026-05-02T12:00:00Z",
            }
        ],
    )
    upsert_staging_observations(
        connection,
        [
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
            }
        ],
    )
    replace_taylor_rule_inputs(
        connection,
        [
            {
                "region": "US",
                "as_of_date": "2026-05-01",
                "policy_rate": 4.5,
                "inflation": 2.9,
                "inflation_target": 2.0,
                "neutral_rate": 1.0,
                "slack_proxy": 0.0,
                "implied_rate": 4.35,
                "policy_gap": 0.15,
                "policy_series_key": "us_policy_rate",
                "policy_source_url": "https://fred.stlouisfed.org/series/DFEDTARU",
                "inflation_series_key": "us_cpi_headline",
                "inflation_source_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
                "slack_source_note": "Assumed neutral slack proxy in v1",
            }
        ],
    )
    replace_currency_ppp_snapshots(
        connection,
        [
            {
                "pair_key": "eurusd",
                "base_month": "2020-01-01",
                "as_of_month": "2026-04-01",
                "base_spot": 1.1111,
                "current_spot": 1.145,
                "implied_ppp": 1.0825,
                "deviation_pct": 5.78,
                "spot_series_key": "eurusd_spot_monthly",
                "spot_source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
                "us_cpi_series_key": "us_cpi_index",
                "us_cpi_source_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
                "ea_cpi_series_key": "ea_cpi_index",
                "ea_cpi_source_url": "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
            }
        ],
    )
    replace_currency_ppp_paths(
        connection,
        [
            {
                "pair_key": "eurusd",
                "base_month": "2020-01-01",
                "observation_month": "2020-02-01",
                "actual_spot": 1.103,
                "implied_ppp": 1.109,
            }
        ],
    )
    replace_currency_irp_snapshots(
        connection,
        [
            {
                "pair_key": "eurusd",
                "as_of_date": "2026-05-30",
                "tenor": "3M",
                "spot": 1.142,
                "eur_rate": 1.94,
                "usd_rate": 3.57,
                "rate_spread": -1.63,
                "cip_implied_forward": 1.1373,
                "observed_forward": None,
                "cip_basis_bps": None,
                "uip_implied_move_pct": -1.63,
                "uip_implied_spot": 1.1234,
                "spot_series_key": "eurusd_spot_daily",
                "spot_source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
                "eur_rate_series_key": "eur_3m_rate",
                "eur_rate_source_url": "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR",
                "usd_rate_series_key": "usd_3m_rate",
                "usd_rate_source_url": "https://fred.stlouisfed.org/series/DTB3",
                "forward_series_key": None,
                "forward_source_url": None,
                "has_observed_forward": False,
            }
        ],
    )
    replace_currency_data_availability(
        connection,
        [
            {
                "pair_key": "eurusd",
                "section_key": "irp",
                "item_key": "3M",
                "status": "partial",
                "detail": "Observed forward unavailable; CIP-only comparison returned.",
                "as_of_date": "2026-05-30",
            }
        ],
    )

    commands = connection.cursor_instance.commands
    assert any("insert into core.series_metadata" in query.lower() for query, _ in commands)
    assert any("insert into raw.series_observations" in query.lower() for query, _ in commands)
    assert any("insert into staging.series_observations" in query.lower() for query, _ in commands)
    assert any("insert into mart.taylor_rule_inputs" in query.lower() for query, _ in commands)
    assert any("delete from mart.taylor_rule_inputs" in query.lower() for query, _ in commands)
    assert any("insert into mart.currency_ppp_snapshots" in query.lower() for query, _ in commands)
    assert any("delete from mart.currency_ppp_snapshots" in query.lower() for query, _ in commands)
    assert any("insert into mart.currency_ppp_paths" in query.lower() for query, _ in commands)
    assert any("delete from mart.currency_ppp_paths" in query.lower() for query, _ in commands)
    assert any("insert into mart.currency_irp_snapshots" in query.lower() for query, _ in commands)
    assert any("delete from mart.currency_irp_snapshots" in query.lower() for query, _ in commands)
    assert any("insert into mart.currency_data_availability" in query.lower() for query, _ in commands)
    assert any("delete from mart.currency_data_availability" in query.lower() for query, _ in commands)
    assert connection.commit_count == 8


def test_checkpoint_helpers_read_write_and_build_reprocessing_window():
    read_connection = FakeConnection(fetchone_result={"last_successful_observation_date": "2026-05-20"})

    checkpoint = read_latest_checkpoint(read_connection, "us_policy_rate")
    options = build_fetch_options_from_checkpoint(checkpoint, reprocess_days=30)

    write_connection = FakeConnection()
    write_successful_checkpoint(
        write_connection,
        series_id="us_policy_rate",
        last_successful_observation_date="2026-05-31",
        last_run_at="2026-06-01T12:00:00Z",
    )
    record_pipeline_run(
        write_connection,
        run_id="run-123",
        domain_key="taylor_rule",
        started_at="2026-06-01T12:00:00Z",
        finished_at="2026-06-01T12:05:00Z",
        status="success",
        error_summary=None,
    )

    assert checkpoint == "2026-05-20"
    assert options.start_date == "2026-04-20"
    assert options.end_date is None
    assert any(
        "insert into etl.series_checkpoints" in query.lower()
        for query, _ in write_connection.cursor_instance.commands
    )
    assert any(
        "insert into etl.pipeline_runs" in query.lower()
        for query, _ in write_connection.cursor_instance.commands
    )
    assert write_connection.commit_count == 2


def test_build_fetch_options_from_checkpoint_accepts_date_objects():
    options = build_fetch_options_from_checkpoint(date(2026, 5, 20), reprocess_days=30)

    assert options.start_date == "2026-04-20"
    assert options.end_date is None


def test_build_fetch_options_for_series_uses_analysis_aware_lookbacks():
    inflation_options = build_fetch_options_for_series(
        date(2026, 5, 20),
        get_series_definition("us_cpi_headline"),
    )
    policy_options = build_fetch_options_for_series(
        date(2026, 5, 20),
        get_series_definition("us_policy_rate"),
    )
    gdp_options = build_fetch_options_for_series(
        date(2026, 5, 20),
        get_series_definition("us_real_gdp"),
    )

    assert inflation_options.start_date == "2025-04-15"
    assert policy_options.start_date == "2026-04-20"
    assert gdp_options.start_date is None

from __future__ import annotations

import os
from pathlib import Path

import psycopg

from src.lib.source.types import SeriesDefinition


def get_database_url() -> str | None:
    return os.getenv("DATABASE_URL")


def get_connection():
    database_url = get_database_url()
    if not database_url:
        return None

    return psycopg.connect(database_url)


def _schema_sql() -> str:
    schema_path = Path(__file__).resolve().parents[1] / "sql" / "taylor_rule_schema.sql"
    return schema_path.read_text(encoding="utf-8")


def bootstrap_taylor_rule_schema(connection) -> None:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(_schema_sql())


def upsert_series_metadata(connection, series_definitions: list[SeriesDefinition]) -> None:
    rows = [
        {
            "series_id": definition.key,
            "key": definition.key,
            "category": definition.category,
            "provider": definition.provider,
            "external_series_id": definition.external_series_id,
            "label": definition.label,
            "region": definition.region,
            "frequency": definition.frequency,
            "unit": definition.unit,
            "source_url": definition.source_url,
        }
        for definition in series_definitions
    ]

    with connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                insert into core.series_metadata (
                    series_id,
                    key,
                    category,
                    provider,
                    external_series_id,
                    label,
                    region,
                    frequency,
                    unit,
                    source_url
                )
                values (
                    %(series_id)s,
                    %(key)s,
                    %(category)s,
                    %(provider)s,
                    %(external_series_id)s,
                    %(label)s,
                    %(region)s,
                    %(frequency)s,
                    %(unit)s,
                    %(source_url)s
                )
                on conflict (series_id) do update
                set
                    category = excluded.category,
                    provider = excluded.provider,
                    external_series_id = excluded.external_series_id,
                    label = excluded.label,
                    region = excluded.region,
                    frequency = excluded.frequency,
                    unit = excluded.unit,
                    source_url = excluded.source_url,
                    updated_at = now()
                """,
                rows,
            )


def upsert_raw_observations(connection, rows: list[dict[str, object]]) -> None:
    with connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                insert into raw.series_observations (
                    series_id,
                    observation_date,
                    value,
                    fetched_at
                )
                values (
                    %(series_id)s,
                    %(observation_date)s,
                    %(value)s,
                    %(fetched_at)s
                )
                on conflict (series_id, observation_date) do update
                set
                    value = excluded.value,
                    fetched_at = excluded.fetched_at
                """,
                rows,
            )


def upsert_staging_observations(connection, rows: list[dict[str, object]]) -> None:
    with connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                insert into staging.series_observations (
                    series_id,
                    observation_date,
                    numeric_value,
                    category,
                    region,
                    frequency,
                    unit,
                    provider,
                    is_valid
                )
                values (
                    %(series_id)s,
                    %(observation_date)s,
                    %(numeric_value)s,
                    %(category)s,
                    %(region)s,
                    %(frequency)s,
                    %(unit)s,
                    %(provider)s,
                    %(is_valid)s
                )
                on conflict (series_id, observation_date) do update
                set
                    numeric_value = excluded.numeric_value,
                    category = excluded.category,
                    region = excluded.region,
                    frequency = excluded.frequency,
                    unit = excluded.unit,
                    provider = excluded.provider,
                    is_valid = excluded.is_valid
                """,
                rows,
            )


def replace_taylor_rule_inputs(connection, rows: list[dict[str, object]]) -> None:
    regions = sorted({row["region"] for row in rows})

    with connection:
        with connection.cursor() as cursor:
            if regions:
                cursor.execute(
                    "delete from mart.taylor_rule_inputs where region = any(%(regions)s)",
                    {"regions": regions},
                )
            cursor.executemany(
                """
                insert into mart.taylor_rule_inputs (
                    region,
                    as_of_date,
                    policy_rate,
                    inflation,
                    inflation_target,
                    neutral_rate,
                    slack_proxy,
                    implied_rate,
                    policy_gap,
                    policy_series_key,
                    policy_source_url,
                    inflation_series_key,
                    inflation_source_url,
                    slack_source_note
                )
                values (
                    %(region)s,
                    %(as_of_date)s,
                    %(policy_rate)s,
                    %(inflation)s,
                    %(inflation_target)s,
                    %(neutral_rate)s,
                    %(slack_proxy)s,
                    %(implied_rate)s,
                    %(policy_gap)s,
                    %(policy_series_key)s,
                    %(policy_source_url)s,
                    %(inflation_series_key)s,
                    %(inflation_source_url)s,
                    %(slack_source_note)s
                )
                on conflict (region, as_of_date) do update
                set
                    policy_rate = excluded.policy_rate,
                    inflation = excluded.inflation,
                    inflation_target = excluded.inflation_target,
                    neutral_rate = excluded.neutral_rate,
                    slack_proxy = excluded.slack_proxy,
                    implied_rate = excluded.implied_rate,
                    policy_gap = excluded.policy_gap,
                    policy_series_key = excluded.policy_series_key,
                    policy_source_url = excluded.policy_source_url,
                    inflation_series_key = excluded.inflation_series_key,
                    inflation_source_url = excluded.inflation_source_url,
                    slack_source_note = excluded.slack_source_note
                """,
                rows,
            )

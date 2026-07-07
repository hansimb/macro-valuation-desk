from __future__ import annotations

from pathlib import Path

from src.lib.source.types import SeriesDefinition

SCHEMA_FILE_NAMES = [
    "001_core.sql",
    "002_etl.sql",
    "010_macro.sql",
    "020_currency.sql",
    "030_equity_market_valuation.sql",
]

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "sql" / "schema"


def _schema_sql() -> str:
    return "\n\n".join((SCHEMA_DIR / file_name).read_text(encoding="utf-8") for file_name in SCHEMA_FILE_NAMES)


def bootstrap_taylor_rule_schema(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(_schema_sql())
    connection.commit()


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
    connection.commit()


def upsert_raw_observations(connection, rows: list[dict[str, object]]) -> None:
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
    connection.commit()


def upsert_staging_observations(connection, rows: list[dict[str, object]]) -> None:
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
                is_valid,
                is_imputed,
                imputation_method,
                imputation_note,
                imputation_source_window
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
                %(is_valid)s,
                %(is_imputed)s,
                %(imputation_method)s,
                %(imputation_note)s,
                %(imputation_source_window)s
            )
            on conflict (series_id, observation_date) do update
            set
                numeric_value = excluded.numeric_value,
                category = excluded.category,
                region = excluded.region,
                frequency = excluded.frequency,
                unit = excluded.unit,
                provider = excluded.provider,
                is_valid = excluded.is_valid,
                is_imputed = excluded.is_imputed,
                imputation_method = excluded.imputation_method,
                imputation_note = excluded.imputation_note,
                imputation_source_window = excluded.imputation_source_window
            """,
            rows,
        )
    connection.commit()


def read_staging_rows_for_series(connection, series_ids: list[str]) -> list[dict[str, object]]:
    if not series_ids:
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            select
                staging.series_id,
                staging.observation_date::text,
                staging.numeric_value,
                staging.category,
                staging.region,
                staging.frequency,
                staging.unit,
                staging.provider,
                metadata.source_url,
                staging.is_valid,
                staging.is_imputed,
                staging.imputation_method,
                staging.imputation_note,
                staging.imputation_source_window
            from staging.series_observations as staging
            join core.series_metadata as metadata
                on metadata.series_id = staging.series_id
            where staging.series_id = any(%(series_ids)s)
            order by staging.series_id asc, staging.observation_date asc
            """,
            {"series_ids": series_ids},
        )
        return list(cursor.fetchall())

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from src.lib.runtime_env import load_project_env
from src.lib.source.types import SeriesDefinition


def get_database_url() -> str | None:
    load_project_env()
    return os.getenv("DATABASE_URL", "postgresql://mvd:mvd@localhost:5432/mvd")


def get_connection():
    database_url = get_database_url()
    if not database_url:
        return None

    return psycopg.connect(database_url, row_factory=dict_row)


def _schema_sql() -> str:
    schema_path = Path(__file__).resolve().parents[1] / "sql" / "taylor_rule_schema.sql"
    return schema_path.read_text(encoding="utf-8")


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


def replace_taylor_rule_inputs(connection, rows: list[dict[str, object]]) -> None:
    regions = sorted({row["region"] for row in rows})

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
    connection.commit()


def replace_macro_reference_metrics(connection, rows: list[dict[str, object]]) -> None:
    with connection.cursor() as cursor:
        if rows:
            cursor.execute(
                "delete from mart.macro_reference_metrics where region = any(%(regions)s)",
                {"regions": sorted({row["region"] for row in rows})},
            )
        cursor.executemany(
            """
            insert into mart.macro_reference_metrics (
                region,
                headline_inflation,
                headline_inflation_as_of_date,
                core_inflation,
                core_inflation_as_of_date,
                policy_real_rate,
                policy_real_rate_as_of_date,
                market_real_rate,
                market_real_rate_as_of_date,
                output_gap,
                output_gap_as_of_date,
                gdp_growth_yoy_current,
                gdp_growth_yoy_historical_average,
                gdp_growth_yoy_gap,
                gdp_growth_yoy_as_of_date,
                gdp_growth_yoy_history_window,
                gdp_growth_qoq_annualized_current,
                gdp_growth_qoq_annualized_historical_average,
                gdp_growth_qoq_annualized_gap,
                gdp_growth_qoq_annualized_as_of_date,
                gdp_growth_qoq_annualized_history_window,
                headline_series_key,
                headline_source_url,
                core_series_key,
                core_source_url,
                market_real_rate_series_key,
                market_real_rate_source_url,
                output_gap_series_key,
                output_gap_source_url,
                gdp_series_key,
                gdp_source_url,
                policy_real_rate_note
            )
            values (
                %(region)s,
                %(headline_inflation)s,
                %(headline_inflation_as_of_date)s,
                %(core_inflation)s,
                %(core_inflation_as_of_date)s,
                %(policy_real_rate)s,
                %(policy_real_rate_as_of_date)s,
                %(market_real_rate)s,
                %(market_real_rate_as_of_date)s,
                %(output_gap)s,
                %(output_gap_as_of_date)s,
                %(gdp_growth_yoy_current)s,
                %(gdp_growth_yoy_historical_average)s,
                %(gdp_growth_yoy_gap)s,
                %(gdp_growth_yoy_as_of_date)s,
                %(gdp_growth_yoy_history_window)s,
                %(gdp_growth_qoq_annualized_current)s,
                %(gdp_growth_qoq_annualized_historical_average)s,
                %(gdp_growth_qoq_annualized_gap)s,
                %(gdp_growth_qoq_annualized_as_of_date)s,
                %(gdp_growth_qoq_annualized_history_window)s,
                %(headline_series_key)s,
                %(headline_source_url)s,
                %(core_series_key)s,
                %(core_source_url)s,
                %(market_real_rate_series_key)s,
                %(market_real_rate_source_url)s,
                %(output_gap_series_key)s,
                %(output_gap_source_url)s,
                %(gdp_series_key)s,
                %(gdp_source_url)s,
                %(policy_real_rate_note)s
            )
            on conflict (region) do update
            set
                headline_inflation = excluded.headline_inflation,
                headline_inflation_as_of_date = excluded.headline_inflation_as_of_date,
                core_inflation = excluded.core_inflation,
                core_inflation_as_of_date = excluded.core_inflation_as_of_date,
                policy_real_rate = excluded.policy_real_rate,
                policy_real_rate_as_of_date = excluded.policy_real_rate_as_of_date,
                market_real_rate = excluded.market_real_rate,
                market_real_rate_as_of_date = excluded.market_real_rate_as_of_date,
                output_gap = excluded.output_gap,
                output_gap_as_of_date = excluded.output_gap_as_of_date,
                gdp_growth_yoy_current = excluded.gdp_growth_yoy_current,
                gdp_growth_yoy_historical_average = excluded.gdp_growth_yoy_historical_average,
                gdp_growth_yoy_gap = excluded.gdp_growth_yoy_gap,
                gdp_growth_yoy_as_of_date = excluded.gdp_growth_yoy_as_of_date,
                gdp_growth_yoy_history_window = excluded.gdp_growth_yoy_history_window,
                gdp_growth_qoq_annualized_current = excluded.gdp_growth_qoq_annualized_current,
                gdp_growth_qoq_annualized_historical_average = excluded.gdp_growth_qoq_annualized_historical_average,
                gdp_growth_qoq_annualized_gap = excluded.gdp_growth_qoq_annualized_gap,
                gdp_growth_qoq_annualized_as_of_date = excluded.gdp_growth_qoq_annualized_as_of_date,
                gdp_growth_qoq_annualized_history_window = excluded.gdp_growth_qoq_annualized_history_window,
                headline_series_key = excluded.headline_series_key,
                headline_source_url = excluded.headline_source_url,
                core_series_key = excluded.core_series_key,
                core_source_url = excluded.core_source_url,
                market_real_rate_series_key = excluded.market_real_rate_series_key,
                market_real_rate_source_url = excluded.market_real_rate_source_url,
                output_gap_series_key = excluded.output_gap_series_key,
                output_gap_source_url = excluded.output_gap_source_url,
                gdp_series_key = excluded.gdp_series_key,
                gdp_source_url = excluded.gdp_source_url,
                policy_real_rate_note = excluded.policy_real_rate_note
            """,
            rows,
        )
    connection.commit()


def replace_currency_ppp_snapshots(connection, rows: list[dict[str, object]]) -> None:
    pair_keys = sorted({row["pair_key"] for row in rows})

    with connection.cursor() as cursor:
        if pair_keys:
            cursor.execute(
                "delete from mart.currency_ppp_snapshots where pair_key = any(%(pair_keys)s)",
                {"pair_keys": pair_keys},
            )
        cursor.executemany(
            """
            insert into mart.currency_ppp_snapshots (
                pair_key,
                base_month,
                anchor_kind,
                anchor_statistic,
                anchor_window_code,
                anchor_start_month,
                anchor_end_month,
                anchor_years_covered,
                base_year,
                as_of_month,
                base_spot,
                current_spot,
                implied_ppp,
                deviation_pct,
                trailing_12m_average_gap_pct,
                spot_series_key,
                spot_source_url,
                us_cpi_series_key,
                us_cpi_source_url,
                ea_cpi_series_key,
                ea_cpi_source_url
            )
            values (
                %(pair_key)s,
                %(base_month)s,
                %(anchor_kind)s,
                %(anchor_statistic)s,
                %(anchor_window_code)s,
                %(anchor_start_month)s,
                %(anchor_end_month)s,
                %(anchor_years_covered)s,
                %(base_year)s,
                %(as_of_month)s,
                %(base_spot)s,
                %(current_spot)s,
                %(implied_ppp)s,
                %(deviation_pct)s,
                %(trailing_12m_average_gap_pct)s,
                %(spot_series_key)s,
                %(spot_source_url)s,
                %(us_cpi_series_key)s,
                %(us_cpi_source_url)s,
                %(ea_cpi_series_key)s,
                %(ea_cpi_source_url)s
            )
            on conflict (pair_key, base_month, anchor_kind, anchor_statistic, as_of_month) do update
            set
                base_spot = excluded.base_spot,
                current_spot = excluded.current_spot,
                implied_ppp = excluded.implied_ppp,
                deviation_pct = excluded.deviation_pct,
                trailing_12m_average_gap_pct = excluded.trailing_12m_average_gap_pct,
                anchor_window_code = excluded.anchor_window_code,
                anchor_start_month = excluded.anchor_start_month,
                anchor_end_month = excluded.anchor_end_month,
                anchor_years_covered = excluded.anchor_years_covered,
                base_year = excluded.base_year,
                spot_series_key = excluded.spot_series_key,
                spot_source_url = excluded.spot_source_url,
                us_cpi_series_key = excluded.us_cpi_series_key,
                us_cpi_source_url = excluded.us_cpi_source_url,
                ea_cpi_series_key = excluded.ea_cpi_series_key,
                ea_cpi_source_url = excluded.ea_cpi_source_url
            """,
            rows,
        )
    connection.commit()


def replace_currency_ppp_paths(connection, rows: list[dict[str, object]]) -> None:
    pair_keys = sorted({row["pair_key"] for row in rows})

    with connection.cursor() as cursor:
        if pair_keys:
            cursor.execute(
                "delete from mart.currency_ppp_paths where pair_key = any(%(pair_keys)s)",
                {"pair_keys": pair_keys},
            )
        cursor.executemany(
            """
            insert into mart.currency_ppp_paths (
                pair_key,
                base_month,
                anchor_kind,
                anchor_statistic,
                anchor_window_code,
                base_year,
                observation_month,
                actual_spot,
                implied_ppp,
                has_imputed_inputs,
                imputation_note
            )
            values (
                %(pair_key)s,
                %(base_month)s,
                %(anchor_kind)s,
                %(anchor_statistic)s,
                %(anchor_window_code)s,
                %(base_year)s,
                %(observation_month)s,
                %(actual_spot)s,
                %(implied_ppp)s,
                %(has_imputed_inputs)s,
                %(imputation_note)s
            )
            on conflict (pair_key, base_month, anchor_kind, anchor_statistic, observation_month) do update
            set
                anchor_window_code = excluded.anchor_window_code,
                base_year = excluded.base_year,
                actual_spot = excluded.actual_spot,
                implied_ppp = excluded.implied_ppp,
                has_imputed_inputs = excluded.has_imputed_inputs,
                imputation_note = excluded.imputation_note
            """,
            rows,
        )
    connection.commit()


def replace_currency_irp_snapshots(connection, rows: list[dict[str, object]]) -> None:
    pair_keys = sorted({row["pair_key"] for row in rows})

    with connection.cursor() as cursor:
        if pair_keys:
            cursor.execute(
                "delete from mart.currency_irp_snapshots where pair_key = any(%(pair_keys)s)",
                {"pair_keys": pair_keys},
            )
        cursor.executemany(
            """
            insert into mart.currency_irp_snapshots (
                pair_key,
                as_of_date,
                tenor,
                spot,
                eur_rate,
                usd_rate,
                rate_spread,
                cip_implied_forward,
                uip_implied_move_pct,
                uip_implied_spot,
                spot_series_key,
                spot_source_url,
                eur_rate_series_key,
                eur_rate_source_url,
                usd_rate_series_key,
                usd_rate_source_url
            )
            values (
                %(pair_key)s,
                %(as_of_date)s,
                %(tenor)s,
                %(spot)s,
                %(eur_rate)s,
                %(usd_rate)s,
                %(rate_spread)s,
                %(cip_implied_forward)s,
                %(uip_implied_move_pct)s,
                %(uip_implied_spot)s,
                %(spot_series_key)s,
                %(spot_source_url)s,
                %(eur_rate_series_key)s,
                %(eur_rate_source_url)s,
                %(usd_rate_series_key)s,
                %(usd_rate_source_url)s
            )
            on conflict (pair_key, as_of_date, tenor) do update
            set
                spot = excluded.spot,
                eur_rate = excluded.eur_rate,
                usd_rate = excluded.usd_rate,
                rate_spread = excluded.rate_spread,
                cip_implied_forward = excluded.cip_implied_forward,
                uip_implied_move_pct = excluded.uip_implied_move_pct,
                uip_implied_spot = excluded.uip_implied_spot,
                spot_series_key = excluded.spot_series_key,
                spot_source_url = excluded.spot_source_url,
                eur_rate_series_key = excluded.eur_rate_series_key,
                eur_rate_source_url = excluded.eur_rate_source_url,
                usd_rate_series_key = excluded.usd_rate_series_key,
                usd_rate_source_url = excluded.usd_rate_source_url
            """,
            rows,
        )
    connection.commit()


def replace_currency_data_availability(connection, rows: list[dict[str, object]]) -> None:
    pair_keys = sorted({row["pair_key"] for row in rows})

    with connection.cursor() as cursor:
        if pair_keys:
            cursor.execute(
                "delete from mart.currency_data_availability where pair_key = any(%(pair_keys)s)",
                {"pair_keys": pair_keys},
            )
        cursor.executemany(
            """
            insert into mart.currency_data_availability (
                pair_key,
                section_key,
                item_key,
                status,
                detail,
                as_of_date
            )
            values (
                %(pair_key)s,
                %(section_key)s,
                %(item_key)s,
                %(status)s,
                %(detail)s,
                %(as_of_date)s
            )
            on conflict (pair_key, section_key, item_key) do update
            set
                status = excluded.status,
                detail = excluded.detail,
                as_of_date = excluded.as_of_date
            """,
            rows,
        )
    connection.commit()

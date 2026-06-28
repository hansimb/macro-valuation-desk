from __future__ import annotations


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

from __future__ import annotations


def upsert_equity_index_constituent_snapshots(connection, rows: list[dict[str, object]]) -> None:
    if not rows:
        return

    with connection.cursor() as cursor:
        cursor.executemany(
            """
            insert into staging.equity_index_constituent_snapshots (
                universe_key,
                as_of_date,
                ticker,
                company,
                country_code,
                country_name,
                sector,
                market_cap,
                trailing_12m_revenue,
                ps_ratio,
                index_weight_pct,
                average_daily_traded_value,
                source_provider,
                source_url
            )
            values (
                %(universe_key)s,
                %(as_of_date)s,
                %(ticker)s,
                %(company)s,
                %(country_code)s,
                %(country_name)s,
                %(sector)s,
                %(market_cap)s,
                %(trailing_12m_revenue)s,
                %(ps_ratio)s,
                %(index_weight_pct)s,
                %(average_daily_traded_value)s,
                %(source_provider)s,
                %(source_url)s
            )
            on conflict (universe_key, as_of_date, ticker) do update
            set
                company = excluded.company,
                country_code = excluded.country_code,
                country_name = excluded.country_name,
                sector = excluded.sector,
                market_cap = excluded.market_cap,
                trailing_12m_revenue = excluded.trailing_12m_revenue,
                ps_ratio = excluded.ps_ratio,
                index_weight_pct = excluded.index_weight_pct,
                average_daily_traded_value = excluded.average_daily_traded_value,
                source_provider = excluded.source_provider,
                source_url = excluded.source_url,
                fetched_at = now()
            """,
            rows,
        )
    connection.commit()


def read_highest_ps_candidate_rows(connection) -> list[dict[str, object]]:
    if connection is None:
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            with latest_snapshot as (
                select max(as_of_date) as as_of_date
                from staging.equity_index_constituent_snapshots
                where universe_key = %(universe_key)s
            )
            select
                'usa' as section_key,
                'USA High P/S Leaders' as section_label,
                constituent.universe_key,
                'S&P 500' as universe_label,
                constituent.as_of_date::text,
                constituent.ticker,
                constituent.company,
                constituent.country_code,
                constituent.country_name,
                constituent.sector,
                constituent.market_cap,
                constituent.average_daily_traded_value,
                coalesce(
                    constituent.ps_ratio,
                    constituent.market_cap / nullif(constituent.trailing_12m_revenue, 0)
                ) as ps_ratio,
                constituent.index_weight_pct
            from staging.equity_index_constituent_snapshots as constituent
            join latest_snapshot
                on latest_snapshot.as_of_date = constituent.as_of_date
            where constituent.universe_key = %(universe_key)s
              and nullif(trim(constituent.ticker), '') is not null
              and nullif(trim(constituent.company), '') is not null
              and nullif(trim(constituent.country_code), '') is not null
              and nullif(trim(constituent.country_name), '') is not null
              and nullif(trim(constituent.sector), '') is not null
              and constituent.market_cap > 0
              and constituent.trailing_12m_revenue > 0
              and coalesce(
                    constituent.ps_ratio,
                    constituent.market_cap / nullif(constituent.trailing_12m_revenue, 0)
                  ) > 0
              and constituent.index_weight_pct > 0
              and constituent.average_daily_traded_value > 0
            order by constituent.ticker asc
            """,
            {"universe_key": "sp500"},
        )
        return list(cursor.fetchall())


def replace_highest_ps_section_summaries(connection, rows: list[dict[str, object]]) -> None:
    section_keys = sorted({row["section_key"] for row in rows})

    with connection.cursor() as cursor:
        if section_keys:
            cursor.execute(
                "delete from mart.highest_ps_section_summaries where section_key = any(%(section_keys)s)",
                {"section_keys": section_keys},
            )
        cursor.executemany(
            """
            insert into mart.highest_ps_section_summaries (
                section_key,
                as_of_date,
                universe_key,
                universe_label,
                section_label,
                benchmark_key,
                benchmark_label,
                average_ps_ratio,
                top_basket_average_ps_ratio,
                top_basket_index_weight_pct,
                eligible_constituent_count,
                unavailable
            )
            values (
                %(section_key)s,
                %(as_of_date)s,
                %(universe_key)s,
                %(universe_label)s,
                %(section_label)s,
                %(benchmark_key)s,
                %(benchmark_label)s,
                %(average_ps_ratio)s,
                %(top_basket_average_ps_ratio)s,
                %(top_basket_index_weight_pct)s,
                %(eligible_constituent_count)s,
                %(unavailable)s
            )
            on conflict (section_key) do update
            set
                as_of_date = excluded.as_of_date,
                universe_key = excluded.universe_key,
                universe_label = excluded.universe_label,
                section_label = excluded.section_label,
                benchmark_key = excluded.benchmark_key,
                benchmark_label = excluded.benchmark_label,
                average_ps_ratio = excluded.average_ps_ratio,
                top_basket_average_ps_ratio = excluded.top_basket_average_ps_ratio,
                top_basket_index_weight_pct = excluded.top_basket_index_weight_pct,
                eligible_constituent_count = excluded.eligible_constituent_count,
                unavailable = excluded.unavailable
            """,
            rows,
        )
    connection.commit()


def replace_highest_ps_section_rankings(connection, rows: list[dict[str, object]]) -> None:
    section_keys = sorted({row["section_key"] for row in rows})

    with connection.cursor() as cursor:
        if section_keys:
            cursor.execute(
                "delete from mart.highest_ps_section_rankings where section_key = any(%(section_keys)s)",
                {"section_keys": section_keys},
            )
        cursor.executemany(
            """
            insert into mart.highest_ps_section_rankings (
                section_key,
                rank,
                ticker,
                company,
                country_code,
                country_name,
                sector,
                ps_ratio,
                sector_average_ps_ratio,
                relative_to_sector_multiple,
                index_weight_pct
            )
            values (
                %(section_key)s,
                %(rank)s,
                %(ticker)s,
                %(company)s,
                %(country_code)s,
                %(country_name)s,
                %(sector)s,
                %(ps_ratio)s,
                %(sector_average_ps_ratio)s,
                %(relative_to_sector_multiple)s,
                %(index_weight_pct)s
            )
            on conflict (section_key, rank) do update
            set
                ticker = excluded.ticker,
                company = excluded.company,
                country_code = excluded.country_code,
                country_name = excluded.country_name,
                sector = excluded.sector,
                ps_ratio = excluded.ps_ratio,
                sector_average_ps_ratio = excluded.sector_average_ps_ratio,
                relative_to_sector_multiple = excluded.relative_to_sector_multiple,
                index_weight_pct = excluded.index_weight_pct
            """,
            rows,
        )
    connection.commit()

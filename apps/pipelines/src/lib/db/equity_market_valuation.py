from __future__ import annotations

import json


def upsert_equity_market_valuation_payloads(connection, rows: list[dict[str, object]]) -> None:
    if connection is None:
        return

    db_rows = [{**row, "payload_json": json.dumps(row["payload_json"])} for row in rows]

    with connection.cursor() as cursor:
        cursor.executemany(
            """
            insert into raw.equity_market_valuation_payloads (
                provider,
                external_symbol,
                fetched_at,
                payload_json
            )
            values (
                %(provider)s,
                %(external_symbol)s,
                %(fetched_at)s,
                %(payload_json)s::jsonb
            )
            on conflict (provider, external_symbol, fetched_at) do update
            set
                payload_json = excluded.payload_json
            """,
            db_rows,
        )


def replace_equity_market_valuation_snapshots(connection, rows: list[dict[str, object]]) -> None:
    if connection is None:
        return

    market_ids = sorted({row["market_id"] for row in rows})
    db_rows = [{**row, "missing_fields": json.dumps(row["missing_fields"])} for row in rows]

    with connection.cursor() as cursor:
        if market_ids:
            cursor.execute(
                "delete from marts.equity_market_valuation_snapshot where market_id = any(%(market_ids)s)",
                {"market_ids": market_ids},
            )
        cursor.executemany(
            """
            insert into marts.equity_market_valuation_snapshot (
                market_id,
                region,
                market_name,
                measured_symbol,
                measured_name,
                measured_type,
                provider,
                source_url,
                as_of,
                trailing_pe,
                price_to_book,
                price_to_sales,
                price_to_cash_flow,
                dividend_yield_pct,
                price_to_free_cash_flow,
                price_to_cash_flow_method,
                price_to_free_cash_flow_method,
                missing_fields
            )
            values (
                %(market_id)s,
                %(region)s,
                %(market_name)s,
                %(measured_symbol)s,
                %(measured_name)s,
                %(measured_type)s,
                %(provider)s,
                %(source_url)s,
                %(as_of)s,
                %(trailing_pe)s,
                %(price_to_book)s,
                %(price_to_sales)s,
                %(price_to_cash_flow)s,
                %(dividend_yield_pct)s,
                %(price_to_free_cash_flow)s,
                %(price_to_cash_flow_method)s,
                %(price_to_free_cash_flow_method)s,
                %(missing_fields)s::jsonb
            )
            on conflict (market_id, as_of) do update
            set
                region = excluded.region,
                market_name = excluded.market_name,
                measured_symbol = excluded.measured_symbol,
                measured_name = excluded.measured_name,
                measured_type = excluded.measured_type,
                provider = excluded.provider,
                source_url = excluded.source_url,
                trailing_pe = excluded.trailing_pe,
                price_to_book = excluded.price_to_book,
                price_to_sales = excluded.price_to_sales,
                price_to_cash_flow = excluded.price_to_cash_flow,
                dividend_yield_pct = excluded.dividend_yield_pct,
                price_to_free_cash_flow = excluded.price_to_free_cash_flow,
                price_to_cash_flow_method = excluded.price_to_cash_flow_method,
                price_to_free_cash_flow_method = excluded.price_to_free_cash_flow_method,
                missing_fields = excluded.missing_fields
            """,
            db_rows,
        )

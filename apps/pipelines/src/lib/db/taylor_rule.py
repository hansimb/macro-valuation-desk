from __future__ import annotations


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

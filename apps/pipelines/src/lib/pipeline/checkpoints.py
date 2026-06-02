from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from src.lib.source.types import FetchOptions


def read_latest_checkpoint(connection, series_id: str) -> str | None:
    if connection is None:
        return None

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select last_successful_observation_date
                from etl.series_checkpoints
                where series_id = %(series_id)s
                """,
                {"series_id": series_id},
            )
            row = cursor.fetchone()

    if not row:
        return None

    return row["last_successful_observation_date"]


def build_fetch_options_from_checkpoint(
    checkpoint_date: str | None,
    *,
    reprocess_days: int = 30,
    end_date: str | None = None,
) -> FetchOptions:
    if checkpoint_date is None:
        return FetchOptions(start_date=None, end_date=end_date)

    start_date = date.fromisoformat(checkpoint_date) - timedelta(days=reprocess_days)
    return FetchOptions(start_date=start_date.isoformat(), end_date=end_date)


def write_successful_checkpoint(
    connection,
    *,
    series_id: str,
    last_successful_observation_date: str,
    last_run_at: str,
) -> None:
    if connection is None:
        return

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                insert into etl.series_checkpoints (
                    series_id,
                    last_successful_observation_date,
                    last_run_at,
                    last_run_status
                )
                values (
                    %(series_id)s,
                    %(last_successful_observation_date)s,
                    %(last_run_at)s,
                    'success'
                )
                on conflict (series_id) do update
                set
                    last_successful_observation_date = excluded.last_successful_observation_date,
                    last_run_at = excluded.last_run_at,
                    last_run_status = excluded.last_run_status
                """,
                {
                    "series_id": series_id,
                    "last_successful_observation_date": last_successful_observation_date,
                    "last_run_at": last_run_at,
                },
            )


def record_pipeline_run(
    connection,
    *,
    run_id: str,
    domain_key: str,
    started_at: str,
    finished_at: str | None,
    status: str,
    error_summary: str | None,
) -> None:
    if connection is None:
        return

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                insert into etl.pipeline_runs (
                    run_id,
                    domain_key,
                    started_at,
                    finished_at,
                    status,
                    error_summary
                )
                values (
                    %(run_id)s,
                    %(domain_key)s,
                    %(started_at)s,
                    %(finished_at)s,
                    %(status)s,
                    %(error_summary)s
                )
                on conflict (run_id) do update
                set
                    finished_at = excluded.finished_at,
                    status = excluded.status,
                    error_summary = excluded.error_summary
                """,
                {
                    "run_id": run_id,
                    "domain_key": domain_key,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "status": status,
                    "error_summary": error_summary,
                },
            )


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

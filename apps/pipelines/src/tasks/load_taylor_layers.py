from __future__ import annotations

from prefect import task

from src.lib.db import (
    bootstrap_taylor_rule_schema,
    replace_taylor_rule_inputs,
    upsert_raw_observations,
    upsert_series_metadata,
    upsert_staging_observations,
)
from src.lib.pipeline.checkpoints import record_pipeline_run, utc_now_iso, write_successful_checkpoint
from src.lib.source.registry import get_series_definition, get_series_definitions
from src.lib.source.types import FetchResult


def _raw_rows_from_results(fetch_results: list[FetchResult], *, fetched_at: str) -> list[dict[str, object]]:
    raw_rows: list[dict[str, object]] = []

    for result in fetch_results:
        if not result.ok or result.series is None:
            continue
        for observation in result.series.observations:
            raw_rows.append(
                {
                    "series_id": result.series.key,
                    "observation_date": f"{observation.date}-01" if len(observation.date) == 7 else observation.date,
                    "value": observation.value,
                    "fetched_at": fetched_at,
                }
            )

    return raw_rows


@task
def load_taylor_layers(
    connection,
    *,
    fetch_results: list[FetchResult],
    staging_rows: list[dict[str, object]],
    mart_rows: list[dict[str, object]],
) -> dict[str, int]:
    run_at = utc_now_iso()
    record_pipeline_run(
        connection,
        run_id=f"taylor-rule-{run_at}",
        domain_key="taylor_rule",
        started_at=run_at,
        finished_at=None,
        status="running",
        error_summary=None,
    )

    successful_series_keys = [
        result.series.key
        for result in fetch_results
        if result.ok and result.series is not None
    ]

    if connection is not None:
        bootstrap_taylor_rule_schema(connection)
        upsert_series_metadata(connection, get_series_definitions(successful_series_keys))
        upsert_raw_observations(connection, _raw_rows_from_results(fetch_results, fetched_at=run_at))
        upsert_staging_observations(connection, staging_rows)
        replace_taylor_rule_inputs(connection, mart_rows)

    for result in fetch_results:
        if not result.ok or result.series is None or not result.series.observations:
            continue
        latest_observation_date = max(
            f"{observation.date}-01" if len(observation.date) == 7 else observation.date
            for observation in result.series.observations
        )
        write_successful_checkpoint(
            connection,
            series_id=result.series.key,
            last_successful_observation_date=latest_observation_date,
            last_run_at=run_at,
        )

    record_pipeline_run(
        connection,
        run_id=f"taylor-rule-{run_at}",
        domain_key="taylor_rule",
        started_at=run_at,
        finished_at=run_at,
        status="success",
        error_summary=None,
    )

    return {
        "series_metadata": len(successful_series_keys),
        "raw_rows": len(_raw_rows_from_results(fetch_results, fetched_at=run_at)),
        "staging_rows": len(staging_rows),
        "mart_rows": len(mart_rows),
    }

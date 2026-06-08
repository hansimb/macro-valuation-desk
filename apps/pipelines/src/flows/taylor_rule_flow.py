from __future__ import annotations

from prefect import flow

from src.lib.db import bootstrap_taylor_rule_schema, get_connection, read_staging_rows_for_series
from src.lib.pipeline.error_handling import collect_fetch_errors
from src.lib.pipeline.transforms.reference_metrics import build_macro_reference_metrics
from src.lib.pipeline.transforms.staging import fill_series_gaps, stage_standardized_series
from src.lib.pipeline.transforms.taylor_rule import build_taylor_rule_inputs
from src.tasks import load_taylor_layers as load_taylor_layers_module
from src.tasks import run_eu_macro_core_etl as run_eu_macro_core_etl_module
from src.tasks import run_us_macro_core_etl as run_us_macro_core_etl_module


def _call_task(task_or_fn, *args, **kwargs):
    if hasattr(task_or_fn, "fn"):
        return task_or_fn.fn(*args, **kwargs)

    return task_or_fn(*args, **kwargs)


def _merge_staging_rows(
    historical_rows: list[dict[str, object]],
    current_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    merged: dict[tuple[str, str], dict[str, object]] = {}

    for row in historical_rows + current_rows:
        merged[(str(row["series_id"]), str(row["observation_date"]))] = row

    return list(merged.values())


def run_taylor_rule_flow() -> dict[str, object]:
    connection = get_connection()
    if connection is not None:
        bootstrap_taylor_rule_schema(connection)
    if connection is None:
        fetch_results = _call_task(run_us_macro_core_etl_module.run_us_macro_core_etl)
        fetch_results += _call_task(run_eu_macro_core_etl_module.run_eu_macro_core_etl)
    else:
        fetch_results = _call_task(run_us_macro_core_etl_module.run_us_macro_core_etl, connection)
        fetch_results += _call_task(run_eu_macro_core_etl_module.run_eu_macro_core_etl, connection)

    failures = collect_fetch_errors(fetch_results)
    if failures:
        return {"status": "failed", "errors": failures}

    staging_rows = [
        row
        for result in fetch_results
        if result.ok and result.series is not None
        for row in stage_standardized_series(result.series)
    ]
    successful_series_keys = [
        result.series.key
        for result in fetch_results
        if result.ok and result.series is not None
    ]
    historical_rows = (
        read_staging_rows_for_series(connection, successful_series_keys)
        if connection is not None
        else []
    )
    prepared_staging_rows = fill_series_gaps(_merge_staging_rows(historical_rows, staging_rows))
    mart_rows = build_taylor_rule_inputs(prepared_staging_rows)
    reference_metric_rows = build_macro_reference_metrics(prepared_staging_rows)
    load_summary = _call_task(
        load_taylor_layers_module.load_taylor_layers,
        connection,
        fetch_results=fetch_results,
        staging_rows=prepared_staging_rows,
        mart_rows=mart_rows,
        reference_metric_rows=reference_metric_rows,
    )

    return {
        "status": "success",
        "series_fetched": len(fetch_results),
        "staging_rows": len(prepared_staging_rows),
        "mart_rows": len(mart_rows),
        "reference_metric_rows": len(reference_metric_rows),
        "load_summary": load_summary,
    }


@flow(name="taylor-rule-flow")
def taylor_rule_flow() -> dict[str, object]:
    return run_taylor_rule_flow()


if __name__ == "__main__":
    taylor_rule_flow()

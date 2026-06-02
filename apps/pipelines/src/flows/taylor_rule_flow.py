from __future__ import annotations

from prefect import flow

from src.lib.db import get_connection
from src.lib.pipeline.transforms.staging import stage_standardized_series
from src.lib.pipeline.transforms.taylor_rule import build_taylor_rule_inputs
from src.tasks import load_taylor_layers as load_taylor_layers_module
from src.tasks import run_eu_macro_core_etl as run_eu_macro_core_etl_module
from src.tasks import run_us_macro_core_etl as run_us_macro_core_etl_module


def _call_task(task_or_fn, *args, **kwargs):
    if hasattr(task_or_fn, "fn"):
        return task_or_fn.fn(*args, **kwargs)

    return task_or_fn(*args, **kwargs)


def run_taylor_rule_flow() -> dict[str, object]:
    connection = get_connection()
    if connection is None:
        fetch_results = _call_task(run_us_macro_core_etl_module.run_us_macro_core_etl)
        fetch_results += _call_task(run_eu_macro_core_etl_module.run_eu_macro_core_etl)
    else:
        fetch_results = _call_task(run_us_macro_core_etl_module.run_us_macro_core_etl, connection)
        fetch_results += _call_task(run_eu_macro_core_etl_module.run_eu_macro_core_etl, connection)

    failures = [
        f"{result.error.key}: {result.error.message}"
        for result in fetch_results
        if not result.ok and result.error is not None
    ]
    if failures:
        return {"status": "failed", "errors": failures}

    staging_rows = [
        row
        for result in fetch_results
        if result.ok and result.series is not None
        for row in stage_standardized_series(result.series)
    ]
    mart_rows = build_taylor_rule_inputs(staging_rows)
    load_summary = _call_task(
        load_taylor_layers_module.load_taylor_layers,
        connection,
        fetch_results=fetch_results,
        staging_rows=staging_rows,
        mart_rows=mart_rows,
    )

    return {
        "status": "success",
        "series_fetched": len(fetch_results),
        "staging_rows": len(staging_rows),
        "mart_rows": len(mart_rows),
        "load_summary": load_summary,
    }


@flow(name="taylor-rule-flow")
def taylor_rule_flow() -> dict[str, object]:
    return run_taylor_rule_flow()

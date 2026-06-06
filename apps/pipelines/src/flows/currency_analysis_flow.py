from __future__ import annotations

from prefect import flow

from src.lib.db import bootstrap_taylor_rule_schema, get_connection
from src.lib.pipeline.error_handling import collect_fetch_errors
from src.lib.pipeline.transforms.currency_irp import build_currency_irp_outputs
from src.lib.pipeline.transforms.currency_ppp import build_currency_ppp_outputs
from src.lib.pipeline.transforms.staging import stage_standardized_series
from src.tasks import load_currency_analysis_layers as load_currency_analysis_layers_module
from src.tasks import run_currency_market_etl as run_currency_market_etl_module


def _call_task(task_or_fn, *args, **kwargs):
    if hasattr(task_or_fn, "fn"):
        return task_or_fn.fn(*args, **kwargs)

    return task_or_fn(*args, **kwargs)


def run_currency_analysis_flow() -> dict[str, object]:
    connection = get_connection()
    if connection is not None:
        bootstrap_taylor_rule_schema(connection)

    fetch_results = (
        _call_task(run_currency_market_etl_module.run_currency_market_etl)
        if connection is None
        else _call_task(run_currency_market_etl_module.run_currency_market_etl, connection)
    )

    failures = collect_fetch_errors(fetch_results)

    staging_rows = [
        row
        for result in fetch_results
        if result.ok and result.series is not None
        for row in stage_standardized_series(result.series)
    ]
    ppp_outputs = build_currency_ppp_outputs(staging_rows)
    irp_outputs = build_currency_irp_outputs(staging_rows)

    if not ppp_outputs["snapshot_rows"] and not irp_outputs["snapshot_rows"]:
        return {
            "status": "failed",
            "errors": failures or ["No currency analysis sections could be built from the fetched inputs."],
        }

    availability_rows = ppp_outputs["availability_rows"] + irp_outputs["availability_rows"]
    load_summary = _call_task(
        load_currency_analysis_layers_module.load_currency_analysis_layers,
        connection,
        fetch_results=fetch_results,
        staging_rows=staging_rows,
        ppp_snapshot_rows=ppp_outputs["snapshot_rows"],
        ppp_path_rows=ppp_outputs["path_rows"],
        irp_snapshot_rows=irp_outputs["snapshot_rows"],
        availability_rows=availability_rows,
    )

    return {
        "status": "success",
        "series_fetched": len(fetch_results),
        "staging_rows": len(staging_rows),
        "ppp_snapshot_rows": len(ppp_outputs["snapshot_rows"]),
        "ppp_path_rows": len(ppp_outputs["path_rows"]),
        "irp_snapshot_rows": len(irp_outputs["snapshot_rows"]),
        "availability_rows": len(availability_rows),
        "fetch_errors": failures,
        "load_summary": load_summary,
    }


@flow(name="currency-analysis-flow")
def currency_analysis_flow() -> dict[str, object]:
    return run_currency_analysis_flow()


if __name__ == "__main__":
    currency_analysis_flow()

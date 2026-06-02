from __future__ import annotations

from prefect import task

from src.lib.pipeline.checkpoints import build_fetch_options_from_checkpoint, read_latest_checkpoint
from src.lib.source.fetch import fetch_registered_series
from src.lib.source.registry import get_series_definition
from src.lib.source.types import FetchResult


US_SERIES_KEYS = ["us_policy_rate", "us_cpi_headline"]


def _run_region_series(series_keys: list[str], connection) -> list[FetchResult]:
    results: list[FetchResult] = []

    for key in series_keys:
        definition = get_series_definition(key)
        checkpoint = read_latest_checkpoint(connection, definition.key)
        fetch_options = build_fetch_options_from_checkpoint(checkpoint, reprocess_days=30)
        results.append(fetch_registered_series(definition, fetch_options))

    return results


@task
def run_us_macro_core_etl(connection=None) -> list[FetchResult]:
    return _run_region_series(US_SERIES_KEYS, connection)

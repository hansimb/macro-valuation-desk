from __future__ import annotations

from prefect import task

from src.lib.pipeline.checkpoints import build_fetch_options_from_checkpoint, read_latest_checkpoint
from src.lib.source.fetch import fetch_registered_series
from src.lib.source.registry import get_series_definition
from src.lib.source.types import FetchResult


EU_SERIES_KEYS = [
    "eu_policy_rate",
    "eu_hicp_headline",
    "eu_hicp_core",
    "eu_market_real_rate",
    "eu_real_gdp",
]


def _run_region_series(series_keys: list[str], connection) -> list[FetchResult]:
    results: list[FetchResult] = []

    for key in series_keys:
        definition = get_series_definition(key)
        checkpoint = read_latest_checkpoint(connection, definition.key)
        fetch_options = build_fetch_options_from_checkpoint(checkpoint, reprocess_days=30)
        results.append(fetch_registered_series(definition, fetch_options))

    return results


@task
def run_eu_macro_core_etl(connection=None) -> list[FetchResult]:
    return _run_region_series(EU_SERIES_KEYS, connection)

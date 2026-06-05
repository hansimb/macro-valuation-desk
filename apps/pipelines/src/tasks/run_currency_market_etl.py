from __future__ import annotations

from prefect import task

from src.lib.pipeline.checkpoints import build_fetch_options_for_series, read_latest_checkpoint
from src.lib.source.fetch import fetch_registered_series
from src.lib.source.registry import get_series_definition
from src.lib.source.types import FetchResult


CURRENCY_SERIES_KEYS = [
    "eurusd_spot_daily",
    "eurusd_spot_monthly",
    "us_cpi_index",
    "ea_cpi_index",
    "eur_3m_rate",
    "eur_6m_rate",
    "eur_12m_rate",
    "usd_3m_rate",
    "usd_6m_rate",
    "usd_12m_rate",
]


@task
def run_currency_market_etl(connection=None) -> list[FetchResult]:
    results: list[FetchResult] = []

    for key in CURRENCY_SERIES_KEYS:
        definition = get_series_definition(key)
        checkpoint = read_latest_checkpoint(connection, definition.key)
        fetch_options = build_fetch_options_for_series(checkpoint, definition)
        results.append(fetch_registered_series(definition, fetch_options))

    return results

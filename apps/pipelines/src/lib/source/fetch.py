from __future__ import annotations

from src.lib.source.adapters.base import SourceAdapter
from src.lib.source.adapters.ecb import EcbAdapter
from src.lib.source.adapters.fred import FredAdapter
from src.lib.source.types import FetchOptions, FetchResult, SeriesDefinition


ADAPTERS: dict[str, SourceAdapter] = {
    "fred": FredAdapter(),
    "ecb": EcbAdapter(),
}


def fetch_registered_series(
    series_definition: SeriesDefinition,
    fetch_options: FetchOptions,
) -> FetchResult:
    adapter = ADAPTERS[series_definition.provider]
    return adapter.fetch_series(series_definition, fetch_options)

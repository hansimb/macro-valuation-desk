from __future__ import annotations

from src.lib.source.adapters.base import SourceAdapter
from src.lib.source.adapters.dbnomics import DbnomicsAdapter
from src.lib.source.adapters.ecb import EcbAdapter
from src.lib.source.adapters.fred import FredAdapter
from src.lib.source.types import FetchOptions, FetchResult, SeriesDefinition


ADAPTERS: dict[str, SourceAdapter] = {
    "dbnomics": DbnomicsAdapter(),
    "fred": FredAdapter(),
    "ecb": EcbAdapter(),
}


def fetch_registered_series(
    series_definition: SeriesDefinition,
    fetch_options: FetchOptions,
) -> FetchResult:
    adapter = ADAPTERS[series_definition.provider]
    result = adapter.fetch_series(series_definition, fetch_options)

    if result.ok or not series_definition.fallback_provider or not series_definition.fallback_external_series_id:
        return result

    fallback_definition = SeriesDefinition(
        key=series_definition.key,
        category=series_definition.category,
        provider=series_definition.fallback_provider,
        external_series_id=series_definition.fallback_external_series_id,
        label=series_definition.fallback_label or series_definition.label,
        region=series_definition.region,
        frequency=series_definition.fallback_frequency or series_definition.frequency,
        unit=series_definition.fallback_unit or series_definition.unit,
        source_url=series_definition.fallback_source_url or series_definition.source_url,
    )
    fallback_adapter = ADAPTERS[fallback_definition.provider]
    fallback_result = fallback_adapter.fetch_series(fallback_definition, fetch_options)

    if fallback_result.ok:
        return fallback_result

    primary_error = result.error.message if result.error else "unknown primary error"
    fallback_error = fallback_result.error.message if fallback_result.error else "unknown fallback error"
    return FetchResult.failure(
        provider=series_definition.provider,
        key=series_definition.key,
        external_series_id=series_definition.external_series_id,
        error_type="fetch_error",
        message=f"Primary source failed: {primary_error} Fallback source failed: {fallback_error}",
    )

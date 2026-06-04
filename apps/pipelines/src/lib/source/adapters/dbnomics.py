from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.lib.source.adapters.base import SourceAdapter
from src.lib.source.types import FetchOptions, FetchResult, Observation, SeriesDefinition, StandardizedSeries


def _format_http_error(exc: HTTPError) -> str:
    response_body = ""
    if exc.fp is not None:
        try:
            response_body = exc.read().decode("utf-8")
        except Exception:
            response_body = ""

    if response_body:
        return f"{exc} for URL {exc.url}. Response body: {response_body}"

    return f"{exc} for URL {exc.url}"


class DbnomicsAdapter(SourceAdapter):
    BASE_URL = "https://api.db.nomics.world/v22/series"

    def fetch_series(
        self,
        series_definition: SeriesDefinition,
        fetch_options: FetchOptions,
    ) -> FetchResult:
        request_url = (
            f"{self.BASE_URL}/AMECO/AVGDGP/{quote(series_definition.external_series_id)}?observations=true"
        )
        request = Request(request_url, headers={"Accept": "application/json", "User-Agent": "macro-valuation-desk/1.0"})

        try:
            with urlopen(request) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return FetchResult.failure(
                provider=series_definition.provider,
                key=series_definition.key,
                external_series_id=series_definition.external_series_id,
                error_type="fetch_error",
                message=_format_http_error(exc),
            )
        except Exception as exc:
            return FetchResult.failure(
                provider=series_definition.provider,
                key=series_definition.key,
                external_series_id=series_definition.external_series_id,
                error_type="fetch_error",
                message=str(exc),
            )

        docs = payload.get("series", {}).get("docs", [])
        if not docs:
            return FetchResult.failure(
                provider=series_definition.provider,
                key=series_definition.key,
                external_series_id=series_definition.external_series_id,
                error_type="fetch_error",
                message=f"No series docs returned for URL {request_url}",
            )

        document = docs[0]
        period_start_days = document.get("period_start_day", [])
        values = document.get("value", [])

        observations = [
            Observation(date=date, value=str(value))
            for date, value in zip(period_start_days, values, strict=False)
            if value != "NA"
        ]

        if fetch_options.start_date:
            observations = [item for item in observations if item.date >= fetch_options.start_date]
        if fetch_options.end_date:
            observations = [item for item in observations if item.date <= fetch_options.end_date]
        if fetch_options.limit is not None:
            observations = observations[: fetch_options.limit]

        return FetchResult.success(
            StandardizedSeries(
                key=series_definition.key,
                category=series_definition.category,
                provider=series_definition.provider,
                series_id=series_definition.external_series_id,
                label=series_definition.label,
                region=series_definition.region,
                frequency=series_definition.frequency,
                unit=series_definition.unit,
                source_url=series_definition.source_url,
                observations=observations,
            )
        )

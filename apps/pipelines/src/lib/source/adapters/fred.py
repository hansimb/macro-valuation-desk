from __future__ import annotations

import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.lib.source.adapters.base import SourceAdapter
from src.lib.runtime_env import load_project_env
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


class FredAdapter(SourceAdapter):
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def fetch_series(
        self,
        series_definition: SeriesDefinition,
        fetch_options: FetchOptions,
    ) -> FetchResult:
        load_project_env()
        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            return FetchResult.failure(
                provider=series_definition.provider,
                key=series_definition.key,
                external_series_id=series_definition.external_series_id,
                error_type="config_error",
                message="FRED_API_KEY is required for FRED series requests.",
            )

        query_params = {
            "series_id": series_definition.external_series_id,
            "api_key": api_key,
            "file_type": "json",
        }
        if fetch_options.start_date:
            query_params["observation_start"] = fetch_options.start_date
        if fetch_options.end_date:
            query_params["observation_end"] = fetch_options.end_date
        if fetch_options.limit is not None:
            query_params["limit"] = str(fetch_options.limit)

        request = Request(f"{self.BASE_URL}?{urlencode(query_params)}")

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

        observations = [
            Observation(date=item["date"], value=item["value"])
            for item in payload.get("observations", [])
        ]

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

from __future__ import annotations

import csv
import io
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.lib.source.adapters.base import SourceAdapter
from src.lib.source.types import FetchOptions, FetchResult, Observation, SeriesDefinition, StandardizedSeries


class EcbAdapter(SourceAdapter):
    BASE_URL = "https://data-api.ecb.europa.eu/service/data"

    def fetch_series(
        self,
        series_definition: SeriesDefinition,
        fetch_options: FetchOptions,
    ) -> FetchResult:
        query_params = {"format": "csvdata"}
        if fetch_options.start_date:
            query_params["startPeriod"] = fetch_options.start_date
        if fetch_options.end_date:
            query_params["endPeriod"] = fetch_options.end_date
        if fetch_options.limit is not None:
            query_params["lastNObservations"] = str(fetch_options.limit)

        request = Request(
            f"{self.BASE_URL}/{series_definition.external_series_id}?{urlencode(query_params)}"
        )

        try:
            with urlopen(request) as response:
                payload = response.read().decode("utf-8")
        except Exception as exc:
            return FetchResult.failure(
                provider=series_definition.provider,
                key=series_definition.key,
                external_series_id=series_definition.external_series_id,
                error_type="fetch_error",
                message=str(exc),
            )

        reader = csv.DictReader(io.StringIO(payload))
        observations = [
            Observation(date=row["TIME_PERIOD"], value=row["OBS_VALUE"])
            for row in reader
            if row.get("TIME_PERIOD") and row.get("OBS_VALUE")
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

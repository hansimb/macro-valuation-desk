from __future__ import annotations

import csv
import io
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
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

    if response_body and "<html" in response_body.lower():
        summary = _summarize_html_response(response_body)
        if summary:
            return f"{exc} for URL {exc.url}. Summary: {summary}"

    if response_body:
        return f"{exc} for URL {exc.url}. Response body: {response_body}"

    return f"{exc} for URL {exc.url}"


def _summarize_html_response(response_body: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", response_body, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    for marker in (
        "Your access has been blocked due to security concerns.",
        "HTTP status code: 400",
    ):
        if marker not in text:
            continue

    snippets: list[str] = []
    if "Your access has been blocked due to security concerns." in text:
        snippets.append("Your access has been blocked due to security concerns.")
    if "We advise you to clean the cookies and try again." in text:
        snippets.append("We advise you to clean the cookies and try again.")
    if "HTTP status code: 400" in text:
        snippets.append("HTTP status code: 400.")

    if snippets:
        return " ".join(snippets)

    return text[:240]


class EcbAdapter(SourceAdapter):
    BASE_URL = "https://data-api.ecb.europa.eu/service/data"
    REQUEST_HEADERS = {
        "Accept": "text/csv,application/vnd.ecb.data+csv;version=1.0.0",
        "User-Agent": "macro-valuation-desk/0.1 (contact: local-dev)",
    }

    @staticmethod
    def _normalize_period(value: str, frequency: str) -> str:
        if frequency == "daily":
            return value
        if frequency == "monthly":
            return value[:7]
        if frequency == "quarterly":
            year, month, _day = value.split("-", 2)
            quarter = ((int(month) - 1) // 3) + 1
            return f"{year}-Q{quarter}"

        return value

    def fetch_series(
        self,
        series_definition: SeriesDefinition,
        fetch_options: FetchOptions,
    ) -> FetchResult:
        query_params = {"format": "csvdata"}
        if fetch_options.start_date:
            query_params["startPeriod"] = self._normalize_period(
                fetch_options.start_date,
                series_definition.frequency,
            )
        if fetch_options.end_date:
            query_params["endPeriod"] = self._normalize_period(
                fetch_options.end_date,
                series_definition.frequency,
            )
        if fetch_options.limit is not None:
            query_params["lastNObservations"] = str(fetch_options.limit)

        flow_ref = series_definition.external_series_id.split(".", 1)[0]
        request = Request(
            f"{self.BASE_URL}/{flow_ref}/{series_definition.external_series_id}?{urlencode(query_params)}",
            headers=self.REQUEST_HEADERS,
        )

        try:
            with urlopen(request) as response:
                payload = response.read().decode("utf-8")
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

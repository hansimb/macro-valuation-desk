from __future__ import annotations

import json
import os
from collections.abc import Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.lib.runtime_env import load_project_env
from src.lib.source.equity_market_valuation import (
    EquityMarketValuationResult,
    parse_eodhd_fundamentals_snapshot,
)


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


class EodhdAdapter:
    BASE_URL = "https://eodhd.com/api/fundamentals"

    def __init__(
        self,
        *,
        api_token: str | None = None,
        opener: Callable[[Request], object] | None = None,
    ) -> None:
        self.api_token = api_token
        self.opener = opener

    def fetch_fundamentals_snapshot(self, symbol: str) -> EquityMarketValuationResult:
        load_project_env()
        api_token = self.api_token or os.getenv("EODHD_API_TOKEN")
        if not api_token:
            return EquityMarketValuationResult.failure(
                provider="eodhd",
                key=symbol,
                external_series_id=symbol,
                error_type="config_error",
                message="EODHD_API_TOKEN is required for EODHD fundamentals requests.",
            )

        request = Request(
            f"{self.BASE_URL}/{symbol}?{urlencode({'api_token': api_token, 'fmt': 'json'})}"
        )

        try:
            opener = self.opener or urlopen
            with opener(request) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return EquityMarketValuationResult.failure(
                provider="eodhd",
                key=symbol,
                external_series_id=symbol,
                error_type="fetch_error",
                message=_format_http_error(exc),
            )
        except json.JSONDecodeError as exc:
            return EquityMarketValuationResult.failure(
                provider="eodhd",
                key=symbol,
                external_series_id=symbol,
                error_type="parse_error",
                message=f"Invalid JSON from EODHD fundamentals response: {exc}",
            )
        except Exception as exc:
            return EquityMarketValuationResult.failure(
                provider="eodhd",
                key=symbol,
                external_series_id=symbol,
                error_type="fetch_error",
                message=str(exc),
            )

        return EquityMarketValuationResult.success(parse_eodhd_fundamentals_snapshot(payload))

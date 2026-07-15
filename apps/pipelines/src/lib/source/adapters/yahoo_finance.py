from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.lib.source.equity_market_valuation import (
    EquityMarketValuationResult,
    EquityMarketValuationSnapshot,
)


MODULES = "price,defaultKeyStatistics,summaryDetail"
BASE_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary"


def _yahoo_symbol(symbol: str) -> str:
    return symbol.removesuffix(".US")


def _raw_float(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("raw")
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dividend_yield_pct(value: Any) -> float | None:
    parsed = _raw_float(value)
    if parsed is None:
        return None
    return parsed * 100 if parsed < 1 else parsed


def _regular_market_date(price: dict[str, Any]) -> str:
    raw_time = _raw_float(price.get("regularMarketTime"))
    if raw_time is None:
        return datetime.now(UTC).date().isoformat()
    return datetime.fromtimestamp(raw_time, UTC).date().isoformat()


def _quote_result(payload: dict[str, Any]) -> dict[str, Any] | None:
    quote_summary = payload.get("quoteSummary") or {}
    results = quote_summary.get("result") or []
    if not results:
        return None
    first_result = results[0]
    return first_result if isinstance(first_result, dict) else None


def parse_yahoo_quote_summary_snapshot(
    payload: dict[str, Any],
    *,
    symbol: str,
    source_url: str,
) -> EquityMarketValuationSnapshot:
    result = _quote_result(payload)
    if result is None:
        raise ValueError("Yahoo Finance quoteSummary response did not include a result.")

    price = result.get("price") or {}
    key_stats = result.get("defaultKeyStatistics") or {}
    summary_detail = result.get("summaryDetail") or {}
    parsed_values = {
        "trailing_pe": _raw_float(key_stats.get("trailingPE") or summary_detail.get("trailingPE")),
        "price_to_book": _raw_float(key_stats.get("priceToBook")),
        "price_to_sales": _raw_float(
            key_stats.get("priceToSalesTrailing12Months")
            or summary_detail.get("priceToSalesTrailing12Months")
        ),
        "price_to_cash_flow": _raw_float(key_stats.get("priceToCashFlow")),
        "dividend_yield_pct": _dividend_yield_pct(summary_detail.get("dividendYield")),
    }
    missing_fields = []
    if parsed_values["trailing_pe"] is None:
        missing_fields.append("quoteSummary.result[0].defaultKeyStatistics.trailingPE")
    if parsed_values["price_to_book"] is None:
        missing_fields.append("quoteSummary.result[0].defaultKeyStatistics.priceToBook")
    if parsed_values["price_to_sales"] is None:
        missing_fields.append("quoteSummary.result[0].summaryDetail.priceToSalesTrailing12Months")
    if parsed_values["price_to_cash_flow"] is None:
        missing_fields.append("quoteSummary.result[0].defaultKeyStatistics.priceToCashFlow")
    if parsed_values["dividend_yield_pct"] is None:
        missing_fields.append("quoteSummary.result[0].summaryDetail.dividendYield")

    return EquityMarketValuationSnapshot(
        provider="yahoo_finance",
        symbol=price.get("symbol") or symbol,
        exchange=price.get("exchangeName"),
        name=price.get("shortName") or price.get("longName"),
        instrument_type=price.get("quoteType"),
        trailing_pe=parsed_values["trailing_pe"],
        price_to_book=parsed_values["price_to_book"],
        price_to_sales=parsed_values["price_to_sales"],
        price_to_cash_flow=parsed_values["price_to_cash_flow"],
        dividend_yield_pct=parsed_values["dividend_yield_pct"],
        price_to_free_cash_flow=None,
        price_to_cash_flow_method=(
            "provider_price_to_cash_flow_proxy"
            if parsed_values["price_to_cash_flow"] is not None
            else "provider_price_to_cash_flow_unavailable"
        ),
        price_to_free_cash_flow_method="provider_exact_price_to_free_cash_flow_unavailable",
        missing_fields=missing_fields,
        source_url=source_url,
        as_of=_regular_market_date(price),
    )


class YahooFinanceAdapter:
    def __init__(self, *, opener=None) -> None:
        self.opener = opener

    def fetch_fundamentals_snapshot(self, symbol: str) -> EquityMarketValuationResult:
        yahoo_symbol = _yahoo_symbol(symbol)
        source_url = f"{BASE_URL}/{yahoo_symbol}"
        request_url = f"{source_url}?{urlencode({'modules': MODULES})}"
        request = Request(request_url, headers={"User-Agent": "macro-valuation-desk/0.1"})

        try:
            opener = self.opener or urlopen
            with opener(request) as response:
                payload = json.loads(response.read().decode("utf-8"))
            snapshot = parse_yahoo_quote_summary_snapshot(
                payload,
                symbol=yahoo_symbol,
                source_url=source_url,
            )
        except json.JSONDecodeError as exc:
            return EquityMarketValuationResult.failure(
                provider="yahoo_finance",
                key=symbol,
                external_series_id=yahoo_symbol,
                error_type="parse_error",
                message=f"Invalid JSON from Yahoo Finance quoteSummary response: {exc}",
            )
        except Exception as exc:
            return EquityMarketValuationResult.failure(
                provider="yahoo_finance",
                key=symbol,
                external_series_id=yahoo_symbol,
                error_type="fetch_error",
                message=str(exc),
            )

        return EquityMarketValuationResult.success(snapshot, payload_json=payload)

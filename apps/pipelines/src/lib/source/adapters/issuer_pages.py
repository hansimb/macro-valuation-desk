from __future__ import annotations

import html
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.lib.source.equity_market_valuation import (
    EquityMarketValuationResult,
    EquityMarketValuationSnapshot,
)


ISHARES_LIST_URL = "https://www.ishares.com/us/products/etf-investments#!type=ishares"
SPDR_SPY_URL = "https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy"
ISHARES_BASE_URL = "https://www.ishares.com"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; macro-valuation-desk/0.1)"}


def _issuer_symbol(symbol: str) -> str:
    return symbol.removesuffix(".US")


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = html.unescape(value).replace(",", "").replace("%", "").strip()
    if not cleaned or cleaned in {"-", "--", "N/A"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _as_of_from_ishares_date(value: str | None) -> str:
    if not value:
        return datetime.now(UTC).date().isoformat()
    try:
        return datetime.strptime(value, "%b %d, %Y").date().isoformat()
    except ValueError:
        return datetime.now(UTC).date().isoformat()


def _last_modified_date(headers: Any) -> str:
    last_modified = headers.get("Last-Modified") if headers is not None else None
    if not last_modified:
        return datetime.now(UTC).date().isoformat()
    try:
        return parsedate_to_datetime(last_modified).date().isoformat()
    except (TypeError, ValueError):
        return datetime.now(UTC).date().isoformat()


def _embedded_value(page_html: str, field_name: str) -> float | None:
    page_html = html.unescape(page_html)
    match = re.search(
        rf'"{re.escape(field_name)}"\s*:\s*\{{.*?"formattedValue"\s*:\s*"([^"]+)"',
        page_html,
        flags=re.S,
    )
    return _optional_float(match.group(1)) if match else None


def _embedded_date(page_html: str, field_name: str) -> str | None:
    page_html = html.unescape(page_html)
    match = re.search(
        rf'"{re.escape(field_name)}"\s*:\s*\{{.*?"formattedAsOfDate"\s*:\s*"([^"]+)"',
        page_html,
        flags=re.S,
    )
    return html.unescape(match.group(1)) if match else None


def parse_ishares_url_from_product_list(page_html: str, symbol: str) -> str:
    match = re.search(
        rf'<a href="([^"]+)">\s*{re.escape(symbol)}\s*</a>',
        page_html,
        flags=re.I,
    )
    if not match:
        raise ValueError(f"Could not find iShares product URL for {symbol}.")
    href = html.unescape(match.group(1))
    return href if href.startswith("http") else f"{ISHARES_BASE_URL}{href}"


def parse_ishares_snapshot(
    page_html: str,
    *,
    symbol: str,
    source_url: str,
) -> EquityMarketValuationSnapshot:
    trailing_pe = _embedded_value(page_html, "priceEarnings")
    price_to_book = _embedded_value(page_html, "priceBook")
    dividend_yield_pct = _embedded_value(page_html, "twelveMonTrlYld")
    as_of = _as_of_from_ishares_date(
        _embedded_date(page_html, "priceEarnings")
        or _embedded_date(page_html, "priceBook")
        or _embedded_date(page_html, "twelveMonTrlYld")
    )
    missing_fields = []
    if trailing_pe is None:
        missing_fields.append("issuer_page.priceEarnings")
    if price_to_book is None:
        missing_fields.append("issuer_page.priceBook")
    if dividend_yield_pct is None:
        missing_fields.append("issuer_page.twelveMonTrlYld")

    return _snapshot(
        symbol=symbol,
        source_url=source_url,
        as_of=as_of,
        trailing_pe=trailing_pe,
        price_to_book=price_to_book,
        dividend_yield_pct=dividend_yield_pct,
        missing_fields=missing_fields,
    )


def _spdr_table_value(page_html: str, label: str) -> float | None:
    match = re.search(
        rf"{re.escape(label)}.*?<td[^>]*class=\"data\"[^>]*>(.*?)</td>",
        page_html,
        flags=re.I | re.S,
    )
    return _optional_float(re.sub(r"<.*?>", "", match.group(1))) if match else None


def parse_spdr_snapshot(
    page_html: str,
    *,
    symbol: str,
    source_url: str,
    as_of: str | None = None,
) -> EquityMarketValuationSnapshot:
    index_date = re.search(
        r'Index Characteristics\s*<span[^>]*class="date"[^>]*>as of ([A-Za-z]{3} \d{1,2} \d{4})</span>',
        page_html,
    )
    if index_date:
        try:
            as_of = datetime.strptime(index_date.group(1), "%b %d %Y").date().isoformat()
        except ValueError:
            pass
    # FY1 is forecast earnings; generic index P/E is not documented here as TTM.
    # Neither can truthfully populate the existing trailing_pe contract.
    trailing_pe = None
    price_to_cash_flow = _spdr_table_value(page_html, "Price/Cash Flow")
    price_to_book = _spdr_table_value(page_html, "Price/Book Ratio")
    dividend_yield_pct = _spdr_table_value(page_html, "Index Dividend Yield")
    missing_fields = []
    if trailing_pe is None:
        missing_fields.append("issuer_page.trailingPe_unavailable_FY1_is_forward")
    if price_to_book is None:
        missing_fields.append("issuer_page.Price/Book Ratio")
    if dividend_yield_pct is None:
        missing_fields.append("issuer_page.Index Dividend Yield")

    return _snapshot(
        symbol=symbol,
        source_url=source_url,
        as_of=as_of or datetime.now(UTC).date().isoformat(),
        price_to_cash_flow=price_to_cash_flow,
        trailing_pe=trailing_pe,
        price_to_book=price_to_book,
        dividend_yield_pct=dividend_yield_pct,
        missing_fields=missing_fields,
    )


def _snapshot(
    *,
    symbol: str,
    source_url: str,
    as_of: str,
    trailing_pe: float | None,
    price_to_book: float | None,
    dividend_yield_pct: float | None,
    missing_fields: list[str],
    price_to_cash_flow: float | None = None,
) -> EquityMarketValuationSnapshot:
    return EquityMarketValuationSnapshot(
        provider="issuer_pages",
        symbol=symbol,
        exchange="US",
        name=None,
        instrument_type="ETF",
        trailing_pe=trailing_pe,
        price_to_book=price_to_book,
        price_to_sales=None,
        price_to_cash_flow=price_to_cash_flow,
        dividend_yield_pct=dividend_yield_pct,
        price_to_free_cash_flow=None,
        price_to_cash_flow_method=(
            "issuer_index_price_to_cash_flow_proxy" if price_to_cash_flow is not None
            else "provider_price_to_cash_flow_unavailable"
        ),
        price_to_free_cash_flow_method="provider_exact_price_to_free_cash_flow_unavailable",
        missing_fields=[
            *missing_fields, "issuer_page.priceToSales", "issuer_page.priceToFreeCashFlow",
            *(["issuer_page.priceToCashFlow"] if price_to_cash_flow is None else []),
        ],
        source_url=source_url,
        as_of=as_of,
    )


class IssuerPagesAdapter:
    def __init__(self, *, opener=None) -> None:
        self.opener = opener

    def _read_url(self, url: str):
        opener = self.opener or urlopen
        request = Request(url, headers=REQUEST_HEADERS)
        with opener(request) as response:
            return response.read().decode("utf-8", "replace"), getattr(response, "headers", None)

    def fetch_fundamentals_snapshot(self, symbol: str) -> EquityMarketValuationResult:
        issuer_symbol = _issuer_symbol(symbol)
        try:
            if issuer_symbol == "SPY":
                page_html, headers = self._read_url(SPDR_SPY_URL)
                snapshot = parse_spdr_snapshot(
                    page_html,
                    symbol=issuer_symbol,
                    source_url=SPDR_SPY_URL,
                    as_of=_last_modified_date(headers),
                )
                return EquityMarketValuationResult.success(
                    snapshot,
                    payload_json={"source": "spdr_page", "source_url": SPDR_SPY_URL},
                )

            product_list_html, _headers = self._read_url(ISHARES_LIST_URL)
            source_url = parse_ishares_url_from_product_list(product_list_html, issuer_symbol)
            page_html, _headers = self._read_url(source_url)
            snapshot = parse_ishares_snapshot(page_html, symbol=issuer_symbol, source_url=source_url)
            return EquityMarketValuationResult.success(
                snapshot,
                payload_json={"source": "ishares_page", "source_url": source_url},
            )
        except HTTPError as exc:
            return EquityMarketValuationResult.failure(
                provider="issuer_pages",
                key=symbol,
                external_series_id=issuer_symbol,
                error_type="fetch_error",
                message=str(exc),
            )
        except Exception as exc:
            return EquityMarketValuationResult.failure(
                provider="issuer_pages",
                key=symbol,
                external_series_id=issuer_symbol,
                error_type="fetch_error",
                message=str(exc),
            )

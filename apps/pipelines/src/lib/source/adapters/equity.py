from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, date, datetime
from html import unescape
from urllib.parse import quote
from urllib.request import Request, urlopen


WIKIPEDIA_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=3mo&interval=1d"
SOURCE_PROVIDER = "wikipedia+sec+yahoo-chart"
DEFAULT_USER_AGENT = "macro-valuation-desk/0.1 contact: local-dev"

REVENUE_TAGS = (
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
)

COUNTRIES = {
    "Bermuda": ("BM", "Bermuda"),
    "Ireland": ("IE", "Ireland"),
    "Netherlands": ("NL", "Netherlands"),
    "Switzerland": ("CH", "Switzerland"),
    "United Kingdom": ("GB", "United Kingdom"),
}


@dataclass(frozen=True)
class Constituent:
    ticker: str
    company: str
    sector: str
    headquarters: str
    cik: str


def _fetch_text(url: str, headers: dict[str, str] | None = None) -> str:
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=8) as response:
        return response.read().decode("utf-8")


def _clean_cell(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_sp500_constituents(html: str) -> list[Constituent]:
    table_match = re.search(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    if not table_match:
        return []

    rows: list[Constituent] = []
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", table_match.group(1), re.DOTALL | re.IGNORECASE):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL | re.IGNORECASE)
        if len(cells) < 7:
            continue

        ticker = _clean_cell(cells[0])
        company = _clean_cell(cells[1])
        sector = _clean_cell(cells[2])
        headquarters = _clean_cell(cells[4])
        cik = _clean_cell(cells[6]).zfill(10)
        if ticker and company and sector and cik:
            rows.append(
                Constituent(
                    ticker=ticker,
                    company=company,
                    sector=sector,
                    headquarters=headquarters,
                    cik=cik,
                )
            )

    return rows


def _country_from_headquarters(headquarters: str) -> tuple[str, str]:
    for needle, country in COUNTRIES.items():
        if needle in headquarters:
            return country

    return ("US", "United States")


def _duration_days(item: dict[str, object]) -> int | None:
    start = item.get("start")
    end = item.get("end")
    if not isinstance(start, str) or not isinstance(end, str):
        return None

    try:
        return (date.fromisoformat(end) - date.fromisoformat(start)).days
    except ValueError:
        return None


def _latest_annual_revenue(companyfacts: dict[str, object]) -> float | None:
    us_gaap = companyfacts.get("facts", {}).get("us-gaap", {})  # type: ignore[union-attr]
    candidates: list[dict[str, object]] = []

    for tag in REVENUE_TAGS:
        values = us_gaap.get(tag, {}).get("units", {}).get("USD", [])  # type: ignore[union-attr]
        for item in values:
            duration = _duration_days(item)
            value = item.get("val")
            if (
                item.get("form") == "10-K"
                and duration is not None
                and 300 <= duration <= 450
                and isinstance(value, int | float)
                and value > 0
            ):
                candidates.append(item)

    if not candidates:
        return None

    latest = max(candidates, key=lambda item: (str(item.get("end") or ""), str(item.get("filed") or "")))
    return float(latest["val"])


def _latest_shares_outstanding(companyfacts: dict[str, object]) -> float | None:
    values = (
        companyfacts.get("facts", {})
        .get("dei", {})
        .get("EntityCommonStockSharesOutstanding", {})
        .get("units", {})
        .get("shares", [])
    )
    candidates = [
        item for item in values if isinstance(item.get("val"), int | float) and float(item["val"]) > 0
    ]
    if not candidates:
        return None

    latest = max(candidates, key=lambda item: (str(item.get("end") or ""), str(item.get("filed") or "")))
    return float(latest["val"])


def _chart_metrics(chart_payload: dict[str, object]) -> tuple[str, float, float] | None:
    result = chart_payload.get("chart", {}).get("result", [])  # type: ignore[union-attr]
    if not result:
        return None

    first = result[0]
    timestamps = first.get("timestamp", [])
    quotes = first.get("indicators", {}).get("quote", [])  # type: ignore[union-attr]
    if not timestamps or not quotes:
        return None

    close_values = quotes[0].get("close", [])
    volume_values = quotes[0].get("volume", [])
    pairs = [
        (int(timestamp), float(close), float(volume))
        for timestamp, close, volume in zip(timestamps, close_values, volume_values, strict=False)
        if close is not None and volume is not None and float(close) > 0 and float(volume) > 0
    ]
    if not pairs:
        return None

    latest_timestamp, latest_close, _latest_volume = pairs[-1]
    traded_values = [close * volume for _timestamp, close, volume in pairs[-60:]]
    average_daily_traded_value = sum(traded_values) / len(traded_values)
    as_of_date = datetime.fromtimestamp(latest_timestamp, tz=UTC).date().isoformat()
    return as_of_date, latest_close, average_daily_traded_value


def _yahoo_symbol(ticker: str) -> str:
    return ticker.replace(".", "-")


def _build_row(
    constituent: Constituent,
    *,
    fetch_text,
    as_of_date: str | None,
) -> dict[str, object] | None:
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    companyfacts = json.loads(fetch_text(SEC_COMPANYFACTS_URL.format(cik=constituent.cik), headers))
    revenue = _latest_annual_revenue(companyfacts)
    shares = _latest_shares_outstanding(companyfacts)
    if revenue is None or shares is None:
        return None

    chart = json.loads(
        fetch_text(
            YAHOO_CHART_URL.format(symbol=quote(_yahoo_symbol(constituent.ticker))),
            headers,
        )
    )
    metrics = _chart_metrics(chart)
    if metrics is None:
        return None

    chart_as_of_date, close_price, average_daily_traded_value = metrics
    market_cap = close_price * shares
    country_code, country_name = _country_from_headquarters(constituent.headquarters)

    return {
        "universe_key": "sp500",
        "as_of_date": as_of_date or chart_as_of_date,
        "ticker": constituent.ticker,
        "company": constituent.company,
        "country_code": country_code,
        "country_name": country_name,
        "sector": constituent.sector,
        "market_cap": market_cap,
        "trailing_12m_revenue": revenue,
        "ps_ratio": market_cap / revenue,
        "index_weight_pct": 0.0,
        "average_daily_traded_value": average_daily_traded_value,
        "source_provider": SOURCE_PROVIDER,
        "source_url": WIKIPEDIA_SP500_URL,
    }


def build_sp500_constituent_snapshot_rows(
    *,
    fetch_text=_fetch_text,
    as_of_date: str | None = None,
    max_workers: int = 24,
    max_constituents: int | None = None,
) -> list[dict[str, object]]:
    try:
        wikipedia_html = fetch_text(WIKIPEDIA_SP500_URL, {"User-Agent": DEFAULT_USER_AGENT})
    except Exception:
        return []

    constituents = _parse_sp500_constituents(wikipedia_html)
    if max_constituents is not None:
        constituents = constituents[:max_constituents]
    rows: list[dict[str, object]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_build_row, constituent, fetch_text=fetch_text, as_of_date=as_of_date)
            for constituent in constituents
        ]
        for future in as_completed(futures):
            try:
                row = future.result()
            except Exception:
                continue
            if row is not None:
                rows.append(row)

    total_market_cap = sum(float(row["market_cap"]) for row in rows)
    if total_market_cap <= 0:
        return []

    for row in rows:
        row["market_cap"] = round(float(row["market_cap"]), 2)
        row["ps_ratio"] = round(float(row["ps_ratio"]), 4)
        row["index_weight_pct"] = round(float(row["market_cap"]) / total_market_cap * 100, 2)
        row["average_daily_traded_value"] = round(float(row["average_daily_traded_value"]), 2)

    return sorted(rows, key=lambda row: float(row["market_cap"]), reverse=True)

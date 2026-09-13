from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from math import isfinite
from urllib.request import Request, urlopen

from src.lib.source.country_index_types import DailyPrice, ProviderLicense, SecurityListing


FetchJson = Callable[[str], Mapping[str, object]]


class DevelopmentPriceAdapter:
    """Development-only Yahoo Finance price adapter with split-only adjustments.

    Yahoo's ``adjclose`` can include dividend adjustments.  It is deliberately
    unused: this adapter derives ``split_adjusted_close_price`` only from raw
    closes and reported split events, leaving dividend adjustments out of the
    country-index price series.
    """

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
    PROVIDER = "yahoo_finance_development"
    LICENSE_CLASS = "development_only"

    def __init__(
        self,
        *,
        fetch_json: FetchJson | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._fetch_json = fetch_json or _fetch_json
        self._now = now or (lambda: datetime.now(UTC))
        self.license = ProviderLicense(
            provider=self.PROVIDER,
            usage=self.LICENSE_CLASS,
            terms_url="https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html",
        )

    def assert_publishable(self, *, environment: str) -> None:
        if environment.lower() == "production":
            raise ValueError("development-only prices cannot be published in production")

    def daily_prices(
        self,
        security: SecurityListing,
        start: date,
        end: date,
    ) -> list[DailyPrice]:
        if not isinstance(start, date) or not isinstance(end, date) or start > end:
            raise ValueError("price date range must have valid start and end dates")
        self.assert_publishable(environment=os.getenv("MVD_ENV", "development"))
        source_url = self._source_url(security.ticker, start, end)
        payload = self._fetch_json(source_url)
        return _parse_prices(
            payload,
            security=security,
            start=start,
            end=end,
            provider_timestamp=_ensure_utc(self._now()),
            source_url=source_url,
        )

    def _source_url(self, ticker: str, start: date, end: date) -> str:
        normalized_ticker = ticker.strip().upper()
        if not normalized_ticker:
            raise ValueError("security ticker is required for development prices")
        return (
            f"{self.BASE_URL}/{normalized_ticker}?interval=1d&period1={_epoch(start)}"
            f"&period2={_epoch(end + timedelta(days=1))}"
        )


def _fetch_json(url: str) -> Mapping[str, object]:
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "macro-valuation-desk/0.1"},
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"development price endpoint returned non-object JSON for {url}")
    return payload


def _parse_prices(
    payload: Mapping[str, object],
    *,
    security: SecurityListing,
    start: date,
    end: date,
    provider_timestamp: datetime,
    source_url: str,
) -> list[DailyPrice]:
    chart = _mapping(payload.get("chart"), "chart")
    results = chart.get("result")
    if not isinstance(results, Sequence) or isinstance(results, (str, bytes)) or len(results) != 1:
        raise ValueError("development price response must contain one chart result")
    result = _mapping(results[0], "chart result")
    timestamps = result.get("timestamp")
    if not isinstance(timestamps, Sequence) or isinstance(timestamps, (str, bytes)) or not timestamps:
        raise ValueError("development price response has missing trading dates")
    closes = _single_mapping(_mapping(result.get("indicators"), "indicators").get("quote"), "quote").get("close")
    if not isinstance(closes, Sequence) or isinstance(closes, (str, bytes)) or len(closes) != len(timestamps):
        raise ValueError("development price response has invalid close prices")

    observations = _observations(timestamps, closes)
    splits = _split_events(result.get("events"))
    prices: list[DailyPrice] = []
    for trading_date, close_price in observations:
        if trading_date < start or trading_date > end:
            continue
        prices.append(
            DailyPrice(
                security_id=security.security_id,
                trading_date=trading_date,
                provider=DevelopmentPriceAdapter.PROVIDER,
                close_price=close_price,
                split_adjusted_close_price=_split_adjusted_close(close_price, trading_date, splits),
                trading_currency=security.trading_currency,
                provider_timestamp=provider_timestamp,
                license_class=DevelopmentPriceAdapter.LICENSE_CLASS,
                adjustment_metadata={"split": splits[trading_date].metadata}
                if trading_date in splits
                else {},
                source_url=source_url,
            )
        )
    return prices


@dataclass(frozen=True)
class _SplitEvent:
    date: date
    factor: Decimal
    metadata: Mapping[str, str]


def _observations(timestamps: Sequence[object], closes: Sequence[object]) -> list[tuple[date, object]]:
    observations: list[tuple[date, object]] = []
    seen_dates: set[date] = set()
    for timestamp, close_price in zip(timestamps, closes, strict=True):
        trading_date = _trading_date(timestamp)
        if trading_date in seen_dates:
            raise ValueError(f"development price response has duplicate trading date {trading_date.isoformat()}")
        seen_dates.add(trading_date)
        if not _is_positive_number(close_price):
            raise ValueError(f"development price response has invalid close price for {trading_date.isoformat()}")
        observations.append((trading_date, close_price))
    return observations


def _split_events(events: object) -> dict[date, _SplitEvent]:
    if events is None:
        return {}
    split_events = _mapping(events, "events").get("splits")
    if split_events is None:
        return {}
    if not isinstance(split_events, Mapping):
        raise ValueError("development price response has invalid split events")
    parsed: dict[date, _SplitEvent] = {}
    for split in split_events.values():
        details = _mapping(split, "split event")
        split_date = _trading_date(details.get("date"))
        factor, ratio = _split_factor(details)
        if split_date in parsed:
            raise ValueError(f"development price response has duplicate split event {split_date.isoformat()}")
        parsed[split_date] = _SplitEvent(
            date=split_date,
            factor=factor,
            metadata={"date": split_date.isoformat(), "ratio": ratio},
        )
    return parsed


def _split_factor(details: Mapping[str, object]) -> tuple[Decimal, str]:
    numerator = details.get("numerator")
    denominator = details.get("denominator")
    if numerator is None or denominator is None:
        raise ValueError("development price response has split ratio without numerator and denominator")
    try:
        top = Decimal(str(numerator))
        bottom = Decimal(str(denominator))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("development price response has invalid split ratio") from exc
    if not top.is_finite() or not bottom.is_finite() or top <= 0 or bottom <= 0:
        raise ValueError("development price response has invalid split ratio")
    ratio = str(details.get("splitRatio") or f"{numerator}:{denominator}").strip()
    return top / bottom, ratio


def _split_adjusted_close(
    close_price: object,
    trading_date: date,
    splits: Mapping[date, _SplitEvent],
) -> Decimal:
    factor = Decimal(1)
    for split_date, split in splits.items():
        if split_date > trading_date:
            factor *= split.factor
    return Decimal(str(close_price)) / factor


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"development price response has invalid {name}")
    return value


def _single_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 1:
        raise ValueError(f"development price response has invalid {name}")
    return _mapping(value[0], name)


def _trading_date(value: object) -> date:
    if isinstance(value, bool) or value is None:
        raise ValueError("development price response has missing trading dates")
    try:
        return datetime.fromtimestamp(float(value), UTC).date()
    except (OverflowError, OSError, TypeError, ValueError) as exc:
        raise ValueError("development price response has invalid trading date") from exc


def _is_positive_number(value: object) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        number = float(value)
        return isfinite(number) and number > 0
    except (TypeError, ValueError):
        return False


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("development price provider timestamp must be timezone-aware")
    return value.astimezone(UTC)


def _epoch(value: date) -> int:
    return int(datetime.combine(value, time.min, UTC).timestamp())

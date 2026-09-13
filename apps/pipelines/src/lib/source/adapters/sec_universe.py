from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from urllib.request import Request, urlopen

from src.lib.source.country_index_types import SecurityListing


FetchJson = Callable[[str, Mapping[str, str]], Mapping[str, object]]


class SecUniverseAdapter:
    """Discover one active US common-stock listing per SEC registrant.

    SEC's exchange/ticker file is discovery metadata, not a security master.  The
    deterministic selection below therefore records exactly one primary common
    listing per CIK and deliberately leaves instruments that cannot represent a
    US common-stock primary listing out of the universe.
    """

    COMPANY_TICKERS_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
    _EXCHANGE_RANK = {"NYSE": 0, "NASDAQ": 1, "NYSE AMERICAN": 2, "NYSE ARCA": 3, "CBOE": 4}
    _INACTIVE_STATUSES = frozenset({"INACTIVE", "DELISTED", "SUSPENDED"})
    _EXCLUDED_NAME_MARKERS = (
        " ETF",
        "EXCHANGE TRADED FUND",
        " FUND",
        "MUTUAL FUND",
        "MONEY MARKET",
        "CLOSED-END",
        "CLOSED END",
        " ETN",
        " PREFERRED",
        " PREF ",
        " DEPOSITARY SHARE",
        " AMERICAN DEPOSITARY",
        " ADR",
        " ADS",
    )

    def __init__(
        self,
        *,
        fetch_json: FetchJson | None = None,
        user_agent: str | None = None,
    ) -> None:
        self._fetch_json = fetch_json or _fetch_json
        self._user_agent = (user_agent or os.getenv("SEC_USER_AGENT") or "").strip()

    def listings_as_of(self, market_id: str, as_of: date) -> list[SecurityListing]:
        if market_id.lower() != "us":
            raise ValueError("SecUniverseAdapter supports only the US market")
        if not isinstance(as_of, date):
            raise ValueError("as_of must be a date")
        if not self._user_agent or "@" not in self._user_agent:
            raise ValueError(
                "SEC_USER_AGENT or an explicit user_agent with an identifiable "
                "organization and monitored contact email is required for SEC requests."
            )

        payload = self._fetch_json(self.COMPANY_TICKERS_EXCHANGE_URL, self._headers())
        candidates = _active_common_stock_candidates(payload, as_of)
        selected_by_cik: dict[str, _ListingCandidate] = {}
        for candidate in candidates:
            incumbent = selected_by_cik.get(candidate.cik)
            if incumbent is None or candidate.sort_key < incumbent.sort_key:
                selected_by_cik[candidate.cik] = candidate

        return [
            candidate.to_listing()
            for candidate in sorted(selected_by_cik.values(), key=lambda item: (item.cik, item.ticker))
        ]

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "User-Agent": self._user_agent}


class _ListingCandidate:
    def __init__(
        self,
        *,
        cik: str,
        issuer_name: str,
        ticker: str,
        exchange_code: str,
        valid_from: date,
        valid_to: date | None,
    ) -> None:
        self.cik = cik
        self.issuer_name = issuer_name
        self.ticker = ticker
        self.exchange_code = exchange_code
        self.valid_from = valid_from
        self.valid_to = valid_to

    @property
    def sort_key(self) -> tuple[int, int, str, str]:
        return (
            SecUniverseAdapter._EXCHANGE_RANK.get(self.exchange_code, 99),
            _share_class_rank(self.issuer_name),
            self.ticker,
            self.exchange_code,
        )

    def to_listing(self) -> SecurityListing:
        external_id = f"{self.cik}:{self.ticker}"
        return SecurityListing(
            listing_id=f"sec:{external_id}",
            security_id=f"sec:{external_id}",
            issuer_id=self.cik,
            issuer_name=self.issuer_name,
            security_type="common_stock",
            market_id="us",
            exchange_code=self.exchange_code,
            ticker=self.ticker,
            trading_currency="USD",
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            listing_status="active",
            source_provider="sec",
            source_external_id=external_id,
            share_class=_share_class(self.issuer_name),
            is_primary=True,
        )


def _fetch_json(url: str, headers: Mapping[str, str]) -> Mapping[str, object]:
    request = Request(url, headers=dict(headers))
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"SEC returned a non-object JSON payload for {url}")
    return payload


def _active_common_stock_candidates(
    payload: Mapping[str, object], as_of: date
) -> list[_ListingCandidate]:
    fields = payload.get("fields")
    rows = payload.get("data")
    if not isinstance(fields, list) or not isinstance(rows, list):
        raise ValueError("SEC ticker metadata must contain fields and data arrays")
    indexes = {str(field).lower(): index for index, field in enumerate(fields)}
    required = ("cik", "name", "ticker", "exchange")
    missing = next((field for field in required if field not in indexes), None)
    if missing is not None:
        raise ValueError(f"SEC ticker metadata is missing field {missing!r}")

    candidates: list[_ListingCandidate] = []
    for row in rows:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
            raise ValueError("SEC ticker metadata contains a malformed row")
        if len(row) <= max(indexes[field] for field in required):
            raise ValueError("SEC ticker metadata contains a malformed row")

        cik = _normalize_cik(row[indexes["cik"]])
        issuer_name = str(row[indexes["name"]]).strip()
        ticker = str(row[indexes["ticker"]]).strip().upper()
        exchange_code = " ".join(str(row[indexes["exchange"]]).upper().split())
        if not issuer_name or not ticker or not exchange_code:
            continue
        if _is_excluded_security(issuer_name) or not _is_active_as_of(row, indexes, as_of):
            continue
        valid_from = _row_date(row, indexes, "valid_from") or _row_date(row, indexes, "active_from")
        valid_to = _row_date(row, indexes, "valid_to") or _row_date(row, indexes, "active_to")
        candidates.append(
            _ListingCandidate(
                cik=cik,
                issuer_name=issuer_name,
                ticker=ticker,
                exchange_code=exchange_code,
                valid_from=valid_from or date.min,
                valid_to=valid_to,
            )
        )
    return candidates


def _is_active_as_of(row: Sequence[object], indexes: Mapping[str, int], as_of: date) -> bool:
    status_index = indexes.get("status")
    if status_index is not None and status_index < len(row):
        status = str(row[status_index]).strip().upper()
        if status in SecUniverseAdapter._INACTIVE_STATUSES:
            return False
    valid_from = _row_date(row, indexes, "valid_from") or _row_date(row, indexes, "active_from")
    valid_to = _row_date(row, indexes, "valid_to") or _row_date(row, indexes, "active_to")
    return (valid_from is None or valid_from <= as_of) and (valid_to is None or as_of <= valid_to)


def _row_date(row: Sequence[object], indexes: Mapping[str, int], field: str) -> date | None:
    index = indexes.get(field)
    if index is None or index >= len(row) or row[index] in (None, ""):
        return None
    value = row[index]
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"SEC ticker metadata has an invalid {field}: {value!r}") from exc


def _normalize_cik(value: object) -> str:
    normalized = str(value).strip()
    if normalized.upper().startswith("CIK"):
        normalized = normalized[3:]
    if not normalized.isdigit() or not normalized:
        raise ValueError(f"SEC CIK must contain only digits: {value!r}")
    return f"{int(normalized):010d}"


def _is_excluded_security(issuer_name: str) -> bool:
    normalized = f" {' '.join(issuer_name.upper().split())} "
    return any(marker in normalized for marker in SecUniverseAdapter._EXCLUDED_NAME_MARKERS)


def _share_class_rank(issuer_name: str) -> int:
    normalized = issuer_name.upper()
    if "CLASS A" in normalized:
        return 0
    if "CLASS B" in normalized:
        return 1
    if "CLASS C" in normalized:
        return 2
    return 0


def _share_class(issuer_name: str) -> str | None:
    normalized = issuer_name.upper()
    for share_class in ("A", "B", "C"):
        if f"CLASS {share_class}" in normalized:
            return share_class
    return None

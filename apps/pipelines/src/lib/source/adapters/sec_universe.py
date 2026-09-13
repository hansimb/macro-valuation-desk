from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from urllib.request import Request, urlopen

from src.lib.source.country_index_types import SecurityListing


FetchJson = Callable[[str, Mapping[str, str]], Mapping[str, object]]


@dataclass(frozen=True)
class SecDiscoveryRow:
    cik: str
    name: str
    ticker: str
    exchange: str

    @property
    def source_external_id(self) -> str:
        return f"{self.cik}:{self.ticker}"


@dataclass(frozen=True)
class ListingEnrichment:
    """Auditable classification and listing-history data supplied outside SEC discovery."""

    listing_id: str
    security_id: str
    issuer_id: str
    issuer_name: str
    security_type: str
    market_id: str
    exchange_code: str
    ticker: str
    trading_currency: str
    valid_from: date
    valid_to: date | None
    listing_status: str
    is_primary: bool
    share_class: str | None
    is_adr: bool
    source_provider: str
    source_external_id: str


@dataclass(frozen=True)
class UniverseAuditEntry:
    source_external_id: str
    ticker: str
    included: bool
    reason: str


@dataclass(frozen=True)
class SecUniverseResult:
    listings: tuple[SecurityListing, ...]
    audit: tuple[UniverseAuditEntry, ...]


EnrichListing = Callable[[SecDiscoveryRow], ListingEnrichment | None]


class SecUniverseAdapter:
    """Use SEC ticker discovery only after injected security-master enrichment.

    ``company_tickers_exchange.json`` is not a security master.  Its four fields
    never establish security type, listing history, currency, or primary-listing
    status.  Rows without an injected ``ListingEnrichment`` therefore fail closed
    and remain inspectable through ``assess_listings_as_of`` audit entries.
    """

    COMPANY_TICKERS_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"

    def __init__(
        self,
        *,
        fetch_json: FetchJson | None = None,
        enrich_listing: EnrichListing | None = None,
        user_agent: str | None = None,
    ) -> None:
        self._fetch_json = fetch_json or _fetch_json
        self._enrich_listing = enrich_listing
        self._user_agent = (user_agent or os.getenv("SEC_USER_AGENT") or "").strip()

    def listings_as_of(self, market_id: str, as_of: date) -> list[SecurityListing]:
        """Return the protocol-compatible eligible listings, omitting failed rows."""
        return list(self.assess_listings_as_of(market_id, as_of).listings)

    def assess_listings_as_of(self, market_id: str, as_of: date) -> SecUniverseResult:
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
        assessments = [self._assess_row(row, as_of) for row in _discovery_rows(payload)]
        selected = _select_primary_security_listings(assessments)
        audit: list[UniverseAuditEntry] = []
        for row, listing, reason in assessments:
            if reason is not None:
                audit.append(UniverseAuditEntry(row.source_external_id, row.ticker, False, reason))
            elif listing is not None and selected.get(listing.security_id) is listing:
                audit.append(UniverseAuditEntry(row.source_external_id, row.ticker, True, "eligible"))
            else:
                audit.append(
                    UniverseAuditEntry(
                        row.source_external_id,
                        row.ticker,
                        False,
                        "duplicate_security_listing",
                    )
                )
        listings = tuple(sorted(selected.values(), key=lambda listing: (listing.security_id, listing.listing_id)))
        return SecUniverseResult(listings=listings, audit=tuple(audit))

    def _assess_row(
        self,
        row: SecDiscoveryRow,
        as_of: date,
    ) -> tuple[SecDiscoveryRow, SecurityListing | None, str | None]:
        if self._enrich_listing is None:
            return row, None, "missing_enrichment"
        try:
            enrichment = self._enrich_listing(row)
        except Exception:
            return row, None, "enrichment_error"
        if enrichment is None:
            return row, None, "missing_enrichment"
        if not isinstance(enrichment, ListingEnrichment):
            return row, None, "invalid_enrichment"
        reason = _eligibility_failure(enrichment, row, as_of)
        if reason is not None:
            return row, None, reason
        return row, _security_listing(enrichment), None

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "User-Agent": self._user_agent}


def _fetch_json(url: str, headers: Mapping[str, str]) -> Mapping[str, object]:
    request = Request(url, headers=dict(headers))
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"SEC returned a non-object JSON payload for {url}")
    return payload


def _discovery_rows(payload: Mapping[str, object]) -> list[SecDiscoveryRow]:
    fields = payload.get("fields")
    rows = payload.get("data")
    if not isinstance(fields, list) or not isinstance(rows, list):
        raise ValueError("SEC ticker metadata must contain fields and data arrays")
    indexes = {str(field).lower(): index for index, field in enumerate(fields)}
    required = ("cik", "name", "ticker", "exchange")
    missing = next((field for field in required if field not in indexes), None)
    if missing is not None:
        raise ValueError(f"SEC ticker metadata is missing field {missing!r}")

    discovery_rows: list[SecDiscoveryRow] = []
    for row in rows:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
            raise ValueError("SEC ticker metadata contains a malformed row")
        if len(row) <= max(indexes[field] for field in required):
            raise ValueError("SEC ticker metadata contains a malformed row")
        cik = _normalize_cik(row[indexes["cik"]])
        name = str(row[indexes["name"]]).strip()
        ticker = str(row[indexes["ticker"]]).strip().upper()
        exchange = " ".join(str(row[indexes["exchange"]]).upper().split())
        if not name or not ticker or not exchange:
            raise ValueError("SEC ticker metadata contains an empty discovery identity")
        discovery_rows.append(SecDiscoveryRow(cik=cik, name=name, ticker=ticker, exchange=exchange))
    return discovery_rows


def _eligibility_failure(
    enrichment: ListingEnrichment,
    row: SecDiscoveryRow,
    as_of: date,
) -> str | None:
    required_text = (
        enrichment.listing_id,
        enrichment.security_id,
        enrichment.issuer_id,
        enrichment.issuer_name,
        enrichment.security_type,
        enrichment.market_id,
        enrichment.exchange_code,
        enrichment.ticker,
        enrichment.trading_currency,
        enrichment.listing_status,
        enrichment.source_provider,
        enrichment.source_external_id,
    )
    if not all(isinstance(value, str) and value.strip() for value in required_text):
        return "invalid_enrichment"
    if not isinstance(enrichment.valid_from, date) or (
        enrichment.valid_to is not None and not isinstance(enrichment.valid_to, date)
    ):
        return "invalid_listing_history"
    if not isinstance(enrichment.is_adr, bool) or not isinstance(enrichment.is_primary, bool):
        return "invalid_enrichment"
    if enrichment.ticker.upper() != row.ticker or enrichment.exchange_code.upper() != row.exchange:
        return "enrichment_identity_mismatch"
    if enrichment.security_type.lower() != "common_stock":
        return f"security_type:{enrichment.security_type.lower()}"
    if enrichment.is_adr:
        return "adr_or_depositary_receipt"
    if enrichment.market_id.lower() != "us":
        return f"market:{enrichment.market_id.lower()}"
    if enrichment.listing_status.lower() != "active":
        return "inactive_as_of"
    if not enrichment.is_primary:
        return "not_primary_listing"
    if enrichment.valid_to is not None and enrichment.valid_to < enrichment.valid_from:
        return "invalid_listing_history"
    if enrichment.valid_from > as_of or (
        enrichment.valid_to is not None and enrichment.valid_to < as_of
    ):
        return "not_active_as_of"
    return None


def _security_listing(enrichment: ListingEnrichment) -> SecurityListing:
    return SecurityListing(
        listing_id=enrichment.listing_id,
        security_id=enrichment.security_id,
        issuer_id=enrichment.issuer_id,
        issuer_name=enrichment.issuer_name,
        security_type=enrichment.security_type.lower(),
        market_id=enrichment.market_id.lower(),
        exchange_code=enrichment.exchange_code.upper(),
        ticker=enrichment.ticker.upper(),
        trading_currency=enrichment.trading_currency.upper(),
        valid_from=enrichment.valid_from,
        valid_to=enrichment.valid_to,
        listing_status=enrichment.listing_status.lower(),
        source_provider=enrichment.source_provider,
        source_external_id=enrichment.source_external_id,
        share_class=enrichment.share_class,
        is_primary=enrichment.is_primary,
    )


def _select_primary_security_listings(
    assessments: Sequence[tuple[SecDiscoveryRow, SecurityListing | None, str | None]],
) -> dict[str, SecurityListing]:
    selected: dict[str, SecurityListing] = {}
    for _, listing, reason in assessments:
        if reason is not None or listing is None:
            continue
        current = selected.get(listing.security_id)
        if current is None or (listing.listing_id, listing.source_external_id) < (
            current.listing_id,
            current.source_external_id,
        ):
            selected[listing.security_id] = listing
    return selected


def _normalize_cik(value: object) -> str:
    normalized = str(value).strip()
    if normalized.upper().startswith("CIK"):
        normalized = normalized[3:]
    if not normalized.isdigit() or not normalized:
        raise ValueError(f"SEC CIK must contain only digits: {value!r}")
    return f"{int(normalized):010d}"

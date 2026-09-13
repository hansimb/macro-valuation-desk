from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from math import isfinite
from types import MappingProxyType
from collections.abc import Mapping


Number = Decimal | float | int


def _require_timezone_aware(field_name: str, value: datetime | None) -> None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_positive(field_name: str, value: Number) -> None:
    try:
        is_valid = not isinstance(value, bool) and isfinite(value) and value > 0
    except (TypeError, ValueError):
        is_valid = False
    if not is_valid:
        raise ValueError(f"{field_name} must be finite and positive")


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType({key: _freeze_value(item) for key, item in value.items()})


def _freeze_value(value: object) -> object:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_value(item) for item in value)
    return value


@dataclass(frozen=True)
class RegulatoryFiling:
    provider: str
    external_id: str
    content_hash: str
    jurisdiction: str
    filer_id: str
    filing_form: str
    document_url: str
    content_json: Mapping[str, object]
    fetched_at: datetime
    filing_date: date | None = None
    accepted_at: datetime | None = None
    published_at: datetime | None = None
    amendment_of_external_id: str | None = None

    def __post_init__(self) -> None:
        _require_timezone_aware("fetched_at", self.fetched_at)
        _require_timezone_aware("accepted_at", self.accepted_at)
        _require_timezone_aware("published_at", self.published_at)
        object.__setattr__(self, "content_json", _freeze_mapping(self.content_json))


@dataclass(frozen=True)
class RawXbrlFact:
    filing_provider: str
    filing_id: str
    filing_content_hash: str
    fact_id: str
    taxonomy: str
    concept_name: str
    value_text: str
    published_at: datetime
    context_id: str | None = None
    entity_id: str | None = None
    security_id: str | None = None
    dimensions: Mapping[str, object] = field(default_factory=dict)
    unit: str | None = None
    decimals: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    instant_date: date | None = None
    filing_date: date | None = None
    filing_form: str | None = None
    frame: str | None = None
    source_url: str | None = None
    amendment_of_filing_id: str | None = None
    amended_at: datetime | None = None
    is_consolidated: bool | None = None
    is_continuing_operations: bool | None = None

    def __post_init__(self) -> None:
        _require_timezone_aware("published_at", self.published_at)
        _require_timezone_aware("amended_at", self.amended_at)
        object.__setattr__(self, "dimensions", _freeze_mapping(self.dimensions))


@dataclass(frozen=True)
class SecurityListing:
    listing_id: str
    security_id: str
    issuer_id: str | None
    issuer_name: str
    security_type: str
    market_id: str
    exchange_code: str
    ticker: str
    trading_currency: str
    valid_from: date
    listing_status: str
    source_provider: str
    source_external_id: str
    share_class: str | None = None
    valid_to: date | None = None
    is_primary: bool = True

    def __post_init__(self) -> None:
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to must not be before valid_from")


@dataclass(frozen=True)
class ProviderLicense:
    provider: str
    usage: str
    terms_url: str | None = None

    def assert_publishable(self, *, environment: str) -> None:
        if environment.lower() == "production" and self.usage != "commercial_production":
            raise ValueError(
                f"Provider {self.provider!r} is not licensed for commercial production"
            )


@dataclass(frozen=True)
class DailyPrice:
    security_id: str
    trading_date: date
    provider: str
    close_price: Number
    split_adjusted_close_price: Number | None
    trading_currency: str
    provider_timestamp: datetime
    license_class: str
    adjustment_metadata: Mapping[str, object] = field(default_factory=dict)
    source_url: str | None = None

    def __post_init__(self) -> None:
        _require_positive("close_price", self.close_price)
        if self.split_adjusted_close_price is not None:
            _require_positive("split_adjusted_close_price", self.split_adjusted_close_price)
        _require_timezone_aware("provider_timestamp", self.provider_timestamp)
        object.__setattr__(self, "adjustment_metadata", _freeze_mapping(self.adjustment_metadata))


@dataclass(frozen=True)
class FxRate:
    base_currency: str
    quote_currency: str
    rate_date: date
    rate: Number
    provider: str
    provider_timestamp: datetime
    source_url: str | None = None

    def __post_init__(self) -> None:
        _require_positive("rate", self.rate)
        _require_timezone_aware("provider_timestamp", self.provider_timestamp)

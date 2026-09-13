from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from src.lib.source.country_index_types import (
    DailyPrice,
    FxRate,
    ProviderLicense,
    RawXbrlFact,
    RegulatoryFiling,
    SecurityListing,
)


class FilingProvider(Protocol):
    def discover(
        self,
        accepted_from: datetime,
        accepted_to: datetime,
    ) -> list[RegulatoryFiling]: ...

    def fetch_facts(self, filing: RegulatoryFiling) -> list[RawXbrlFact]: ...


class UniverseProvider(Protocol):
    def listings_as_of(self, market_id: str, as_of: date) -> list[SecurityListing]: ...


class PriceProvider(Protocol):
    license: ProviderLicense

    def daily_prices(
        self,
        security: SecurityListing,
        start: date,
        end: date,
    ) -> list[DailyPrice]: ...


class FxProvider(Protocol):
    license: ProviderLicense

    def daily_rates(
        self,
        base_currency: str,
        quote_currency: str,
        start: date,
        end: date,
    ) -> list[FxRate]: ...

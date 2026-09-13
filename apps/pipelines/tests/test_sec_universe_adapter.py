from __future__ import annotations

from datetime import date

from src.lib.source.adapters.sec_universe import SecUniverseAdapter


SEC_USER_AGENT = "MVD test runner test-contact@example.test"


def test_listings_as_of_keeps_one_active_primary_common_listing_per_issuer():
    requests: list[tuple[str, dict[str, str]]] = []
    payload = {
        "fields": ["cik", "name", "ticker", "exchange", "valid_from", "valid_to", "status"],
        "data": [
            [1, "Alpha Corporation Class A", "ALPHA", "Nasdaq", "2020-01-01", None, "active"],
            [1, "Alpha Corporation Class C", "ALPHC", "Nasdaq", "2020-01-01", None, "active"],
            [2, "Arcade Corporation", "ARC", "NYSE", "2020-01-01", None, "active"],
            [2, "Arcade Corporation", "ARCD", "Nasdaq", "2020-01-01", None, "active"],
            [2, "Arcade Corporation ADR", "ARCADR", "NYSE", "2020-01-01", None, "active"],
            [3, "Beta ETF Trust", "BETA", "NYSE", "2020-01-01", None, "active"],
            [4, "Capital Income Fund", "CAPX", "Nasdaq", "2020-01-01", None, "active"],
            [5, "Delta Corporation 5% Preferred", "DLTP", "NYSE", "2020-01-01", None, "active"],
            [6, "Epsilon PLC ADR", "EPS", "NYSE", "2020-01-01", None, "active"],
            [7, "Former Corporation", "FORM", "NYSE", "2020-01-01", "2024-12-31", "inactive"],
            [8, "Future Corporation", "FUTR", "Nasdaq", "2026-01-01", None, "active"],
        ],
    }

    def fetch_json(url: str, headers: dict[str, str]) -> dict[str, object]:
        requests.append((url, headers))
        return payload

    listings = SecUniverseAdapter(fetch_json=fetch_json, user_agent=SEC_USER_AGENT).listings_as_of(
        "us", date(2025, 1, 2)
    )

    assert [(listing.issuer_id, listing.ticker, listing.exchange_code) for listing in listings] == [
        ("0000000001", "ALPHA", "NASDAQ"),
        ("0000000002", "ARC", "NYSE"),
    ]
    assert all(listing.security_type == "common_stock" for listing in listings)
    assert all(listing.is_primary for listing in listings)
    assert all(listing.trading_currency == "USD" for listing in listings)
    assert requests == [
        (
            "https://www.sec.gov/files/company_tickers_exchange.json",
            {"Accept": "application/json", "User-Agent": SEC_USER_AGENT},
        )
    ]


def test_listings_as_of_rejects_non_us_market_and_requires_sec_contact_identity():
    requests: list[tuple[str, dict[str, str]]] = []

    def fetch_json(url: str, headers: dict[str, str]) -> dict[str, object]:
        requests.append((url, headers))
        return {}

    adapter = SecUniverseAdapter(fetch_json=fetch_json, user_agent="")

    try:
        adapter.listings_as_of("ca", date(2025, 1, 2))
    except ValueError as exc:
        assert "US" in str(exc)
    else:
        raise AssertionError("non-US market must be rejected")

    try:
        adapter.listings_as_of("us", date(2025, 1, 2))
    except ValueError as exc:
        assert "SEC_USER_AGENT" in str(exc)
    else:
        raise AssertionError("SEC requests without an identifiable contact must be rejected")
    assert requests == []

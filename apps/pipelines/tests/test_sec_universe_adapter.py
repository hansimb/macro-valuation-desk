from __future__ import annotations

from datetime import date

from src.lib.source.adapters.sec_universe import ListingEnrichment, SecUniverseAdapter


SEC_USER_AGENT = "MVD test runner test-contact@example.test"
RAW_SEC_PAYLOAD = {
    "fields": ["cik", "name", "ticker", "exchange"],
    "data": [
        [1, "Alpha Corporation", "ALPA", "Nasdaq"],
        [1, "Alpha Corporation", "ALPC", "Nasdaq"],
        [2, "Beta ETF Trust", "BETA", "NYSE"],
        [3, "Capital Fund", "CAPX", "Nasdaq"],
        [4, "Delta Corporation", "DLTP", "NYSE"],
        [5, "Epsilon PLC", "EPS", "NYSE"],
        [6, "Former Corporation", "FORM", "NYSE"],
        [7, "Future Corporation", "FUTR", "Nasdaq"],
    ],
}


def _enrichment(
    ticker: str,
    *,
    security_id: str | None = None,
    listing_id: str | None = None,
    security_type: str = "common_stock",
    is_adr: bool = False,
    valid_from: date = date(2020, 1, 1),
    valid_to: date | None = None,
    listing_status: str = "active",
    is_primary: bool = True,
    share_class: str | None = None,
    exchange_code: str | None = None,
) -> ListingEnrichment:
    return ListingEnrichment(
        listing_id=listing_id or f"security-master:{ticker}",
        security_id=security_id or f"security-master:{ticker}",
        issuer_id="issuer:alpha" if ticker.startswith("ALP") else f"issuer:{ticker}",
        issuer_name="Enriched " + ticker,
        security_type=security_type,
        market_id="us",
        exchange_code=exchange_code
        or ("NASDAQ" if ticker.startswith("ALP") or ticker in {"CAPX", "FUTR"} else "NYSE"),
        ticker=ticker,
        trading_currency="USD",
        valid_from=valid_from,
        valid_to=valid_to,
        listing_status=listing_status,
        is_primary=is_primary,
        share_class=share_class,
        is_adr=is_adr,
        source_provider="security_master",
        source_external_id=f"master:{ticker}",
    )


def test_real_four_field_sec_discovery_rows_fail_closed_without_enrichment():
    requests: list[tuple[str, dict[str, str]]] = []

    def fetch_json(url: str, headers: dict[str, str]) -> dict[str, object]:
        requests.append((url, headers))
        return RAW_SEC_PAYLOAD

    adapter = SecUniverseAdapter(fetch_json=fetch_json, user_agent=SEC_USER_AGENT)
    result = adapter.assess_listings_as_of("us", date(2025, 1, 2))

    assert result.listings == ()
    assert {entry.reason for entry in result.audit} == {"missing_enrichment"}
    assert requests == [
        (
            "https://www.sec.gov/files/company_tickers_exchange.json",
            {"Accept": "application/json", "User-Agent": SEC_USER_AGENT},
        )
    ]


def test_explicit_enrichment_preserves_eligible_share_classes_and_audits_exclusions():
    enrichments = {
        "ALPA": _enrichment("ALPA", security_id="security:alpha:a", share_class="A"),
        "ALPC": _enrichment("ALPC", security_id="security:alpha:c", share_class="C"),
        "BETA": _enrichment("BETA", security_type="exchange_traded_fund"),
        "CAPX": _enrichment("CAPX", security_type="fund"),
        "DLTP": _enrichment("DLTP", security_type="preferred_stock"),
        "EPS": _enrichment("EPS", is_adr=True),
        "FORM": _enrichment("FORM", valid_to=date(2024, 12, 31), listing_status="inactive"),
        "FUTR": _enrichment("FUTR", valid_from=date(2026, 1, 1)),
    }
    adapter = SecUniverseAdapter(
        fetch_json=lambda _url, _headers: RAW_SEC_PAYLOAD,
        enrich_listing=lambda row: enrichments[row.ticker],
        user_agent=SEC_USER_AGENT,
    )

    result = adapter.assess_listings_as_of("us", date(2025, 1, 2))

    assert [(row.security_id, row.ticker, row.share_class, row.is_primary) for row in result.listings] == [
        ("security:alpha:a", "ALPA", "A", True),
        ("security:alpha:c", "ALPC", "C", True),
    ]
    assert {entry.reason for entry in result.audit if not entry.included} == {
        "adr_or_depositary_receipt",
        "inactive_as_of",
        "security_type:exchange_traded_fund",
        "security_type:fund",
        "security_type:preferred_stock",
        "not_active_as_of",
    }
    assert adapter.listings_as_of("us", date(2025, 1, 2)) == list(result.listings)


def test_enrichment_selects_one_explicit_primary_listing_per_security_and_keeps_audit():
    payload = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [
            [1, "Alpha Corporation", "ALPA", "Nasdaq"],
            [1, "Alpha Corporation", "ALPA2", "NYSE"],
            [1, "Alpha Corporation", "ALPA3", "NYSE"],
        ],
    }
    enrichments = {
        "ALPA": _enrichment("ALPA", security_id="security:alpha:a", listing_id="listing:alpha:a"),
        "ALPA2": _enrichment(
            "ALPA2",
            security_id="security:alpha:a",
            listing_id="listing:alpha:a:2",
            exchange_code="NYSE",
        ),
        "ALPA3": _enrichment(
            "ALPA3",
            security_id="security:alpha:a",
            listing_id="listing:alpha:a:3",
            is_primary=False,
            exchange_code="NYSE",
        ),
    }
    adapter = SecUniverseAdapter(
        fetch_json=lambda _url, _headers: payload,
        enrich_listing=lambda row: enrichments[row.ticker],
        user_agent=SEC_USER_AGENT,
    )

    result = adapter.assess_listings_as_of("us", date(2025, 1, 2))

    assert [(row.security_id, row.ticker) for row in result.listings] == [("security:alpha:a", "ALPA")]
    assert {entry.reason for entry in result.audit if not entry.included} == {
        "duplicate_security_listing",
        "not_primary_listing",
    }


def test_listings_as_of_rejects_non_us_market_and_requires_sec_contact_identity():
    requests: list[tuple[str, dict[str, str]]] = []

    def fetch_json(url: str, headers: dict[str, str]) -> dict[str, object]:
        requests.append((url, headers))
        return {}

    adapter = SecUniverseAdapter(fetch_json=fetch_json, user_agent="")

    for market_id, message in (("ca", "US"), ("us", "SEC_USER_AGENT")):
        try:
            adapter.listings_as_of(market_id, date(2025, 1, 2))
        except ValueError as exc:
            assert message in str(exc)
        else:
            raise AssertionError(f"{market_id} must be rejected")
    assert requests == []

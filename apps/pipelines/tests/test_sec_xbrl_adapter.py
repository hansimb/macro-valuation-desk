from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.lib.source.adapters.sec_xbrl import SecXbrlAdapter


FIXTURES = Path(__file__).parent / "fixtures" / "sec"


def _fixture_fetcher(requests: list[tuple[str, dict[str, str]]]):
    payloads = {
        "https://www.sec.gov/files/company_tickers_exchange.json": json.loads(
            (FIXTURES / "company_tickers_exchange.json").read_text(encoding="utf-8")
        ),
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json": json.loads(
            (FIXTURES / "companyfacts_aapl.json").read_text(encoding="utf-8")
        ),
    }

    def fetch_json(url: str, headers: dict[str, str]) -> dict[str, object]:
        requests.append((url, headers))
        return payloads[url]

    return fetch_json


def test_discover_company_returns_identified_exchange_company_from_fixture():
    requests: list[tuple[str, dict[str, str]]] = []
    result = SecXbrlAdapter(fetch_json=_fixture_fetcher(requests)).discover_company("320193")

    assert result.ok is True
    assert result.error is None
    assert result.company is not None
    assert result.company.cik == "0000320193"
    assert result.company.name == "Apple Inc."
    assert result.company.ticker == "AAPL"
    assert result.company.exchange == "Nasdaq"
    assert requests[0][0] == "https://www.sec.gov/files/company_tickers_exchange.json"


def test_fetch_companyfacts_preserves_amendment_lineage_and_distinct_timestamps():
    requests: list[tuple[str, dict[str, str]]] = []
    result = SecXbrlAdapter(fetch_json=_fixture_fetcher(requests)).fetch_companyfacts("320193")

    assert result.ok is True
    assert result.error is None
    amended_filing = next(filing for filing in result.filings if filing.external_id.endswith("079A"))
    original_filing = next(filing for filing in result.filings if filing.external_id.endswith("079"))
    amended_fact = next(fact for fact in result.facts if fact.filing_id.endswith("079A"))

    assert amended_filing.amendment_of_external_id == original_filing.external_id
    assert amended_filing.accepted_at is not None
    assert amended_filing.published_at is not None
    assert amended_filing.accepted_at.isoformat() == "2025-11-07T15:20:00+00:00"
    assert amended_filing.published_at.isoformat() == "2025-11-07T15:25:00+00:00"
    assert amended_filing.fetched_at > amended_filing.published_at
    assert amended_fact.amendment_of_filing_id == original_filing.external_id
    assert amended_fact.amended_at == amended_filing.published_at
    assert amended_fact.published_at == amended_filing.published_at
    assert amended_fact.filing_content_hash.startswith("sha256:")


def test_fetch_companyfacts_preserves_custom_taxonomy_context_unit_frame_and_source_url():
    requests: list[tuple[str, dict[str, str]]] = []
    result = SecXbrlAdapter(fetch_json=_fixture_fetcher(requests)).fetch_companyfacts("0000320193")

    custom_fact = next(fact for fact in result.facts if fact.taxonomy == "aapl")

    assert custom_fact.concept_name == "StoreVisits"
    assert custom_fact.context_id == "CustomMetricContext"
    assert custom_fact.unit == "visits"
    assert custom_fact.frame == "CY2025Q3"
    assert custom_fact.period_start is not None
    assert custom_fact.period_start.isoformat() == "2025-06-29"
    assert custom_fact.period_end is not None
    assert custom_fact.period_end.isoformat() == "2025-09-27"
    assert custom_fact.source_url == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"

    with pytest.raises(TypeError):
        custom_fact.dimensions["new"] = "dimension"


def test_fetch_companyfacts_keeps_supported_sec_forms_and_excludes_other_forms():
    requests: list[tuple[str, dict[str, str]]] = []
    result = SecXbrlAdapter(fetch_json=_fixture_fetcher(requests)).fetch_companyfacts("320193")

    forms = {fact.filing_form for fact in result.facts}

    assert {"10-K", "10-Q", "20-F", "40-F"}.issubset(forms)
    assert "10-K/A" in forms
    assert "8-K" not in forms


def test_sec_requests_use_identifiable_compliant_user_agent():
    requests: list[tuple[str, dict[str, str]]] = []
    adapter = SecXbrlAdapter(fetch_json=_fixture_fetcher(requests))

    adapter.discover_company("320193")
    adapter.fetch_companyfacts("320193")

    assert len(requests) == 2
    for _, headers in requests:
        assert headers["Accept"] == "application/json"
        assert "Macro Valuation Desk" in headers["User-Agent"]
        assert "@" in headers["User-Agent"]


def test_fetch_companyfacts_returns_typed_source_error_when_transport_fails():
    def unavailable(_url: str, _headers: dict[str, str]) -> dict[str, object]:
        raise OSError("SEC unavailable")

    result = SecXbrlAdapter(fetch_json=unavailable).fetch_companyfacts("320193")

    assert result.ok is False
    assert result.facts == ()
    assert result.error is not None
    assert result.error.provider == "sec"
    assert result.error.error_type == "fetch_error"
    assert "SEC unavailable" in result.error.message

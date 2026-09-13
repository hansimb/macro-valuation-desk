from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.lib.source.country_index_types import (
    DailyPrice,
    FxRate,
    ProviderLicense,
    RawXbrlFact,
    RegulatoryFiling,
)


def test_price_license_blocks_development_provider_in_production():
    license_info = ProviderLicense(provider="fixture", usage="development_only")

    with pytest.raises(ValueError, match="commercial production"):
        license_info.assert_publishable(environment="production")


def test_raw_fact_keeps_point_in_time_lineage():
    fact = RawXbrlFact(
        filing_provider="sec",
        filing_id="0000320193-26-000123",
        filing_content_hash="sha256:filing",
        fact_id="us-gaap:Revenues:1",
        taxonomy="us-gaap",
        concept_name="Revenues",
        context_id="FY2025",
        value_text="416161000000",
        published_at=datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc),
    )

    assert fact.filing_id == "0000320193-26-000123"
    assert fact.taxonomy == "us-gaap"
    assert fact.context_id == "FY2025"


def test_contracts_reject_naive_datetimes_at_construction():
    with pytest.raises(ValueError, match="timezone-aware"):
        RawXbrlFact(
            filing_provider="sec",
            filing_id="0000320193-26-000123",
            filing_content_hash="sha256:filing",
            fact_id="us-gaap:Revenues:1",
            taxonomy="us-gaap",
            concept_name="Revenues",
            context_id="FY2025",
            value_text="416161000000",
            published_at=datetime(2026, 5, 1, 12, 0),
        )


def test_daily_price_rejects_non_positive_close_price():
    with pytest.raises(ValueError, match="positive"):
        DailyPrice(
            security_id="AAPL-common",
            trading_date=date(2026, 5, 1),
            provider="fixture",
            close_price=0,
            split_adjusted_close_price=None,
            trading_currency="USD",
            provider_timestamp=datetime(2026, 5, 1, 21, 0, tzinfo=timezone.utc),
            license_class="development_only",
        )


@pytest.mark.parametrize("price_field", ["close_price", "split_adjusted_close_price"])
def test_daily_price_rejects_nan_price(price_field: str):
    values = {"close_price": 100.0, "split_adjusted_close_price": 99.0}
    values[price_field] = float("nan")

    with pytest.raises(ValueError, match="finite and positive"):
        DailyPrice(
            security_id="AAPL-common",
            trading_date=date(2026, 5, 1),
            provider="fixture",
            trading_currency="USD",
            provider_timestamp=datetime(2026, 5, 1, 21, 0, tzinfo=timezone.utc),
            license_class="development_only",
            **values,
        )


def test_fx_rate_rejects_nan_rate():
    with pytest.raises(ValueError, match="finite and positive"):
        FxRate(
            base_currency="USD",
            quote_currency="EUR",
            rate_date=date(2026, 5, 1),
            rate=float("nan"),
            provider="fixture",
            provider_timestamp=datetime(2026, 5, 1, 21, 0, tzinfo=timezone.utc),
        )


def test_regulatory_filing_deep_freezes_nested_lineage_content():
    filing = RegulatoryFiling(
        provider="sec",
        external_id="0000320193-26-000123",
        content_hash="sha256:filing",
        jurisdiction="US",
        filer_id="0000320193",
        filing_form="10-K",
        document_url="https://www.sec.gov/Archives/example",
        content_json={"documents": [{"accession": "0000320193-26-000123"}]},
        fetched_at=datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(TypeError):
        filing.content_json["documents"][0]["accession"] = "altered"


def test_raw_fact_deep_freezes_nested_dimensions():
    fact = RawXbrlFact(
        filing_provider="sec",
        filing_id="0000320193-26-000123",
        filing_content_hash="sha256:filing",
        fact_id="us-gaap:Revenues:1",
        taxonomy="us-gaap",
        concept_name="Revenues",
        value_text="416161000000",
        published_at=datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc),
        dimensions={"segments": [{"axis": "us-gaap:StatementBusinessSegmentsAxis"}]},
    )

    with pytest.raises(TypeError):
        fact.dimensions["segments"][0]["axis"] = "altered"


def test_daily_price_deep_freezes_nested_adjustment_metadata():
    price = DailyPrice(
        security_id="AAPL-common",
        trading_date=date(2026, 5, 1),
        provider="fixture",
        close_price=100.0,
        split_adjusted_close_price=99.0,
        trading_currency="USD",
        provider_timestamp=datetime(2026, 5, 1, 21, 0, tzinfo=timezone.utc),
        license_class="development_only",
        adjustment_metadata={"split": {"ratio": [4, 1]}},
    )

    with pytest.raises(TypeError):
        price.adjustment_metadata["split"]["ratio"][0] = 5

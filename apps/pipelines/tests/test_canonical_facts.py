from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from src.lib.source.country_index_types import RawXbrlFact


def raw_fact(concept="Revenues", **changes):
    values = dict(
        filing_provider="sec", filing_id="original", filing_content_hash="sha256:one",
        fact_id="fact-1", taxonomy="us-gaap", concept_name=concept, value_text="12.34",
        published_at=datetime(2025, 2, 1, tzinfo=timezone.utc), security_id="US:ONE",
        entity_id="0000000001", unit="USD", period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31), is_consolidated=True,
    )
    values.update(changes)
    return RawXbrlFact(**values)


@pytest.mark.parametrize("taxonomy,concept,metric,instant,unit", [
    ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax", "revenue", False, "USD"),
    ("us-gaap", "NetIncomeLossAvailableToCommonStockholdersBasic", "net_income", False, "USD"),
    ("us-gaap", "NetIncomeLoss", "net_income", False, "USD"),
    ("us-gaap", "CommonStockholdersEquity", "common_equity", True, "USD"),
    ("us-gaap", "StockholdersEquity", "common_equity", True, "USD"),
    ("us-gaap", "NetCashProvidedByUsedInOperatingActivities", "operating_cash_flow", False, "USD"),
    ("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment", "capex", False, "USD"),
    ("us-gaap", "PaymentsOfDividendsCommonStock", "dividends", False, "USD"),
    ("us-gaap", "WeightedAverageNumberOfSharesOutstandingBasic", "weighted_average_shares", False, "shares"),
    ("us-gaap", "CommonStockSharesOutstanding", "period_end_shares", True, "shares"),
    ("dei", "EntityCommonStockSharesOutstanding", "period_end_shares", True, "shares"),
    ("ifrs-full", "Revenue", "revenue", False, "EUR"),
    ("ifrs-full", "ProfitLossAttributableToOwnersOfParent", "net_income", False, "EUR"),
    ("ifrs-full", "EquityAttributableToOwnersOfParent", "common_equity", True, "EUR"),
    ("ifrs-full", "CashFlowsFromUsedInOperatingActivities", "operating_cash_flow", False, "EUR"),
    ("ifrs-full", "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities", "capex", False, "EUR"),
    ("ifrs-full", "DividendsPaidClassifiedAsFinancingActivities", "dividends", False, "EUR"),
    ("ifrs-full", "WeightedAverageNumberOfOrdinarySharesOutstanding", "weighted_average_shares", False, "shares"),
    ("ifrs-full", "NumberOfSharesOutstanding", "period_end_shares", True, "shares"),
])
def test_standard_concepts_keep_original_fact_and_map_to_canonical_metric(taxonomy, concept, metric, instant, unit):
    from src.lib.pipeline.canonical_facts import normalize_facts

    raw = raw_fact(concept, taxonomy=taxonomy, unit=unit,
                   period_start=None if instant else date(2024, 1, 1),
                   period_end=None if instant else date(2024, 12, 31),
                   instant_date=date(2024, 12, 31) if instant else None)
    [fact] = normalize_facts([raw], "sec-v1")
    assert fact.metric == metric
    assert fact.value == Decimal("12.34")
    assert fact.raw == raw
    assert fact.rejection_reasons == ()
    assert fact.taxonomy_version == "sec-v1"


@pytest.mark.parametrize("unit,value,expected,expected_unit", [
    ("USD millions", "1.23456789", "1234567.89", "USD"),
    ("iso4217:USD", "123.45", "123.45", "USD"),
    ("USD", "123456000", "123456000", "USD"),
    ("shares thousands", "12.345", "12345", "shares"),
])
def test_explicit_unit_scaling_is_exact_and_decimals_is_precision_only(unit, value, expected, expected_unit):
    from src.lib.pipeline.canonical_facts import normalize_facts

    concept = "WeightedAverageNumberOfSharesOutstandingBasic" if unit.startswith("shares") else "Revenues"
    [fact] = normalize_facts([raw_fact(concept, unit=unit, value_text=value, decimals="-6")], "sec-v1")
    assert fact.value == Decimal(expected)
    assert fact.unit == expected_unit


@pytest.mark.parametrize("changes,reason", [
    ({"concept_name": "UnmappedExtension"}, "unmapped_concept"),
    ({"taxonomy": "custom"}, "unmapped_concept"),
    ({"unit": "USD/shares"}, "unsupported_unit"),
    ({"unit": "shares"}, "incompatible_unit"),
    ({"value_text": "NaN"}, "invalid_numeric_value"),
    ({"value_text": "Infinity"}, "invalid_numeric_value"),
    ({"value_text": "unavailable"}, "invalid_numeric_value"),
    ({"period_start": None}, "invalid_period"),
    ({"period_start": date(2025, 1, 1)}, "invalid_period"),
    ({"dimensions": {"ProductAxis": "PhoneMember"}}, "dimensional_context"),
    ({"is_continuing_operations": False}, "non_continuing_operations"),
])
def test_invalid_candidates_are_preserved_with_reasons(changes, reason):
    from src.lib.pipeline.canonical_facts import normalize_facts

    raw = raw_fact(**changes)
    [fact] = normalize_facts([raw], "sec-v1")
    assert fact.raw == raw
    assert reason in fact.rejection_reasons


def test_metadata_is_not_a_segment_and_conflicting_candidates_are_not_deduplicated():
    from src.lib.pipeline.canonical_facts import normalize_facts

    raw = raw_fact(is_consolidated=None, dimensions={"__mvd_source_metadata__": {
        "availability_precision": "filing_date_only_next_sec_day"}})
    other = replace(raw, value_text="99", fact_id="conflict")
    result = normalize_facts([raw, other], "sec-v1")
    assert len(result) == 2
    assert all(not fact.rejection_reasons for fact in result)
    assert {fact.value for fact in result} == {Decimal("12.34"), Decimal("99")}


def test_mapping_version_must_be_known():
    from src.lib.pipeline.canonical_facts import normalize_facts

    with pytest.raises(ValueError, match="taxonomy version"):
        normalize_facts([], "unregistered-version")


@pytest.mark.parametrize("value", ["0", "-1"])
def test_nonpositive_shares_are_preserved_but_rejected(value):
    from src.lib.pipeline.canonical_facts import normalize_facts

    [fact] = normalize_facts([raw_fact("WeightedAverageNumberOfSharesOutstandingBasic",
                                      unit="shares", value_text=value)], "sec-v1")
    assert "nonpositive_shares" in fact.rejection_reasons


def test_broad_attribution_fallbacks_are_identified_in_warnings():
    from src.lib.pipeline.canonical_facts import normalize_facts

    [fact] = normalize_facts([raw_fact("StockholdersEquity", period_start=None,
                                      period_end=None, instant_date=date(2024, 12, 31))], "sec-v1")
    assert "preferred_equity_not_separated" in fact.warnings

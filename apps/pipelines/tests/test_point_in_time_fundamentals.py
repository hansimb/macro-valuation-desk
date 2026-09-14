from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, localcontext

import pytest

from src.lib.source.country_index_types import RawXbrlFact


SECURITY = "US:ONE"
CUTOFF = datetime(2025, 3, 1, tzinfo=timezone.utc)
QUARTERS = [("2024-01-01", "2024-03-31"), ("2024-04-01", "2024-06-30"),
            ("2024-07-01", "2024-09-30"), ("2024-10-01", "2024-12-31")]


def fact(concept, value, start="2024-01-01", end="2024-12-31", **changes):
    instant = changes.pop("instant", False)
    values = dict(
        filing_provider="sec", filing_id="original", filing_content_hash="sha256:one",
        fact_id=f"{concept}:{start}:{end}:{value}", taxonomy="us-gaap", concept_name=concept,
        value_text=str(value), published_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
        security_id=SECURITY, entity_id="0000000001", is_consolidated=True,
        unit="shares" if "Shares" in concept else "USD",
        period_start=None if instant else date.fromisoformat(start),
        period_end=None if instant else date.fromisoformat(end),
        instant_date=date.fromisoformat(end) if instant else None,
    )
    values.update(changes)
    return RawXbrlFact(**values)


def evaluate(facts, cutoff=CUTOFF):
    from src.lib.pipeline.canonical_facts import normalize_facts
    from src.lib.pipeline.point_in_time import fundamentals_as_of

    return fundamentals_as_of(SECURITY, cutoff, normalize_facts(facts, "sec-v1"))


def quarters(concept, values, **changes):
    return [fact(concept, value, start, end, **changes)
            for (start, end), value in zip(QUARTERS, values, strict=True)]


def test_direct_quarters_and_dividends_sum_without_double_counting_annual_fact():
    raw = quarters("Revenues", [10, 20, 30, 40])
    raw += [fact("Revenues", 100)]
    raw += quarters("PaymentsOfDividendsCommonStock", ["0.1", "0.2", "0.3", "0.4"])
    result = evaluate(raw)
    assert result.ttm_revenue == Decimal("100")
    assert result.ttm_dividends == Decimal("1.0")
    assert [q.value for q in result.revenue.quarters] == list(map(Decimal, [10, 20, 30, 40]))
    assert result.revenue.period_start == date(2024, 1, 1)
    assert result.revenue.period_end == date(2024, 12, 31)
    assert all(t <= CUTOFF for t in result.revenue.lineage.publication_times)


def test_cumulative_reports_derive_q2_from_h1_and_q4_from_fy_minus_nine_months():
    raw = [fact("NetIncomeLoss", value, end=end)
           for end, value in [("2024-03-31", 10), ("2024-06-30", 35),
                              ("2024-09-30", 65), ("2024-12-31", 105)]]
    result = evaluate(raw)
    assert result.ttm_net_income == Decimal("105")
    assert [q.value for q in result.net_income.quarters] == list(map(Decimal, [10, 25, 30, 40]))
    assert len(result.net_income.quarters[1].lineage.facts) == 2
    assert {f.raw.fact_id for f in result.net_income.lineage.facts} == {f.fact_id for f in raw}
    assert all(t <= CUTOFF for t in result.net_income.lineage.publication_times)


def test_latest_amendment_is_visible_exactly_at_publication_not_period_end():
    raw = quarters("NetIncomeLoss", [10, 20, 30, 40])
    published = CUTOFF + timedelta(hours=12)
    amendment = replace(raw[-1], value_text="50", fact_id="amended-q4", filing_id="amendment",
                        filing_form="10-Q/A", amendment_of_filing_id="original",
                        amended_at=published, published_at=published)
    before = evaluate(raw + [amendment], published - timedelta(microseconds=1))
    after = evaluate(raw + [amendment], published)
    assert before.ttm_net_income == Decimal("100")
    assert after.ttm_net_income == Decimal("110")
    assert amendment.fact_id not in {f.raw.fact_id for f in before.net_income.lineage.facts}
    assert any(r.fact.raw.fact_id == amendment.fact_id and r.reason == "not_yet_published"
               for r in before.rejections)
    assert any(r.fact.raw.fact_id == raw[-1].fact_id for r in after.rejections)


def test_consolidated_context_wins_over_newer_parent_only_and_segments():
    base = fact("Revenues", 100)
    parent = replace(base, fact_id="parent", is_consolidated=False, value_text="25",
                     published_at=CUTOFF)
    segment = replace(base, fact_id="segment", dimensions={"ProductAxis": "Phone"}, value_text="90")
    result = evaluate([parent, segment, base])
    assert result.ttm_revenue == Decimal("100")
    assert {r.fact.raw.fact_id for r in result.rejections} == {"parent", "segment"}
    assert result.revenue.lineage.facts[0].raw == base


def test_latest_equity_and_period_end_shares_are_publication_aware_instants():
    raw = [fact("CommonStockholdersEquity", 500, end="2024-09-30", instant=True),
           fact("CommonStockholdersEquity", 600, instant=True),
           fact("CommonStockholdersEquity", 700, end="2025-02-28", instant=True,
                published_at=CUTOFF + timedelta(days=1)),
           fact("CommonStockSharesOutstanding", 100, instant=True)]
    result = evaluate(raw)
    assert result.common_equity.value == Decimal("600")
    assert result.period_end_shares.value == Decimal("100")
    assert result.common_equity.period_end == date(2024, 12, 31)


def test_fcf_uses_exact_cash_capex_and_never_adds_lease_or_noncash_acquisitions():
    raw = quarters("NetCashProvidedByUsedInOperatingActivities", ["10.11", "20.22", "30.33", "40.44"])
    raw += quarters("PaymentsToAcquirePropertyPlantAndEquipment", ["1.01", "2.02", "3.03", "4.04"])
    raw += [fact("PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization", 999)]
    result = evaluate(raw)
    assert result.ttm_operating_cash_flow == Decimal("101.10")
    assert result.ttm_capex == Decimal("10.10")
    assert result.ttm_free_cash_flow == Decimal("91.00")
    assert result.ttm_free_cash_flow == result.ttm_operating_cash_flow - result.ttm_capex
    assert len(result.free_cash_flow.lineage.facts) == 8


def test_missing_quarter_or_dividends_is_missing_not_zero_or_annualized():
    result = evaluate(quarters("NetIncomeLoss", [10, 20, 30, 40])[:-1])
    assert result.ttm_net_income is None
    assert result.ttm_dividends is None
    assert result.ttm_free_cash_flow is None
    assert "incomplete_ttm" in result.net_income.warnings


def test_fiscal_year_dates_and_annual_only_filer_are_supported():
    raw = [fact("NetIncomeLoss", 123, start="2023-09-24", end="2024-09-28")]
    result = evaluate(raw)
    assert result.ttm_net_income == Decimal("123")
    assert result.net_income.period_start == date(2023, 9, 24)
    assert result.net_income.period_end == date(2024, 9, 28)


def test_weighted_average_shares_use_day_weighted_mean_not_sum():
    result = evaluate(quarters("WeightedAverageNumberOfSharesOutstandingBasic", [100, 100, 200, 200]))
    assert abs(result.weighted_average_shares.value - Decimal("150.2732240437158469945355191")) < Decimal("1e-24")
    assert result.weighted_average_shares.unit == "shares"


def test_cumulative_weighted_shares_derive_with_share_days_not_simple_subtraction():
    raw = [fact("WeightedAverageNumberOfSharesOutstandingBasic", value, end=end)
           for end, value in [("2024-03-31", 100), ("2024-06-30", 150),
                              ("2024-09-30", 150), ("2024-12-31", 150)]]
    result = evaluate(raw)
    assert result.weighted_average_shares.value == Decimal("150")
    assert result.weighted_average_shares.quarters[1].value == Decimal("200")


def test_security_binding_and_naive_cutoff_are_rejected():
    from src.lib.pipeline.point_in_time import fundamentals_as_of

    result = evaluate([fact("Revenues", 900, security_id="US:TWO"),
                       fact("Revenues", 800, security_id=None)])
    assert result.ttm_revenue is None
    assert all(r.reason == "security_mismatch" for r in result.rejections)
    with pytest.raises(ValueError, match="timezone-aware"):
        fundamentals_as_of(SECURITY, datetime(2025, 3, 1), [])


def test_mixed_currency_and_mismatched_cashflow_periods_cannot_produce_fcf():
    result = evaluate([fact("NetCashProvidedByUsedInOperatingActivities", 100),
                       fact("PaymentsToAcquirePropertyPlantAndEquipment", 10, unit="EUR")])
    assert result.ttm_free_cash_flow is None
    assert "incompatible_cash_flow_period_or_unit" in result.free_cash_flow.warnings
    result = evaluate([fact("NetCashProvidedByUsedInOperatingActivities", 100),
                       fact("PaymentsToAcquirePropertyPlantAndEquipment", 10,
                            start="2023-10-01", end="2024-09-30")])
    assert result.ttm_free_cash_flow is None


def test_conflicting_equal_priority_facts_are_missing_and_all_lineage_is_preserved():
    a = fact("Revenues", 100)
    b = replace(a, fact_id="conflict", value_text="200")
    result = evaluate([a, b])
    assert result.ttm_revenue is None
    assert {r.fact.raw.fact_id for r in result.rejections} == {a.fact_id, b.fact_id}
    assert all(r.reason == "conflicting_facts" for r in result.rejections)
    assert result == evaluate([b, a])


def test_foreign_currencies_are_not_summed_and_future_periods_are_excluded():
    raw = quarters("Revenues", [10, 20, 30, 40])
    raw[-1] = replace(raw[-1], unit="EUR")
    assert evaluate(raw).ttm_revenue is None
    result = evaluate([fact("CommonStockholdersEquity", 900, end="2026-12-31", instant=True)])
    assert result.common_equity.value is None
    assert result.rejections[0].reason == "future_period"


def test_decimal_context_does_not_change_exact_cash_flow_arithmetic():
    raw = [fact("NetCashProvidedByUsedInOperatingActivities", "123456789012345678901234567890.12"),
           fact("PaymentsToAcquirePropertyPlantAndEquipment", "0.01")]
    with localcontext() as context:
        context.prec = 6
        result = evaluate(raw)
    assert result.ttm_free_cash_flow == Decimal("123456789012345678901234567890.11")


def test_rolling_ttm_uses_previous_fiscal_year_quarters_and_current_q1():
    raw = quarters("NetIncomeLoss", [10, 20, 30, 40])
    raw += [fact("NetIncomeLoss", 50, start="2025-01-01", end="2025-03-31",
                 published_at=datetime(2025, 4, 15, tzinfo=timezone.utc))]
    result = evaluate(raw, datetime(2025, 5, 1, tzinfo=timezone.utc))
    assert result.ttm_net_income == Decimal("140")
    assert result.net_income.period_start == date(2024, 4, 1)


def test_one_day_gap_does_not_form_ttm():
    raw = quarters("NetIncomeLoss", [10, 20, 30, 40])
    raw[1] = replace(raw[1], period_start=date(2024, 4, 2))
    assert evaluate(raw).ttm_net_income is None


@pytest.mark.parametrize("changes", [{"entity_id": "0000000002"}, {"is_consolidated": False}])
def test_ttm_does_not_combine_different_entities_or_reporting_scopes(changes):
    raw = quarters("Revenues", [10, 20, 30, 40])
    raw[-1] = replace(raw[-1], **changes)
    assert evaluate(raw).ttm_revenue is None


def test_reported_quarter_outranks_same_publication_derived_quarter_with_diagnostic():
    raw = quarters("NetIncomeLoss", [10, 20, 30, 40])
    raw += [fact("NetIncomeLoss", 45, end="2024-06-30")]
    result = evaluate(raw)
    assert result.ttm_net_income == Decimal("100")
    assert "reported_derived_disagreement" in result.net_income.warnings
    assert any(r.fact.raw.period_start == date(2024, 1, 1)
               and r.fact.raw.period_end == date(2024, 6, 30) for r in result.rejections)


def test_later_amended_cumulative_report_revises_derived_quarter_only_when_visible():
    raw = [fact("NetIncomeLoss", value, end=end)
           for end, value in [("2024-03-31", 10), ("2024-06-30", 35),
                              ("2024-09-30", 65), ("2024-12-31", 105)]]
    amended_at = CUTOFF + timedelta(days=1)
    raw += [replace(raw[-1], value_text="115", fact_id="amended-fy", filing_id="amended",
                    amendment_of_filing_id="original", published_at=amended_at)]
    assert evaluate(raw).ttm_net_income == Decimal("105")
    after = evaluate(raw, amended_at)
    assert after.ttm_net_income == Decimal("115")
    assert after.net_income.quarters[-1].value == Decimal("50")


def test_conflicting_latest_instant_does_not_fall_back_to_old_equity():
    old = fact("CommonStockholdersEquity", 400, end="2024-09-30", instant=True)
    new = fact("CommonStockholdersEquity", 500, instant=True)
    conflict = replace(new, value_text="600", fact_id="conflict")
    assert evaluate([old, new, conflict]).common_equity.value is None


def test_amended_at_is_an_additional_publication_lower_bound():
    raw = fact("Revenues", 100, amended_at=CUTOFF + timedelta(days=1))
    assert evaluate([raw]).ttm_revenue is None


def test_mapping_specificity_selects_attributable_income_and_retains_rejection():
    result = evaluate([fact("NetIncomeLossAvailableToCommonStockholdersBasic", 90),
                       fact("NetIncomeLoss", 100)])
    assert result.ttm_net_income == Decimal("90")
    assert result.rejections[0].reason == "less_preferred_concept"


def test_sec_adapter_date_only_metadata_and_publication_cutoff_are_preserved_end_to_end():
    from src.lib.source.adapters.sec_xbrl import SecXbrlAdapter

    payload = {"cik": 1, "entityName": "One", "facts": {"us-gaap": {"Revenues": {"units": {
        "USD": [{"start": "2024-01-01", "end": "2024-12-31", "val": 100,
                 "accn": "original", "form": "10-K", "filed": "2025-02-01"}]
    }}}}}
    adapter = SecXbrlAdapter(fetch_json=lambda url, headers: payload, user_agent="Test contact@example.com")
    response = adapter.fetch_companyfacts("1")
    assert response.ok
    raw = [replace(raw, security_id=SECURITY) for raw in response.facts]
    assert evaluate(raw, datetime(2025, 2, 2, 4, 59, tzinfo=timezone.utc)).ttm_revenue is None
    assert evaluate(raw, datetime(2025, 2, 2, 5, tzinfo=timezone.utc)).ttm_revenue == Decimal("100")


def test_fcf_cannot_mix_parent_capex_with_consolidated_operating_cash_flow():
    result = evaluate([fact("NetCashProvidedByUsedInOperatingActivities", 100),
                       fact("PaymentsToAcquirePropertyPlantAndEquipment", 10, is_consolidated=False)])
    assert result.ttm_free_cash_flow is None
    assert "incompatible_cash_flow_scope" in result.free_cash_flow.warnings


def test_negative_discrete_weighted_shares_do_not_become_a_valid_ttm_average():
    raw = [fact("WeightedAverageNumberOfSharesOutstandingBasic", value, end=end)
           for end, value in [("2024-03-31", 100), ("2024-06-30", 10),
                              ("2024-09-30", 100)]]
    raw += [fact("WeightedAverageNumberOfSharesOutstandingBasic", 100,
                 start="2024-10-01", end="2024-12-31")]
    result = evaluate(raw)
    assert result.weighted_average_shares.value is None


def test_future_fact_from_another_mapping_version_cannot_change_historical_result():
    from src.lib.pipeline.canonical_facts import normalize_facts
    from src.lib.pipeline.point_in_time import fundamentals_as_of

    [current, future] = normalize_facts([fact("Revenues", 100),
                                      fact("Revenues", 200, published_at=CUTOFF + timedelta(days=1))], "sec-v1")
    future = replace(future, taxonomy_version="future-v2")
    result = fundamentals_as_of(SECURITY, CUTOFF, [current, future])
    assert result.ttm_revenue == Decimal("100")

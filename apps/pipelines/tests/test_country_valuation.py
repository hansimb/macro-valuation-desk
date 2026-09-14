from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

import pytest

from src.lib.pipeline.country_cohorts import CountryCohort
from src.lib.pipeline.point_in_time import FundamentalValue, PointInTimeFundamentals
from src.lib.source.country_index_types import DailyPrice, FxRate


D = Decimal
DAY = date(2026, 9, 11)
CUTOFF = datetime(2026, 9, 11, 21, tzinfo=timezone.utc)
FIELDS = ("net_income", "common_equity", "revenue", "operating_cash_flow", "capex", "dividends")


def inputs():
    from src.lib.pipeline.country_valuation import CompanyFundamentals, ValuationFx, ValuationPrice

    cohort = CountryCohort("us", date(2026, 1, 1), ("US:A", "US:B", "US:C"), 3, D("0.78"))
    prices = []
    fundamentals = []
    # Caps 100/300/600, profits 10/15/75: aggregate P/E 10, mean P/E 38/3.
    for security, cap, amounts in zip(cohort.security_ids, (100, 300, 600),
                                     ((10, 20, 100, 20, 5, 1),
                                      (15, 60, 300, 30, 5, 3),
                                      (75, 120, 600, 50, 10, 6)), strict=True):
        raw_price = DailyPrice(security, DAY, "fixture", D(cap), D("999"), "USD", CUTOFF,
                               "development_only")
        prices.append(ValuationPrice(raw_price, D(1), industry="other", revenue_comparable=True))
        facts = {name: FundamentalValue(D(value), "USD", date(2025, 7, 1), date(2026, 6, 30))
                 for name, value in zip(FIELDS, amounts, strict=True)}
        facts.update(free_cash_flow=FundamentalValue(D("999999"), "USD"),
                     weighted_average_shares=FundamentalValue(D(99), "shares"),
                     period_end_shares=FundamentalValue(D(99), "shares"))
        fundamentals.append(CompanyFundamentals(PointInTimeFundamentals(security, CUTOFF, **facts)))
    return cohort, prices, fundamentals, ValuationFx("USD"), "mvd-v1"


def calculate(args):
    from src.lib.pipeline.country_valuation import calculate_daily_country_metrics
    return {row.metric: row for row in calculate_daily_country_metrics(*args)}


def change_fact(args, index, name, value, *, unit="USD", status=None):
    company = args[2][index]
    fact = replace(getattr(company.fundamentals, name), value=None if value is None else D(value), unit=unit)
    statuses = dict(company.statuses)
    if status is not None:
        statuses[name] = status
    args[2][index] = replace(company, fundamentals=replace(company.fundamentals, **{name: fact}), statuses=statuses)


def test_all_six_use_aggregate_amounts_and_exact_cash_fcf_not_company_multiples():
    metrics = calculate(inputs())
    assert {name: row.value for name, row in metrics.items()} == {
        "pe": D(10), "pb": D(5), "ps": D(1), "pcf": D(10),
        "pfcf": D("12.5"), "dividend_yield": D("0.01"),
    }
    assert metrics["pe"].value != (D(10) + D(20) + D(8)) / D(3)
    assert metrics["pfcf"].aggregate_denominator == D(80)
    assert metrics["dividend_yield"].aggregate_numerator == D(10)
    assert all(row.status == "complete" for row in metrics.values())


@pytest.mark.parametrize("last_profit,expected", [("-5", "50"), ("-25", None), ("-30", None)])
def test_losses_stay_in_aggregate_and_nonpositive_denominators_are_unavailable(last_profit, expected):
    args = inputs()
    change_fact(args, 2, "net_income", last_profit)
    row = calculate(args)["pe"]
    assert row.value == (D(expected) if expected else None)
    if expected is None:
        assert row.reason == "non_positive_denominator"
        assert row.status == "unavailable"


@pytest.mark.parametrize("metric,field", [("pb", "common_equity"), ("ps", "revenue"),
                                          ("pcf", "operating_cash_flow"), ("pfcf", "operating_cash_flow")])
def test_nonpositive_rule_applies_to_each_multiple(metric, field):
    args = inputs()
    for index in range(3):
        change_fact(args, index, field, "0")
    row = calculate(args)[metric]
    assert row.value is None
    assert row.reason == "non_positive_denominator"


def test_banks_insurers_and_noncomparable_revenue_have_explicit_eligible_scopes():
    args = inputs()
    args[1][1] = replace(args[1][1], industry="bank", revenue_comparable=False)
    args[1][2] = replace(args[1][2], industry="insurer", revenue_comparable=True)
    metrics = calculate(args)
    assert metrics["pcf"].value == D(5)
    assert metrics["pfcf"].aggregate_numerator == D(100)
    assert metrics["pcf"].eligible_security_ids == ("US:A",)
    assert metrics["pcf"].eligible_weight == D("0.1")
    assert metrics["pcf"].whole_cohort_coverage.reported == D("0.1")
    assert metrics["pcf"].whole_cohort_coverage.ineligible == D("0.9")
    assert metrics["pcf"].eligible_scope_coverage.reported == D(1)
    assert metrics["ps"].eligible_security_ids == ("US:A", "US:C")
    assert metrics["ps"].aggregate_numerator == D(700)
    assert metrics["pe"].aggregate_numerator == D(1000)


def test_unknown_industry_and_unverified_revenue_fail_closed():
    args = inputs()
    args = (args[0], [replace(p, industry="unknown", revenue_comparable=False) for p in args[1]], *args[2:])
    metrics = calculate(args)
    for metric in ("ps", "pcf", "pfcf"):
        assert metrics[metric].value is None
        assert metrics[metric].reason == "no_eligible_constituents"
    assert metrics["pe"].value == D(10)


def test_reported_carried_and_imputed_weights_are_distinct_and_imputation_is_not_source_coverage():
    args = inputs()
    change_fact(args, 1, "net_income", "15", status="carried_forward")
    change_fact(args, 2, "net_income", "75", status="imputed")
    row = calculate(args)["pe"]
    coverage = row.whole_cohort_coverage
    assert (coverage.reported, coverage.carried_forward, coverage.imputed, coverage.missing_or_invalid) == (
        D("0.1"), D("0.3"), D("0.6"), D(0))
    assert coverage.source_coverage == D("0.4")
    assert row.value == D(10)
    assert row.status == "warning"
    assert row.reason == "partly_estimated"
    assert row.observed_numerator == D(400)
    assert row.observed_denominator == D(25)
    assert row.observed_value == D(16)


def test_missing_fixed_member_retains_its_weight_and_direct_aggregates_for_imputation():
    args = inputs()
    change_fact(args, 2, "net_income", None)
    row = calculate(args)["pe"]
    assert row.value is None
    assert row.reason == "awaiting_imputation"
    assert row.aggregate_market_cap == D(1000)
    assert row.aggregate_numerator == D(1000)
    assert row.aggregate_denominator is None
    assert row.observed_numerator == D(400)
    assert row.observed_denominator == D(25)
    assert row.observed_value == D(16)
    assert row.whole_cohort_coverage.missing_or_invalid == D("0.6")
    assert row.whole_cohort_coverage.source_coverage == D("0.4")
    assert row.constituent_count == row.constituent_target_count == 3
    assert row.security_ids == ("US:A", "US:B", "US:C")
    assert calculate(args)["pb"].value == D(5)
    args[2].pop()
    assert calculate(args)["pe"].whole_cohort_coverage.missing_or_invalid == D("0.6")


def test_invalid_facts_and_mixed_fcf_sources_have_conservative_combined_status():
    args = inputs()
    change_fact(args, 0, "capex", "5", status="carried_forward")
    change_fact(args, 1, "capex", "5", status="imputed")
    change_fact(args, 2, "capex", "10", status="invalid")
    row = calculate(args)["pfcf"]
    coverage = row.whole_cohort_coverage
    assert (coverage.reported, coverage.carried_forward, coverage.imputed, coverage.missing_or_invalid) == (
        D(0), D("0.1"), D("0.3"), D("0.6"))
    assert row.value is None
    assert calculate(args)["pcf"].value == D(10)


def test_exact_fcf_requires_matching_ttm_periods_and_accepts_zero_cash_capex():
    args = inputs()
    change_fact(args, 0, "capex", "0")
    assert calculate(args)["pfcf"].aggregate_denominator == D(85)
    company = args[2][2]
    capex = replace(company.fundamentals.capex, period_start=date(2026, 1, 1))
    args[2][2] = replace(company, fundamentals=replace(company.fundamentals, capex=capex))
    row = calculate(args)["pfcf"]
    assert row.value is None
    assert row.whole_cohort_coverage.missing_or_invalid == D("0.6")
    assert calculate(args)["pcf"].value == D(10)


def test_exact_fcf_rejects_undated_cash_flow_inputs():
    args = inputs()
    company = args[2][2]
    changes = {name: replace(getattr(company.fundamentals, name), period_start=None, period_end=None)
               for name in ("operating_cash_flow", "capex")}
    args[2][2] = replace(company, fundamentals=replace(company.fundamentals, **changes))
    assert calculate(args)["pfcf"].value is None


def test_currency_conversion_covers_prices_and_each_fundamental_currency():
    from src.lib.pipeline.country_valuation import ValuationFx
    args = inputs()
    args[1][2] = replace(args[1][2], price=replace(args[1][2].price, close_price=D(300), trading_currency="EUR"))
    for field, amount in zip(FIELDS, ("37.5", "60", "300", "25", "5", "3"), strict=True):
        change_fact(args, 2, field, amount, unit="EUR")
    fx = ValuationFx("USD", [FxRate("EUR", "USD", DAY, D(2), "fixture", CUTOFF)])
    converted = calculate((*args[:3], fx, args[4]))
    baseline = calculate(inputs())
    assert converted == baseline


def test_missing_fact_fx_is_missing_coverage_but_missing_price_fx_never_renormalizes():
    args = inputs()
    change_fact(args, 2, "net_income", "75", unit="EUR")
    row = calculate(args)["pe"]
    assert row.reason == "awaiting_imputation"
    assert row.whole_cohort_coverage.missing_or_invalid == D("0.6")
    args[1][2] = replace(args[1][2], price=replace(args[1][2].price, trading_currency="EUR"))
    row = calculate(args)["pe"]
    assert row.reason == "missing_constituent_market_cap"
    assert row.whole_cohort_coverage is None
    assert row.largest_constituent_weight is None
    assert row.constituent_count == 3


def test_missing_price_disables_weights_instead_of_reporting_smaller_cohort():
    args = inputs()
    args[1].pop()
    row = calculate(args)["pe"]
    assert row.value is None
    assert row.reason == "missing_constituent_market_cap"
    assert row.constituent_count == 3
    assert row.priced_constituent_count == 2
    assert row.effective_constituent_count is None
    assert row.constituent_weights == ()


def test_concentration_counts_and_formation_coverage_are_explicit():
    row = calculate(inputs())["pe"]
    assert dict(row.constituent_weights) == {"US:A": D("0.1"), "US:B": D("0.3"), "US:C": D("0.6")}
    assert row.largest_constituent_weight == D("0.6")
    assert row.top_five_weight == row.top_ten_weight == D(1)
    assert abs(row.effective_constituent_count - D("2.173913043478260869565217391")) < D("1e-27")
    assert row.formation_market_coverage == D("0.78")
    assert row.market_coverage is None  # No full current-market denominator in these inputs.
    assert row.valuation_date == DAY
    assert row.cohort_effective_date == date(2026, 1, 1)
    assert row.methodology_version == "mvd-v1"


def test_concentration_top_five_and_top_ten_have_distinct_scopes():
    args = inputs()
    ids = tuple(f"US:{i:02d}" for i in range(12))
    cohort = replace(args[0], security_ids=ids, constituent_target_count=12)
    prices = [replace(args[1][0], price=replace(args[1][0].price, security_id=s, close_price=D(10))) for s in ids]
    facts = [replace(args[2][0], fundamentals=replace(args[2][0].fundamentals, security_id=s)) for s in ids]
    row = calculate((cohort, prices, facts, *args[3:]))["pe"]
    assert row.effective_constituent_count == D(12)
    assert abs(row.top_five_weight - D("0.4166666666666666666666666667")) < D("1e-27")
    assert abs(row.top_ten_weight - D("0.8333333333333333333333333333")) < D("1e-27")


@pytest.mark.parametrize("value", [D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), 1.5, True])
def test_nonfinite_or_nondecimal_fundamentals_are_rejected(value):
    args = inputs()
    company = args[2][0]
    with pytest.raises(ValueError, match="finite Decimal"):
        replace(company, fundamentals=replace(company.fundamentals, net_income=FundamentalValue(value, "USD")))


@pytest.mark.parametrize("value", [D(0), D(-1), D("NaN"), 1.0, True])
def test_share_counts_must_be_finite_positive_decimals(value):
    with pytest.raises(ValueError, match="positive Decimal"):
        replace(inputs()[1][0], shares_outstanding=value)


def test_negative_cash_outflows_are_invalid_and_zero_dividends_are_valid():
    args = inputs()
    change_fact(args, 2, "capex", "-10")
    assert calculate(args)["pfcf"].reason == "awaiting_imputation"
    for i in range(3):
        change_fact(args, i, "dividends", "0")
    assert calculate(args)["dividend_yield"].value == D(0)


def test_mismatched_dates_duplicate_ids_and_blank_methodology_are_rejected():
    args = inputs()
    with pytest.raises(ValueError, match="unique"):
        calculate((args[0], [*args[1], args[1][0]], *args[2:]))
    with pytest.raises(ValueError, match="unique"):
        calculate((*args[:2], [*args[2], args[2][0]], *args[3:]))
    with pytest.raises(ValueError, match="methodology_version"):
        calculate((*args[:4], " "))
    args[1][0] = replace(args[1][0], price=replace(args[1][0].price, trading_date=DAY - timedelta(days=1)))
    with pytest.raises(ValueError, match="same valuation date"):
        calculate(args)


def test_stale_fx_future_fundamentals_and_pre_cohort_dates_are_rejected():
    from src.lib.pipeline.country_valuation import ValuationFx
    args = inputs()
    stale = FxRate("EUR", "USD", DAY - timedelta(days=1), D(2), "fixture", CUTOFF)
    with pytest.raises(ValueError, match="FX.*valuation date"):
        calculate((*args[:3], ValuationFx("USD", (stale,)), args[4]))
    company = args[2][0]
    args[2][0] = replace(company, fundamentals=replace(company.fundamentals, valuation_at=CUTOFF + timedelta(days=1)))
    with pytest.raises(ValueError, match="fundamentals.*valuation date"):
        calculate(args)
    args = inputs()
    with pytest.raises(ValueError, match="cohort effective"):
        calculate((replace(args[0], effective_date=DAY + timedelta(days=1)), *args[1:]))


def test_immutable_status_snapshot_and_results_are_deterministic_under_caller_context():
    args = inputs()
    statuses = {"net_income": "imputed"}
    args[2][0] = replace(args[2][0], statuses=statuses)
    statuses["net_income"] = "invalid"
    with pytest.raises(TypeError):
        args[2][0].statuses["net_income"] = "reported"
    baseline = calculate(args)
    with pytest.raises(FrozenInstanceError):
        baseline["pe"].value = D(99)
    with pytest.raises(FrozenInstanceError):
        baseline["pe"].whole_cohort_coverage.reported = D(99)
    with localcontext() as ctx:
        ctx.prec = 2
        ctx.rounding = ROUND_DOWN
        ctx.traps[Inexact] = True
        actual = calculate((args[0], reversed(args[1]), reversed(args[2]), *args[3:]))
        assert actual == baseline
        assert actual["pe"].whole_cohort_coverage.source_coverage == D("0.9")


def test_metadata_validation_rejects_unknown_status_industry_and_fx_collisions():
    from src.lib.pipeline.country_valuation import ValuationFx
    args = inputs()
    with pytest.raises(ValueError, match="status"):
        replace(args[2][0], statuses={"net_income": "estimated"})
    with pytest.raises(ValueError, match="field"):
        replace(args[2][0], statuses={"earnings": "reported"})
    with pytest.raises(ValueError, match="industry"):
        replace(args[1][0], industry="banks")
    rate = FxRate("EUR", "USD", DAY, D(2), "fixture", CUTOFF)
    with pytest.raises(ValueError, match="unique"):
        ValuationFx("USD", (rate, rate))


def test_price_and_fx_wrappers_reject_float_inputs_from_permissive_provider_contracts():
    from src.lib.pipeline.country_valuation import ValuationFx
    args = inputs()
    with pytest.raises(ValueError, match="positive Decimal"):
        replace(args[1][0], price=replace(args[1][0].price, close_price=100.0))
    with pytest.raises(ValueError, match="positive Decimal"):
        ValuationFx("USD", (FxRate("EUR", "USD", DAY, 2.0, "fixture", CUTOFF),))


def test_fundamental_cutoffs_must_agree_within_one_day():
    args = inputs()
    company = args[2][0]
    args[2][0] = replace(company, fundamentals=replace(company.fundamentals, valuation_at=CUTOFF - timedelta(hours=1)))
    with pytest.raises(ValueError, match="same valuation cutoff"):
        calculate(args)

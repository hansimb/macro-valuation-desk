from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import date, timedelta
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

import pytest

from src.lib.pipeline.country_valuation import CoverageWeights, DailyCountryMetric
from src.lib.pipeline.weekly_valuation import summarize_week


D = Decimal
MONDAY = date(2026, 6, 1)


def _daily(day: date, value: str | None, *, status: str = "complete", reason: str | None = None) -> DailyCountryMetric:
    return DailyCountryMetric(
        market_id="us", valuation_date=day, cohort_effective_date=date(2026, 1, 1),
        methodology_version="mvd-v1", metric="pe", common_currency="USD",
        security_ids=("A", "B"), constituent_count=2, constituent_target_count=2,
        priced_constituent_count=2, formation_market_coverage=D("0.78"), market_coverage=D("0.77"),
        eligible_security_ids=("A", "B"), eligible_weight=D(1), aggregate_market_cap=D(100),
        aggregate_numerator=D(100), aggregate_denominator=D(10), value=None if value is None else D(value),
        status=status, reason=reason,
        whole_cohort_coverage=CoverageWeights(D("0.6"), D("0.2"), D("0.1"), D("0.1")),
        eligible_scope_coverage=CoverageWeights(D("0.6"), D("0.2"), D("0.1"), D("0.1")),
        constituent_weights=(("A", D("0.7")), ("B", D("0.3"))), largest_constituent_weight=D("0.7"),
        top_five_weight=D(1), top_ten_weight=D(1), effective_constituent_count=D("1.724137931034482758620689655"),
    )


def _week(values: tuple[str | None, ...]) -> list[DailyCountryMetric]:
    return [_daily(MONDAY + timedelta(days=index), value, status="complete" if value else "unavailable")
            for index, value in enumerate(values)]


def test_weekly_headline_is_median_of_five_daily_aggregate_values():
    weekly = summarize_week(_week(("18", "10", "14", "12", "16")))

    assert weekly.value == D("14")
    assert weekly.minimum == D("10")
    assert weekly.maximum == D("18")
    assert weekly.valid_observation_count == 5
    assert weekly.valuation_dates == tuple(MONDAY + timedelta(days=index) for index in range(5))


def test_four_day_holiday_week_is_publishable_and_preserves_observed_range():
    weekly = summarize_week(_week(("10", "12", None, "16", "14")))

    assert weekly.status == "warning"
    assert weekly.value == D("13")
    assert weekly.minimum == D("10")
    assert weekly.maximum == D("16")
    assert weekly.valid_observation_count == 4
    assert weekly.warning_codes == ("holiday_or_missing_trading_day",)


def test_fewer_than_three_daily_values_is_unavailable_with_exact_reason():
    rows = _week(("10", None, None, "14", None))
    rows[1] = replace(rows[1], reason="awaiting_imputation")
    rows[2] = replace(rows[2], reason="non_positive_denominator")
    weekly = summarize_week(rows)

    assert weekly.status == "unavailable"
    assert weekly.reason == "fewer_than_three_valid_daily_observations"
    assert weekly.value is None
    assert weekly.valid_observation_count == 2
    assert weekly.warning_codes == (
        "awaiting_imputation", "holiday_or_missing_trading_day", "non_positive_denominator",
    )


def test_rejects_mixed_context_duplicate_days_and_non_weekdays():
    rows = _week(("10", "11", "12", "13", "14"))
    with pytest.raises(ValueError, match="same market"):
        summarize_week([rows[0], replace(rows[1], market_id="ca"), *rows[2:]])
    with pytest.raises(ValueError, match="unique"):
        summarize_week([*rows, rows[0]])
    with pytest.raises(ValueError, match="Monday.*Friday"):
        summarize_week([replace(rows[0], valuation_date=MONDAY + timedelta(days=6)), *rows[1:]])
    with pytest.raises(ValueError, match="same metric"):
        summarize_week([rows[0], replace(rows[1], metric="pb"), *rows[2:]])
    with pytest.raises(ValueError, match="same cohort membership"):
        summarize_week([rows[0], replace(rows[1], security_ids=("A", "C")), *rows[2:]])


def test_weekly_summary_retains_daily_pit_cutoff_effect_without_lookahead():
    # Tuesday's filing is public only at Tuesday's cutoff; Monday stays on the old 10x result.
    rows = _week(("10", "20", "20", "20", "20"))
    weekly = summarize_week(reversed(rows))

    assert weekly.value == D("20")
    assert weekly.daily_values == ((MONDAY, D("10")),) + tuple((MONDAY + timedelta(days=index), D("20")) for index in range(1, 5))


def test_weekly_coverage_counts_and_concentration_are_explicit_and_context_independent():
    rows = _week(("10", "12", "14", "16", "18"))
    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        weekly = summarize_week(rows)
    assert weekly.constituent_count == weekly.constituent_target_count == 2
    assert weekly.formation_market_coverage == D("0.78")
    assert weekly.market_coverage == D("0.77")
    assert weekly.whole_cohort_coverage.reported == D("0.6")
    assert weekly.whole_cohort_coverage.imputed == D("0.1")
    assert weekly.eligible_weight == D(1)
    assert weekly.effective_constituent_count == D("1.724137931034482758620689655")
    assert weekly.warning_codes == ()
    with pytest.raises(FrozenInstanceError):
        weekly.value = D(99)


def test_interpolated_even_day_median_uses_conservative_multi_day_diagnostics_not_monday_snapshot():
    rows = _week(("10", "20", "30", "40"))
    reported = ("0.9", "0.8", "0.7", "0.6")
    imputed = ("0.1", "0.2", "0.3", "0.4")
    largest = ("0.2", "0.5", "0.7", "0.4")
    effective = ("5", "4", "3", "2")
    rows = [replace(
        row,
        eligible_weight=D(reported[index]),
        whole_cohort_coverage=CoverageWeights(D(reported[index]), D(0), D(imputed[index]), D(0)),
        eligible_scope_coverage=CoverageWeights(D(reported[index]), D(0), D(imputed[index]), D(0)),
        largest_constituent_weight=D(largest[index]),
        effective_constituent_count=D(effective[index]),
    ) for index, row in enumerate(rows)]

    weekly = summarize_week(rows)

    assert weekly.value == D("25")
    assert weekly.whole_cohort_coverage.reported_min == D("0.6")
    assert weekly.whole_cohort_coverage.imputed_max == D("0.4")
    assert weekly.whole_cohort_coverage.source_coverage_min == D("0.6")
    assert weekly.eligible_weight == D("0.6")
    assert weekly.largest_constituent_weight == D("0.7")
    assert weekly.effective_constituent_count == D("2")
    assert weekly.diagnostic_policy == "conservative_valid_day_bounds_v1"

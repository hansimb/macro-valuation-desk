from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import date
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

import pytest

from src.lib.pipeline.country_cohorts import CountryCohort
from src.lib.pipeline.country_valuation import CoverageWeights, DailyCountryMetric
from src.lib.pipeline.uncertainty import AggregateContribution, SensitivityInput, estimate_sensitivity


D = Decimal


def _metric() -> DailyCountryMetric:
    return DailyCountryMetric(
        market_id="us", valuation_date=date(2026, 6, 5), cohort_effective_date=date(2026, 1, 1),
        methodology_version="mvd-v1", metric="pe", common_currency="USD", security_ids=("A", "B"),
        constituent_count=2, constituent_target_count=2, priced_constituent_count=2,
        formation_market_coverage=D("0.78"), aggregate_market_cap=D(100), aggregate_numerator=D(100),
        aggregate_denominator=None, observed_numerator=D(60), observed_denominator=D(6), observed_value=D(10),
        reason="awaiting_imputation", whole_cohort_coverage=CoverageWeights(D("0.6"), D(0), D(0), D("0.4")),
        eligible_scope_coverage=CoverageWeights(D("0.6"), D(0), D(0), D("0.4")),
        constituent_weights=(("A", D("0.6")), ("B", D("0.4"))), largest_constituent_weight=D("0.6"),
        top_five_weight=D(1), top_ten_weight=D(1), effective_constituent_count=D("1.923076923076923076923076923"),
    )


def _input(**changes: object) -> SensitivityInput:
    values: dict[str, object] = dict(
        metric=_metric(), contributions={"A": AggregateContribution(D("60"), D("6")), "B": None},
        peer_contributions={"B": (
            AggregateContribution(D("40"), D("10")), AggregateContribution(D("40"), D("14")),
            AggregateContribution(D("40"), D("18")),
        )},
        staleness_changes={"A": D("0.05")}, cohort_transition_impact=D("0.4"),
        omitted_tail_impact=D("0.2"),
    )
    values.update(changes)
    return SensitivityInput(**values)  # type: ignore[arg-type]


def test_seeded_sensitivity_is_deterministic_and_uses_all_draws_for_percentiles():
    cohort = CountryCohort("us", date(2026, 1, 1), ("A", "B"), 2, D("0.78"))
    result = estimate_sensitivity(_input(), cohort, seed=7, draws=11)

    assert result == estimate_sensitivity(_input(), cohort, seed=7, draws=11)
    assert result != estimate_sensitivity(_input(), cohort, seed=8, draws=11)
    assert result.lower <= result.point_estimate <= result.upper
    assert len(result.draw_values) == 11
    assert result.lower == sorted(result.draw_values)[0]
    assert result.upper == sorted(result.draw_values)[-1]
    assert result.status == "experimental"
    assert "confidence" not in result.interval_label.lower()


def test_median_imputation_is_the_point_value_and_stays_out_of_source_coverage():
    cohort = CountryCohort("us", date(2026, 1, 1), ("A", "B"), 2, D("0.78"))
    result = estimate_sensitivity(_input(), cohort, seed=1, draws=3)

    # This is aggregate market-cap / aggregate fundamentals (100 / (6 + 14)),
    # deliberately not a cap-weighted average of the two company multiples.
    assert result.point_estimate == D("5")
    assert result.imputed_weight == D("0.4")
    assert result.reported_weight == D("0.6")
    assert result.carried_forward_weight == D(0)


def test_reports_leave_one_out_effective_count_and_stably_ordered_component_warnings():
    cohort = CountryCohort("us", date(2026, 1, 1), ("A", "B"), 2, D("0.78"))
    result = estimate_sensitivity(_input(), cohort, seed=4, draws=20)

    assert result.leave_one_out_impact > D(0)
    assert result.top_group_impact == D("2.1428571428571428571428571428571428571428571428571")
    assert result.top_group_impact != result.leave_one_out_impact
    assert result.effective_constituent_count == D("1.923076923076923076923076923")
    assert tuple(warning.code for warning in result.warnings) == tuple(sorted(warning.code for warning in result.warnings))
    assert {warning.code for warning in result.warnings} >= {"missing_fact", "staleness", "concentration", "cohort_transition", "omitted_tail"}


def test_staleness_component_is_measured_in_aggregate_metric_units():
    cohort = CountryCohort("us", date(2026, 1, 1), ("A", "B"), 2, D("0.78"))
    result = estimate_sensitivity(_input(), cohort, seed=4, draws=20)
    component = next(item for item in result.components if item.code == "staleness")

    # Moving a 6-unit fundamental by 5% changes the country ratio by about
    # 0.15x; reporting 0.60 fundamental units as interval width is invalid.
    assert D(0) < component.interval_width_contribution < D("0.2")


@pytest.mark.parametrize("seed,draws", [(True, 2), ("1", 2), (1, 0), (1, True)])
def test_rejects_invalid_seed_and_draw_count(seed: object, draws: object):
    cohort = CountryCohort("us", date(2026, 1, 1), ("A", "B"), 2, D("0.78"))
    with pytest.raises(ValueError):
        estimate_sensitivity(_input(), cohort, seed=seed, draws=draws)  # type: ignore[arg-type]


def test_nonpositive_aggregate_denominator_is_unavailable_without_erasing_losses():
    cohort = CountryCohort("us", date(2026, 1, 1), ("A", "B"), 2, D("0.78"))
    invalid = _input(contributions={
        "A": AggregateContribution(D("60"), D("6")),
        "B": AggregateContribution(D("40"), D("-10")),
    })

    result = estimate_sensitivity(invalid, cohort, seed=1, draws=3)
    assert result.status == "unavailable"
    assert result.reason == "non_positive_denominator"
    assert result.point_estimate is None


def test_dividend_yield_recomputes_dividends_over_market_cap_for_each_imputation():
    cohort = CountryCohort("us", date(2026, 1, 1), ("A", "B"), 2, D("0.78"))
    yield_metric = replace(_metric(), metric="dividend_yield")
    input_value = _input(
        metric=yield_metric,
        contributions={"A": AggregateContribution(D("5"), D("60")), "B": None},
        peer_contributions={"B": (
            AggregateContribution(D("2"), D("40")), AggregateContribution(D("4"), D("40")),
            AggregateContribution(D("6"), D("40")),
        )},
    )

    result = estimate_sensitivity(input_value, cohort, seed=1, draws=3)
    assert result.point_estimate == D("0.09")


def test_input_and_result_are_immutable_and_ignore_caller_decimal_context():
    peers = {"B": [AggregateContribution(D("40"), D("10")), AggregateContribution(D("40"), D("14")), AggregateContribution(D("40"), D("18"))]}
    input_value = _input(peer_contributions=peers)
    peers["B"].append(AggregateContribution(D("999"), D("999")))
    cohort = CountryCohort("us", date(2026, 1, 1), ("A", "B"), 2, D("0.78"))
    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        result = estimate_sensitivity(input_value, cohort, seed=2, draws=7)
    assert AggregateContribution(D("999"), D("999")) not in input_value.peer_contributions["B"]
    with pytest.raises(FrozenInstanceError):
        result.lower = D(0)

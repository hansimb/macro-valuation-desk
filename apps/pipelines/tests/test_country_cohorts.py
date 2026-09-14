from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal, localcontext

import pytest

from src.lib.pipeline.country_cohorts import (
    CohortCandidate,
    form_cohort,
    evaluate_cohort_coverage,
)


def _candidate(
    security_id: str,
    market_cap: str,
    *,
    was_member: bool = False,
    forced_replacement: bool = False,
) -> CohortCandidate:
    return CohortCandidate(
        security_id=security_id,
        market_cap=Decimal(market_cap),
        was_member=was_member,
        forced_replacement=forced_replacement,
    )


def test_form_cohort_uses_the_smallest_constituent_count_in_the_formation_band():
    cohort = form_cohort(
        "us_total_market",
        date(2026, 1, 1),
        [_candidate("A", "40"), _candidate("B", "35"), _candidate("C", "20"), _candidate("D", "5")],
    )

    assert cohort.security_ids == ("A", "B")
    assert cohort.constituent_target_count == 2
    assert cohort.achieved_market_coverage == Decimal("0.75")
    assert cohort.reasons == ()


def test_form_cohort_breaks_equal_market_cap_ties_by_security_id():
    cohort = form_cohort(
        "us_total_market",
        date(2026, 1, 1),
        [_candidate("B", "40"), _candidate("A", "40"), _candidate("C", "20")],
    )

    assert cohort.security_ids == ("A", "B")
    assert cohort.achieved_market_coverage == Decimal("0.80")


def test_form_cohort_uses_the_closest_coverage_at_or_above_lower_target_when_band_is_unreachable():
    cohort = form_cohort(
        "us_total_market",
        date(2026, 1, 1),
        [_candidate("A", "60"), _candidate("B", "30"), _candidate("C", "10")],
    )

    assert cohort.security_ids == ("A", "B")
    assert cohort.achieved_market_coverage == Decimal("0.90")
    assert cohort.reasons == ("coverage_band_unreachable",)


@pytest.mark.parametrize(
    ("market_caps", "reason"),
    [
        ({"A": Decimal("40"), "B": Decimal("32"), "C": Decimal("28")}, "coverage_below_tolerance"),
        ({"A": Decimal("50"), "B": Decimal("34"), "C": Decimal("16")}, "coverage_above_tolerance"),
    ],
)
def test_evaluate_cohort_coverage_warns_outside_operating_tolerance(market_caps, reason):
    cohort = form_cohort(
        "us_total_market",
        date(2026, 1, 1),
        [_candidate("A", "40"), _candidate("B", "35"), _candidate("C", "25")],
    )

    coverage = evaluate_cohort_coverage(cohort, market_caps)

    assert coverage.market_coverage == (Decimal("0.72") if reason == "coverage_below_tolerance" else Decimal("0.84"))
    assert coverage.reasons == (reason,)
    assert coverage.consecutive_outside_tolerance_weeks == 1
    assert not coverage.exceptional_reconstitution_required


def test_evaluate_cohort_coverage_requires_two_consecutive_outside_weeks_for_exceptional_reconstitution():
    cohort = form_cohort(
        "us_total_market",
        date(2026, 1, 1),
        [_candidate("A", "40"), _candidate("B", "35"), _candidate("C", "25")],
    )
    first_week = evaluate_cohort_coverage(
        cohort,
        {"A": Decimal("40"), "B": Decimal("32"), "C": Decimal("28")},
    )
    second_week_cohort = cohort.with_outside_tolerance_weeks(
        first_week.consecutive_outside_tolerance_weeks,
    )

    second_week = evaluate_cohort_coverage(
        second_week_cohort,
        {"A": Decimal("40"), "B": Decimal("32"), "C": Decimal("28")},
    )

    assert first_week.consecutive_outside_tolerance_weeks == 1
    assert not first_week.exceptional_reconstitution_required
    assert second_week.consecutive_outside_tolerance_weeks == 2
    assert second_week.exceptional_reconstitution_required
    assert second_week.reasons == ("coverage_below_tolerance", "exceptional_reconstitution_required")


def test_form_cohort_forced_replacement_keeps_the_previous_constituent_count():
    cohort = form_cohort(
        "us_total_market",
        date(2026, 2, 1),
        [
            _candidate("A", "50", was_member=True),
            _candidate("B", "25", forced_replacement=True),
            _candidate("C", "25"),
        ],
        prior_constituent_target_count=2,
    )

    assert cohort.security_ids == ("A", "B")
    assert cohort.constituent_target_count == 2
    assert cohort.achieved_market_coverage == Decimal("0.75")
    assert cohort.reasons == ("forced_replacement",)


def test_form_cohort_keeps_the_band_warning_when_a_forced_replacement_cannot_meet_the_target():
    cohort = form_cohort(
        "us_total_market",
        date(2026, 2, 1),
        [
            _candidate("A", "60", was_member=True),
            _candidate("B", "30", forced_replacement=True),
            _candidate("C", "10"),
        ],
        prior_constituent_target_count=2,
    )

    assert cohort.constituent_target_count == 2
    assert cohort.achieved_market_coverage == Decimal("0.90")
    assert cohort.reasons == ("forced_replacement", "coverage_band_unreachable")


def test_form_cohort_forced_replacement_preserves_explicit_prior_count_when_an_outgoing_member_is_absent():
    cohort = form_cohort(
        "us_total_market",
        date(2026, 2, 1),
        [
            _candidate("A", "60", was_member=True),
            _candidate("B", "20", forced_replacement=True),
            _candidate("C", "20"),
        ],
        prior_constituent_target_count=2,
    )

    assert cohort.security_ids == ("A", "B")
    assert cohort.constituent_target_count == 2
    assert cohort.reasons == ("forced_replacement",)


def test_form_cohort_retains_valid_prior_members_before_forced_or_unrelated_candidates():
    cohort = form_cohort(
        "us_total_market",
        date(2026, 2, 1),
        [
            _candidate("A", "20", was_member=True),
            _candidate("B", "10", was_member=True),
            _candidate("C", "30", forced_replacement=True),
            _candidate("D", "100"),
        ],
        prior_constituent_target_count=3,
    )

    assert cohort.security_ids == ("C", "A", "B")
    assert cohort.constituent_target_count == 3
    assert "D" not in cohort.security_ids


def test_form_cohort_requires_a_positive_explicit_prior_count_for_forced_replacements():
    candidates = [_candidate("A", "60", was_member=True), _candidate("B", "40", forced_replacement=True)]

    with pytest.raises(ValueError, match="prior_constituent_target_count"):
        form_cohort("us_total_market", date(2026, 2, 1), candidates)
    with pytest.raises(ValueError, match="prior_constituent_target_count"):
        form_cohort("us_total_market", date(2026, 2, 1), candidates, prior_constituent_target_count=0)
    with pytest.raises(ValueError, match="prior_constituent_target_count"):
        form_cohort("us_total_market", date(2026, 2, 1), candidates, prior_constituent_target_count=True)


def test_cohort_outputs_are_immutable_and_decimal_math_ignores_caller_precision():
    candidates = [
        _candidate("A", "123456789012345678901234567890"),
        _candidate("B", "123456789012345678901234567890"),
    ]

    with localcontext() as context:
        context.prec = 6
        cohort = form_cohort("us_total_market", date(2026, 1, 1), candidates)

    assert cohort.achieved_market_coverage == Decimal("1")
    with pytest.raises(FrozenInstanceError):
        cohort.market_id = "changed"
    with pytest.raises(AttributeError):
        cohort.security_ids += ("C",)


def test_form_cohort_requires_a_calendar_effective_date():
    with pytest.raises(ValueError, match="effective_date"):
        form_cohort("us_total_market", "2026-01-01", [_candidate("A", "100")])

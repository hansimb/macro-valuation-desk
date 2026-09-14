"""Pure, deterministic country-index cohort formation and coverage checks.

The caller owns persistence and the weekly history hand-off.  A cohort records
the current consecutive out-of-tolerance count; :class:`CohortCoverage` returns
the next count, which can be installed with ``with_outside_tolerance_weeks``.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Context, Decimal, localcontext
from fractions import Fraction


FORMATION_TARGET = (Decimal("0.75"), Decimal("0.80"))
OPERATING_TOLERANCE = Decimal("0.025")


@dataclass(frozen=True)
class CohortCandidate:
    """An eligible security and its point-in-time market capitalization.

    ``was_member`` and ``forced_replacement`` are supplied by the reconstitution
    orchestrator.  They let this pure module preserve a frozen count while a
    required incoming security replaces an outgoing one.
    """

    security_id: str
    market_cap: Decimal
    was_member: bool = False
    forced_replacement: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.security_id, str) or not self.security_id:
            raise ValueError("security_id must be a non-empty string")
        _require_positive_decimal("market_cap", self.market_cap)


@dataclass(frozen=True)
class CountryCohort:
    market_id: str
    effective_date: date
    security_ids: tuple[str, ...]
    constituent_target_count: int
    achieved_market_coverage: Decimal
    target: tuple[Decimal, Decimal] = FORMATION_TARGET
    reasons: tuple[str, ...] = ()
    consecutive_outside_tolerance_weeks: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.market_id, str) or not self.market_id:
            raise ValueError("market_id must be a non-empty string")
        if not isinstance(self.effective_date, date) or isinstance(self.effective_date, datetime):
            raise ValueError("effective_date must be a calendar date")
        if not self.security_ids:
            raise ValueError("security_ids must not be empty")
        if len(self.security_ids) != len(set(self.security_ids)):
            raise ValueError("security_ids must be unique")
        if self.constituent_target_count != len(self.security_ids):
            raise ValueError("constituent_target_count must equal security_ids length")
        if self.consecutive_outside_tolerance_weeks < 0:
            raise ValueError("consecutive_outside_tolerance_weeks must not be negative")
        _validate_target(self.target)
        _require_unit_decimal("achieved_market_coverage", self.achieved_market_coverage)

    def with_outside_tolerance_weeks(self, weeks: int) -> CountryCohort:
        """Return the immutable next-week history state without changing membership."""
        if isinstance(weeks, bool) or not isinstance(weeks, int) or weeks < 0:
            raise ValueError("weeks must be a non-negative integer")
        return replace(self, consecutive_outside_tolerance_weeks=weeks)


@dataclass(frozen=True)
class CohortCoverage:
    market_coverage: Decimal
    constituent_market_cap: Decimal
    eligible_market_cap: Decimal
    reasons: tuple[str, ...] = ()
    consecutive_outside_tolerance_weeks: int = 0
    exceptional_reconstitution_required: bool = False


def form_cohort(
    market_id: str,
    effective_date: date,
    candidates: Iterable[CohortCandidate],
    target: tuple[Decimal, Decimal] = FORMATION_TARGET,
) -> CountryCohort:
    """Choose a deterministic formation cohort without reading or mutating state.

    The normal path takes the smallest descending-capitalization prefix in the
    target band.  If no such prefix exists, the first prefix at or above the
    lower bound is necessarily closest to it and gets a persistent reason code.
    Forced replacements use the prior member count and reserve a slot for every
    forced incoming candidate.
    """
    _validate_target(target)
    items = _validated_candidates(candidates)
    ranked = tuple(sorted(items, key=_rank_key))
    forced = tuple(candidate for candidate in ranked if candidate.forced_replacement)
    previous_count = sum(candidate.was_member for candidate in items)

    if forced:
        if previous_count == 0:
            raise ValueError("forced replacements require a prior constituent count")
        if len(forced) > previous_count:
            raise ValueError("forced replacements exceed the prior constituent count")
        selected = list(forced)
        selected_ids = {candidate.security_id for candidate in selected}
        for candidate in ranked:
            if len(selected) == previous_count:
                break
            if candidate.security_id not in selected_ids:
                selected.append(candidate)
                selected_ids.add(candidate.security_id)
        if len(selected) != previous_count:
            raise ValueError("not enough eligible candidates to preserve constituent count")
        selected.sort(key=_rank_key)
        reasons = ["forced_replacement"]
    else:
        selected, in_band = _smallest_formation_prefix(ranked, target)
        reasons = [] if in_band else ["coverage_band_unreachable"]

    universe_cap = sum((Fraction(candidate.market_cap) for candidate in ranked), Fraction())
    selected_cap = sum((Fraction(candidate.market_cap) for candidate in selected), Fraction())
    if forced and not Fraction(target[0]) <= selected_cap / universe_cap <= Fraction(target[1]):
        reasons.append("coverage_band_unreachable")
    return CountryCohort(
        market_id=market_id,
        effective_date=effective_date,
        security_ids=tuple(candidate.security_id for candidate in selected),
        constituent_target_count=len(selected),
        achieved_market_coverage=_decimal_ratio(selected_cap, universe_cap),
        target=target,
        reasons=tuple(reasons),
    )


def evaluate_cohort_coverage(
    cohort: CountryCohort,
    market_caps: Mapping[str, Decimal],
) -> CohortCoverage:
    """Evaluate a frozen cohort against one published weekly eligible universe."""
    caps = _validated_market_caps(market_caps)
    eligible_cap = sum((Fraction(value) for value in caps.values()), Fraction())
    if not eligible_cap:
        raise ValueError("market_caps must contain at least one eligible security")

    missing = tuple(security_id for security_id in cohort.security_ids if security_id not in caps)
    constituent_cap = sum((Fraction(caps[security_id]) for security_id in cohort.security_ids if security_id in caps), Fraction())
    coverage = _decimal_ratio(constituent_cap, eligible_cap)
    lower, upper = cohort.target
    operating_lower = lower - OPERATING_TOLERANCE
    operating_upper = upper + OPERATING_TOLERANCE
    reasons: list[str] = ["missing_constituent_market_cap"] if missing else []
    outside = coverage < operating_lower or coverage > operating_upper
    if coverage < operating_lower:
        reasons.append("coverage_below_tolerance")
    elif coverage > operating_upper:
        reasons.append("coverage_above_tolerance")

    weeks = cohort.consecutive_outside_tolerance_weeks + 1 if outside else 0
    exceptional = weeks >= 2
    if exceptional:
        reasons.append("exceptional_reconstitution_required")
    return CohortCoverage(
        market_coverage=coverage,
        constituent_market_cap=_decimal_fraction(constituent_cap),
        eligible_market_cap=_decimal_fraction(eligible_cap),
        reasons=tuple(reasons),
        consecutive_outside_tolerance_weeks=weeks,
        exceptional_reconstitution_required=exceptional,
    )


def _smallest_formation_prefix(
    ranked: tuple[CohortCandidate, ...], target: tuple[Decimal, Decimal],
) -> tuple[list[CohortCandidate], bool]:
    lower, upper = (Fraction(value) for value in target)
    universe_cap = sum((Fraction(candidate.market_cap) for candidate in ranked), Fraction())
    selected: list[CohortCandidate] = []
    selected_cap = Fraction()
    for candidate in ranked:
        selected.append(candidate)
        selected_cap += Fraction(candidate.market_cap)
        coverage = selected_cap / universe_cap
        if lower <= coverage <= upper:
            return selected, True
        if coverage >= lower:
            return selected, False
    raise AssertionError("positive candidate caps must reach the lower target")


def _validated_candidates(candidates: Iterable[CohortCandidate]) -> tuple[CohortCandidate, ...]:
    items = tuple(candidates)
    if not items:
        raise ValueError("candidates must not be empty")
    if not all(isinstance(candidate, CohortCandidate) for candidate in items):
        raise TypeError("candidates must contain CohortCandidate values")
    security_ids = tuple(candidate.security_id for candidate in items)
    if len(security_ids) != len(set(security_ids)):
        raise ValueError("candidate security_ids must be unique")
    return items


def _validated_market_caps(market_caps: Mapping[str, Decimal]) -> dict[str, Decimal]:
    values = dict(market_caps)
    for security_id, market_cap in values.items():
        if not isinstance(security_id, str) or not security_id:
            raise ValueError("market_caps keys must be non-empty strings")
        _require_positive_decimal("market_cap", market_cap)
    return values


def _rank_key(candidate: CohortCandidate) -> tuple[Fraction, str]:
    return (-Fraction(candidate.market_cap), candidate.security_id)


def _validate_target(target: tuple[Decimal, Decimal]) -> None:
    if not isinstance(target, tuple) or len(target) != 2:
        raise ValueError("target must be a two-Decimal tuple")
    lower, upper = target
    _require_unit_decimal("target lower", lower)
    _require_unit_decimal("target upper", upper)
    if lower > upper:
        raise ValueError("target lower must not exceed target upper")


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        raise ValueError(f"{field_name} must be a finite positive Decimal")


def _require_unit_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0 or value > 1:
        raise ValueError(f"{field_name} must be a finite Decimal from zero through one")


def _decimal_ratio(numerator: Fraction, denominator: Fraction) -> Decimal:
    return _decimal_fraction(numerator / denominator)


def _decimal_fraction(value: Fraction) -> Decimal:
    """Render a rational value independent of the caller's Decimal context."""
    precision = max(50, len(str(abs(value.numerator))) + len(str(value.denominator)) + 10)
    with localcontext(Context(prec=precision)):
        return Decimal(value.numerator) / Decimal(value.denominator)

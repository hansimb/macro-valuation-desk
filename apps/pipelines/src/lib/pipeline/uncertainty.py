"""Deterministic, explicitly experimental valuation sensitivity intervals.

Country valuation metrics are ratios of aggregate contributions. This module
simulates numerator and denominator contributions, then recomputes the country
ratio for every draw. It never averages company multiples.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Context, Decimal, localcontext
from fractions import Fraction
from math import ceil
from random import Random
from types import MappingProxyType

from src.lib.pipeline.country_cohorts import CountryCohort
from src.lib.pipeline.country_valuation import DailyCountryMetric


def _decimal(value: Fraction) -> Decimal:
    precision = max(50, len(str(abs(value.numerator))) + len(str(value.denominator)) + 10)
    with localcontext(Context(prec=precision)):
        return Decimal(value.numerator) / Decimal(value.denominator)


def _finite(name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")


@dataclass(frozen=True)
class AggregateContribution:
    """One constituent's inputs to a country-level valuation ratio.

    Price multiples use market capitalization / the relevant fundamental.
    Dividend yield uses dividends / market capitalization. Negative fundamental
    contributions remain present; a non-positive aggregate denominator is
    unavailable rather than reweighted away.
    """

    numerator: Decimal
    denominator: Decimal

    def __post_init__(self) -> None:
        _finite("contribution numerator", self.numerator)
        _finite("contribution denominator", self.denominator)


@dataclass(frozen=True)
class SensitivityInput:
    """Point-in-time contribution inputs unavailable on ``DailyCountryMetric``.

    Missing fixed-cohort contributions require a caller-selected peer
    distribution from the applicable country, industry, size band and metric.
    The point estimate uses componentwise medians; simulation keeps paired peer
    contributions and recomputes the aggregate ratio.
    """

    metric: DailyCountryMetric
    contributions: Mapping[str, AggregateContribution | None] = field(default_factory=dict)
    peer_contributions: Mapping[str, tuple[AggregateContribution, ...]] = field(default_factory=dict)
    staleness_changes: Mapping[str, Decimal] = field(default_factory=dict)
    cohort_transition_impact: Decimal | None = None
    omitted_tail_impact: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.metric, DailyCountryMetric):
            raise TypeError("metric must be a DailyCountryMetric")
        contributions = dict(self.contributions)
        peers = {key: tuple(value) for key, value in self.peer_contributions.items()}
        stale = dict(self.staleness_changes)
        for name, mapping in (("contributions", contributions), ("peer_contributions", peers), ("staleness_changes", stale)):
            if any(not isinstance(key, str) or not key for key in mapping):
                raise ValueError(f"{name} keys must be non-empty strings")
        if any(value is not None and not isinstance(value, AggregateContribution) for value in contributions.values()):
            raise TypeError("contributions must contain AggregateContribution values or None")
        for distribution in peers.values():
            if not distribution:
                raise ValueError("peer contributions must not be empty")
            if any(not isinstance(value, AggregateContribution) for value in distribution):
                raise TypeError("peer contributions must contain AggregateContribution values")
        for value in stale.values():
            _finite("staleness change", value)
            if value < 0:
                raise ValueError("staleness changes must not be negative")
        for name in ("cohort_transition_impact", "omitted_tail_impact"):
            value = getattr(self, name)
            if value is not None:
                _finite(name, value)
                if value < 0:
                    raise ValueError(f"{name} must not be negative")
        object.__setattr__(self, "contributions", MappingProxyType(contributions))
        object.__setattr__(self, "peer_contributions", MappingProxyType(peers))
        object.__setattr__(self, "staleness_changes", MappingProxyType(stale))


@dataclass(frozen=True)
class SensitivityWarning:
    code: str
    explanation: str
    affected_market_cap_weight: Decimal
    interval_width_contribution: Decimal | None


@dataclass(frozen=True)
class SensitivityComponent:
    code: str
    interval_width_contribution: Decimal | None
    available: bool


@dataclass(frozen=True)
class SensitivityResult:
    point_estimate: Decimal | None
    lower: Decimal | None
    upper: Decimal | None
    draw_values: tuple[Decimal, ...]
    draws: int
    seed: int
    interval_label: str
    status: str
    reason: str | None
    warning_level: str
    imputed_weight: Decimal
    reported_weight: Decimal
    carried_forward_weight: Decimal
    effective_constituent_count: Decimal | None
    leave_one_out_impact: Decimal | None
    top_group_impact: Decimal | None
    components: tuple[SensitivityComponent, ...]
    warnings: tuple[SensitivityWarning, ...]


def estimate_sensitivity(metric: DailyCountryMetric | SensitivityInput, cohort: CountryCohort,
                         seed: int, draws: int = 1000) -> SensitivityResult:
    """Return a deterministic seeded sensitivity interval, never a confidence interval."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if isinstance(draws, bool) or not isinstance(draws, int) or draws <= 0:
        raise ValueError("draws must be a positive integer")
    if not isinstance(cohort, CountryCohort):
        raise TypeError("cohort must be a CountryCohort")
    input_value = metric if isinstance(metric, SensitivityInput) else SensitivityInput(metric=metric)
    row = input_value.metric
    _validate_context(row, cohort)
    weights = dict(row.constituent_weights)
    _validate_weights(weights, cohort)
    if not input_value.contributions:
        return _without_contributions(row, seed, draws)
    _validate_contributions(input_value, cohort)

    point_contributions = {security: contribution if contribution is not None else _median_contribution(input_value.peer_contributions[security])
                           for security, contribution in input_value.contributions.items()}
    point = _aggregate_value(point_contributions)
    imputed_weight = _weight_for_missing(input_value.contributions, weights)
    reported_weight, carried_weight = _source_weights(row)
    if point is None:
        return _unavailable(row, seed, draws, imputed_weight, reported_weight, carried_weight, "non_positive_denominator")

    random = Random(seed)
    draw_values: list[Decimal] = []
    for _ in range(draws):
        draw = dict(point_contributions)
        for security, contribution in input_value.contributions.items():
            if contribution is None:
                peers = input_value.peer_contributions[security]
                draw[security] = peers[random.randrange(len(peers))]
        draw = _apply_staleness(draw, input_value, random)
        simulated = _aggregate_value(draw)
        if simulated is None:
            return _unavailable(row, seed, draws, imputed_weight, reported_weight, carried_weight,
                                "non_positive_denominator_in_sensitivity_draw")
        if input_value.cohort_transition_impact is not None:
            simulated = _decimal(Fraction(simulated) + Fraction(input_value.cohort_transition_impact) * (1 if random.randrange(2) else -1))
        if input_value.omitted_tail_impact is not None:
            simulated = _decimal(Fraction(simulated) + Fraction(input_value.omitted_tail_impact) * (1 if random.randrange(2) else -1))
        draw_values.append(simulated)
    ordered = tuple(sorted(draw_values))
    lower, upper = _percentile(ordered, Decimal("0.05")), _percentile(ordered, Decimal("0.95"))
    loo = _leave_one_out(point_contributions)
    top_group = _leave_top_group(point_contributions, weights)
    components = _components(input_value, point_contributions, loo, top_group)
    warnings = _warnings(input_value, imputed_weight, weights, components)
    return SensitivityResult(point, lower, upper, tuple(draw_values), draws, seed,
                             "experimental seeded sensitivity interval", "experimental", None, "experimental",
                             imputed_weight, reported_weight, carried_weight, row.effective_constituent_count,
                             loo, top_group, components, warnings)


def _without_contributions(row: DailyCountryMetric, seed: int, draws: int) -> SensitivityResult:
    reported, carried = _source_weights(row)
    if row.aggregate_denominator is not None and row.aggregate_denominator <= 0:
        return _unavailable(row, seed, draws, Decimal(0), reported, carried, "non_positive_denominator")
    if row.value is None or not row.value.is_finite():
        raise ValueError("aggregate contribution inputs are required when a daily metric has no finite value")
    component = SensitivityComponent("missing_aggregate_contributions", None, False)
    warning = SensitivityWarning("missing_aggregate_contributions", "Per-constituent aggregate inputs were not supplied.", Decimal(0), None)
    return SensitivityResult(row.value, row.value, row.value, tuple(row.value for _ in range(draws)), draws, seed,
                             "experimental seeded sensitivity interval", "experimental", None, "experimental", Decimal(0),
                             reported, carried, row.effective_constituent_count, None, None, (component,), (warning,))


def _unavailable(row: DailyCountryMetric, seed: int, draws: int, imputed: Decimal, reported: Decimal,
                 carried: Decimal, reason: str) -> SensitivityResult:
    component = SensitivityComponent("non_positive_denominator", None, True)
    warning = SensitivityWarning("non_positive_denominator", "Aggregate denominator is non-positive; the metric is unavailable.", imputed, None)
    return SensitivityResult(None, None, None, (), draws, seed, "experimental seeded sensitivity interval",
                             "unavailable", reason, "experimental", imputed, reported, carried,
                             row.effective_constituent_count, None, None, (component,), (warning,))


def _validate_context(row: DailyCountryMetric, cohort: CountryCohort) -> None:
    if row.market_id != cohort.market_id:
        raise ValueError("metric and cohort must use the same market")
    if row.cohort_effective_date != cohort.effective_date:
        raise ValueError("metric and cohort must use the same cohort effective date")
    if tuple(row.security_ids) != tuple(cohort.security_ids):
        raise ValueError("metric and cohort must use the same security_ids")


def _validate_weights(weights: dict[str, Decimal], cohort: CountryCohort) -> None:
    if set(weights) != set(cohort.security_ids):
        raise ValueError("constituent weights must cover the fixed cohort")
    for weight in weights.values():
        _finite("constituent weight", weight)
        if weight < 0:
            raise ValueError("constituent weights must not be negative")
    if sum((Fraction(weight) for weight in weights.values()), Fraction()) != 1:
        raise ValueError("constituent weights must sum exactly to one")


def _validate_contributions(input_value: SensitivityInput, cohort: CountryCohort) -> None:
    expected = set(cohort.security_ids)
    if set(input_value.contributions) != expected:
        raise ValueError("contributions must cover the fixed cohort")
    if not set(input_value.peer_contributions) <= expected:
        raise ValueError("peer contributions must belong to the fixed cohort")
    for security, contribution in input_value.contributions.items():
        if contribution is None and security not in input_value.peer_contributions:
            raise ValueError("missing contributions require point-in-time peer contributions")
    if not set(input_value.staleness_changes) <= expected:
        raise ValueError("staleness changes must belong to the fixed cohort")


def _median_contribution(values: tuple[AggregateContribution, ...]) -> AggregateContribution:
    return AggregateContribution(_median(tuple(value.numerator for value in values)), _median(tuple(value.denominator for value in values)))


def _median(values: tuple[Decimal, ...]) -> Decimal:
    ordered = tuple(sorted(values))
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else _decimal((Fraction(ordered[middle - 1]) + Fraction(ordered[middle])) / 2)


def _aggregate_value(contributions: Mapping[str, AggregateContribution]) -> Decimal | None:
    numerator = sum((Fraction(item.numerator) for item in contributions.values()), Fraction())
    denominator = sum((Fraction(item.denominator) for item in contributions.values()), Fraction())
    return None if denominator <= 0 else _decimal(numerator / denominator)


def _apply_staleness(values: Mapping[str, AggregateContribution], input_value: SensitivityInput,
                     random: Random) -> dict[str, AggregateContribution]:
    result = dict(values)
    for security, change in input_value.staleness_changes.items():
        current = result[security]
        direction = 1 if random.randrange(2) else -1
        result[security] = _adjust_contribution(current, input_value.metric.metric, change, direction)
    return result


def _adjust_contribution(current: AggregateContribution, metric_key: str, change: Decimal,
                         direction: int) -> AggregateContribution:
    multiplier = 1 + Fraction(change) * direction
    if metric_key == "dividend_yield":
        return AggregateContribution(_decimal(Fraction(current.numerator) * multiplier), current.denominator)
    return AggregateContribution(current.numerator, _decimal(Fraction(current.denominator) * multiplier))


def _percentile(values: tuple[Decimal, ...], percentile: Decimal) -> Decimal:
    return values[max(0, ceil(Fraction(percentile) * len(values)) - 1)]


def _source_weights(row: DailyCountryMetric) -> tuple[Decimal, Decimal]:
    coverage = row.eligible_scope_coverage or row.whole_cohort_coverage
    return (Decimal(0), Decimal(0)) if coverage is None else (coverage.reported, coverage.carried_forward)


def _weight_for_missing(contributions: Mapping[str, AggregateContribution | None], weights: Mapping[str, Decimal]) -> Decimal:
    return _decimal(sum((Fraction(weights[security]) for security, value in contributions.items() if value is None), Fraction()))


def _leave_one_out(values: Mapping[str, AggregateContribution]) -> Decimal | None:
    point = _aggregate_value(values)
    if point is None:
        return None
    impacts = []
    for security in values:
        comparison = _aggregate_value({key: item for key, item in values.items() if key != security})
        if comparison is not None:
            impacts.append(abs(Fraction(point) - Fraction(comparison)))
    return _decimal(max(impacts, default=Fraction()))


def _leave_top_group(values: Mapping[str, AggregateContribution], weights: Mapping[str, Decimal]) -> Decimal | None:
    point = _aggregate_value(values)
    group_size = min(5, len(values) - 1)
    if point is None or group_size <= 0:
        return None
    removed = {security for security, _ in sorted(weights.items(), key=lambda item: (-Fraction(item[1]), item[0]))[:group_size]}
    comparison = _aggregate_value({security: value for security, value in values.items() if security not in removed})
    return None if comparison is None else _decimal(abs(Fraction(point) - Fraction(comparison)))


def _components(input_value: SensitivityInput, point_values: Mapping[str, AggregateContribution],
                loo: Decimal | None, top_group: Decimal | None) -> tuple[SensitivityComponent, ...]:
    missing_width = Fraction()
    for security, value in input_value.contributions.items():
        if value is None:
            possible = []
            for peer in input_value.peer_contributions[security]:
                trial = dict(point_values)
                trial[security] = peer
                result = _aggregate_value(trial)
                if result is not None:
                    possible.append(Fraction(result))
            if possible:
                missing_width += max(possible) - min(possible)
    staleness_width = Fraction()
    for security, change in input_value.staleness_changes.items():
        current = point_values[security]
        lower_values, upper_values = dict(point_values), dict(point_values)
        lower_values[security] = _adjust_contribution(current, input_value.metric.metric, change, -1)
        upper_values[security] = _adjust_contribution(current, input_value.metric.metric, change, 1)
        lower_ratio, upper_ratio = _aggregate_value(lower_values), _aggregate_value(upper_values)
        if lower_ratio is not None and upper_ratio is not None:
            staleness_width += abs(Fraction(upper_ratio) - Fraction(lower_ratio))
    concentration = max((item for item in (loo, top_group) if item is not None), default=Decimal(0))
    return tuple(sorted((
        SensitivityComponent("cohort_transition", _decimal(Fraction(input_value.cohort_transition_impact) * 2) if input_value.cohort_transition_impact is not None else None, input_value.cohort_transition_impact is not None),
        SensitivityComponent("concentration", concentration, concentration > 0),
        SensitivityComponent("missing_fact", _decimal(missing_width) if missing_width else None, bool(missing_width)),
        SensitivityComponent("omitted_tail", _decimal(Fraction(input_value.omitted_tail_impact) * 2) if input_value.omitted_tail_impact is not None else None, input_value.omitted_tail_impact is not None),
        SensitivityComponent("staleness", _decimal(staleness_width) if staleness_width else None, bool(staleness_width)),
    ), key=lambda item: item.code))


def _warnings(input_value: SensitivityInput, imputed_weight: Decimal, weights: Mapping[str, Decimal],
              components: tuple[SensitivityComponent, ...]) -> tuple[SensitivityWarning, ...]:
    component = {item.code: item for item in components}
    entries = [SensitivityWarning("concentration", "Leave-one-out and leave-top-group sensitivity measure constituent concentration.", max(weights.values(), default=Decimal(0)), component["concentration"].interval_width_contribution)]
    if component["missing_fact"].available:
        entries.append(SensitivityWarning("missing_fact", "Missing fixed-cohort facts use point-in-time peer contribution imputation.", imputed_weight, component["missing_fact"].interval_width_contribution))
    if component["staleness"].available:
        entries.append(SensitivityWarning("staleness", "Carried facts have supplied filing-to-filing change sensitivity.", _decimal(sum((Fraction(weights[key]) for key in input_value.staleness_changes), Fraction())), component["staleness"].interval_width_contribution))
    if component["cohort_transition"].available:
        entries.append(SensitivityWarning("cohort_transition", "A supplied dual-cohort transition impact changes the estimate.", Decimal(0), component["cohort_transition"].interval_width_contribution))
    if component["omitted_tail"].available:
        entries.append(SensitivityWarning("omitted_tail", "A supplied omitted-market-tail impact changes the estimate.", Decimal(0), component["omitted_tail"].interval_width_contribution))
    return tuple(sorted(entries, key=lambda item: item.code))

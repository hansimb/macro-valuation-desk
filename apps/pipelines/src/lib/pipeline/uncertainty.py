"""Deterministic, explicitly experimental valuation sensitivity intervals.

This is not a random-sample inference model.  Callers that need missing-fact
simulation supply a :class:`SensitivityInput` with point-in-time peer values;
the module deliberately does not infer peers from a daily aggregate.
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
class SensitivityInput:
    """Auditable inputs unavailable on ``DailyCountryMetric`` alone.

    ``company_values`` must be values compatible with a capitalization-weighted
    aggregate for the supplied metric.  A ``None`` requires a non-empty,
    point-in-time peer distribution selected by the caller's country, industry,
    size-band and metric policy.  Optional calibration inputs remain absent
    rather than being fabricated.
    """

    metric: DailyCountryMetric
    company_values: Mapping[str, Decimal | None] = field(default_factory=dict)
    peer_distributions: Mapping[str, tuple[Decimal, ...]] = field(default_factory=dict)
    staleness_changes: Mapping[str, Decimal] = field(default_factory=dict)
    cohort_transition_impact: Decimal | None = None
    omitted_tail_impact: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.metric, DailyCountryMetric):
            raise TypeError("metric must be a DailyCountryMetric")
        values = dict(self.company_values)
        peers = {key: tuple(value) for key, value in self.peer_distributions.items()}
        stale = dict(self.staleness_changes)
        for name, mapping in (("company_values", values), ("peer_distributions", peers), ("staleness_changes", stale)):
            if any(not isinstance(key, str) or not key for key in mapping):
                raise ValueError(f"{name} keys must be non-empty strings")
        for value in values.values():
            if value is not None:
                _finite("company value", value)
        for distribution in peers.values():
            if not distribution:
                raise ValueError("peer distributions must not be empty")
            for value in distribution:
                _finite("peer distribution value", value)
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
        object.__setattr__(self, "company_values", MappingProxyType(values))
        object.__setattr__(self, "peer_distributions", MappingProxyType(peers))
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
    warning_level: str
    imputed_weight: Decimal
    reported_weight: Decimal
    carried_forward_weight: Decimal
    effective_constituent_count: Decimal | None
    leave_one_out_impact: Decimal | None
    top_group_impact: Decimal | None
    components: tuple[SensitivityComponent, ...]
    warnings: tuple[SensitivityWarning, ...]


def estimate_sensitivity(
    metric: DailyCountryMetric | SensitivityInput,
    cohort: CountryCohort,
    seed: int,
    draws: int = 1000,
) -> SensitivityResult:
    """Return deterministic seeded sensitivity values, never a confidence interval."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if isinstance(draws, bool) or not isinstance(draws, int) or draws <= 0:
        raise ValueError("draws must be a positive integer")
    if not isinstance(cohort, CountryCohort):
        raise TypeError("cohort must be a CountryCohort")
    input_value = metric if isinstance(metric, SensitivityInput) else SensitivityInput(metric=metric)
    row = input_value.metric
    _validate_context(row, cohort)
    if row.aggregate_denominator is not None and row.aggregate_denominator <= 0:
        raise ValueError("non-positive denominator cannot produce a sensitivity estimate")
    weights = dict(row.constituent_weights)
    _validate_weights(weights, row, cohort)
    if not input_value.company_values:
        return _without_company_inputs(row, seed, draws)
    _validate_company_inputs(input_value, cohort)

    point_values = {security: value if value is not None else _median(input_value.peer_distributions[security])
                    for security, value in input_value.company_values.items()}
    point = _aggregate(point_values, weights)
    random = Random(seed)
    draw_values: list[Decimal] = []
    for _ in range(draws):
        values = dict(point_values)
        for security, value in input_value.company_values.items():
            if value is None:
                values[security] = input_value.peer_distributions[security][random.randrange(len(input_value.peer_distributions[security]))]
        simulated = _aggregate_fraction(values, weights)
        for security, change in input_value.staleness_changes.items():
            direction = 1 if random.randrange(2) else -1
            simulated += Fraction(weights[security]) * Fraction(values[security]) * Fraction(change) * direction
        if input_value.cohort_transition_impact is not None:
            simulated += Fraction(input_value.cohort_transition_impact) * (1 if random.randrange(2) else -1)
        if input_value.omitted_tail_impact is not None:
            simulated += Fraction(input_value.omitted_tail_impact) * (1 if random.randrange(2) else -1)
        draw_values.append(_decimal(simulated))
    ordered = tuple(sorted(draw_values))
    lower, upper = _percentile(ordered, Decimal("0.05")), _percentile(ordered, Decimal("0.95"))
    imputed_weight = _decimal(sum((Fraction(weight) for security, weight in weights.items()
                                   if input_value.company_values[security] is None), Fraction()))
    reported_weight, carried_weight = _source_weights(row)
    loo = _leave_one_out(point_values, weights)
    components = _components(input_value, lower, upper, loo)
    warnings = _warnings(input_value, imputed_weight, components, loo)
    return SensitivityResult(point, lower, upper, tuple(draw_values), draws, seed,
                             "experimental seeded sensitivity interval", "experimental", "experimental",
                             imputed_weight, reported_weight, carried_weight, row.effective_constituent_count,
                             loo, loo, components, warnings)


def _without_company_inputs(row: DailyCountryMetric, seed: int, draws: int) -> SensitivityResult:
    if row.value is None or not row.value.is_finite():
        raise ValueError("company sensitivity inputs are required when a daily metric has no finite value")
    reported, carried = _source_weights(row)
    component = SensitivityComponent("missing_company_inputs", None, False)
    warning = SensitivityWarning("missing_company_inputs", "Per-company point-in-time inputs were not supplied.",
                                 Decimal(0), None)
    return SensitivityResult(row.value, row.value, row.value, tuple(row.value for _ in range(draws)), draws, seed,
                             "experimental seeded sensitivity interval", "experimental", "experimental", Decimal(0),
                             reported, carried, row.effective_constituent_count, None, None, (component,), (warning,))


def _validate_context(row: DailyCountryMetric, cohort: CountryCohort) -> None:
    if row.market_id != cohort.market_id:
        raise ValueError("metric and cohort must use the same market")
    if row.cohort_effective_date != cohort.effective_date:
        raise ValueError("metric and cohort must use the same cohort effective date")
    if tuple(row.security_ids) != tuple(cohort.security_ids):
        raise ValueError("metric and cohort must use the same security_ids")


def _validate_weights(weights: dict[str, Decimal], row: DailyCountryMetric, cohort: CountryCohort) -> None:
    if set(weights) != set(cohort.security_ids):
        raise ValueError("constituent weights must cover the fixed cohort")
    for weight in weights.values():
        _finite("constituent weight", weight)
        if weight < 0:
            raise ValueError("constituent weights must not be negative")
    total = sum((Fraction(weight) for weight in weights.values()), Fraction())
    if total != 1:
        raise ValueError("constituent weights must sum exactly to one")


def _validate_company_inputs(input_value: SensitivityInput, cohort: CountryCohort) -> None:
    expected = set(cohort.security_ids)
    if set(input_value.company_values) != expected:
        raise ValueError("company_values must cover the fixed cohort")
    extras = set(input_value.peer_distributions) - expected
    if extras:
        raise ValueError("peer distributions must belong to the fixed cohort")
    for security, value in input_value.company_values.items():
        if value is None and security not in input_value.peer_distributions:
            raise ValueError("missing company values require a point-in-time peer distribution")
    if not set(input_value.staleness_changes) <= expected:
        raise ValueError("staleness changes must belong to the fixed cohort")


def _median(values: tuple[Decimal, ...]) -> Decimal:
    ordered = tuple(sorted(values))
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else _decimal((Fraction(ordered[middle - 1]) + Fraction(ordered[middle])) / 2)


def _aggregate(values: Mapping[str, Decimal], weights: Mapping[str, Decimal]) -> Decimal:
    return _decimal(_aggregate_fraction(values, weights))


def _aggregate_fraction(values: Mapping[str, Decimal], weights: Mapping[str, Decimal]) -> Fraction:
    return sum((Fraction(values[security]) * Fraction(weight) for security, weight in weights.items()), Fraction())


def _percentile(values: tuple[Decimal, ...], percentile: Decimal) -> Decimal:
    # Nearest-rank keeps the stored interval traceable to an actual simulation draw.
    index = max(0, ceil(Fraction(percentile) * len(values)) - 1)
    return values[index]


def _source_weights(row: DailyCountryMetric) -> tuple[Decimal, Decimal]:
    coverage = row.eligible_scope_coverage or row.whole_cohort_coverage
    if coverage is None:
        return Decimal(0), Decimal(0)
    return coverage.reported, coverage.carried_forward


def _leave_one_out(values: Mapping[str, Decimal], weights: Mapping[str, Decimal]) -> Decimal:
    point = _aggregate_fraction(values, weights)
    impacts = []
    for omitted, weight in weights.items():
        remaining = Fraction(1) - Fraction(weight)
        if remaining <= 0:
            continue
        values_without = {security: value for security, value in values.items() if security != omitted}
        weights_without = {security: _decimal(Fraction(value) / remaining) for security, value in weights.items() if security != omitted}
        impacts.append(abs(point - _aggregate_fraction(values_without, weights_without)))
    return _decimal(max(impacts, default=Fraction()))


def _components(input_value: SensitivityInput, lower: Decimal, upper: Decimal, loo: Decimal) -> tuple[SensitivityComponent, ...]:
    weights = dict(input_value.metric.constituent_weights)
    missing_width = sum((
        (max(Fraction(value) for value in input_value.peer_distributions[security])
         - min(Fraction(value) for value in input_value.peer_distributions[security])) * Fraction(weights[security])
        for security, value in input_value.company_values.items() if value is None
    ), Fraction())
    staleness_width = sum((
        Fraction(weights[security]) * Fraction(input_value.company_values[security] or _median(input_value.peer_distributions.get(security, (Decimal(0),))))
        * Fraction(change) * 2
        for security, change in input_value.staleness_changes.items()
    ), Fraction())
    return tuple(sorted((
        SensitivityComponent("cohort_transition", _decimal(Fraction(input_value.cohort_transition_impact) * 2) if input_value.cohort_transition_impact is not None else None, input_value.cohort_transition_impact is not None),
        SensitivityComponent("concentration", _decimal(Fraction(loo) * 2), True),
        SensitivityComponent("missing_fact", _decimal(missing_width) if missing_width else None, bool(missing_width)),
        SensitivityComponent("omitted_tail", _decimal(Fraction(input_value.omitted_tail_impact) * 2) if input_value.omitted_tail_impact is not None else None, input_value.omitted_tail_impact is not None),
        SensitivityComponent("staleness", _decimal(staleness_width) if staleness_width else None, bool(staleness_width)),
    ), key=lambda component: component.code))


def _warnings(input_value: SensitivityInput, imputed_weight: Decimal, components: tuple[SensitivityComponent, ...], loo: Decimal) -> tuple[SensitivityWarning, ...]:
    component = {item.code: item for item in components}
    entries: list[SensitivityWarning] = [
        SensitivityWarning("concentration", "Leave-one-out sensitivity from concentrated constituents.", max(dict(input_value.metric.constituent_weights).values(), default=Decimal(0)), component["concentration"].interval_width_contribution),
    ]
    if component["missing_fact"].available:
        entries.append(SensitivityWarning("missing_fact", "Missing fixed-cohort facts use point-in-time peer imputation.", imputed_weight, component["missing_fact"].interval_width_contribution))
    if component["staleness"].available:
        entries.append(SensitivityWarning("staleness", "Carried facts have supplied filing-to-filing change sensitivity.", _decimal(sum((Fraction(dict(input_value.metric.constituent_weights)[key]) for key in input_value.staleness_changes), Fraction())), component["staleness"].interval_width_contribution))
    if component["cohort_transition"].available:
        entries.append(SensitivityWarning("cohort_transition", "A supplied dual-cohort transition impact changes the estimate.", Decimal(0), component["cohort_transition"].interval_width_contribution))
    if component["omitted_tail"].available:
        entries.append(SensitivityWarning("omitted_tail", "A supplied omitted-market-tail impact changes the estimate.", Decimal(0), component["omitted_tail"].interval_width_contribution))
    return tuple(sorted(entries, key=lambda warning: warning.code))

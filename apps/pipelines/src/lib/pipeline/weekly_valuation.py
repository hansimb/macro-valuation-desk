"""Pure weekly summaries for point-in-time country valuation observations.

The weekly headline is deliberately a median of already-aggregated daily
country values.  It is never a median or average of company multiples.  The
daily rows retain their own point-in-time fundamental cutoff; this module does
not select, replace, or otherwise revise them.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Context, Decimal, localcontext
from fractions import Fraction
from typing import Iterable

from src.lib.pipeline.country_valuation import DailyCountryMetric


def _decimal(value: Fraction) -> Decimal:
    precision = max(50, len(str(abs(value.numerator))) + len(str(value.denominator)) + 10)
    with localcontext(Context(prec=precision)):
        return Decimal(value.numerator) / Decimal(value.denominator)


def _median(values: tuple[Decimal, ...]) -> Decimal:
    ordered = tuple(sorted(values))
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else _decimal((Fraction(ordered[middle - 1]) + Fraction(ordered[middle])) / 2)


@dataclass(frozen=True)
class WeeklyCoverageDiagnostics:
    """Conservative valid-day bounds, never a fabricated weekly bucket split."""

    reported_min: Decimal
    carried_forward_min: Decimal
    imputed_max: Decimal
    missing_or_invalid_max: Decimal
    ineligible_max: Decimal
    source_coverage_min: Decimal

    @property
    def reported(self) -> Decimal:
        return self.reported_min

    @property
    def carried_forward(self) -> Decimal:
        return self.carried_forward_min

    @property
    def imputed(self) -> Decimal:
        return self.imputed_max

    @property
    def missing_or_invalid(self) -> Decimal:
        return self.missing_or_invalid_max

    @property
    def ineligible(self) -> Decimal:
        return self.ineligible_max


@dataclass(frozen=True)
class WeeklyCountryMetric:
    """An auditable weekly observation and the unchanged daily inputs behind it.

    Coverage and concentration diagnostics are conservative valid-day bounds,
    not the diagnostics of any individual daily row. ``daily_metrics`` and
    ``daily_values`` preserve the complete auditable range behind the headline.
    """

    market_id: str
    week_start: date
    metric: str
    common_currency: str
    cohort_effective_date: date
    methodology_version: str
    value: Decimal | None
    minimum: Decimal | None
    maximum: Decimal | None
    status: str
    reason: str | None
    valid_observation_count: int
    observation_count: int
    valuation_dates: tuple[date, ...]
    valid_valuation_dates: tuple[date, ...]
    daily_values: tuple[tuple[date, Decimal], ...]
    daily_metrics: tuple[DailyCountryMetric, ...]
    warning_codes: tuple[str, ...]
    diagnostic_policy: str
    constituent_count: int
    constituent_target_count: int
    priced_constituent_count: int
    formation_market_coverage: Decimal
    market_coverage: Decimal | None
    eligible_security_ids: tuple[str, ...]
    eligible_weight: Decimal | None
    whole_cohort_coverage: WeeklyCoverageDiagnostics | None
    eligible_scope_coverage: WeeklyCoverageDiagnostics | None
    largest_constituent_weight: Decimal | None
    top_five_weight: Decimal | None
    top_ten_weight: Decimal | None
    effective_constituent_count: Decimal | None

    @property
    def weekly_minimum(self) -> Decimal | None:
        return self.minimum

    @property
    def weekly_maximum(self) -> Decimal | None:
        return self.maximum

    @property
    def actual_constituent_count(self) -> int:
        return self.constituent_count


def summarize_week(daily_metrics: Iterable[DailyCountryMetric]) -> WeeklyCountryMetric:
    """Summarize up to five Monday--Friday daily country aggregates.

    Three valid values are the minimum publishable set.  A four-day holiday
    week is valid and marked as such.  Input order is intentionally ignored;
    chronological order is restored before all decisions.
    """
    rows = tuple(daily_metrics)
    if not rows:
        raise ValueError("daily_metrics must not be empty")
    if not all(isinstance(row, DailyCountryMetric) for row in rows):
        raise TypeError("daily_metrics must contain DailyCountryMetric values")
    ordered = tuple(sorted(rows, key=lambda row: row.valuation_date))
    dates = tuple(row.valuation_date for row in ordered)
    if len(dates) != len(set(dates)):
        raise ValueError("daily valuation dates must be unique")
    if any(row.valuation_date.weekday() > 4 for row in ordered):
        raise ValueError("daily valuation dates must be Monday through Friday")
    week_start = dates[0] - timedelta(days=dates[0].weekday())
    if any(day < week_start or day > week_start + timedelta(days=4) for day in dates):
        raise ValueError("daily valuation dates must belong to one Monday through Friday week")
    if len(ordered) > 5:
        raise ValueError("a weekly summary permits at most five daily observations")
    _same_context(ordered)

    valid_rows = tuple(row for row in ordered if _valid_value(row))
    values = tuple(row.value for row in valid_rows)
    assert all(value is not None for value in values)
    valid_values = tuple(value for value in values if value is not None)
    median = _median(valid_values) if valid_values else None
    first = ordered[0]
    warnings = set()
    if len(ordered) < 5 or len(valid_rows) != len(ordered):
        warnings.add("holiday_or_missing_trading_day")
    for row in ordered:
        if row.reason and (row.status == "warning" or not _valid_value(row)):
            warnings.add(row.reason)
    warning_codes = tuple(sorted(warnings))
    unavailable = len(valid_rows) < 3
    status = "unavailable" if unavailable else "warning" if warning_codes else "complete"
    return WeeklyCountryMetric(
        market_id=first.market_id, week_start=week_start, metric=first.metric,
        common_currency=first.common_currency, cohort_effective_date=first.cohort_effective_date,
        methodology_version=first.methodology_version, value=None if unavailable else median,
        minimum=None if not valid_values else min(valid_values), maximum=None if not valid_values else max(valid_values),
        status=status, reason="fewer_than_three_valid_daily_observations" if unavailable else None,
        valid_observation_count=len(valid_rows), observation_count=len(ordered), valuation_dates=dates,
        valid_valuation_dates=tuple(row.valuation_date for row in valid_rows),
        daily_values=tuple((row.valuation_date, row.value) for row in valid_rows if row.value is not None),
        daily_metrics=ordered, warning_codes=warning_codes, diagnostic_policy="conservative_valid_day_bounds_v1",
        constituent_count=min(row.constituent_count for row in valid_rows) if valid_rows else min(row.constituent_count for row in ordered),
        constituent_target_count=first.constituent_target_count,
        priced_constituent_count=min(row.priced_constituent_count for row in valid_rows) if valid_rows else min(row.priced_constituent_count for row in ordered),
        formation_market_coverage=min(row.formation_market_coverage for row in valid_rows) if valid_rows else min(row.formation_market_coverage for row in ordered),
        market_coverage=_minimum_optional(valid_rows, "market_coverage"),
        eligible_security_ids=tuple(security for security in first.eligible_security_ids if all(security in row.eligible_security_ids for row in valid_rows)),
        eligible_weight=_minimum_optional(valid_rows, "eligible_weight"),
        whole_cohort_coverage=_coverage_bounds(valid_rows, "whole_cohort_coverage"),
        eligible_scope_coverage=_coverage_bounds(valid_rows, "eligible_scope_coverage"),
        largest_constituent_weight=_maximum_optional(valid_rows, "largest_constituent_weight"),
        top_five_weight=_maximum_optional(valid_rows, "top_five_weight"), top_ten_weight=_maximum_optional(valid_rows, "top_ten_weight"),
        effective_constituent_count=_minimum_optional(valid_rows, "effective_constituent_count"),
    )


def _valid_value(row: DailyCountryMetric) -> bool:
    return row.status in ("complete", "warning") and row.value is not None and row.value.is_finite()


def _minimum_optional(rows: tuple[DailyCountryMetric, ...], field: str) -> Decimal | None:
    values = tuple(getattr(row, field) for row in rows)
    return None if not values or any(value is None for value in values) else min(values)


def _maximum_optional(rows: tuple[DailyCountryMetric, ...], field: str) -> Decimal | None:
    values = tuple(getattr(row, field) for row in rows)
    return None if not values or any(value is None for value in values) else max(values)


def _coverage_bounds(rows: tuple[DailyCountryMetric, ...], field: str) -> WeeklyCoverageDiagnostics | None:
    coverage = tuple(getattr(row, field) for row in rows)
    if not coverage or any(value is None for value in coverage):
        return None
    values = tuple(value for value in coverage if value is not None)
    source = tuple(_decimal(Fraction(value.reported) + Fraction(value.carried_forward)) for value in values)
    return WeeklyCoverageDiagnostics(
        reported_min=min(value.reported for value in values),
        carried_forward_min=min(value.carried_forward for value in values),
        imputed_max=max(value.imputed for value in values),
        missing_or_invalid_max=max(value.missing_or_invalid for value in values),
        ineligible_max=max(value.ineligible for value in values),
        source_coverage_min=min(source),
    )


def _same_context(rows: tuple[DailyCountryMetric, ...]) -> None:
    first = rows[0]
    fields = (
        ("market", "market_id"), ("metric", "metric"), ("cohort", "cohort_effective_date"),
        ("methodology", "methodology_version"), ("currency", "common_currency"),
        ("cohort membership", "security_ids"),
        ("constituent target count", "constituent_target_count"),
    )
    for label, field in fields:
        if any(getattr(row, field) != getattr(first, field) for row in rows[1:]):
            raise ValueError(f"daily metrics must use the same {label}")

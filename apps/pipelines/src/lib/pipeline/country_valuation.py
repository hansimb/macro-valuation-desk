"""Pure daily country valuations over a fixed cohort.

Callers supply the day's split-consistent outstanding share state alongside raw
close prices (never dividend/split-adjusted prices times unadjusted shares).
Eligibility metadata belongs to that security state, independently of whether
its fundamentals were retrieved. Classification and carry/imputation decisions
are explicit inputs, not guesses based on the availability of convenient facts.

All monetary arithmetic uses exact rational representations of validated Decimal
inputs; final Decimal rendering uses a fresh context. Dividend yield is a ratio,
not a percentage. FX rates mean quote units per one base unit, for this day only.

Incomplete fundamentals retain the fixed capitalization and coverage denominator.
``observed_*`` are diagnostics for the reported/carried subset, never publishable
country values. Task 8 supplies imputed inputs before a final point estimate is available.
Current whole-market coverage requires a complete eligible-universe denominator,
which this interface does not supply; formation coverage is explicitly separate.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from decimal import Context, Decimal, localcontext
from fractions import Fraction
import re
from types import MappingProxyType

from src.lib.pipeline.country_cohorts import CountryCohort
from src.lib.pipeline.point_in_time import FundamentalValue, PointInTimeFundamentals
from src.lib.source.country_index_types import DailyPrice, FxRate


_FIELDS = ("net_income", "common_equity", "revenue", "operating_cash_flow", "capex", "dividends")
_METRICS = {
    "pe": ("net_income",), "pb": ("common_equity",), "ps": ("revenue",),
    "pcf": ("operating_cash_flow",), "pfcf": ("operating_cash_flow", "capex"),
    "dividend_yield": ("dividends",),
}
_STATES = ("reported", "carried_forward", "imputed", "missing", "invalid")


def _decimal(value: Fraction) -> Decimal:
    precision = max(50, len(str(abs(value.numerator))) + len(str(value.denominator)) + 10)
    with localcontext(Context(prec=precision)):
        return Decimal(value.numerator) / Decimal(value.denominator)


def _require_decimal(name: str, value: Decimal, *, positive: bool = False) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or (positive and value <= 0):
        qualifier = "positive " if positive else ""
        raise ValueError(f"{name} must be a finite {qualifier}Decimal")


def _require_string(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_currency(value: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[A-Z]{3}", value) is None:
        raise ValueError("currency must be an uppercase three-letter code")


@dataclass(frozen=True)
class ValuationPrice:
    """Audited day-specific share state and metric classification for a security.

    ``industry`` is one of bank/insurer/other/unknown. ``other`` explicitly
    certifies comparable cash-flow presentation; unknown fails closed for cash
    multiples. Revenue requires its own comparability certification in every
    industry. The share count must match the raw close's share basis on the day.
    """

    price: DailyPrice
    shares_outstanding: Decimal
    industry: str = "unknown"
    revenue_comparable: bool = False

    def __post_init__(self) -> None:
        _require_decimal("shares_outstanding", self.shares_outstanding, positive=True)
        _require_decimal("close_price", self.price.close_price, positive=True)
        _require_string("security_id", self.price.security_id)
        _require_currency(self.price.trading_currency)
        if not isinstance(self.price.trading_date, date) or isinstance(self.price.trading_date, datetime):
            raise ValueError("trading_date must be a calendar date")
        if self.industry not in ("bank", "insurer", "other", "unknown"):
            raise ValueError("industry must be bank, insurer, other, or unknown")
        if not isinstance(self.revenue_comparable, bool):
            raise ValueError("revenue_comparable must be boolean")


def _snapshot(value: FundamentalValue) -> FundamentalValue:
    if value.value is not None:
        _require_decimal("fundamental value", value.value)
    return replace(value, lineage=replace(value.lineage, facts=tuple(value.lineage.facts)),
                   quarters=tuple(_snapshot(quarter) for quarter in value.quarters),
                   warnings=tuple(value.warnings))


@dataclass(frozen=True)
class CompanyFundamentals:
    """Task 5 values plus caller-certified per-field provenance status.

    Absent overrides mean reported. Derived TTM/discrete-quarter arithmetic from
    source filings is still reported source coverage. A carried value must have
    passed the caller's staleness policy; imputed values are never source coverage.
    FCF's status is the worst status of its operating-cash-flow and capex inputs.
    """

    fundamentals: PointInTimeFundamentals
    statuses: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_string("security_id", self.fundamentals.security_id)
        cutoff = self.fundamentals.valuation_at
        if not isinstance(cutoff, datetime) or cutoff.tzinfo is None or cutoff.utcoffset() is None:
            raise ValueError("fundamentals valuation_at must be timezone-aware")
        statuses = dict(self.statuses)
        if any(name not in _FIELDS for name in statuses):
            raise ValueError("status field must be a canonical valuation field")
        if any(status not in _STATES for status in statuses.values()):
            raise ValueError("unknown fundamental status")
        values = {name: _snapshot(getattr(self.fundamentals, name))
                  for name in (*_FIELDS, "free_cash_flow", "weighted_average_shares", "period_end_shares")}
        object.__setattr__(self, "fundamentals", replace(
            self.fundamentals, **values, candidates=tuple(self.fundamentals.candidates),
            rejections=tuple(self.fundamentals.rejections)))
        object.__setattr__(self, "statuses", MappingProxyType(statuses))


@dataclass(frozen=True)
class ValuationFx:
    common_currency: str
    rates: tuple[FxRate, ...] = ()

    def __post_init__(self) -> None:
        _require_currency(self.common_currency)
        rates = tuple(self.rates)
        pairs = set()
        for rate in rates:
            _require_decimal("FX rate", rate.rate, positive=True)
            _require_currency(rate.base_currency)
            _require_currency(rate.quote_currency)
            if rate.quote_currency != self.common_currency:
                raise ValueError("FX quote_currency must equal common_currency")
            if rate.base_currency in pairs:
                raise ValueError("FX base currencies must be unique")
            if rate.base_currency == self.common_currency and rate.rate != 1:
                raise ValueError("same-currency FX rate must equal one")
            pairs.add(rate.base_currency)
        object.__setattr__(self, "rates", rates)


@dataclass(frozen=True)
class CoverageWeights:
    """Disjoint weights; whole-cohort includes ineligible weight, eligible scope does not."""

    reported: Decimal
    carried_forward: Decimal
    imputed: Decimal
    missing_or_invalid: Decimal
    ineligible: Decimal = Decimal(0)

    def __post_init__(self) -> None:
        for name in ("reported", "carried_forward", "imputed", "missing_or_invalid", "ineligible"):
            value = getattr(self, name)
            _require_decimal(name, value)
            if not 0 <= value <= 1:
                raise ValueError("coverage weights must be between zero and one")

    @property
    def source_coverage(self) -> Decimal:
        return _decimal(Fraction(self.reported) + Fraction(self.carried_forward))


@dataclass(frozen=True)
class DailyCountryMetric:
    market_id: str
    valuation_date: date
    cohort_effective_date: date
    methodology_version: str
    metric: str
    common_currency: str
    security_ids: tuple[str, ...]
    constituent_count: int
    constituent_target_count: int
    priced_constituent_count: int
    formation_market_coverage: Decimal
    # Task 6 / orchestration can attach independently evaluated current coverage.
    market_coverage: Decimal | None = None
    eligible_security_ids: tuple[str, ...] = ()
    eligible_weight: Decimal | None = None
    aggregate_market_cap: Decimal | None = None
    aggregate_numerator: Decimal | None = None
    aggregate_denominator: Decimal | None = None
    observed_numerator: Decimal | None = None
    observed_denominator: Decimal | None = None
    observed_value: Decimal | None = None
    value: Decimal | None = None
    status: str = "unavailable"
    reason: str | None = None
    whole_cohort_coverage: CoverageWeights | None = None
    eligible_scope_coverage: CoverageWeights | None = None
    constituent_weights: tuple[tuple[str, Decimal], ...] = ()
    largest_constituent_weight: Decimal | None = None
    top_five_weight: Decimal | None = None
    top_ten_weight: Decimal | None = None
    effective_constituent_count: Decimal | None = None

    def __post_init__(self) -> None:
        _require_string("methodology_version", self.methodology_version)
        for name in ("formation_market_coverage", "market_coverage", "eligible_weight", "aggregate_market_cap",
                     "aggregate_numerator", "aggregate_denominator", "observed_numerator", "observed_denominator",
                     "observed_value", "value", "largest_constituent_weight", "top_five_weight", "top_ten_weight",
                     "effective_constituent_count"):
            value = getattr(self, name)
            if value is not None:
                _require_decimal(name, value)
        object.__setattr__(self, "security_ids", tuple(self.security_ids))
        object.__setattr__(self, "eligible_security_ids", tuple(self.eligible_security_ids))
        weights = tuple((security, weight) for security, weight in self.constituent_weights)
        for _, weight in weights:
            _require_decimal("constituent weight", weight)
        object.__setattr__(self, "constituent_weights", weights)


def _eligible(metric: str, price: ValuationPrice) -> bool:
    if metric in ("pcf", "pfcf"):
        return price.industry == "other"
    if metric == "ps":
        return price.revenue_comparable
    return True


def _amount(
    company: CompanyFundamentals | None, metric: str, rates: Mapping[str, Fraction],
) -> tuple[Fraction | None, str]:
    if company is None:
        return None, "missing_or_invalid"
    if metric == "pfcf":
        cash_flow = company.fundamentals.operating_cash_flow
        capex = company.fundamentals.capex
        if (cash_flow.period_start is None or cash_flow.period_end is None
                or (cash_flow.period_start, cash_flow.period_end) != (capex.period_start, capex.period_end)):
            return None, "missing_or_invalid"
    amounts = []
    statuses = []
    for name in _METRICS[metric]:
        value = getattr(company.fundamentals, name)
        state = company.statuses.get(name, "reported")
        if value.value is None or state in ("missing", "invalid") or value.unit not in rates:
            return None, "missing_or_invalid"
        if name in ("capex", "dividends") and value.value < 0:
            return None, "missing_or_invalid"
        if any(publication > company.fundamentals.valuation_at for publication in value.lineage.publication_times):
            return None, "missing_or_invalid"
        amounts.append(Fraction(value.value) * rates[value.unit])
        statuses.append(state)
    state = "imputed" if "imputed" in statuses else "carried_forward" if "carried_forward" in statuses else "reported"
    return (amounts[0] - amounts[1] if metric == "pfcf" else amounts[0]), state


def _coverage(amounts: Mapping[str, Fraction], denominator: Fraction) -> CoverageWeights:
    return CoverageWeights(**{name: _decimal(value / denominator) for name, value in amounts.items()})


def calculate_daily_country_metrics(
    cohort: CountryCohort,
    prices: Iterable[ValuationPrice],
    fundamentals: Iterable[CompanyFundamentals],
    fx: ValuationFx,
    methodology_version: str,
) -> list[DailyCountryMetric]:
    """Calculate six metrics without I/O, company-multiple averaging, or imputation.

    At least one price supplies the trading date. Missing constituent prices/FX
    make all cap-based weights unknown instead of renormalizing the survivors.
    Missing metric facts affect only that metric. All PIT objects must represent
    the same cutoff on the valuation date. Extra non-cohort rows are ignored;
    they are not assumed to constitute a complete local-market universe.
    """
    _require_string("methodology_version", methodology_version)
    price_rows = tuple(prices)
    companies = tuple(fundamentals)
    if not price_rows:
        raise ValueError("at least one price is needed to identify the valuation date")
    price_map = {row.price.security_id: row for row in price_rows}
    company_map = {row.fundamentals.security_id: row for row in companies}
    if len(price_map) != len(price_rows) or len(company_map) != len(companies):
        raise ValueError("price and fundamental security_ids must each be unique")
    days = {row.price.trading_date for row in price_rows}
    if len(days) != 1:
        raise ValueError("prices must have the same valuation date")
    valuation_date = next(iter(days))
    if valuation_date < cohort.effective_date:
        raise ValueError("valuation date precedes cohort effective date")
    cutoffs = {row.fundamentals.valuation_at for row in companies}
    if any(cutoff.date() != valuation_date for cutoff in cutoffs):
        raise ValueError("fundamentals must be selected for the valuation date")
    if len(cutoffs) > 1:
        raise ValueError("fundamentals must use the same valuation cutoff")
    if any(rate.rate_date != valuation_date for rate in fx.rates):
        raise ValueError("FX rates must match the valuation date")
    rates = {rate.base_currency: Fraction(rate.rate) for rate in fx.rates}
    rates[fx.common_currency] = Fraction(1)
    ids = tuple(cohort.security_ids)
    caps = {
        security: Fraction(price_map[security].price.close_price) * Fraction(price_map[security].shares_outstanding)
        * rates[price_map[security].price.trading_currency]
        for security in ids if security in price_map and price_map[security].price.trading_currency in rates
    }
    common = dict(
        market_id=cohort.market_id, valuation_date=valuation_date, cohort_effective_date=cohort.effective_date,
        methodology_version=methodology_version, common_currency=fx.common_currency, security_ids=ids,
        constituent_count=len(ids), constituent_target_count=cohort.constituent_target_count,
        priced_constituent_count=len(caps), formation_market_coverage=cohort.achieved_market_coverage,
    )
    if len(caps) != len(ids):
        return [DailyCountryMetric(**common, metric=metric, reason="missing_constituent_market_cap")
                for metric in _METRICS]

    total_cap = sum(caps.values(), Fraction())
    ranked = sorted(caps.values(), reverse=True)
    common.update(
        aggregate_market_cap=_decimal(total_cap),
        constituent_weights=tuple((security, _decimal(caps[security] / total_cap)) for security in ids),
        largest_constituent_weight=_decimal(ranked[0] / total_cap),
        top_five_weight=_decimal(sum(ranked[:5], Fraction()) / total_cap),
        top_ten_weight=_decimal(sum(ranked[:10], Fraction()) / total_cap),
        effective_constituent_count=_decimal(total_cap * total_cap / sum((cap * cap for cap in caps.values()), Fraction())),
    )
    results = []
    for metric in _METRICS:
        eligible = tuple(security for security in ids if _eligible(metric, price_map[security]))
        eligible_cap = sum((caps[security] for security in eligible), Fraction())
        buckets = dict.fromkeys(("reported", "carried_forward", "imputed", "missing_or_invalid", "ineligible"), Fraction())
        buckets["ineligible"] = total_cap - eligible_cap
        observed_cap = Fraction()
        observed_fact = Fraction()
        aggregate_fact = Fraction()
        for security in eligible:
            amount, state = _amount(company_map.get(security), metric, rates)
            buckets[state] += caps[security]
            if amount is not None:
                aggregate_fact += amount
                if state != "imputed":
                    observed_cap += caps[security]
                    observed_fact += amount

        is_yield = metric == "dividend_yield"
        observed_num, observed_den = (observed_fact, observed_cap) if is_yield else (observed_cap, observed_fact)
        missing = bool(buckets["missing_or_invalid"])
        numerator = (None if missing else _decimal(aggregate_fact)) if is_yield else _decimal(eligible_cap)
        denominator = _decimal(eligible_cap) if is_yield else (None if missing else _decimal(aggregate_fact))
        status, reason, value = "unavailable", None, None
        if not eligible:
            reason = "no_eligible_constituents"
        elif missing:
            reason = "awaiting_imputation"
        elif denominator <= 0:
            reason = "non_positive_denominator"
        else:
            value = _decimal(aggregate_fact / eligible_cap if is_yield else eligible_cap / aggregate_fact)
            status = "warning" if buckets["imputed"] else "complete"
            reason = "partly_estimated" if buckets["imputed"] else None
        results.append(DailyCountryMetric(
            **common, metric=metric, eligible_security_ids=eligible, eligible_weight=_decimal(eligible_cap / total_cap),
            aggregate_numerator=numerator, aggregate_denominator=denominator,
            observed_numerator=_decimal(observed_num), observed_denominator=_decimal(observed_den),
            observed_value=_decimal(observed_num / observed_den) if observed_cap and observed_den > 0 else None,
            value=value, status=status, reason=reason,
            whole_cohort_coverage=_coverage(buckets, total_cap),
            eligible_scope_coverage=_coverage({**buckets, "ineligible": Fraction()}, eligible_cap) if eligible_cap else None,
        ))
    return results

"""Pure publication-aware SEC fundamentals with exact monetary arithmetic.

Selection policy: consolidated context, specific concept, then latest visible
publication. Equal-rank disagreements are missing, never resolved by input order.
TTM uses four contiguous fiscal quarters or a reported 52/53-week annual period.
Calendar frames and filing ``fy`` labels are deliberately not used as periods.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Context, Decimal, localcontext
from fractions import Fraction

from src.lib.pipeline.canonical_facts import CanonicalFact, INSTANT_METRICS


@dataclass(frozen=True)
class FactLineage:
    facts: tuple[CanonicalFact, ...] = ()
    formula: str = "missing"

    @property
    def publication_times(self) -> tuple[datetime, ...]:
        return tuple(sorted({_available_at(fact) for fact in self.facts}))


@dataclass(frozen=True)
class FundamentalValue:
    value: Decimal | None = None
    unit: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    lineage: FactLineage = FactLineage()
    quarters: tuple[FundamentalValue, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class FactRejection:
    fact: CanonicalFact
    reason: str


@dataclass(frozen=True)
class PointInTimeFundamentals:
    security_id: str
    valuation_at: datetime
    revenue: FundamentalValue
    net_income: FundamentalValue
    common_equity: FundamentalValue
    operating_cash_flow: FundamentalValue
    capex: FundamentalValue
    free_cash_flow: FundamentalValue
    dividends: FundamentalValue
    weighted_average_shares: FundamentalValue
    period_end_shares: FundamentalValue
    candidates: tuple[CanonicalFact, ...] = ()
    rejections: tuple[FactRejection, ...] = ()

    @property
    def ttm_revenue(self) -> Decimal | None:
        return self.revenue.value

    @property
    def ttm_net_income(self) -> Decimal | None:
        return self.net_income.value

    @property
    def ttm_operating_cash_flow(self) -> Decimal | None:
        return self.operating_cash_flow.value

    @property
    def ttm_capex(self) -> Decimal | None:
        return self.capex.value

    @property
    def ttm_free_cash_flow(self) -> Decimal | None:
        return self.free_cash_flow.value

    @property
    def ttm_dividends(self) -> Decimal | None:
        return self.dividends.value


@dataclass(frozen=True)
class _Observation:
    amount: Fraction
    unit: str
    start: date | None
    end: date
    facts: tuple[CanonicalFact, ...]
    formula: str = "reported"
    warnings: tuple[str, ...] = ()

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1 if self.start is not None else 0


def _available_at(fact: CanonicalFact) -> datetime:
    # Raw published_at already incorporates SEC acceptance/date-only semantics.
    # A separately supplied amendment timestamp is an additional lower bound.
    return max(fact.raw.published_at, fact.raw.amended_at or fact.raw.published_at)


def _key(fact: CanonicalFact) -> tuple[str, ...]:
    raw = fact.raw
    return (raw.filing_provider, raw.filing_id, raw.filing_content_hash, raw.fact_id,
            raw.value_text, raw.unit or "", raw.published_at.isoformat(),
            fact.taxonomy_version)


def _scope(fact: CanonicalFact) -> int:
    return {True: 0, None: 1, False: 2}[fact.raw.is_consolidated]


def _sources(facts: Iterable[CanonicalFact]) -> tuple[CanonicalFact, ...]:
    return tuple(sorted({_key(fact): fact for fact in facts}.values(), key=_key))


def _decimal(value: Fraction) -> Decimal:
    # Fraction keeps derivations and share-day arithmetic exact. A fresh context
    # makes output independent of a caller's rounding mode/precision/traps.
    precision = max(50, len(str(abs(value.numerator))) + len(str(value.denominator)) + 10)
    with localcontext(Context(prec=precision)):
        return Decimal(value.numerator) / Decimal(value.denominator)


def _value(observation: _Observation, quarters: tuple[FundamentalValue, ...] = ()) -> FundamentalValue:
    return FundamentalValue(
        value=_decimal(observation.amount), unit=observation.unit,
        period_start=observation.start, period_end=observation.end,
        lineage=FactLineage(observation.facts, observation.formula), quarters=quarters,
        warnings=tuple(sorted({*observation.warnings,
                               *(warning for fact in observation.facts for warning in fact.warnings)})),
    )


def _select_periods(
    facts: list[CanonicalFact], rejected: dict[tuple[str, ...], str],
) -> list[_Observation]:
    groups: dict[tuple, list[CanonicalFact]] = defaultdict(list)
    for fact in facts:
        raw = fact.raw
        groups[(raw.period_start, raw.period_end, raw.instant_date)].append(fact)
    selected = []
    for group in groups.values():
        scope = min(_scope(fact) for fact in group)
        scoped = [fact for fact in group if _scope(fact) == scope]
        priority = min(fact.mapping_priority for fact in scoped)
        specific = [fact for fact in scoped if fact.mapping_priority == priority]
        latest = max(_available_at(fact) for fact in specific)
        best = [fact for fact in specific if _available_at(fact) == latest]
        conflict = len({(fact.value, fact.unit, fact.raw.entity_id) for fact in best}) > 1
        winner = None if conflict else min(best, key=_key)
        for fact in group:
            if fact is winner:
                continue
            if conflict and fact in best:
                reason = "conflicting_facts"
            elif _scope(fact) != scope:
                reason = "less_preferred_context"
            elif fact.mapping_priority != priority:
                reason = "less_preferred_concept"
            elif _available_at(fact) != latest:
                reason = "superseded_publication"
            else:
                reason = "duplicate_equivalent_fact"
            rejected[_key(fact)] = reason
        if winner is not None:
            raw = winner.raw
            selected.append(_Observation(
                Fraction(winner.value), winner.unit, raw.period_start,
                raw.instant_date or raw.period_end, (winner,),
            ))
    return selected


def _derivation_compatible(left: _Observation, right: _Observation) -> bool:
    a, b = left.facts[0], right.facts[0]
    return (left.unit == right.unit and left.start == right.start
            and a.raw.taxonomy == b.raw.taxonomy and a.raw.concept_name == b.raw.concept_name
            and a.raw.entity_id == b.raw.entity_id and _scope(a) == _scope(b))


def _quarter_candidates(observations: list[_Observation], *, shares: bool) -> list[_Observation]:
    quarters = [observation for observation in observations if 70 <= observation.days <= 110]
    for cumulative in observations:
        if not 150 <= cumulative.days <= 380:
            continue
        for prefix in observations:
            days = (cumulative.end - prefix.end).days
            if not 70 <= days <= 110 or not _derivation_compatible(cumulative, prefix):
                continue
            if shares:
                amount = (cumulative.amount * cumulative.days - prefix.amount * prefix.days) / days
                formula = "(cumulative_share_days - prefix_share_days) / quarter_days"
            else:
                amount = cumulative.amount - prefix.amount
                formula = "cumulative - prefix"
            if shares and amount <= 0:
                continue
            quarters.append(_Observation(
                amount, cumulative.unit, prefix.end + timedelta(days=1), cumulative.end,
                _sources((*cumulative.facts, *prefix.facts)), formula,
            ))
    return quarters


def _quarter_rank(observation: _Observation) -> tuple:
    # Prefer a direct quarter at the same publication, but a visible later
    # restatement can replace a quarter derived or reported in an older filing.
    return (max(_scope(fact) for fact in observation.facts),
            -max(_available_at(fact).timestamp() for fact in observation.facts),
            observation.formula != "reported",
            max(fact.mapping_priority for fact in observation.facts))


def _ttm(observations: list[_Observation], target: date, *, shares: bool) -> FundamentalValue:
    groups: dict[tuple, list[_Observation]] = defaultdict(list)
    for quarter in _quarter_candidates(observations, shares=shares):
        groups[(quarter.start, quarter.end, quarter.unit)].append(quarter)
    selected = []
    for group in groups.values():
        best_rank = min(_quarter_rank(quarter) for quarter in group)
        best = [quarter for quarter in group if _quarter_rank(quarter) == best_rank]
        if len({quarter.amount for quarter in best}) == 1:
            winner = min(best, key=lambda q: tuple(_key(f) for f in q.facts))
            if len({quarter.amount for quarter in group}) > 1:
                winner = replace(winner, warnings=("reported_derived_disagreement",))
            selected.append(winner)
    by_end: dict[date, list[_Observation]] = defaultdict(list)
    for quarter in selected:
        by_end[quarter.end].append(quarter)

    chains: list[tuple[_Observation, ...]] = []

    def extend(end: date, tail: tuple[_Observation, ...]) -> None:
        if len(tail) == 4:
            if 350 <= (tail[-1].end - tail[0].start).days + 1 <= 380:
                chains.append(tail)
            return
        for quarter in by_end[end]:
            if tail and quarter.unit != tail[0].unit:
                continue
            if tail and {(fact.raw.entity_id, _scope(fact)) for fact in quarter.facts} != {
                (fact.raw.entity_id, _scope(fact)) for fact in tail[0].facts
            }:
                continue
            extend(quarter.start - timedelta(days=1), (quarter, *tail))

    extend(target, ())
    if chains:
        # Multiple equally plausible fiscal boundaries/currencies stay missing.
        signatures = {(chain[0].start, chain[-1].end, chain[0].unit,
                       tuple(quarter.amount for quarter in chain)) for chain in chains}
        if len(signatures) > 1:
            return FundamentalValue(period_end=target, warnings=("ambiguous_ttm",))
        chain = min(chains, key=lambda c: tuple(tuple(_key(f) for f in q.facts) for q in c))
        if shares:
            amount = sum((quarter.amount * quarter.days for quarter in chain), Fraction()) / sum(q.days for q in chain)
            formula = "sum(quarter_share_days) / ttm_days"
        else:
            amount = sum((quarter.amount for quarter in chain), Fraction())
            formula = "sum(four_contiguous_quarters)"
        observation = _Observation(amount, chain[0].unit, chain[0].start, target,
                                   _sources(f for q in chain for f in q.facts), formula,
                                   tuple(sorted({warning for q in chain for warning in q.warnings})))
        return _value(observation, tuple(_value(quarter) for quarter in chain))
    annuals = [observation for observation in observations if observation.end == target and 350 <= observation.days <= 380]
    if len(annuals) == 1:
        return _value(annuals[0])
    return FundamentalValue(period_end=target, warnings=("incomplete_ttm",))


def _free_cash_flow(operating: FundamentalValue, capex: FundamentalValue) -> FundamentalValue:
    if operating.value is None or capex.value is None:
        return FundamentalValue(warnings=("missing_cash_flow_component",))
    if (operating.period_start, operating.period_end, operating.unit) != (capex.period_start, capex.period_end, capex.unit):
        return FundamentalValue(warnings=("incompatible_cash_flow_period_or_unit",))
    if {(fact.raw.entity_id, _scope(fact)) for fact in operating.lineage.facts} != {
        (fact.raw.entity_id, _scope(fact)) for fact in capex.lineage.facts
    }:
        return FundamentalValue(warnings=("incompatible_cash_flow_scope",))
    return _value(_Observation(
        Fraction(operating.value) - Fraction(capex.value), operating.unit,
        operating.period_start, operating.period_end,
        _sources((*operating.lineage.facts, *capex.lineage.facts)),
        "ttm_operating_cash_flow - ttm_capex",
    ))


def fundamentals_as_of(
    security_id: str, valuation_at: datetime, facts: Iterable[CanonicalFact],
) -> PointInTimeFundamentals:
    """Select only published, explicitly security-bound facts and retain all rejects.

    Missing components remain None (including absent dividends). Different TTM
    windows/currencies cannot yield FCF. No wall clock, I/O or input mutation.
    """
    if valuation_at.tzinfo is None or valuation_at.utcoffset() is None:
        raise ValueError("valuation_at must be timezone-aware")
    cutoff_date = valuation_at.astimezone(timezone.utc).date()
    candidates = tuple(sorted(facts, key=_key))
    rejected: dict[tuple[str, ...], str] = {}
    eligible: dict[str, list[CanonicalFact]] = defaultdict(list)
    for fact in candidates:
        raw = fact.raw
        if raw.security_id != security_id:
            reason = "security_mismatch"
        elif _available_at(fact) > valuation_at:
            reason = "not_yet_published"
        elif fact.rejection_reasons:
            reason = fact.rejection_reasons[0]
        elif (raw.instant_date or raw.period_end) > cutoff_date:
            reason = "future_period"
        else:
            eligible[fact.metric].append(fact)
            continue
        rejected[_key(fact)] = reason
    versions = {fact.taxonomy_version for metric_facts in eligible.values() for fact in metric_facts}
    if len(versions) > 1:
        raise ValueError("Cannot mix taxonomy versions in one valuation")
    metrics = {}
    for metric in ("revenue", "net_income", "common_equity", "operating_cash_flow", "capex",
                   "dividends", "weighted_average_shares", "period_end_shares"):
        metric_facts = eligible[metric]
        if not metric_facts:
            metrics[metric] = FundamentalValue(warnings=("missing_facts",))
            continue
        target = max(fact.raw.instant_date or fact.raw.period_end for fact in metric_facts)
        observations = _select_periods(metric_facts, rejected)
        if metric in INSTANT_METRICS:
            latest = [observation for observation in observations if observation.end == target]
            metrics[metric] = _value(latest[0]) if latest else FundamentalValue(period_end=target, warnings=("conflicting_facts",))
        else:
            metrics[metric] = _ttm(observations, target, shares=metric == "weighted_average_shares")
    metrics["free_cash_flow"] = _free_cash_flow(metrics["operating_cash_flow"], metrics["capex"])
    used = {_key(fact) for metric in metrics.values() for fact in metric.lineage.facts}
    for fact in candidates:
        if _key(fact) not in used:
            rejected.setdefault(_key(fact), "not_used_in_selected_period")
    return PointInTimeFundamentals(
        security_id=security_id, valuation_at=valuation_at, **metrics, candidates=candidates,
        rejections=tuple(FactRejection(fact, rejected[_key(fact)]) for fact in candidates if _key(fact) in rejected),
    )

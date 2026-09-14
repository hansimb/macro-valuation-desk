"""Versioned, lossless SEC concept normalization (no filing selection or I/O).

``sec-v1`` is the mapping policy version, not the source taxonomy's release year.
Only explicitly listed concepts are mapped; per-share dividends, aggregate profit
including noncontrolling interests, leases and noncash capex are not substitutes.
Raw facts, including invalid and competing candidates, remain inspectable.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from types import MappingProxyType

from src.lib.source.country_index_types import RawXbrlFact


DEFAULT_TAXONOMY_VERSION = "sec-v1"
INSTANT_METRICS = frozenset({"common_equity", "period_end_shares"})
SHARE_METRICS = frozenset({"weighted_average_shares", "period_end_shares"})


@dataclass(frozen=True)
class ConceptMapping:
    metric: str
    priority: int = 0
    warnings: tuple[str, ...] = ()


# Broad parent-owner totals are identified explicitly so consumers can enforce
# stricter common-only coverage. They never outrank a common-specific concept.
_MAPPINGS = MappingProxyType({
    ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"): ConceptMapping("revenue"),
    ("us-gaap", "Revenues"): ConceptMapping("revenue", 1),
    ("us-gaap", "SalesRevenueNet"): ConceptMapping("revenue", 2),
    ("us-gaap", "NetIncomeLossAvailableToCommonStockholdersBasic"): ConceptMapping("net_income"),
    ("us-gaap", "NetIncomeLoss"): ConceptMapping("net_income", 1, ("preferred_dividends_not_separated",)),
    ("us-gaap", "CommonStockholdersEquity"): ConceptMapping("common_equity"),
    ("us-gaap", "StockholdersEquity"): ConceptMapping("common_equity", 1, ("preferred_equity_not_separated",)),
    ("us-gaap", "NetCashProvidedByUsedInOperatingActivities"): ConceptMapping("operating_cash_flow"),
    ("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"): ConceptMapping("capex"),
    ("us-gaap", "PaymentsOfDividendsCommonStock"): ConceptMapping("dividends"),
    ("us-gaap", "WeightedAverageNumberOfSharesOutstandingBasic"): ConceptMapping("weighted_average_shares"),
    ("us-gaap", "CommonStockSharesOutstanding"): ConceptMapping("period_end_shares"),
    ("dei", "EntityCommonStockSharesOutstanding"): ConceptMapping("period_end_shares", 1),
    ("ifrs-full", "Revenue"): ConceptMapping("revenue"),
    ("ifrs-full", "ProfitLossAttributableToOrdinaryEquityHoldersOfParentEntity"): ConceptMapping("net_income"),
    ("ifrs-full", "ProfitLossAttributableToOwnersOfParent"): ConceptMapping("net_income", 1, ("preferred_dividends_not_separated",)),
    ("ifrs-full", "EquityAttributableToOwnersOfParent"): ConceptMapping("common_equity", 1, ("preferred_equity_not_separated",)),
    ("ifrs-full", "CashFlowsFromUsedInOperatingActivities"): ConceptMapping("operating_cash_flow"),
    ("ifrs-full", "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"): ConceptMapping("capex"),
    ("ifrs-full", "DividendsPaidClassifiedAsFinancingActivities"): ConceptMapping("dividends", 1, ("common_dividend_scope_unverified",)),
    ("ifrs-full", "DividendsPaidClassifiedAsOperatingActivities"): ConceptMapping("dividends", 1, ("common_dividend_scope_unverified",)),
    ("ifrs-full", "WeightedAverageNumberOfOrdinarySharesOutstanding"): ConceptMapping("weighted_average_shares"),
    ("ifrs-full", "NumberOfSharesOutstanding"): ConceptMapping("period_end_shares", 1, ("common_share_scope_unverified",)),
})
_VERSIONS = MappingProxyType({DEFAULT_TAXONOMY_VERSION: _MAPPINGS})
_UNIT = re.compile(r"(?:iso4217:)?([A-Z]{3}|shares)(?: (thousands|millions|billions))?\Z")
_SCALE = {None: 0, "thousands": 3, "millions": 6, "billions": 9}


@dataclass(frozen=True)
class CanonicalFact:
    raw: RawXbrlFact
    taxonomy_version: str
    metric: str | None
    value: Decimal | None
    unit: str | None
    mapping_priority: int
    rejection_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def normalize_facts(
    facts: Iterable[RawXbrlFact], taxonomy_version: str,
) -> list[CanonicalFact]:
    """Normalize units and concepts without discarding, mutating or selecting facts.

    SEC ``val`` is already scaled; ``decimals`` states accuracy, never a multiplier.
    Explicit unit suffixes such as ``USD millions`` alone trigger conversion.
    Monetary units retain their currency: this function does not perform FX.
    """
    if taxonomy_version not in _VERSIONS:
        raise ValueError(f"Unknown taxonomy version: {taxonomy_version!r}")
    mapping = _VERSIONS[taxonomy_version]
    normalized = []
    for raw in facts:
        rule = mapping.get((raw.taxonomy, raw.concept_name))
        reasons: list[str] = []
        warnings = list(rule.warnings if rule else ())
        if rule is None:
            reasons.append("unmapped_concept")
        value = None
        try:
            parsed = Decimal(raw.value_text)
            if not parsed.is_finite():
                raise InvalidOperation
            value = parsed
        except (InvalidOperation, ValueError):
            reasons.append("invalid_numeric_value")
        match = _UNIT.fullmatch(raw.unit or "")
        unit = match[1] if match else None
        if match is None:
            reasons.append("unsupported_unit")
        else:
            if value is not None:
                sign, digits, exponent = value.as_tuple()
                value = Decimal((sign, digits, exponent + _SCALE[match[2]]))
            if rule and (rule.metric in SHARE_METRICS) != (unit == "shares"):
                reasons.append("incompatible_unit")
        if rule:
            if rule.metric in INSTANT_METRICS:
                valid_period = raw.instant_date is not None and raw.period_start is None and raw.period_end is None
            else:
                valid_period = (raw.period_start is not None and raw.period_end is not None
                                and raw.period_start <= raw.period_end and raw.instant_date is None)
            if not valid_period:
                reasons.append("invalid_period")
            if rule.metric in SHARE_METRICS and value is not None and value <= 0:
                reasons.append("nonpositive_shares")
        if any(key != "__mvd_source_metadata__" for key in raw.dimensions):
            reasons.append("dimensional_context")
        if raw.is_continuing_operations is False:
            reasons.append("non_continuing_operations")
        if raw.is_consolidated is False:
            warnings.append("parent_only_context")
        normalized.append(CanonicalFact(
            raw=raw, taxonomy_version=taxonomy_version, metric=rule.metric if rule else None,
            value=value, unit=unit, mapping_priority=rule.priority if rule else 999,
            rejection_reasons=tuple(reasons), warnings=tuple(warnings),
        ))
    return normalized

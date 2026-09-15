"""Restartable orchestration for the US country-index vertical slice.

The task keeps providers at the boundary and delegates selection and valuation
arithmetic to the reusable pipeline modules. Pure stage payloads use versioned,
checksummed JSON checkpoints. All database
writes and publication commit together in a top-level transaction.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import fields, is_dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import inspect
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from src.lib.db.country_indices import (
    PublicationInvariantError,
    publish_completed_run,
    upsert_canonical_facts,
    upsert_country_cohort_members,
    upsert_country_cohorts,
    upsert_country_daily_metrics,
    upsert_country_index_runs,
    upsert_country_metric_warnings,
    upsert_country_weekly_metrics,
    upsert_point_in_time_fundamentals,
    upsert_regulatory_facts,
    upsert_regulatory_filings,
    upsert_security_prices,
    upsert_securities,
    upsert_security_listings,
    upsert_primary_security_listings,
)
from src.lib.pipeline.canonical_facts import normalize_facts
from src.lib.pipeline.country_cohorts import CohortCandidate, CountryCohort, form_cohort, evaluate_cohort_coverage
from src.lib.pipeline.country_valuation import (
    CompanyFundamentals,
    ValuationFx,
    ValuationPrice,
    calculate_daily_country_metrics,
)
from src.lib.pipeline.point_in_time import fundamentals_as_of
from src.lib.pipeline.uncertainty import AggregateContribution, SensitivityInput, estimate_sensitivity
from src.lib.pipeline.weekly_valuation import WeeklyCountryMetric, summarize_week
from src.lib.source.country_index_types import DailyPrice, FxRate, ProviderLicense, SecurityListing


STAGES = (
    "immutable_acquisition",
    "normalization_point_in_time",
    "eligible_universe_prices_fx",
    "cohort_evaluation",
    "daily_calculations",
    "weekly_summaries",
    "sensitivity",
    "validation",
    "persistence_publication",
)
METRICS = ("pe", "pb", "ps", "pcf", "pfcf", "dividend_yield")
DEFAULT_METHODOLOGY = "us-country-index-v1"


CHECKPOINT_VERSION = 3

# Explicit trusted modules; checkpoint data can never choose an import or execute code.
from src.lib.pipeline import canonical_facts, country_cohorts, country_valuation, point_in_time, uncertainty, weekly_valuation
from src.lib.source import country_index_types
_CHECKPOINT_TYPES = {
    f"{cls.__module__}.{cls.__name__}": cls
    for module in (canonical_facts, country_cohorts, country_valuation, point_in_time,
                   uncertainty, weekly_valuation, country_index_types)
    for cls in vars(module).values() if isinstance(cls, type) and is_dataclass(cls)
}


def _encode(value):
    if is_dataclass(value):
        return {"type": f"{type(value).__module__}.{type(value).__name__}",
                "fields": {f.name: _encode(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, (Decimal, datetime, date)):
        return {"type": type(value).__name__, "value": str(value)}
    if isinstance(value, Mapping):
        pairs = [[_encode(k), _encode(v)] for k, v in value.items()]
        return {"type": "mapping", "items": sorted(pairs, key=lambda pair: _canonical(pair[0]))}
    if isinstance(value, (tuple, list, set, frozenset)):
        items = [_encode(v) for v in value]
        if isinstance(value, (set, frozenset)):
            items.sort(key=_canonical)
        return {"type": type(value).__name__, "items": items}
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ValueError(f"unsupported checkpoint value: {type(value).__name__}")


def _decode(value):
    if not isinstance(value, dict):
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        raise ValueError("invalid checkpoint scalar")
    kind = value.get("type")
    if kind in _CHECKPOINT_TYPES and set(value) == {"type", "fields"}:
        cls = _CHECKPOINT_TYPES[kind]
        if set(value["fields"]) != {f.name for f in fields(cls)}:
            raise ValueError("invalid checkpoint dataclass fields")
        return cls(**{k: _decode(v) for k, v in value["fields"].items()})
    if kind in ("Decimal", "date", "datetime") and set(value) == {"type", "value"}:
        return {"Decimal": Decimal, "date": date.fromisoformat, "datetime": datetime.fromisoformat}[kind](value["value"])
    if set(value) == {"type", "items"}:
        if kind == "mapping":
            result = {_decode(k): _decode(v) for k, v in value["items"]}
            if len(result) != len(value["items"]):
                raise ValueError("duplicate checkpoint mapping keys")
            return result
        if kind in ("tuple", "list", "set", "frozenset"):
            return {"tuple": tuple, "list": list, "set": set, "frozenset": frozenset}[kind](_decode(v) for v in value["items"])
    raise ValueError("unknown checkpoint type or fields")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _identity(provider):
    if provider is None:
        return None
    if isinstance(provider, Mapping):
        return {"type": "mapping", "config": provider}
    identity = {"type": f"{type(provider).__module__}.{type(provider).__qualname__}"}
    explicit = getattr(provider, "checkpoint_config", None)
    if callable(explicit):
        explicit = explicit()
    identity["config"] = explicit
    for name in ("provider", "version", "license", "config", "identity"):
        if hasattr(provider, name):
            identity[name] = getattr(provider, name)
    # Explicit configuration is authoritative for stateful repositories. Otherwise
    # include serializable private settings as well (SEC user agent, endpoints).
    for name, value in (getattr(provider, "__dict__", {}) if explicit is None else {}).items():
        if name.lstrip("_") in {"calls", "call_count", "cache", "session", "client"}:
            continue
        try:
            _encode(value)
        except ValueError:
            continue
        identity[name] = value
    target = provider if inspect.isfunction(provider) else type(provider)
    try:
        identity["implementation"] = hashlib.sha256(inspect.getsource(target).encode()).hexdigest()
    except (TypeError, OSError):
        identity["implementation"] = getattr(provider, "__qualname__", identity["type"])
    if inspect.isfunction(provider) and explicit is None:
        identity["defaults"] = provider.__defaults__
        identity["closure"] = tuple(cell.cell_contents for cell in (provider.__closure__ or ()))
    return identity


def _write_checkpoint(path, fingerprint, name, value):
    payload = _encode(value)
    envelope = {"version": CHECKPOINT_VERSION, "fingerprint": fingerprint, "stage": name,
                "sha256": hashlib.sha256(_canonical(payload).encode()).hexdigest(), "payload": payload}
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(_canonical(envelope))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _read_checkpoint(path, fingerprint, name):
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        if (set(envelope) != {"version", "fingerprint", "stage", "sha256", "payload"}
                or envelope["version"] != CHECKPOINT_VERSION or envelope["fingerprint"] != fingerprint
                or envelope["stage"] != name
                or envelope["sha256"] != hashlib.sha256(_canonical(envelope["payload"]).encode()).hexdigest()):
            raise ValueError("configuration, version, or checksum mismatch")
        return _decode(envelope["payload"])
    except Exception as exc:
        raise ValueError(f"checkpoint {name}: {exc}") from exc


def _jsonable(value: object) -> object:
    if is_dataclass(value):
        return {f.name: _jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _db_decimal(value: object) -> object:
    return +value if isinstance(value, Decimal) else value


def _rational_decimal(value: Fraction) -> Decimal:
    with localcontext() as context:
        context.prec = max(50, len(str(abs(value.numerator))) + len(str(value.denominator)) + 10)
        return Decimal(value.numerator) / Decimal(value.denominator)


def _contribution_totals(input_value: SensitivityInput) -> tuple[Decimal, Decimal]:
    """Use Task 8's componentwise peer median rule without rounding summands."""
    totals = [Fraction(), Fraction()]
    for sid, contribution in input_value.contributions.items():
        for index, field in enumerate(("numerator", "denominator")):
            if contribution is not None:
                amount = Fraction(getattr(contribution, field))
            else:
                amounts = sorted(Fraction(getattr(peer, field)) for peer in input_value.peer_contributions[sid])
                middle = len(amounts) // 2
                amount = amounts[middle] if len(amounts) % 2 else (amounts[middle - 1] + amounts[middle]) / 2
            totals[index] += amount
    return tuple(_rational_decimal(value) for value in totals)


def _sensitivity_issue(result, metric):
    if result is None or result.status not in {"experimental", "complete", "warning"}:
        return "sensitivity_unavailable"
    numbers = (result.point_estimate, result.lower, result.upper, *result.draw_values)
    if any(not isinstance(value, Decimal) or not value.is_finite() for value in numbers):
        return "sensitivity_nonfinite_or_missing_interval"
    if (len(result.draw_values) != result.draws or result.draws <= 0 or result.lower > result.upper
            or any(value < 0 if metric == "dividend_yield" else value <= 0 for value in numbers)):
        return "sensitivity_invalid_interval_or_draw"
    return None


def _merge_diagnostics(results, field):
    """One deterministic warning/component per code across valid daily inputs."""
    grouped = {}
    for result in results:
        for entry in getattr(result, field):
            grouped.setdefault(entry.code, []).append(entry)
    merged = []
    for code, entries in sorted(grouped.items()):
        entry = entries[0]
        widths = [item.interval_width_contribution for item in entries if item.interval_width_contribution is not None]
        updates = {"interval_width_contribution": max(widths) if widths else None}
        if field == "warnings":
            updates["affected_market_cap_weight"] = max(item.affected_market_cap_weight for item in entries)
            updates["explanation"] = min(item.explanation for item in entries)
        else:
            updates["available"] = any(item.available for item in entries)
        merged.append(replace(entry, **updates))
    return tuple(merged)


def _read_publication_state(connection, run_id):
    """Read durable recovery evidence under the publisher's advisory lock."""
    with connection.cursor() as cursor:
        cursor.execute("select pg_advisory_xact_lock(hashtext('marts.country_index_publications'))")
        cursor.execute("""
            select run_status, methodology_version, completed_at, source_coverage
            from core.country_index_runs where run_id = %(run_id)s for update
        """, {"run_id": run_id})
        run = cursor.fetchone()
        if run is None:
            return None
        if not isinstance(run, Mapping):
            raise ValueError("publication recovery requires mapping database rows")
        cursor.execute("""
            select market_id, metric_key, week_id from marts.country_index_publications
            where run_id = %(run_id)s and is_current
        """, {"run_id": run_id})
        return {**run, "current_keys": tuple((row["market_id"], row["metric_key"], row["week_id"]) for row in cursor.fetchall())}


def _error_dict(error: object, *, security_id: str, stage: str) -> dict[str, object]:
    if hasattr(error, "__dict__"):
        result = dict(vars(error))
    elif isinstance(error, Mapping):
        result = dict(error)
    else:
        result = {"message": str(error)}
    result.setdefault("provider", "sec")
    result.setdefault("key", security_id)
    result.setdefault("external_series_id", None)
    result.setdefault("error_type", "source_error")
    result.setdefault("message", str(error))
    result["security_id"] = security_id
    result["stage"] = stage
    return result


def _license_guard(provider: object, environment: str) -> None:
    license_info = getattr(provider, "license", None)
    if not isinstance(license_info, ProviderLicense):
        raise ValueError("price provider must expose a ProviderLicense")
    if environment.lower() == "production":
        if license_info.provider.lower() in {"yahoo", "yahoo_finance", "yahoo_finance_development"}:
            raise ValueError("Yahoo price source is not approved for commercial production")
        license_info.assert_publishable(environment=environment)


def _checkpoint_paths(checkpoint_dir: Path, run_id: str) -> dict[str, Path]:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id)
    return {stage: checkpoint_dir / f"{safe_id}.{stage}.json" for stage in STAGES}


def _week_start(now: datetime) -> date:
    current = now.astimezone(UTC).date()
    return current - timedelta(days=current.weekday() + 7)


def _call_facts(provider: object, security_id: str, start: datetime, end: datetime) -> object:
    fetch_companyfacts = getattr(provider, "fetch_companyfacts", None)
    if callable(fetch_companyfacts):
        return fetch_companyfacts(security_id)
    discover = getattr(provider, "discover", None)
    fetch_facts = getattr(provider, "fetch_facts", None)
    if not callable(discover) or not callable(fetch_facts):
        raise ValueError("filing provider must implement fetch_companyfacts or discover/fetch_facts")
    discovered = discover(start, end)
    filings = [filing for filing in discovered if filing.filer_id == security_id or filing.external_id == security_id]
    facts = tuple(fact for filing in filings for fact in fetch_facts(filing))
    return type("FactsResult", (), {"ok": True, "filings": tuple(filings), "facts": facts, "error": None})()


def _filing_row(filing: object) -> dict[str, object]:
    return {
        "provider": filing.provider, "external_id": filing.external_id, "content_hash": filing.content_hash,
        "jurisdiction": filing.jurisdiction, "filer_id": filing.filer_id, "filing_form": filing.filing_form,
        "filing_date": filing.filing_date, "accepted_at": filing.accepted_at, "published_at": filing.published_at,
        "amendment_of_external_id": filing.amendment_of_external_id, "document_url": filing.document_url,
        "content_json": dict(filing.content_json), "fetched_at": filing.fetched_at,
    }


def _fact_row(fact: object) -> dict[str, object]:
    return {
        "filing_provider": fact.filing_provider, "filing_external_id": fact.filing_id,
        "filing_content_hash": fact.filing_content_hash, "fact_id": fact.fact_id,
        "entity_id": fact.entity_id, "security_id": fact.security_id, "taxonomy": fact.taxonomy,
        "concept_name": fact.concept_name, "context_id": fact.context_id, "dimensions_json": dict(fact.dimensions),
        "unit": fact.unit, "decimals": fact.decimals, "value_text": fact.value_text,
        "period_start": fact.period_start, "period_end": fact.period_end, "instant_date": fact.instant_date,
        "is_consolidated": fact.is_consolidated, "is_continuing_operations": fact.is_continuing_operations,
    }


def _price_row(price: DailyPrice) -> dict[str, object]:
    return {
        "security_id": price.security_id, "trading_date": price.trading_date, "provider": price.provider,
        "close_price": price.close_price, "split_adjusted_close_price": price.split_adjusted_close_price,
        "trading_currency": price.trading_currency, "adjustment_metadata": dict(price.adjustment_metadata),
        "provider_timestamp": price.provider_timestamp, "license_class": price.license_class,
        "source_url": price.source_url,
    }


def _cohort_row(cohort: CountryCohort, methodology_version: str, week: date) -> dict[str, object]:
    return {
        "market_id": cohort.market_id, "cohort_version": cohort.effective_date.isoformat(),
        "effective_from": cohort.effective_date, "effective_to": None,
        "target_coverage_lower": cohort.target[0], "target_coverage_upper": cohort.target[1],
        "achieved_market_coverage": cohort.achieved_market_coverage,
        "constituent_target_count": cohort.constituent_target_count,
        "cohort_status": "complete", "structured_reasons": list(cohort.reasons),
        "methodology_version": methodology_version,
    }


def _daily_row(run_id: str, row: object, cohort: CountryCohort, sensitivity: object | None = None) -> dict[str, object]:
    whole = row.whole_cohort_coverage
    reasons = [row.reason] if row.reason else []
    return {
        "run_id": run_id, "market_id": row.market_id, "metric_key": row.metric,
        "valuation_date": row.valuation_date, "cohort_version": cohort.effective_date.isoformat(),
        "methodology_version": row.methodology_version, "metric_value": _db_decimal(row.value),
        "value_currency": row.common_currency, "metric_status": row.status,
        "market_coverage": _db_decimal(row.market_coverage), "reported_fact_coverage": _db_decimal(whole.reported) if whole else None,
        "carried_forward_coverage": _db_decimal(whole.carried_forward) if whole else None,
        "imputed_coverage": _db_decimal(whole.imputed) if whole else None,
        "missing_or_invalid_coverage": _db_decimal(whole.missing_or_invalid) if whole else None,
        "metric_eligible_coverage": _db_decimal(row.eligible_weight),
        "actual_constituent_count": row.constituent_count, "cohort_target_count": row.constituent_target_count,
        "effective_constituent_count": _db_decimal(row.effective_constituent_count),
        "largest_constituent_weight": _db_decimal(row.largest_constituent_weight),
        "top_five_concentration": _db_decimal(row.top_five_weight), "top_ten_concentration": _db_decimal(row.top_ten_weight),
        "membership_overlap": None, "interval_lower": _db_decimal(getattr(sensitivity, "lower", None)),
        "interval_upper": _db_decimal(getattr(sensitivity, "upper", None)),
        "source_coverage": {"price": "provider", "fundamentals": "point_in_time",
                            "sensitivity": {"interval_label": getattr(sensitivity, "interval_label", "unavailable"),
                                            "status": getattr(sensitivity, "status", "unavailable"),
                                            "reason": getattr(sensitivity, "reason", None),
                                            "components": _jsonable(getattr(sensitivity, "components", ())),
                                            "imputed_weight": _jsonable(getattr(sensitivity, "imputed_weight", None))}},
        "structured_reasons": reasons,
    }


def _weekly_row(run_id: str, weekly: WeeklyCountryMetric, sensitivity: object | None, cohort: CountryCohort) -> dict[str, object]:
    whole = weekly.whole_cohort_coverage
    # Reconcile the headline against the exact values written to the daily table,
    # including the persistence Decimal precision for even observation counts.
    persisted_values = sorted(_db_decimal(value) for _, value in weekly.daily_values)
    middle = len(persisted_values) // 2
    persisted_median = None if weekly.value is None else (
        persisted_values[middle] if len(persisted_values) % 2
        else (persisted_values[middle - 1] + persisted_values[middle]) / Decimal(2))
    reasons = list(weekly.warning_codes)
    if weekly.reason:
        reasons.append(weekly.reason)
    reasons.extend(warning.code for warning in getattr(sensitivity, "warnings", ()))
    reasons = sorted(set(reasons))
    return {
        "run_id": run_id, "market_id": weekly.market_id, "metric_key": weekly.metric,
        "week_id": weekly.week_start, "cohort_version": cohort.effective_date.isoformat(),
        "methodology_version": weekly.methodology_version, "metric_value": persisted_median,
        "weekly_min_value": _db_decimal(weekly.minimum), "weekly_max_value": _db_decimal(weekly.maximum),
        "valuation_dates": list(weekly.valid_valuation_dates), "daily_observation_count": weekly.valid_observation_count,
        "metric_status": "warning" if weekly.value is not None and reasons else weekly.status,
        "market_coverage": _db_decimal(weekly.market_coverage),
        "reported_fact_coverage": _db_decimal(whole.reported) if whole else None,
        "carried_forward_coverage": _db_decimal(whole.carried_forward) if whole else None,
        "imputed_coverage": _db_decimal(whole.imputed) if whole else None,
        "missing_or_invalid_coverage": _db_decimal(whole.missing_or_invalid) if whole else None,
        "metric_eligible_coverage": _db_decimal(weekly.eligible_weight),
        "actual_constituent_count": weekly.constituent_count,
        "cohort_target_count": weekly.constituent_target_count,
        "effective_constituent_count": _db_decimal(weekly.effective_constituent_count),
        "largest_constituent_weight": _db_decimal(weekly.largest_constituent_weight),
        "top_five_concentration": _db_decimal(weekly.top_five_weight), "top_ten_concentration": _db_decimal(weekly.top_ten_weight),
        "membership_overlap": None, "interval_lower": _db_decimal(getattr(sensitivity, "lower", None)),
        "interval_upper": _db_decimal(getattr(sensitivity, "upper", None)),
        "source_coverage": {"sensitivity": {"interval_label": getattr(sensitivity, "interval_label", "unavailable"),
                                                     "seed": getattr(sensitivity, "seed", None),
                                                     "draws": getattr(sensitivity, "draws", None),
                                                     "point_estimate": _jsonable(getattr(sensitivity, "point_estimate", None)),
                                                     "components": _jsonable(getattr(sensitivity, "components", ())),
                                                     "warnings": _jsonable(getattr(sensitivity, "warnings", ()))},
                             "reported": weekly.whole_cohort_coverage is not None},
        "structured_reasons": reasons,
    }


def _warning_rows(run_id, weekly_rows, sensitivity_results):
    rows = []
    for weekly in weekly_rows:
        result = sensitivity_results[weekly["metric_key"]]
        warnings = {warning.code: warning for warning in getattr(result, "warnings", ())}
        components = {component.code: component for component in getattr(result, "components", ())}
        for code in sorted(set(weekly["structured_reasons"])):
            warning, component = warnings.get(code), components.get(code)
            rows.append({"run_id": run_id, "market_id": weekly["market_id"], "metric_key": weekly["metric_key"],
                         "week_id": weekly["week_id"], "warning_code": code,
                         "warning_level": getattr(result, "warning_level", "warning") if warning else "warning",
                         "warning_message": warning.explanation if warning else code,
                         "affected_market_weight": _db_decimal(warning.affected_market_cap_weight) if warning else Decimal(0),
                         "interval_width_contribution": _db_decimal(warning.interval_width_contribution) if warning else None,
                         "structured_reason": {"code": code, "component": _jsonable(component)}})
    return rows


def run_us_country_index_etl(
    connection: Any = None, *, universe_provider=None, filing_provider=None, price_provider=None,
    fx_provider=None, share_state=None, cohort_state=None, sensitivity_context=None,
    clock=None, run_id=None, checkpoint_dir=None, environment="development",
    methodology_version=DEFAULT_METHODOLOGY, market_id="us", stage_hook=None, sensitivity_draws=1000,
) -> dict[str, object]:
    """Run the previous Mon-Fri window with injected source and cohort repositories.

    ``cohort_state`` is a callback (or repository.load) returning None on first
    formation, otherwise {cohort, formation_caps, evaluated_week}. It may also
    supply forced_replacements (outgoing -> incoming). A repository.save method
    receives the next state and the persistence connection inside the transaction.
    Callbacks can persist the returned next_cohort_state with their own scheduler.
    ``checkpoint_config`` on providers/callbacks identifies external configuration.
    ``sensitivity_context`` supplies per-day peer contribution distributions and
    optional staleness inputs. Missing peers leave the metric unavailable; peer
    draws retain that security's observed market capitalization. Publication
    recovery reads the completed run and current manifest under the DB lock.
    """
    started_at = (clock or (lambda: datetime.now(UTC)))()
    stage_counts = OrderedDict()
    reused = []
    source_errors = []
    current_stage = "configuration"
    expected_keys = ()
    committed = False
    metric_warning_count = 0
    try:
        if started_at.tzinfo is None or started_at.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        if connection is None or not callable(getattr(connection, "transaction", None)):
            raise ValueError("a database connection with transaction support is required")
        # A psycopg transaction entered after implicit BEGIN is only a savepoint.
        # Never claim durable publication in a transaction owned by our caller.
        if getattr(getattr(connection, "info", None), "transaction_status", 0) != 0:
            raise ValueError("country-index publication requires an idle database connection")
        if any(provider is None for provider in (universe_provider, filing_provider, price_provider)):
            raise ValueError("universe, filing and price providers must be configured")
        if not methodology_version:
            raise ValueError("methodology_version is required")
        _license_guard(price_provider, environment)
        if environment == "production" and cohort_state is None:
            raise ValueError("production requires a persistent cohort state repository")
        run_id = run_id or hashlib.sha256(started_at.isoformat().encode()).hexdigest()[:16]
        week = _week_start(started_at)
        days = tuple(week + timedelta(days=i) for i in range(5))
        expected_keys = tuple((market_id, metric, week) for metric in METRICS)
        current_stage = "checkpoint"
        config = {"run_id": run_id, "methodology": methodology_version, "market": market_id,
                  "week": week, "environment": environment, "sensitivity_draws": sensitivity_draws,
                  "sources": [_identity(p) for p in (universe_provider, filing_provider, price_provider,
                                                     fx_provider, share_state, cohort_state, sensitivity_context)]}
        fingerprint = hashlib.sha256(_canonical(_encode(config)).encode()).hexdigest()
        paths = _checkpoint_paths(Path(checkpoint_dir or ".mvd-checkpoints"), run_id)
        # Validate every existing file before using any cached stage.
        cached = {name: _read_checkpoint(path, fingerprint, name) for name, path in paths.items() if path.exists()}

        def stage(name, action, count):
            nonlocal current_stage
            current_stage = name
            if name in cached and name != STAGES[8]:
                value = cached[name]
                reused.append(name)
            else:
                if stage_hook and name not in cached:
                    stage_hook(name)
                value = action()
                if name == STAGES[8] and value.get("recovered"):
                    reused.append(name)
                _write_checkpoint(paths[name], fingerprint, name, value)
            stage_counts[name] = count(value)
            return value

        def acquire():
            listings = tuple(l for l in universe_provider.listings_as_of(market_id, week)
                             if l.is_primary and l.market_id == market_id and l.listing_status == "active"
                             and l.valid_from <= week and (l.valid_to is None or l.valid_to >= week))
            if not listings or len({l.security_id for l in listings}) != len(listings):
                raise ValueError("US universe must contain unique eligible primary listings")
            filings, facts, errors = [], [], []
            for listing in listings:
                try:
                    result = _call_facts(filing_provider, listing.security_id,
                                         datetime.combine(week, time(tzinfo=UTC)), started_at)
                    if not getattr(result, "ok", False):
                        errors.append(_error_dict(getattr(result, "error", result), security_id=listing.security_id, stage=STAGES[0]))
                        continue
                    filings.extend(result.filings)
                    facts.extend(result.facts)
                except Exception as exc:
                    errors.append(_error_dict(exc, security_id=listing.security_id, stage=STAGES[0]))
            if not facts:
                raise ValueError("filing provider returned no usable facts")
            return {"listings": listings, "filings": tuple(filings), "facts": tuple(facts), "source_errors": errors}

        acquired = stage(STAGES[0], acquire, lambda value: len(value["facts"]))
        source_errors = acquired["source_errors"]

        def normalize():
            canonical = tuple(normalize_facts(acquired["facts"], "sec-v1"))
            fundamentals, pit_rows = {}, []
            for day in days:
                for listing in acquired["listings"]:
                    selected = [f for f in canonical if f.raw.security_id == listing.security_id]
                    pit = fundamentals_as_of(listing.security_id, datetime.combine(day, time(23, 59, tzinfo=UTC)), selected)
                    fundamentals[(listing.security_id, day)] = CompanyFundamentals(pit)
                    monetary = [getattr(pit, name) for name in ("revenue", "net_income", "common_equity", "operating_cash_flow", "capex", "free_cash_flow", "dividends")]
                    currencies = {f.unit for f in monetary if f.value is not None}
                    if len(currencies) > 1:
                        raise ValueError("PIT monetary fields have mixed reporting currencies")
                    currency = next(iter(currencies), None)
                    lineage_fields = monetary + [pit.period_end_shares]
                    lineage = sorted({f.raw.fact_id for field in lineage_fields for f in field.lineage.facts})
                    reasons = sorted({reason for field in lineage_fields for reason in field.warnings})
                    if any(field.value is None for field in monetary):
                        reasons.append("missing_fundamental_fields")
                    reported = Decimal(sum(f.value is not None for f in monetary)) / Decimal(len(monetary))
                    pit_rows.append({
                        "security_id": listing.security_id, "valuation_date": day, "methodology_version": methodology_version,
                        "reporting_currency": currency, "market_cap": None, "ttm_revenue": pit.ttm_revenue,
                        "ttm_net_income": pit.ttm_net_income, "common_equity": pit.common_equity.value,
                        "ttm_operating_cash_flow": pit.ttm_operating_cash_flow, "ttm_cash_capex": pit.ttm_capex,
                        "ttm_free_cash_flow": pit.ttm_free_cash_flow, "ttm_common_dividends": pit.ttm_dividends,
                        "shares_outstanding": pit.period_end_shares.value, "reported_fact_coverage": reported,
                        "carried_forward_coverage": Decimal(0), "imputed_coverage": Decimal(0),
                        "missing_or_invalid_coverage": Decimal(1) - reported,
                        "source_lineage": lineage, "structured_reasons": reasons})
            return {"canonical": canonical, "fundamentals": fundamentals, "pit_rows": pit_rows}

        normalized = stage(STAGES[1], normalize, lambda value: len(value["canonical"]))

        def prices_and_fx():
            all_prices, prices, states = [], {}, {}
            for listing in acquired["listings"]:
                rows = tuple(price_provider.daily_prices(listing, days[0], days[-1]))
                if len({p.trading_date for p in rows}) != len(rows):
                    raise ValueError("duplicate security price dates")
                for price in rows:
                    if price.trading_date not in days or price.security_id != listing.security_id:
                        raise ValueError("price must match the security and Monday-Friday run window")
                    if price.trading_currency != listing.trading_currency:
                        raise ValueError("price currency does not match listing currency")
                    if price.provider != price_provider.license.provider or price.license_class != price_provider.license.usage:
                        raise ValueError("price lineage does not match provider license")
                    if share_state is None:
                        raise ValueError("shares must come from an explicit reconciliation callback")
                    state = dict(share_state(listing, price.trading_date, normalized["fundamentals"].get((listing.security_id, price.trading_date)), price))
                    shares = state.get("shares_outstanding")
                    if not isinstance(shares, Decimal) or not shares.is_finite() or shares <= 0 or not state.get("source"):
                        raise ValueError("shares reconciliation requires positive Decimal shares and source lineage")
                    states[(listing.security_id, price.trading_date)] = state
                prices[listing.security_id] = rows
                all_prices.extend(rows)
            if not all_prices:
                raise ValueError("price provider returned no prices")
            currencies = {l.trading_currency for l in acquired["listings"]}
            currencies.update(row["reporting_currency"] for row in normalized["pit_rows"] if row["reporting_currency"])
            fx = {}
            for day in days:
                rates = []
                for currency in sorted(currencies - {"USD"}):
                    if fx_provider is None:
                        raise ValueError("FX provider is required for non-USD amounts")
                    fetched = tuple(fx_provider.daily_rates(currency, "USD", day, day))
                    if len(fetched) != 1:
                        raise ValueError("FX provider must return exactly one rate per currency/day")
                    rate = fetched[0]
                    if (rate.base_currency, rate.quote_currency, rate.rate_date) != (currency, "USD", day) or not rate.provider or not rate.source_url:
                        raise ValueError("FX rate identity/date/source lineage mismatch")
                    rates.append(rate)
                fx[day] = ValuationFx("USD", tuple(rates))
            return {"all_prices": tuple(all_prices), "prices": prices, "states": states, "fx": fx}

        priced = stage(STAGES[2], prices_and_fx, lambda value: len(value["all_prices"]))

        def day_cap(sid, day):
            price = next((p for p in priced["prices"].get(sid, ()) if p.trading_date == day), None)
            if price is None:
                return None
            rate = Decimal(1) if price.trading_currency == "USD" else next(r.rate for r in priced["fx"][day].rates if r.base_currency == price.trading_currency)
            return price.close_price * priced["states"][(sid, day)]["shares_outstanding"] * rate

        def cohorts():
            caps = {l.security_id: day_cap(l.security_id, days[0]) for l in acquired["listings"]}
            if any(cap is None for cap in caps.values()):
                raise ValueError("formation/evaluation requires complete eligible-universe capitalization")
            loader = getattr(cohort_state, "load", cohort_state)
            prior = loader(market_id=market_id, methodology_version=methodology_version, week=week) if callable(loader) else cohort_state
            if isinstance(prior, CountryCohort):
                raise ValueError("active cohort state must include actual formation_caps and evaluated_week")
            active = prior["cohort"] if prior else None
            replacements = dict(prior.get("forced_replacements", {})) if prior else {}
            evaluation = None
            if active:
                if active.market_id != market_id or active.effective_date > week:
                    raise ValueError("active cohort identity/date mismatch")
                previous_week = prior.get("evaluated_week")
                if previous_week is not None and previous_week > week:
                    raise ValueError("cohort state cannot follow the valuation week")
                history = active if previous_week == week - timedelta(days=7) else active.with_outside_tolerance_weeks(0)
                evaluation = evaluate_cohort_coverage(history, caps)
                if previous_week == week:
                    evaluation = replace(evaluation, consecutive_outside_tolerance_weeks=active.consecutive_outside_tolerance_weeks,
                                         exceptional_reconstitution_required=False)
                missing = set(active.security_ids) - caps.keys()
                if missing - replacements.keys():
                    raise ValueError("missing cohort member requires an explicit forced replacement")
            annual = active is not None and active.effective_date.year < week.year
            exceptional = evaluation is not None and evaluation.exceptional_reconstitution_required
            reform = active is None or annual or bool(replacements) or exceptional
            if reform:
                candidates = [CohortCandidate(sid, cap, bool(active and sid in active.security_ids and sid not in replacements), sid in replacements.values()) for sid, cap in caps.items() if sid not in replacements]
                cohort = form_cohort(market_id, week, candidates, prior_constituent_target_count=active.constituent_target_count if replacements else None)
                reason = "first_formation" if active is None else "forced_replacement" if replacements else "annual_reconstitution" if annual else "exceptional_reconstitution"
                cohort = replace(cohort, reasons=tuple(dict.fromkeys((*cohort.reasons, reason))))
                formation_caps = {sid: caps[sid] for sid in cohort.security_ids}
            else:
                cohort = active.with_outside_tolerance_weeks(evaluation.consecutive_outside_tolerance_weeks)
                formation_caps = dict(prior["formation_caps"])
                if set(formation_caps) != set(cohort.security_ids) or any(not isinstance(v, Decimal) or not v.is_finite() or v <= 0 for v in formation_caps.values()):
                    raise ValueError("active cohort requires actual positive formation caps for every member")
            return {"cohort": cohort, "formation_caps": formation_caps, "evaluated_week": week,
                    "coverage_reasons": evaluation.reasons if evaluation else (),
                    "current_coverage": evaluate_cohort_coverage(cohort.with_outside_tolerance_weeks(0), caps).market_coverage}

        next_state = stage(STAGES[3], cohorts, lambda value: len(value["cohort"].security_ids))
        cohort = next_state["cohort"]

        def calculation_inputs(day, securities):
            prices, fundamentals = [], []
            for sid in securities:
                price = next((p for p in priced["prices"].get(sid, ()) if p.trading_date == day), None)
                if price is not None:
                    state = priced["states"][(sid, day)]
                    prices.append(ValuationPrice(price, state["shares_outstanding"], state.get("industry", "unknown"), state.get("revenue_comparable", False)))
                company = normalized["fundamentals"].get((sid, day))
                if company is not None:
                    fundamentals.append(company)
            return prices, fundamentals

        def sensitivity_input(row):
            # Task 7's finite-Decimal weights may have a rounding residual.
            weights = list(row.constituent_weights)
            with localcontext() as context:
                context.prec = max(len(weight.as_tuple().digits) for _, weight in weights) + 20
                weights[-1] = (weights[-1][0], Decimal(1) - sum((weight for _, weight in weights[:-1]), Decimal(0)))
            row = replace(row, constituent_weights=tuple(weights))
            contributions = {}
            for sid in cohort.security_ids:
                if sid not in row.eligible_security_ids:
                    contributions[sid] = AggregateContribution(Decimal(0), Decimal(0))
                    continue
                singleton = replace(cohort, security_ids=(sid,), constituent_target_count=1)
                prices, fundamentals = calculation_inputs(row.valuation_date, (sid,))
                isolated = next((r for r in calculate_daily_country_metrics(singleton, prices, fundamentals, priced["fx"][row.valuation_date], methodology_version) if r.metric == row.metric), None) if prices else None
                contributions[sid] = AggregateContribution(isolated.aggregate_numerator, isolated.aggregate_denominator) if isolated and isolated.aggregate_numerator is not None and isolated.aggregate_denominator is not None else None
            extra = dict(sensitivity_context(metric=row, cohort=cohort, fundamentals=normalized["fundamentals"], share_states=priced["states"])) if sensitivity_context else {}
            input_value = SensitivityInput(row, contributions=contributions, **extra)
            # Peer fundamentals may vary, but today's observed market cap cannot.
            for sid, peers in input_value.peer_contributions.items():
                if contributions[sid] is None:
                    cap = day_cap(sid, row.valuation_date)
                    cap_field = "denominator" if row.metric == "dividend_yield" else "numerator"
                    if any(getattr(peer, cap_field) != cap for peer in peers):
                        raise ValueError("peer contributions must preserve the missing constituent's observed market cap")
            return input_value

        def daily():
            rows, results, inputs = [], {}, {}
            for day in days:
                prices, fundamentals = calculation_inputs(day, cohort.security_ids)
                if not prices:
                    continue
                caps = {l.security_id: day_cap(l.security_id, day) for l in acquired["listings"]}
                coverage = evaluate_cohort_coverage(cohort, caps).market_coverage if all(v is not None for v in caps.values()) else None
                coverage_warning = next((reason for reason in next_state["coverage_reasons"] if reason.startswith("coverage_")), None)
                for row in calculate_daily_country_metrics(cohort, prices, fundamentals, priced["fx"][day], methodology_version):
                    row = replace(row, market_coverage=coverage,
                                  status="warning" if row.value is not None and coverage_warning else row.status,
                                  reason=row.reason or coverage_warning)
                    key = (row.metric, day)
                    result = None
                    if row.value is not None or row.reason == "awaiting_imputation":
                        input_value = sensitivity_input(row)
                        inputs[key] = input_value
                        missing = [sid for sid, contribution in input_value.contributions.items() if contribution is None]
                        if any(sid not in input_value.peer_contributions for sid in missing):
                            row = replace(row, status="unavailable", value=None, reason="missing_peer_contributions")
                        else:
                            result = estimate_sensitivity(input_value, cohort, seed=17, draws=sensitivity_draws)
                            if any(component.code == "missing_aggregate_contributions" for component in result.components):
                                raise ValueError("publishable metric requires real aggregate contribution sensitivity")
                            issue = _sensitivity_issue(result, row.metric)
                            if issue:
                                row = replace(row, status="unavailable", value=None, reason=issue)
                                # Do not let nonfinite engine outputs enter persisted JSON/interval columns.
                                result = replace(result, status="unavailable", point_estimate=None, lower=None, upper=None,
                                                 draw_values=(), reason=result.reason or issue)
                            elif missing:
                                numerator, denominator = _contribution_totals(input_value)
                                def imputed_coverage(coverage):
                                    return replace(coverage, imputed=coverage.imputed + coverage.missing_or_invalid, missing_or_invalid=Decimal(0)) if coverage else None
                                row = replace(row, status="warning", reason="partly_estimated", value=result.point_estimate,
                                              aggregate_numerator=numerator, aggregate_denominator=denominator,
                                              whole_cohort_coverage=imputed_coverage(row.whole_cohort_coverage),
                                              eligible_scope_coverage=imputed_coverage(row.eligible_scope_coverage))
                    rows.append(row)
                    results[key] = result
            if not rows:
                raise ValueError("daily calculation produced no observations")
            return {"metrics": tuple(rows), "sensitivity": results, "inputs": inputs}

        calculated = stage(STAGES[4], daily, lambda value: len(value["metrics"]))
        daily_metrics = calculated["metrics"]
        weekly_metrics = stage(STAGES[5], lambda: tuple(summarize_week([row for row in daily_metrics if row.metric == metric]) for metric in METRICS if any(row.metric == metric for row in daily_metrics)), len)

        def sensitivity():
            results = {}
            for weekly in weekly_metrics:
                available = sorted((row for row in daily_metrics if row.metric == weekly.metric and row.value is not None), key=lambda row: (row.value, row.valuation_date))
                all_results = [result for (metric, _), result in calculated["sensitivity"].items()
                               if metric == weekly.metric and result is not None]
                if not available or weekly.value is None:
                    results[weekly.metric] = replace(all_results[0], status="unavailable", point_estimate=None,
                                                     lower=None, upper=None, draw_values=(), reason=weekly.reason,
                                                     warnings=_merge_diagnostics(all_results, "warnings"),
                                                     components=_merge_diagnostics(all_results, "components")) if all_results else None
                    continue
                central = available[(len(available)-1)//2:len(available)//2+1]
                intervals = [calculated["sensitivity"][(row.metric, row.valuation_date)] for row in central]
                result = intervals[0]
                if len(intervals) == 2:
                    other = intervals[1]
                    result = replace(result, point_estimate=(result.point_estimate + other.point_estimate)/2,
                                     lower=(result.lower + other.lower)/2, upper=(result.upper + other.upper)/2,
                                     draw_values=tuple((a+b)/2 for a,b in zip(result.draw_values, other.draw_values)))
                results[weekly.metric] = replace(result, warnings=_merge_diagnostics(all_results, "warnings"),
                                                components=_merge_diagnostics(all_results, "components"))
            return results

        sensitivity_results = stage(STAGES[6], sensitivity, len)

        def validate():
            failures = [error for error in source_errors if error["security_id"] in cohort.security_ids]
            if failures:
                raise ValueError("source failure for selected cohort member: " + ", ".join(error["security_id"] for error in failures))
            if tuple((row.market_id, row.metric, row.week_start) for row in weekly_metrics) != expected_keys:
                raise PublicationInvariantError("manifest does not match expected weekly metric keys")
            if any(row.valuation_date not in days for row in daily_metrics) or len(daily_metrics) != sum(row.observation_count for row in weekly_metrics):
                raise PublicationInvariantError("daily observations do not reconcile to weekly summaries")
            for row in weekly_metrics:
                result = sensitivity_results[row.metric]
                if row.value is not None and (_sensitivity_issue(result, row.metric) or any(component.code == "missing_aggregate_contributions" for component in result.components)):
                    raise ValueError("publishable metric requires real aggregate contribution sensitivity")
            weekly_rows = tuple(_weekly_row(run_id, row, sensitivity_results[row.metric], cohort) for row in weekly_metrics)
            return {"daily_rows": tuple(_daily_row(run_id, row, cohort, calculated["sensitivity"][(row.metric, row.valuation_date)]) for row in daily_metrics),
                    "weekly_rows": weekly_rows, "warning_rows": _warning_rows(run_id, weekly_rows, sensitivity_results)}

        validated = stage(STAGES[7], validate, lambda value: len(value["weekly_rows"]))
        metric_warning_count = len(validated["warning_rows"])

        def persist():
            nonlocal committed
            # No SQL has executed before this point. Nested publisher transaction
            # is a savepoint; only this outer transaction commits the complete run.
            if getattr(getattr(connection, "info", None), "transaction_status", 0) != 0:
                raise ValueError("cohort/source repository left the persistence connection in a transaction")
            recovered = False
            with connection.transaction():
                durable = _read_publication_state(connection, run_id)
                if durable is not None:
                    if (durable["run_status"] != "completed" or durable["completed_at"] is None
                            or durable["methodology_version"] != methodology_version
                            or durable.get("source_coverage", {}).get("checkpoint_fingerprint") != fingerprint):
                        raise ValueError("durable run cannot be recovered with this completed-run configuration")
                    if set(durable["current_keys"]) != set(expected_keys) or len(durable["current_keys"]) != len(expected_keys):
                        raise ValueError("completed run is not current for its complete publication manifest")
                    recovered = True
                elif STAGES[8] in cached:
                    raise ValueError("publication checkpoint has no durable completed run")
                if not recovered:
                    coverage = {"source_errors": source_errors, "fx_rates": _jsonable(tuple(r for fx in priced["fx"].values() for r in fx.rates)),
                                "share_state": _jsonable([{ "security_id": sid, "date": day, **state} for (sid, day), state in priced["states"].items()]),
                                "cohort_state": _encode(next_state), "checkpoint_fingerprint": fingerprint,
                                "sensitivity_inputs": [{"metric": metric, "date": day.isoformat(), "input": _encode(value)} for (metric, day), value in calculated["inputs"].items()]}
                    run_row = {"run_id": run_id, "methodology_version": methodology_version, "run_status": "running", "started_at": started_at, "completed_at": None, "source_coverage": coverage, "structured_reasons": []}
                    upsert_country_index_runs(connection, [run_row])
                    upsert_securities(connection, [{"security_id": l.security_id, "issuer_id": l.issuer_id, "issuer_name": l.issuer_name, "security_type": l.security_type, "share_class": l.share_class, "is_active": True} for l in acquired["listings"]])
                    upsert_security_listings(connection, [{"listing_id": l.listing_id, "security_id": l.security_id, "market_id": l.market_id, "exchange_code": l.exchange_code, "ticker": l.ticker, "trading_currency": l.trading_currency, "valid_from": l.valid_from, "valid_to": l.valid_to, "listing_status": l.listing_status, "source_provider": l.source_provider, "source_external_id": l.source_external_id} for l in acquired["listings"]])
                    upsert_primary_security_listings(connection, [{"security_id": l.security_id, "market_id": l.market_id, "listing_id": l.listing_id, "effective_from": l.valid_from, "effective_to": l.valid_to} for l in acquired["listings"]])
                    upsert_regulatory_filings(connection, [_filing_row(f) for f in acquired["filings"]])
                    upsert_regulatory_facts(connection, [_fact_row(f) for f in acquired["facts"]])
                    upsert_canonical_facts(connection, [{"canonical_fact_id": f"{fact.raw.filing_id}:{fact.raw.fact_id}:{fact.taxonomy_version}", "security_id": fact.raw.security_id, "concept_key": fact.metric or "unmapped", "taxonomy_version": fact.taxonomy_version, "value": fact.value, "unit": fact.unit, "period_start": fact.raw.period_start, "period_end": fact.raw.period_end, "instant_date": fact.raw.instant_date, "published_at": fact.raw.published_at, "availability_status": "accepted" if not fact.rejection_reasons else "rejected", "derivation_method": "reported", "source_lineage": [fact.raw.fact_id]} for fact in normalized["canonical"]])
                    upsert_point_in_time_fundamentals(connection, normalized["pit_rows"])
                    upsert_security_prices(connection, [_price_row(p) for p in priced["all_prices"]])
                    upsert_country_cohorts(connection, [_cohort_row(cohort, methodology_version, week)])
                    total = sum(next_state["formation_caps"].values())
                    upsert_country_cohort_members(connection, [{"market_id": market_id, "cohort_version": cohort.effective_date.isoformat(), "security_id": sid, "primary_listing_id": next(l.listing_id for l in acquired["listings"] if l.security_id == sid), "member_rank": rank, "market_cap_at_formation": next_state["formation_caps"][sid], "market_weight_at_formation": next_state["formation_caps"][sid]/total, "membership_status": "active", "membership_reason": {"code": "formation", "currency": "USD"}} for rank, sid in enumerate(cohort.security_ids, 1)])
                    upsert_country_daily_metrics(connection, validated["daily_rows"])
                    upsert_country_weekly_metrics(connection, validated["weekly_rows"])
                    upsert_country_metric_warnings(connection, validated["warning_rows"])
                    saver = getattr(cohort_state, "save", None)
                    if callable(saver):
                        saver(connection=connection, market_id=market_id, methodology_version=methodology_version, state=next_state)
                    upsert_country_index_runs(connection, [{**run_row, "run_status": "completed", "completed_at": (clock or (lambda: datetime.now(UTC)))()}])
                    publish_completed_run(connection, run_id, expected_keys=expected_keys)
            committed = True
            return {"published": True, "recovered": recovered}

        stage(STAGES[8], persist, lambda value: 1)
        return {"status": "success", "stage_counts": stage_counts, "reused_stages": reused,
                "publication_status": "published", "source_errors": source_errors,
                "source_warning_count": len(source_errors), "warning_count": metric_warning_count + len(source_errors),
                "previous_publication_preserved": False, "expected_keys": expected_keys, "next_cohort_state": next_state}
    except Exception as exc:
        publication_status = "published" if committed else "blocked_license" if "license" in str(exc).lower() or "yahoo" in str(exc).lower() else "preserved"
        return {"status": "failed", "stage_counts": stage_counts, "reused_stages": reused,
                "publication_status": publication_status, "source_errors": source_errors,
                "source_warning_count": len(source_errors), "warning_count": metric_warning_count + len(source_errors),
                "previous_publication_preserved": not committed, "failed_stage": current_stage,
                "failure_summary": str(exc), "errors": [str(exc)], "expected_keys": expected_keys}

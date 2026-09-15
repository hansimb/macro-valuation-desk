"""Restartable orchestration for the US country-index vertical slice.

The task deliberately keeps providers at the boundary and delegates all
selection and valuation arithmetic to the reusable pipeline modules.  Stage
payloads are checkpointed with pickle because they contain frozen domain
objects; checkpoints are scoped by run id and methodology configuration.
"""
from __future__ import annotations

from collections import OrderedDict
from contextlib import nullcontext
from dataclasses import asdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
import copyreg
import hashlib
import pickle
from pathlib import Path
from types import MappingProxyType
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
)
from src.lib.pipeline.canonical_facts import normalize_facts
from src.lib.pipeline.country_cohorts import CohortCandidate, CountryCohort, form_cohort
from src.lib.pipeline.country_valuation import (
    CompanyFundamentals,
    ValuationFx,
    ValuationPrice,
    calculate_daily_country_metrics,
)
from src.lib.pipeline.point_in_time import fundamentals_as_of
from src.lib.pipeline.uncertainty import estimate_sensitivity
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


copyreg.pickle(MappingProxyType, lambda value: (dict, (dict(value),)))


def _jsonable(value: object) -> object:
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


def _checkpoint_paths(checkpoint_dir: Path, run_id: str) -> tuple[Path, dict[str, Path]]:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id)
    meta = checkpoint_dir / f"{safe_id}.meta.pkl"
    return meta, {stage: checkpoint_dir / f"{safe_id}.{stage}.pkl" for stage in STAGES}


def _week_start(now: datetime) -> date:
    current = now.astimezone(UTC).date()
    return current - timedelta(days=current.weekday() + 7)


def _call_facts(provider: object, security_id: str) -> object:
    fetch_companyfacts = getattr(provider, "fetch_companyfacts", None)
    if callable(fetch_companyfacts):
        return fetch_companyfacts(security_id)
    discover = getattr(provider, "discover", None)
    fetch_facts = getattr(provider, "fetch_facts", None)
    if not callable(discover) or not callable(fetch_facts):
        raise ValueError("filing provider must implement fetch_companyfacts or discover/fetch_facts")
    discovered = discover(datetime.min.replace(tzinfo=UTC), datetime.max.replace(tzinfo=UTC))
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
    eligible = row.eligible_scope_coverage
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
        "source_coverage": {"price": "provider", "fundamentals": "point_in_time"},
        "structured_reasons": reasons,
    }


def _weekly_row(run_id: str, weekly: WeeklyCountryMetric, sensitivity: object | None, cohort: CountryCohort) -> dict[str, object]:
    whole = weekly.whole_cohort_coverage
    eligible = weekly.eligible_scope_coverage
    reasons = list(weekly.warning_codes)
    if weekly.reason:
        reasons.append(weekly.reason)
    return {
        "run_id": run_id, "market_id": weekly.market_id, "metric_key": weekly.metric,
        "week_id": weekly.week_start, "cohort_version": cohort.effective_date.isoformat(),
        "methodology_version": weekly.methodology_version, "metric_value": _db_decimal(weekly.value),
        "weekly_min_value": _db_decimal(weekly.minimum), "weekly_max_value": _db_decimal(weekly.maximum),
        "valuation_dates": list(weekly.valid_valuation_dates), "daily_observation_count": weekly.valid_observation_count,
        "metric_status": weekly.status, "market_coverage": _db_decimal(weekly.market_coverage),
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
        "source_coverage": {"sensitivity": {"interval_label": getattr(sensitivity, "interval_label", "unavailable")},
                             "reported": weekly.whole_cohort_coverage is not None},
        "structured_reasons": reasons,
    }


def run_us_country_index_etl(
    connection: Any,
    *,
    universe_provider: object,
    filing_provider: object,
    price_provider: object,
    fx_provider: object | None = None,
    share_state: Callable[[SecurityListing, date, object, DailyPrice], Mapping[str, object]] | None = None,
    clock: Callable[[], datetime] | None = None,
    run_id: str | None = None,
    checkpoint_dir: str | Path | None = None,
    environment: str = "development",
    methodology_version: str = DEFAULT_METHODOLOGY,
    market_id: str = "us",
    stage_hook: Callable[[str], None] | None = None,
    sensitivity_draws: int = 1000,
) -> dict[str, object]:
    started_at = (clock or (lambda: datetime.now(UTC)))()
    if started_at.tzinfo is None or started_at.utcoffset() is None:
        raise ValueError("clock must return a timezone-aware datetime")
    run_id = run_id or hashlib.sha256(started_at.isoformat().encode()).hexdigest()[:16]
    if connection is None:
        return {"status": "failed", "publication_status": "preserved", "previous_publication_preserved": True,
                "failure_summary": "a database connection is required for country-index publication", "errors": []}
    if not methodology_version:
        return {"status": "failed", "publication_status": "preserved", "previous_publication_preserved": True,
                "failure_summary": "methodology_version is required", "errors": []}
    week = _week_start(started_at)
    days = tuple(week + timedelta(days=i) for i in range(5))
    expected_keys = tuple((market_id, metric, week) for metric in METRICS)
    meta_path, paths = _checkpoint_paths(Path(checkpoint_dir or ".mvd-checkpoints"), run_id)
    config = {"methodology_version": methodology_version, "market_id": market_id, "week": week,
              "environment": environment, "run_id": run_id}
    try:
        if meta_path.exists():
            with meta_path.open("rb") as handle:
                if pickle.load(handle) != config:
                    raise RuntimeError("checkpoint configuration does not match this run")
        else:
            with meta_path.open("wb") as handle:
                pickle.dump(config, handle)
    except Exception as exc:
        return {"status": "failed", "publication_status": "preserved", "previous_publication_preserved": True,
                "failure_summary": f"checkpoint: {exc}", "failed_stage": "checkpoint", "errors": [str(exc)]}

    stage_counts: OrderedDict[str, int] = OrderedDict()
    reused: list[str] = []
    source_errors: list[dict[str, object]] = []

    def stage(name: str, action: Callable[[], object], count: Callable[[object], int]) -> object:
        path = paths[name]
        if path.exists():
            with path.open("rb") as handle:
                value = pickle.load(handle)
            reused.append(name)
        else:
            if stage_hook:
                stage_hook(name)
            value = action()
            with path.open("wb") as handle:
                pickle.dump(value, handle)
        stage_counts[name] = count(value)
        return value

    try:
        def acquire() -> dict[str, object]:
            listings = list(universe_provider.listings_as_of(market_id, week))
            if not listings:
                raise ValueError("US universe provider returned no eligible listings")
            filings: list[object] = []
            facts: list[object] = []
            for listing in listings:
                result = _call_facts(filing_provider, listing.security_id)
                if not getattr(result, "ok", False):
                    source_errors.append(_error_dict(getattr(result, "error", result), security_id=listing.security_id, stage=STAGES[0]))
                    continue
                filings.extend(getattr(result, "filings", ()))
                facts.extend(getattr(result, "facts", ()))
            if not facts:
                raise ValueError("filing provider returned no usable facts")
            upsert_regulatory_filings(connection, [_filing_row(item) for item in filings])
            upsert_regulatory_facts(connection, [_fact_row(item) for item in facts])
            return {"listings": tuple(listings), "filings": tuple(filings), "facts": tuple(facts)}

        acquired = stage(STAGES[0], acquire, lambda v: len(v["facts"]))

        def normalize() -> dict[str, object]:
            canonical = tuple(normalize_facts(acquired["facts"], "sec-v1"))
            fundamentals: dict[tuple[str, date], CompanyFundamentals] = {}
            pit_rows: list[dict[str, object]] = []
            for day in days:
                cutoff = datetime.combine(day, time(23, 59, tzinfo=UTC))
                for listing in acquired["listings"]:
                    facts_for_security = [fact for fact in canonical if fact.raw.security_id == listing.security_id]
                    if not facts_for_security:
                        continue
                    pit = fundamentals_as_of(listing.security_id, cutoff, facts_for_security)
                    fundamentals[(listing.security_id, day)] = CompanyFundamentals(pit)
                    for metric_name in ("revenue", "net_income", "common_equity", "operating_cash_flow", "capex", "free_cash_flow", "dividends"):
                        field = getattr(pit, metric_name)
                        pit_rows.append({
                            "security_id": listing.security_id, "valuation_date": day,
                            "methodology_version": methodology_version, "reporting_currency": field.unit or "USD",
                            "market_cap": None, "ttm_revenue": pit.ttm_revenue, "ttm_net_income": pit.ttm_net_income,
                            "common_equity": pit.common_equity.value, "ttm_operating_cash_flow": pit.ttm_operating_cash_flow,
                            "ttm_cash_capex": pit.ttm_capex, "ttm_free_cash_flow": pit.ttm_free_cash_flow,
                            "ttm_common_dividends": pit.ttm_dividends, "shares_outstanding": pit.period_end_shares.value,
                            "reported_fact_coverage": Decimal(1), "carried_forward_coverage": Decimal(0),
                            "imputed_coverage": Decimal(0), "missing_or_invalid_coverage": Decimal(0),
                            "source_lineage": [fact.raw.fact_id for fact in field.lineage.facts],
                            "structured_reasons": list(field.warnings),
                        })
            upsert_canonical_facts(connection, [{
                "canonical_fact_id": f"{fact.raw.filing_id}:{fact.raw.fact_id}:{fact.taxonomy_version}",
                "security_id": fact.raw.security_id, "concept_key": fact.metric or "unmapped",
                "taxonomy_version": fact.taxonomy_version, "value": fact.value, "unit": fact.unit,
                "period_start": fact.raw.period_start, "period_end": fact.raw.period_end,
                "instant_date": fact.raw.instant_date, "published_at": fact.raw.published_at,
                "availability_status": "accepted" if not fact.rejection_reasons else "rejected",
                "derivation_method": "reported", "source_lineage": [fact.raw.fact_id],
            } for fact in canonical])
            upsert_point_in_time_fundamentals(connection, pit_rows)
            return {"canonical": canonical, "fundamentals": fundamentals, "pit_rows": pit_rows}

        normalized = stage(STAGES[1], normalize, lambda v: len(v["canonical"]))

        def prices_and_fx() -> dict[str, object]:
            _license_guard(price_provider, environment)
            all_prices: list[DailyPrice] = []
            prices_by_security: dict[str, tuple[DailyPrice, ...]] = {}
            for listing in acquired["listings"]:
                rows = tuple(price_provider.daily_prices(listing, days[0], days[-1]))
                if not rows:
                    continue
                prices_by_security[listing.security_id] = rows
                all_prices.extend(rows)
            if not all_prices:
                raise ValueError("price provider returned no prices")
            states: dict[tuple[str, date], Mapping[str, object]] = {}
            for listing in acquired["listings"]:
                for price in prices_by_security.get(listing.security_id, ()):
                    if share_state is None:
                        raise ValueError("shares must come from an explicit reconciliation callback")
                    pit = normalized["fundamentals"].get((listing.security_id, price.trading_date))
                    states[(listing.security_id, price.trading_date)] = dict(share_state(listing, price.trading_date, pit, price))
                    if not states[(listing.security_id, price.trading_date)].get("shares_outstanding"):
                        raise ValueError("shares reconciliation returned no positive shares")
            fx_by_day: dict[date, ValuationFx] = {}
            currencies = {listing.trading_currency for listing in acquired["listings"]}
            for day in days:
                rates: tuple[FxRate, ...] = ()
                if currencies - {"USD"}:
                    if fx_provider is None:
                        raise ValueError("FX provider is required for non-USD listings")
                    rates = tuple(fx_provider.daily_rates("USD", "USD", day, day))
                fx_by_day[day] = ValuationFx("USD", rates)
            upsert_securities(connection, [{"security_id": l.security_id, "issuer_id": l.issuer_id, "issuer_name": l.issuer_name, "security_type": l.security_type, "share_class": l.share_class, "is_active": l.listing_status == "active"} for l in acquired["listings"]])
            upsert_security_listings(connection, [{"listing_id": l.listing_id, "security_id": l.security_id, "market_id": l.market_id, "exchange_code": l.exchange_code, "ticker": l.ticker, "trading_currency": l.trading_currency, "valid_from": l.valid_from, "valid_to": l.valid_to, "listing_status": l.listing_status, "source_provider": l.source_provider, "source_external_id": l.source_external_id} for l in acquired["listings"]])
            upsert_security_prices(connection, [_price_row(p) for p in all_prices])
            return {"prices": prices_by_security, "states": states, "fx": fx_by_day, "all_prices": tuple(all_prices)}

        priced = stage(STAGES[2], prices_and_fx, lambda v: len(v["all_prices"]))

        def cohorts() -> dict[str, object]:
            formation_day = days[0]
            candidates = []
            for listing in acquired["listings"]:
                rows = [p for p in priced["prices"].get(listing.security_id, ()) if p.trading_date == formation_day]
                state = priced["states"].get((listing.security_id, formation_day))
                if not rows or not state:
                    continue
                candidates.append(CohortCandidate(listing.security_id, rows[0].close_price * state["shares_outstanding"]))
            if not candidates:
                raise ValueError("no eligible universe candidates with reconciled shares")
            cohort = form_cohort(market_id, formation_day, candidates)
            upsert_country_cohorts(connection, [_cohort_row(cohort, methodology_version, formation_day)])
            upsert_country_cohort_members(connection, [{"market_id": market_id, "cohort_version": cohort.effective_date.isoformat(), "security_id": sid, "primary_listing_id": next(l.listing_id for l in acquired["listings"] if l.security_id == sid), "member_rank": rank, "market_cap_at_formation": next(c.market_cap for c in candidates if c.security_id == sid), "market_weight_at_formation": Decimal(1) / cohort.constituent_target_count, "membership_status": "active", "membership_reason": {"code": "formation"}} for rank, sid in enumerate(cohort.security_ids, 1)])
            return cohort

        cohort = stage(STAGES[3], cohorts, lambda v: len(v.security_ids))

        def daily() -> tuple[object, ...]:
            rows = []
            listing_by_id = {l.security_id: l for l in acquired["listings"]}
            for day in days:
                prices = []
                fundamentals = []
                for sid in cohort.security_ids:
                    listing = listing_by_id[sid]
                    price = next((p for p in priced["prices"].get(sid, ()) if p.trading_date == day), None)
                    if price is not None:
                        state = priced["states"][(sid, day)]
                        prices.append(ValuationPrice(price, state["shares_outstanding"], state.get("industry", "unknown"), state.get("revenue_comparable", False)))
                    company = normalized["fundamentals"].get((sid, day))
                    if company is not None:
                        fundamentals.append(company)
                if not prices:
                    continue
                rows.extend(calculate_daily_country_metrics(cohort, prices, fundamentals, priced["fx"][day], methodology_version))
            if not rows:
                raise ValueError("daily calculation produced no observations")
            return tuple(rows)

        daily_metrics = stage(STAGES[4], daily, len)

        def weekly() -> tuple[WeeklyCountryMetric, ...]:
            summaries = []
            for metric in METRICS:
                rows = [row for row in daily_metrics if row.metric == metric]
                if rows:
                    summaries.append(summarize_week(rows))
            return tuple(summaries)

        weekly_metrics = stage(STAGES[5], weekly, len)

        def sensitivity() -> dict[str, object]:
            result = {}
            for metric in METRICS:
                daily_row = next((row for row in daily_metrics if row.metric == metric), None)
                result[metric] = estimate_sensitivity(daily_row, cohort, seed=17, draws=sensitivity_draws) if daily_row else None
            return result

        sensitivity_results = stage(STAGES[6], sensitivity, lambda v: len(v))

        def validate() -> dict[str, object]:
            actual = tuple((row.market_id, row.metric, week) for row in weekly_metrics)
            if actual != expected_keys:
                raise PublicationInvariantError("manifest does not match expected weekly metric keys")
            if len(daily_metrics) != sum(metric.observation_count for metric in weekly_metrics):
                raise PublicationInvariantError("daily observations do not reconcile to weekly summaries")
            return {"expected_keys": expected_keys, "daily_rows": tuple(_daily_row(run_id, row, cohort) for row in daily_metrics), "weekly_rows": tuple(_weekly_row(run_id, row, sensitivity_results[row.metric], cohort) for row in weekly_metrics)}

        validated = stage(STAGES[7], validate, lambda v: len(v["weekly_rows"]))

        def persist() -> dict[str, object]:
            tx = getattr(connection, "transaction", None)
            with tx() if callable(tx) else nullcontext():
                now = (clock or (lambda: datetime.now(UTC)))()
                upsert_country_daily_metrics(connection, validated["daily_rows"])
                upsert_country_weekly_metrics(connection, validated["weekly_rows"])
                warning_rows = []
                for weekly_row in validated["weekly_rows"]:
                    for code in weekly_row["structured_reasons"]:
                        warning_rows.append({"run_id": run_id, "market_id": market_id, "metric_key": weekly_row["metric_key"], "week_id": week, "warning_code": code, "warning_level": "warning", "warning_message": code, "affected_market_weight": Decimal(0), "interval_width_contribution": None, "structured_reason": {"code": code}})
                upsert_country_metric_warnings(connection, warning_rows)
                upsert_country_index_runs(connection, [{"run_id": run_id, "methodology_version": methodology_version, "run_status": "completed", "started_at": started_at, "completed_at": now, "source_coverage": {"provider": "sec"}, "structured_reasons": []}])
                publish_completed_run(connection, run_id, expected_keys=expected_keys)
            return {"published": True}

        stage(STAGES[8], persist, lambda v: 1)
        return {"status": "success", "stage_counts": stage_counts, "reused_stages": reused,
                "publication_status": "published", "source_errors": source_errors,
                "source_warning_count": len(source_errors), "warning_count": sum(len(row["structured_reasons"]) for row in validated["weekly_rows"]) + len(source_errors),
                "previous_publication_preserved": False, "expected_keys": expected_keys}
    except Exception as exc:
        failed_stage = next((stage_name for stage_name in STAGES if stage_name not in stage_counts), STAGES[-1])
        publication_status = "blocked_license" if "license" in str(exc).lower() or "yahoo" in str(exc).lower() else "preserved"
        return {"status": "failed", "stage_counts": stage_counts, "reused_stages": reused,
                "publication_status": publication_status, "source_errors": source_errors,
                "source_warning_count": len(source_errors), "warning_count": len(source_errors),
                "previous_publication_preserved": True, "failed_stage": failed_stage,
                "failure_summary": str(exc), "errors": [str(exc)], "expected_keys": expected_keys}

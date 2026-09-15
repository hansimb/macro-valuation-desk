"""Idempotent persistence and atomic publication for country-index runs.

Rows are deliberately accepted as mappings.  Stage orchestration owns the
domain objects and supplies the schema-shaped records; this module owns the
database boundary, including JSONB adaptation and publication invariants.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
import json
from typing import Any


class CountryIndexContractError(ValueError):
    """A stage supplied a row that cannot be represented by the Task 1 schema."""


class PublicationInvariantError(RuntimeError):
    """A run is not complete enough to replace a current publication pointer."""


def _json_default(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def _json(value: object) -> str:
    return json.dumps(value, default=_json_default, separators=(",", ":"), sort_keys=True)


def _prepared_rows(
    rows: Iterable[Mapping[str, object]], *, required: tuple[str, ...], json_columns: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    prepared: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise CountryIndexContractError(f"row {index} must be a mapping")
        missing = tuple(column for column in required if column not in row)
        if missing:
            raise CountryIndexContractError(f"row {index} is missing schema columns: {', '.join(missing)}")
        value = dict(row)
        for column in json_columns:
            value[column] = _json(value[column])
        prepared.append(value)
    return prepared


def _executemany(connection: Any, query: str, rows: list[dict[str, object]]) -> None:
    if connection is None or not rows:
        return
    with connection.cursor() as cursor:
        cursor.executemany(query, rows)


_FILINGS = (
    "provider", "external_id", "content_hash", "jurisdiction", "filer_id", "filing_form", "filing_date",
    "accepted_at", "published_at", "amendment_of_external_id", "document_url", "content_json", "fetched_at",
)


def upsert_regulatory_filings(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    """Insert content-addressed filing documents without changing prior evidence."""
    values = _prepared_rows(rows, required=_FILINGS, json_columns=("content_json",))
    _executemany(connection, """
        insert into raw.regulatory_filings (
            provider, external_id, content_hash, jurisdiction, filer_id, filing_form, filing_date,
            accepted_at, published_at, amendment_of_external_id, document_url, content_json, fetched_at
        ) values (
            %(provider)s, %(external_id)s, %(content_hash)s, %(jurisdiction)s, %(filer_id)s, %(filing_form)s,
            %(filing_date)s, %(accepted_at)s, %(published_at)s, %(amendment_of_external_id)s, %(document_url)s,
            %(content_json)s::jsonb, %(fetched_at)s
        ) on conflict (provider, external_id, content_hash) do nothing
    """, values)


_FACTS = (
    "filing_provider", "filing_external_id", "filing_content_hash", "fact_id", "entity_id", "security_id",
    "taxonomy", "concept_name", "context_id", "dimensions_json", "unit", "decimals", "value_text",
    "period_start", "period_end", "instant_date", "is_consolidated", "is_continuing_operations",
)


def upsert_regulatory_facts(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    """Insert immutable extracted XBRL facts keyed by immutable filing content."""
    values = _prepared_rows(rows, required=_FACTS, json_columns=("dimensions_json",))
    _executemany(connection, """
        insert into raw.regulatory_facts (
            filing_provider, filing_external_id, filing_content_hash, fact_id, entity_id, security_id, taxonomy,
            concept_name, context_id, dimensions_json, unit, decimals, value_text, period_start, period_end,
            instant_date, is_consolidated, is_continuing_operations
        ) values (
            %(filing_provider)s, %(filing_external_id)s, %(filing_content_hash)s, %(fact_id)s, %(entity_id)s,
            %(security_id)s, %(taxonomy)s, %(concept_name)s, %(context_id)s, %(dimensions_json)s::jsonb, %(unit)s,
            %(decimals)s, %(value_text)s, %(period_start)s, %(period_end)s, %(instant_date)s, %(is_consolidated)s,
            %(is_continuing_operations)s
        ) on conflict (filing_provider, filing_external_id, filing_content_hash, fact_id) do nothing
    """, values)


_PRICES = (
    "security_id", "trading_date", "provider", "close_price", "split_adjusted_close_price", "trading_currency",
    "adjustment_metadata", "provider_timestamp", "license_class", "source_url",
)


def upsert_security_prices(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    """Insert immutable provider price observations with their provider timestamp intact."""
    values = _prepared_rows(rows, required=_PRICES, json_columns=("adjustment_metadata",))
    _executemany(connection, """
        insert into raw.security_prices (
            security_id, trading_date, provider, close_price, split_adjusted_close_price, trading_currency,
            adjustment_metadata, provider_timestamp, license_class, source_url
        ) values (
            %(security_id)s, %(trading_date)s, %(provider)s, %(close_price)s, %(split_adjusted_close_price)s,
            %(trading_currency)s, %(adjustment_metadata)s::jsonb, %(provider_timestamp)s, %(license_class)s,
            %(source_url)s
        ) on conflict (security_id, trading_date, provider) do nothing
    """, values)


def upsert_securities(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    values = _prepared_rows(rows, required=("security_id", "issuer_id", "issuer_name", "security_type", "share_class", "is_active"))
    _executemany(connection, """
        insert into core.securities (security_id, issuer_id, issuer_name, security_type, share_class, is_active)
        values (%(security_id)s, %(issuer_id)s, %(issuer_name)s, %(security_type)s, %(share_class)s, %(is_active)s)
        on conflict (security_id) do update set
            issuer_id = excluded.issuer_id, issuer_name = excluded.issuer_name,
            security_type = excluded.security_type, share_class = excluded.share_class,
            is_active = excluded.is_active, updated_at = now()
    """, values)


def upsert_security_listings(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    required = ("listing_id", "security_id", "market_id", "exchange_code", "ticker", "trading_currency", "valid_from", "valid_to", "listing_status", "source_provider", "source_external_id")
    values = _prepared_rows(rows, required=required)
    _executemany(connection, """
        insert into core.security_listings (
            listing_id, security_id, market_id, exchange_code, ticker, trading_currency, valid_from, valid_to,
            listing_status, source_provider, source_external_id
        ) values (
            %(listing_id)s, %(security_id)s, %(market_id)s, %(exchange_code)s, %(ticker)s, %(trading_currency)s,
            %(valid_from)s, %(valid_to)s, %(listing_status)s, %(source_provider)s, %(source_external_id)s
        ) on conflict (listing_id) do update set
            exchange_code = excluded.exchange_code, ticker = excluded.ticker,
            trading_currency = excluded.trading_currency, valid_from = excluded.valid_from, valid_to = excluded.valid_to,
            listing_status = excluded.listing_status, source_provider = excluded.source_provider,
            source_external_id = excluded.source_external_id
        where core.security_listings.security_id = excluded.security_id
          and core.security_listings.market_id = excluded.market_id
    """, values)


def upsert_primary_security_listings(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    values = _prepared_rows(rows, required=("security_id", "market_id", "listing_id", "effective_from", "effective_to"))
    _executemany(connection, """
        insert into core.primary_security_listings (security_id, market_id, listing_id, effective_from, effective_to)
        values (%(security_id)s, %(market_id)s, %(listing_id)s, %(effective_from)s, %(effective_to)s)
        on conflict (listing_id) do update set effective_from = excluded.effective_from, effective_to = excluded.effective_to
        where core.primary_security_listings.security_id = excluded.security_id
          and core.primary_security_listings.market_id = excluded.market_id
    """, values)


def upsert_canonical_facts(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    required = ("canonical_fact_id", "security_id", "concept_key", "taxonomy_version", "value", "unit", "period_start", "period_end", "instant_date", "published_at", "availability_status", "derivation_method", "source_lineage")
    values = _prepared_rows(rows, required=required, json_columns=("source_lineage",))
    _executemany(connection, """
        insert into core.canonical_facts (
            canonical_fact_id, security_id, concept_key, taxonomy_version, value, unit, period_start, period_end,
            instant_date, published_at, availability_status, derivation_method, source_lineage
        ) values (
            %(canonical_fact_id)s, %(security_id)s, %(concept_key)s, %(taxonomy_version)s, %(value)s, %(unit)s,
            %(period_start)s, %(period_end)s, %(instant_date)s, %(published_at)s, %(availability_status)s,
            %(derivation_method)s, %(source_lineage)s::jsonb
        ) on conflict (canonical_fact_id) do update set
            value = excluded.value, unit = excluded.unit, period_start = excluded.period_start,
            period_end = excluded.period_end, instant_date = excluded.instant_date, published_at = excluded.published_at,
            availability_status = excluded.availability_status, derivation_method = excluded.derivation_method,
            source_lineage = excluded.source_lineage
        where core.canonical_facts.security_id = excluded.security_id
          and core.canonical_facts.concept_key = excluded.concept_key
          and core.canonical_facts.taxonomy_version = excluded.taxonomy_version
    """, values)


def upsert_country_cohorts(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    required = ("market_id", "cohort_version", "effective_from", "effective_to", "target_coverage_lower", "target_coverage_upper", "achieved_market_coverage", "constituent_target_count", "cohort_status", "structured_reasons", "methodology_version")
    values = _prepared_rows(rows, required=required, json_columns=("structured_reasons",))
    _executemany(connection, """
        insert into core.country_cohorts (
            market_id, cohort_version, effective_from, effective_to, target_coverage_lower, target_coverage_upper,
            achieved_market_coverage, constituent_target_count, cohort_status, structured_reasons, methodology_version
        ) values (
            %(market_id)s, %(cohort_version)s, %(effective_from)s, %(effective_to)s, %(target_coverage_lower)s,
            %(target_coverage_upper)s, %(achieved_market_coverage)s, %(constituent_target_count)s,
            %(cohort_status)s, %(structured_reasons)s::jsonb, %(methodology_version)s
        ) on conflict (market_id, cohort_version) do update set
            effective_from = excluded.effective_from, effective_to = excluded.effective_to,
            target_coverage_lower = excluded.target_coverage_lower, target_coverage_upper = excluded.target_coverage_upper,
            achieved_market_coverage = excluded.achieved_market_coverage,
            constituent_target_count = excluded.constituent_target_count, cohort_status = excluded.cohort_status,
            structured_reasons = excluded.structured_reasons
        where core.country_cohorts.methodology_version = excluded.methodology_version
    """, values)


def upsert_country_cohort_members(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    required = ("market_id", "cohort_version", "security_id", "primary_listing_id", "member_rank", "market_cap_at_formation", "market_weight_at_formation", "membership_status", "membership_reason")
    values = _prepared_rows(rows, required=required, json_columns=("membership_reason",))
    _executemany(connection, """
        insert into core.country_cohort_members (
            market_id, cohort_version, security_id, primary_listing_id, member_rank, market_cap_at_formation,
            market_weight_at_formation, membership_status, membership_reason
        ) values (
            %(market_id)s, %(cohort_version)s, %(security_id)s, %(primary_listing_id)s, %(member_rank)s,
            %(market_cap_at_formation)s, %(market_weight_at_formation)s, %(membership_status)s,
            %(membership_reason)s::jsonb
        ) on conflict (market_id, cohort_version, security_id) do update set
            primary_listing_id = excluded.primary_listing_id, member_rank = excluded.member_rank,
            market_cap_at_formation = excluded.market_cap_at_formation,
            market_weight_at_formation = excluded.market_weight_at_formation,
            membership_status = excluded.membership_status, membership_reason = excluded.membership_reason
    """, values)


def upsert_point_in_time_fundamentals(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    required = ("security_id", "valuation_date", "methodology_version", "reporting_currency", "market_cap", "ttm_revenue", "ttm_net_income", "common_equity", "ttm_operating_cash_flow", "ttm_cash_capex", "ttm_free_cash_flow", "ttm_common_dividends", "shares_outstanding", "reported_fact_coverage", "carried_forward_coverage", "imputed_coverage", "missing_or_invalid_coverage", "source_lineage", "structured_reasons")
    values = _prepared_rows(rows, required=required, json_columns=("source_lineage", "structured_reasons"))
    _executemany(connection, """
        insert into core.point_in_time_fundamentals (
            security_id, valuation_date, methodology_version, reporting_currency, market_cap, ttm_revenue,
            ttm_net_income, common_equity, ttm_operating_cash_flow, ttm_cash_capex, ttm_free_cash_flow,
            ttm_common_dividends, shares_outstanding, reported_fact_coverage, carried_forward_coverage,
            imputed_coverage, missing_or_invalid_coverage, source_lineage, structured_reasons
        ) values (
            %(security_id)s, %(valuation_date)s, %(methodology_version)s, %(reporting_currency)s, %(market_cap)s,
            %(ttm_revenue)s, %(ttm_net_income)s, %(common_equity)s, %(ttm_operating_cash_flow)s,
            %(ttm_cash_capex)s, %(ttm_free_cash_flow)s, %(ttm_common_dividends)s, %(shares_outstanding)s,
            %(reported_fact_coverage)s, %(carried_forward_coverage)s, %(imputed_coverage)s,
            %(missing_or_invalid_coverage)s, %(source_lineage)s::jsonb, %(structured_reasons)s::jsonb
        ) on conflict (security_id, valuation_date, methodology_version) do update set
            reporting_currency = excluded.reporting_currency, market_cap = excluded.market_cap,
            ttm_revenue = excluded.ttm_revenue, ttm_net_income = excluded.ttm_net_income,
            common_equity = excluded.common_equity, ttm_operating_cash_flow = excluded.ttm_operating_cash_flow,
            ttm_cash_capex = excluded.ttm_cash_capex, ttm_free_cash_flow = excluded.ttm_free_cash_flow,
            ttm_common_dividends = excluded.ttm_common_dividends, shares_outstanding = excluded.shares_outstanding,
            reported_fact_coverage = excluded.reported_fact_coverage,
            carried_forward_coverage = excluded.carried_forward_coverage, imputed_coverage = excluded.imputed_coverage,
            missing_or_invalid_coverage = excluded.missing_or_invalid_coverage,
            source_lineage = excluded.source_lineage, structured_reasons = excluded.structured_reasons
    """, values)


def upsert_country_index_runs(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    required = ("run_id", "methodology_version", "run_status", "started_at", "completed_at", "source_coverage", "structured_reasons")
    values = _prepared_rows(rows, required=required, json_columns=("source_coverage", "structured_reasons"))
    _executemany(connection, """
        insert into core.country_index_runs (
            run_id, methodology_version, run_status, started_at, completed_at, source_coverage, structured_reasons
        ) values (
            %(run_id)s, %(methodology_version)s, %(run_status)s, %(started_at)s, %(completed_at)s,
            %(source_coverage)s::jsonb, %(structured_reasons)s::jsonb
        ) on conflict (run_id) do update set run_status = excluded.run_status, completed_at = excluded.completed_at,
            source_coverage = excluded.source_coverage, structured_reasons = excluded.structured_reasons
        where core.country_index_runs.methodology_version = excluded.methodology_version
    """, values)


_DAILY = (
    "run_id", "market_id", "metric_key", "valuation_date", "cohort_version", "methodology_version", "metric_value",
    "value_currency", "metric_status", "market_coverage", "reported_fact_coverage", "carried_forward_coverage",
    "imputed_coverage", "missing_or_invalid_coverage", "metric_eligible_coverage", "actual_constituent_count",
    "cohort_target_count", "effective_constituent_count", "largest_constituent_weight", "top_five_concentration",
    "top_ten_concentration", "membership_overlap", "interval_lower", "interval_upper", "source_coverage", "structured_reasons",
)


def upsert_country_daily_metrics(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    values = _prepared_rows(rows, required=_DAILY, json_columns=("source_coverage", "structured_reasons"))
    _executemany(connection, """
        insert into core.country_daily_metrics (
            run_id, market_id, metric_key, valuation_date, cohort_version, methodology_version, metric_value,
            value_currency, metric_status, market_coverage, reported_fact_coverage, carried_forward_coverage,
            imputed_coverage, missing_or_invalid_coverage, metric_eligible_coverage, actual_constituent_count,
            cohort_target_count, effective_constituent_count, largest_constituent_weight, top_five_concentration,
            top_ten_concentration, membership_overlap, interval_lower, interval_upper, source_coverage,
            structured_reasons
        ) values (
            %(run_id)s, %(market_id)s, %(metric_key)s, %(valuation_date)s, %(cohort_version)s,
            %(methodology_version)s, %(metric_value)s, %(value_currency)s, %(metric_status)s, %(market_coverage)s,
            %(reported_fact_coverage)s, %(carried_forward_coverage)s, %(imputed_coverage)s,
            %(missing_or_invalid_coverage)s, %(metric_eligible_coverage)s, %(actual_constituent_count)s,
            %(cohort_target_count)s, %(effective_constituent_count)s, %(largest_constituent_weight)s,
            %(top_five_concentration)s, %(top_ten_concentration)s, %(membership_overlap)s, %(interval_lower)s,
            %(interval_upper)s, %(source_coverage)s::jsonb, %(structured_reasons)s::jsonb
        ) on conflict (run_id, market_id, metric_key, valuation_date) do update set
            metric_value = excluded.metric_value, value_currency = excluded.value_currency,
            metric_status = excluded.metric_status, market_coverage = excluded.market_coverage,
            reported_fact_coverage = excluded.reported_fact_coverage,
            carried_forward_coverage = excluded.carried_forward_coverage,
            imputed_coverage = excluded.imputed_coverage,
            missing_or_invalid_coverage = excluded.missing_or_invalid_coverage,
            metric_eligible_coverage = excluded.metric_eligible_coverage,
            actual_constituent_count = excluded.actual_constituent_count,
            cohort_target_count = excluded.cohort_target_count,
            effective_constituent_count = excluded.effective_constituent_count,
            largest_constituent_weight = excluded.largest_constituent_weight,
            top_five_concentration = excluded.top_five_concentration,
            top_ten_concentration = excluded.top_ten_concentration,
            membership_overlap = excluded.membership_overlap, interval_lower = excluded.interval_lower,
            interval_upper = excluded.interval_upper, source_coverage = excluded.source_coverage,
            structured_reasons = excluded.structured_reasons
        where core.country_daily_metrics.methodology_version = excluded.methodology_version
          and core.country_daily_metrics.cohort_version = excluded.cohort_version
    """, values)


_WEEKLY = (
    "run_id", "market_id", "metric_key", "week_id", "cohort_version", "methodology_version", "metric_value",
    "weekly_min_value", "weekly_max_value", "valuation_dates", "daily_observation_count", "metric_status",
    "market_coverage", "reported_fact_coverage", "carried_forward_coverage", "imputed_coverage",
    "missing_or_invalid_coverage", "metric_eligible_coverage", "actual_constituent_count", "cohort_target_count",
    "effective_constituent_count", "largest_constituent_weight", "top_five_concentration",
    "top_ten_concentration", "membership_overlap", "interval_lower", "interval_upper", "source_coverage",
    "structured_reasons",
)


def upsert_country_weekly_metrics(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    values = _prepared_rows(rows, required=_WEEKLY, json_columns=("source_coverage", "structured_reasons"))
    _executemany(connection, """
        insert into core.country_weekly_metrics (
            run_id, market_id, metric_key, week_id, cohort_version, methodology_version, metric_value,
            weekly_min_value, weekly_max_value, valuation_dates, daily_observation_count, metric_status,
            market_coverage, reported_fact_coverage, carried_forward_coverage, imputed_coverage,
            missing_or_invalid_coverage, metric_eligible_coverage, actual_constituent_count, cohort_target_count,
            effective_constituent_count, largest_constituent_weight, top_five_concentration,
            top_ten_concentration, membership_overlap, interval_lower, interval_upper, source_coverage,
            structured_reasons
        ) values (
            %(run_id)s, %(market_id)s, %(metric_key)s, %(week_id)s, %(cohort_version)s, %(methodology_version)s,
            %(metric_value)s, %(weekly_min_value)s, %(weekly_max_value)s, %(valuation_dates)s,
            %(daily_observation_count)s, %(metric_status)s, %(market_coverage)s, %(reported_fact_coverage)s,
            %(carried_forward_coverage)s, %(imputed_coverage)s, %(missing_or_invalid_coverage)s,
            %(metric_eligible_coverage)s, %(actual_constituent_count)s, %(cohort_target_count)s,
            %(effective_constituent_count)s, %(largest_constituent_weight)s, %(top_five_concentration)s,
            %(top_ten_concentration)s, %(membership_overlap)s, %(interval_lower)s, %(interval_upper)s,
            %(source_coverage)s::jsonb, %(structured_reasons)s::jsonb
        ) on conflict (run_id, market_id, metric_key, week_id) do update set
            metric_value = excluded.metric_value, weekly_min_value = excluded.weekly_min_value,
            weekly_max_value = excluded.weekly_max_value, valuation_dates = excluded.valuation_dates,
            daily_observation_count = excluded.daily_observation_count, metric_status = excluded.metric_status,
            market_coverage = excluded.market_coverage, reported_fact_coverage = excluded.reported_fact_coverage,
            carried_forward_coverage = excluded.carried_forward_coverage, imputed_coverage = excluded.imputed_coverage,
            missing_or_invalid_coverage = excluded.missing_or_invalid_coverage,
            metric_eligible_coverage = excluded.metric_eligible_coverage,
            actual_constituent_count = excluded.actual_constituent_count,
            cohort_target_count = excluded.cohort_target_count,
            effective_constituent_count = excluded.effective_constituent_count,
            largest_constituent_weight = excluded.largest_constituent_weight,
            top_five_concentration = excluded.top_five_concentration,
            top_ten_concentration = excluded.top_ten_concentration,
            membership_overlap = excluded.membership_overlap, interval_lower = excluded.interval_lower,
            interval_upper = excluded.interval_upper, source_coverage = excluded.source_coverage,
            structured_reasons = excluded.structured_reasons
        where core.country_weekly_metrics.methodology_version = excluded.methodology_version
          and core.country_weekly_metrics.cohort_version = excluded.cohort_version
    """, values)


def upsert_country_metric_warnings(connection: Any, rows: Iterable[Mapping[str, object]]) -> None:
    required = ("run_id", "market_id", "metric_key", "week_id", "warning_code", "warning_level", "warning_message", "affected_market_weight", "interval_width_contribution", "structured_reason")
    values = _prepared_rows(rows, required=required, json_columns=("structured_reason",))
    _executemany(connection, """
        insert into core.country_metric_warnings (
            run_id, market_id, metric_key, week_id, warning_code, warning_level, warning_message,
            affected_market_weight, interval_width_contribution, structured_reason
        ) values (
            %(run_id)s, %(market_id)s, %(metric_key)s, %(week_id)s, %(warning_code)s, %(warning_level)s,
            %(warning_message)s, %(affected_market_weight)s, %(interval_width_contribution)s,
            %(structured_reason)s::jsonb
        ) on conflict (run_id, market_id, metric_key, week_id, warning_code) do update set
            warning_level = excluded.warning_level, warning_message = excluded.warning_message,
            affected_market_weight = excluded.affected_market_weight,
            interval_width_contribution = excluded.interval_width_contribution,
            structured_reason = excluded.structured_reason
    """, values)


@contextmanager
def _publication_transaction(connection: Any):
    """Use psycopg's nested-safe transaction API, with a small test-double fallback."""
    transaction = getattr(connection, "transaction", None)
    if callable(transaction):
        with transaction():
            yield
        return
    with connection.cursor() as cursor:
        cursor.execute("begin")
    try:
        yield
    except BaseException:
        with connection.cursor() as cursor:
            cursor.execute("rollback")
        raise
    else:
        with connection.cursor() as cursor:
            cursor.execute("commit")


def _mapping_row(row: object, *, query: str) -> Mapping[str, object]:
    if not isinstance(row, Mapping):
        raise PublicationInvariantError(f"{query} must return mapping rows; configure psycopg dict_row")
    return row


def _expected_key(row: object) -> tuple[object, object, object]:
    if isinstance(row, Mapping):
        try:
            return (row["market_id"], row["metric_key"], row["week_id"])
        except KeyError as exc:
            raise PublicationInvariantError("expected weekly market/metric query returned an incomplete row") from exc
    if isinstance(row, tuple) and len(row) == 3:
        return row
    raise PublicationInvariantError("expected weekly market/metric query returned an unsupported row")


def _require_weekly_invariants(row: Mapping[str, object], methodology_version: object) -> tuple[object, object, object]:
    required = ("market_id", "metric_key", "week_id", "methodology_version", "metric_value", "weekly_min_value", "weekly_max_value", "valuation_dates", "daily_observation_count", "metric_status", "source_coverage", "structured_reasons")
    missing = tuple(column for column in required if column not in row)
    if missing:
        raise PublicationInvariantError(f"weekly metric row is missing required lineage/status columns: {', '.join(missing)}")
    if row["methodology_version"] != methodology_version:
        raise PublicationInvariantError("weekly metric methodology does not match its run")
    status = row["metric_status"]
    if status not in {"complete", "warning", "unavailable"}:
        raise PublicationInvariantError("completed run contains a failed or unknown weekly metric status")
    if not isinstance(row["source_coverage"], Mapping):
        raise PublicationInvariantError("weekly metric source_coverage must preserve object lineage")
    reasons = row["structured_reasons"]
    if not isinstance(reasons, (list, tuple)):
        raise PublicationInvariantError("weekly metric structured_reasons must preserve an ordered reason list")
    dates = row["valuation_dates"]
    count = row["daily_observation_count"]
    if not isinstance(dates, (list, tuple)) or isinstance(count, bool) or not isinstance(count, int) or count != len(dates):
        raise PublicationInvariantError("weekly metric daily observation count must match its valuation dates")
    value, minimum, maximum = row["metric_value"], row["weekly_min_value"], row["weekly_max_value"]
    if status in {"complete", "warning"}:
        if count < 3 or value is None or minimum is None or maximum is None:
            raise PublicationInvariantError("publishable weekly metrics require three valid daily observations and a range")
        try:
            if minimum > maximum or value < minimum or value > maximum:
                raise PublicationInvariantError("weekly metric value must lie inside its recorded daily range")
        except TypeError as exc:
            raise PublicationInvariantError("weekly metric range values are not comparable") from exc
    elif value is not None or not reasons:
        raise PublicationInvariantError("unavailable weekly metrics require no value and a structured reason")
    return (row["market_id"], row["metric_key"], row["week_id"])


def publish_completed_run(connection: Any, run_id: str) -> None:
    """Atomically replace current pointers only after a complete run reconciles.

    The expected market/metric/week set is the persisted daily set for the run;
    there is no separate expectation table in the Task 1 schema.  The global
    transaction advisory lock serializes competing pointer swaps while allowing
    independent immutable stage writes to continue.
    """
    if connection is None:
        raise PublicationInvariantError("a database connection is required to publish a run")
    if not isinstance(run_id, str) or not run_id:
        raise CountryIndexContractError("run_id must be a non-empty string")

    with _publication_transaction(connection):
        with connection.cursor() as cursor:
            cursor.execute("select pg_advisory_xact_lock(hashtext('marts.country_index_publications'))")
            cursor.execute("""
                select run_id, methodology_version, run_status, completed_at
                from core.country_index_runs
                where run_id = %(run_id)s
                for update
            """, {"run_id": run_id})
            run = cursor.fetchone()
            if not run:
                raise PublicationInvariantError("country-index run does not exist")
            run = _mapping_row(run, query="country-index run")
            if run.get("run_status") != "completed" or run.get("completed_at") is None:
                raise PublicationInvariantError("only a completed run with completed_at may publish")
            methodology_version = run.get("methodology_version")
            if not isinstance(methodology_version, str) or not methodology_version:
                raise PublicationInvariantError("completed run has no methodology version")

            cursor.execute("""
                select distinct daily.market_id, daily.metric_key,
                    date_trunc('week', daily.valuation_date)::date as week_id
                from core.country_daily_metrics as daily
                where daily.run_id = %(run_id)s
                  and daily.methodology_version = %(methodology_version)s
                order by daily.market_id, daily.metric_key, week_id
            """, {"run_id": run_id, "methodology_version": methodology_version})
            expected = {_expected_key(row) for row in cursor.fetchall()}
            if not expected:
                raise PublicationInvariantError("completed run has no expected daily market/metric weeks")

            cursor.execute("""
                select market_id, metric_key, week_id, cohort_version, methodology_version, metric_value,
                    weekly_min_value, weekly_max_value, valuation_dates, daily_observation_count, metric_status,
                    market_coverage, reported_fact_coverage, carried_forward_coverage, imputed_coverage,
                    missing_or_invalid_coverage, metric_eligible_coverage, actual_constituent_count,
                    cohort_target_count, effective_constituent_count, largest_constituent_weight,
                    top_five_concentration, top_ten_concentration, membership_overlap, interval_lower,
                    interval_upper, source_coverage, structured_reasons
                from core.country_weekly_metrics
                where run_id = %(run_id)s
                order by market_id, metric_key, week_id
            """, {"run_id": run_id})
            weekly = [_mapping_row(row, query="country weekly metrics") for row in cursor.fetchall()]
            actual = {_require_weekly_invariants(row, methodology_version) for row in weekly}
            if actual != expected:
                raise PublicationInvariantError("completed run is missing expected weekly market/metric rows or contains extras")

            cursor.execute("""
                update marts.country_index_publications as publication
                set is_current = false
                where publication.is_current
                  and exists (
                    select 1
                    from core.country_weekly_metrics as weekly
                    where weekly.run_id = %(run_id)s
                      and weekly.market_id = publication.market_id
                      and weekly.metric_key = publication.metric_key
                      and weekly.week_id = publication.week_id
                  )
            """, {"run_id": run_id})
            cursor.execute("""
                insert into marts.country_index_publications (
                    run_id, market_id, metric_key, week_id, published_at, is_current, publication_metadata
                )
                select weekly.run_id, weekly.market_id, weekly.metric_key, weekly.week_id, now(), true, '{}'::jsonb
                from core.country_weekly_metrics as weekly
                where weekly.run_id = %(run_id)s
                on conflict (run_id, market_id, metric_key, week_id) do update
                set is_current = true
            """, {"run_id": run_id})

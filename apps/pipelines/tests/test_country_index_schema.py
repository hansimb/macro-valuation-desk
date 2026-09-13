from __future__ import annotations

import re

from src.lib.db.schema import SCHEMA_FILES, _schema_sql


def _compact(sql: str) -> str:
    return " ".join(sql.lower().split())


def _table_definition(sql: str, table_name: str) -> str:
    table_start = sql.index(f"create table if not exists {table_name}")
    return sql[table_start : sql.index(" );", table_start) + 2]


def test_country_index_schema_runs_after_legacy_valuation_schema():
    assert SCHEMA_FILES[-1] == "040_mvd_country_indices.sql"


def test_country_index_schema_preserves_source_and_version_lineage_constraints():
    sql = _compact(_schema_sql())

    for table_name in (
        "raw.regulatory_filings",
        "raw.regulatory_facts",
        "raw.security_prices",
        "core.securities",
        "core.security_listings",
        "core.canonical_facts",
        "core.country_cohorts",
        "core.country_cohort_members",
        "core.point_in_time_fundamentals",
        "core.country_daily_metrics",
        "core.country_weekly_metrics",
        "core.country_metric_warnings",
        "core.country_index_runs",
        "marts.country_index_publications",
    ):
        assert f"create table if not exists {table_name}" in sql

    for primary_key in (
        "primary key (provider, external_id, content_hash)",
        "primary key (filing_provider, filing_external_id, filing_content_hash, fact_id)",
        "primary key (security_id, trading_date, provider)",
        "primary key (market_id, cohort_version, security_id)",
        "primary key (run_id, market_id, metric_key, valuation_date)",
        "primary key (run_id, market_id, metric_key, week_id)",
        "primary key (run_id)",
        "primary key (run_id, market_id, metric_key, week_id, warning_code)",
    ):
        assert primary_key in sql

    cohort_parent_key = "foreign key (market_id, cohort_version) references core.country_cohorts (market_id, cohort_version)"
    assert sql.count(cohort_parent_key) >= 2
    assert "foreign key (run_id) references core.country_index_runs (run_id)" in sql


def test_country_index_publications_are_lineage_pointers_to_weekly_metrics():
    publication = _table_definition(_compact(_schema_sql()), "marts.country_index_publications")

    for duplicated_metric_field in ("cohort_version", "methodology_version", "metric_value", "metric_status"):
        assert duplicated_metric_field not in publication

    assert (
        "foreign key (run_id, market_id, metric_key, week_id) "
        "references core.country_weekly_metrics (run_id, market_id, metric_key, week_id)"
    ) in publication


def test_country_cohort_members_require_the_security_primary_listing_market():
    sql = _compact(_schema_sql())
    primary_listing = _table_definition(sql, "core.primary_security_listings")
    membership = _table_definition(sql, "core.country_cohort_members")

    assert "foreign key (listing_id, security_id, market_id) references core.security_listings (listing_id, security_id, market_id)" in primary_listing
    assert "primary key (listing_id)" in primary_listing
    assert "primary key (security_id)" not in primary_listing
    assert "unique (listing_id, security_id, market_id)" in primary_listing
    assert "primary_listing_id text not null" in membership
    assert (
        "foreign key (primary_listing_id, security_id, market_id) "
        "references core.primary_security_listings (listing_id, security_id, market_id)"
    ) in membership


def test_primary_listing_intervals_and_cohort_membership_coverage_are_enforced():
    sql = _compact(_schema_sql())
    primary_listing = _table_definition(sql, "core.primary_security_listings")

    assert "effective_from date not null" in primary_listing
    assert "effective_to date" in primary_listing
    assert "check (effective_to is null or effective_to >= effective_from)" in primary_listing
    assert "create or replace function core.assert_primary_listing_intervals_do_not_overlap()" in sql
    assert "daterange(other.effective_from, other.effective_to, '[]') && daterange(new.effective_from, new.effective_to, '[]')" in sql
    assert "create constraint trigger primary_security_listing_non_overlapping" in sql
    assert "deferrable initially immediate" in sql
    assert "create or replace function core.assert_cohort_member_listing_coverage()" in sql
    assert "primary_listing.effective_from <= cohort.effective_from" in sql
    assert re.search(
        r"\(\s*primary_listing\.effective_to is null\s+or\s+"
        r"primary_listing\.effective_to >= cohort\.effective_from\s*\)",
        sql,
    )

    for trigger_name in (
        "country_cohort_member_primary_listing_coverage",
        "primary_security_listing_membership_coverage",
        "country_cohort_membership_listing_coverage",
    ):
        assert f"create constraint trigger {trigger_name}" in sql

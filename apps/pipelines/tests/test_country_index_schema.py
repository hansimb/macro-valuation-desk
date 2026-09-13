from __future__ import annotations

from src.lib.db.schema import SCHEMA_FILES, _schema_sql


def _compact(sql: str) -> str:
    return " ".join(sql.lower().split())


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
    assert sql.count(cohort_parent_key) >= 3
    assert "foreign key (run_id) references core.country_index_runs (run_id)" in sql

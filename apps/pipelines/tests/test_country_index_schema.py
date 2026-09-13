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


def test_primary_mapping_must_fit_its_exact_underlying_listing_on_both_write_paths():
    sql = _compact(_schema_sql())
    marker = "create or replace function core.assert_primary_listing_validity_coverage()"
    assert marker in sql
    coverage = sql[sql.index(marker) : sql.index("$$;", sql.index(marker))]

    for condition in (
        "listing.listing_id = primary_listing.listing_id",
        "listing.security_id = primary_listing.security_id",
        "listing.market_id = primary_listing.market_id",
        "primary_listing.listing_id = new.listing_id",
        "primary_listing.effective_from < listing.valid_from",
        "listing.valid_to is not null",
        "primary_listing.effective_to is null or primary_listing.effective_to > listing.valid_to",
        "raise exception",
        "for share",
    ):
        assert condition in coverage

    for trigger_name, table_name in (
        ("primary_security_listing_validity_coverage", "core.primary_security_listings"),
        ("security_listing_primary_validity_coverage", "core.security_listings"),
    ):
        assert f"drop trigger if exists {trigger_name} on {table_name}" in sql
        assert (
            f"create constraint trigger {trigger_name} after insert or update on {table_name} "
            "deferrable initially immediate for each row "
            "execute function core.assert_primary_listing_validity_coverage()"
        ) in sql


def test_prior_primary_listing_shapes_are_backfilled_before_functions_use_new_columns():
    sql = _compact(_schema_sql())
    function_start = sql.index("create or replace function core.assert_primary_listing_intervals_do_not_overlap()")
    migration = sql[:function_start]

    assert "add column if not exists effective_from date" in migration
    assert "add column if not exists effective_to date" in migration
    assert (
        "update core.primary_security_listings as primary_listing "
        "set effective_from = listing.valid_from, effective_to = listing.valid_to "
        "from core.security_listings as listing"
    ) in migration
    for identity in ("listing_id", "security_id", "market_id"):
        assert f"primary_listing.{identity} = listing.{identity}" in migration
    assert "and primary_listing.effective_from is null" in migration
    assert "alter column effective_from set not null" in migration
    assert "add constraint primary_security_listings_check check (effective_to is null or effective_to >= effective_from)" in migration
    assert "pg_constraint" in migration
    assert "conrelid = 'core.primary_security_listings'::regclass" in migration


def test_legacy_member_keys_are_replaced_without_losing_recorded_listing_identity():
    sql = _compact(_schema_sql())
    assert "add column if not exists primary_listing_id text" in sql
    assert "set primary_listing_id = ( select primary_listing.listing_id" in sql
    assert "where member.primary_listing_id is null" in sql
    assert "primary_listing.security_id = member.security_id" in sql
    assert "primary_listing.market_id = member.market_id" in sql
    assert "primary_listing.effective_from <= cohort.effective_from" in sql
    assert "alter column primary_listing_id set not null" in sql
    assert "limit 1" not in sql  # An ambiguous historical identity must fail, not pick a row.

    drop_old_fk = sql.index("drop constraint if exists country_cohort_members_market_id_security_id_fkey")
    drop_old_unique = sql.index("drop constraint if exists primary_security_listings_market_id_security_id_key")
    drop_old_pk = sql.index("drop constraint primary_security_listings_pkey")
    assert drop_old_fk < drop_old_unique < drop_old_pk
    assert "pg_get_constraintdef(oid) = 'primary key (security_id)'" in sql
    assert "add constraint primary_security_listings_pkey primary key (listing_id)" in sql
    assert (
        "add constraint country_cohort_members_primary_listing_fkey "
        "foreign key (primary_listing_id, security_id, market_id) "
        "references core.primary_security_listings (listing_id, security_id, market_id)"
    ) in sql


def test_migration_revalidates_existing_intervals_and_cohort_dates():
    sql = _compact(_schema_sql())
    marker = "do $validate_primary_listing_history$"
    assert marker in sql
    validation = sql[sql.index(marker) : sql.index("$validate_primary_listing_history$;", sql.index(marker))]
    for condition in (
        "primary_listing.effective_from < listing.valid_from",
        "primary_listing.effective_to is null or primary_listing.effective_to > listing.valid_to",
        "other.security_id = primary_listing.security_id",
        "other.listing_id <> primary_listing.listing_id",
        "daterange(other.effective_from, other.effective_to, '[]') && daterange(primary_listing.effective_from, primary_listing.effective_to, '[]')",
        "primary_listing.listing_id = member.primary_listing_id",
        "primary_listing.effective_from <= cohort.effective_from",
        "primary_listing.effective_to >= cohort.effective_from",
    ):
        assert condition in validation
    assert validation.count("raise exception") == 3


def test_original_listing_flags_migrate_to_explicit_historical_mappings():
    sql = _compact(_schema_sql())
    marker = "do $upgrade_primary_listing_flags$"
    assert marker in sql
    migration = sql[sql.index(marker) : sql.index("$upgrade_primary_listing_flags$;", sql.index(marker))]
    assert "attrelid = 'core.security_listings'::regclass" in migration
    assert "attname = 'is_primary' and not attisdropped" in migration
    assert (
        "insert into core.primary_security_listings (security_id, market_id, listing_id, effective_from, effective_to) "
        "select security_id, market_id, listing_id, valid_from, valid_to "
        "from core.security_listings where is_primary on conflict (listing_id) do nothing"
    ) in migration
    assert "alter table core.security_listings drop column is_primary" in migration
    assert sql.index("add constraint primary_security_listings_pkey primary key (listing_id)") < sql.index(marker)
    assert sql.index(marker) < sql.index("set primary_listing_id = (")


def test_original_publication_duplicates_are_archived_then_removed_on_upgrade():
    sql = _compact(_schema_sql())
    marker = "do $upgrade_publication_pointer$"
    assert marker in sql
    migration = sql[sql.index(marker) : sql.index("$upgrade_publication_pointer$;", sql.index(marker))]
    assert "attrelid = 'marts.country_index_publications'::regclass" in migration
    assert "attname = 'cohort_version' and not attisdropped" in migration
    assert "publication_metadata = publication_metadata || jsonb_build_object(" in migration
    for field in ("cohort_version", "methodology_version", "metric_value", "metric_status"):
        assert f"'{field}', {field}" in migration
        assert f"drop column {field}" in migration
    assert migration.index("update marts.country_index_publications") < migration.index("drop column")

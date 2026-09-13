create schema if not exists raw;
create schema if not exists core;
create schema if not exists marts;

create table if not exists raw.regulatory_filings (
    provider text not null,
    external_id text not null,
    content_hash text not null,
    jurisdiction text not null,
    filer_id text not null,
    filing_form text not null,
    filing_date date,
    accepted_at timestamptz,
    published_at timestamptz,
    amendment_of_external_id text,
    document_url text not null,
    content_json jsonb not null,
    fetched_at timestamptz not null,
    created_at timestamptz not null default now(),
    primary key (provider, external_id, content_hash)
);

create table if not exists raw.regulatory_facts (
    filing_provider text not null,
    filing_external_id text not null,
    filing_content_hash text not null,
    fact_id text not null,
    entity_id text,
    security_id text,
    taxonomy text not null,
    concept_name text not null,
    context_id text,
    dimensions_json jsonb not null default '{}'::jsonb,
    unit text,
    decimals text,
    value_text text not null,
    period_start date,
    period_end date,
    instant_date date,
    is_consolidated boolean,
    is_continuing_operations boolean,
    created_at timestamptz not null default now(),
    primary key (filing_provider, filing_external_id, filing_content_hash, fact_id),
    foreign key (filing_provider, filing_external_id, filing_content_hash)
        references raw.regulatory_filings (provider, external_id, content_hash)
);

create table if not exists raw.security_prices (
    security_id text not null,
    trading_date date not null,
    provider text not null,
    close_price numeric not null,
    split_adjusted_close_price numeric,
    trading_currency text not null,
    adjustment_metadata jsonb not null default '{}'::jsonb,
    provider_timestamp timestamptz not null,
    license_class text not null,
    source_url text,
    created_at timestamptz not null default now(),
    primary key (security_id, trading_date, provider)
);

create table if not exists core.securities (
    security_id text primary key,
    issuer_id text,
    issuer_name text not null,
    security_type text not null,
    share_class text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists core.security_listings (
    listing_id text primary key,
    security_id text not null references core.securities (security_id),
    market_id text not null,
    exchange_code text not null,
    ticker text not null,
    trading_currency text not null,
    valid_from date not null,
    valid_to date,
    listing_status text not null,
    source_provider text not null,
    source_external_id text not null,
    created_at timestamptz not null default now(),
    unique (listing_id, security_id, market_id),
    unique (market_id, exchange_code, ticker, valid_from)
);

create table if not exists core.primary_security_listings (
    security_id text not null,
    market_id text not null,
    listing_id text not null,
    created_at timestamptz not null default now(),
    primary key (listing_id),
    unique (listing_id, security_id, market_id),
    foreign key (listing_id, security_id, market_id)
        references core.security_listings (listing_id, security_id, market_id)
);

create table if not exists core.canonical_facts (
    canonical_fact_id text primary key,
    security_id text not null references core.securities (security_id),
    concept_key text not null,
    taxonomy_version text not null,
    value numeric,
    unit text,
    period_start date,
    period_end date,
    instant_date date,
    published_at timestamptz not null,
    availability_status text not null,
    derivation_method text not null,
    source_lineage jsonb not null,
    created_at timestamptz not null default now()
);

create table if not exists core.country_cohorts (
    market_id text not null,
    cohort_version text not null,
    effective_from date not null,
    effective_to date,
    target_coverage_lower numeric not null,
    target_coverage_upper numeric not null,
    achieved_market_coverage numeric not null,
    constituent_target_count integer not null,
    cohort_status text not null,
    structured_reasons jsonb not null default '[]'::jsonb,
    methodology_version text not null,
    created_at timestamptz not null default now(),
    primary key (market_id, cohort_version)
);

create table if not exists core.country_index_runs (
    run_id text not null,
    methodology_version text not null,
    run_status text not null,
    started_at timestamptz not null,
    completed_at timestamptz,
    source_coverage jsonb not null default '{}'::jsonb,
    structured_reasons jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    primary key (run_id)
);

create table if not exists core.country_cohort_members (
    market_id text not null,
    cohort_version text not null,
    security_id text not null,
    primary_listing_id text not null,
    member_rank integer not null,
    market_cap_at_formation numeric not null,
    market_weight_at_formation numeric not null,
    membership_status text not null,
    membership_reason jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    primary key (market_id, cohort_version, security_id),
    foreign key (market_id, cohort_version)
        references core.country_cohorts (market_id, cohort_version),
    foreign key (primary_listing_id, security_id, market_id)
        references core.primary_security_listings (listing_id, security_id, market_id)
);

create table if not exists core.point_in_time_fundamentals (
    security_id text not null,
    valuation_date date not null,
    methodology_version text not null,
    reporting_currency text,
    market_cap numeric,
    ttm_revenue numeric,
    ttm_net_income numeric,
    common_equity numeric,
    ttm_operating_cash_flow numeric,
    ttm_cash_capex numeric,
    ttm_free_cash_flow numeric,
    ttm_common_dividends numeric,
    shares_outstanding numeric,
    reported_fact_coverage numeric not null default 0,
    carried_forward_coverage numeric not null default 0,
    imputed_coverage numeric not null default 0,
    missing_or_invalid_coverage numeric not null default 0,
    source_lineage jsonb not null default '[]'::jsonb,
    structured_reasons jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    primary key (security_id, valuation_date, methodology_version),
    foreign key (security_id) references core.securities (security_id)
);

create table if not exists core.country_daily_metrics (
    run_id text not null,
    market_id text not null,
    metric_key text not null,
    valuation_date date not null,
    cohort_version text not null,
    methodology_version text not null,
    metric_value numeric,
    value_currency text,
    metric_status text not null,
    market_coverage numeric not null,
    reported_fact_coverage numeric not null,
    carried_forward_coverage numeric not null,
    imputed_coverage numeric not null,
    missing_or_invalid_coverage numeric not null,
    metric_eligible_coverage numeric not null,
    actual_constituent_count integer not null,
    cohort_target_count integer not null,
    effective_constituent_count numeric,
    largest_constituent_weight numeric,
    top_five_concentration numeric,
    top_ten_concentration numeric,
    membership_overlap numeric,
    interval_lower numeric,
    interval_upper numeric,
    source_coverage jsonb not null default '{}'::jsonb,
    structured_reasons jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    primary key (run_id, market_id, metric_key, valuation_date),
    foreign key (run_id) references core.country_index_runs (run_id),
    foreign key (market_id, cohort_version)
        references core.country_cohorts (market_id, cohort_version)
);

create table if not exists core.country_weekly_metrics (
    run_id text not null,
    market_id text not null,
    metric_key text not null,
    week_id date not null,
    cohort_version text not null,
    methodology_version text not null,
    metric_value numeric,
    weekly_min_value numeric,
    weekly_max_value numeric,
    valuation_dates date[] not null default '{}'::date[],
    daily_observation_count integer not null,
    metric_status text not null,
    market_coverage numeric not null,
    reported_fact_coverage numeric not null,
    carried_forward_coverage numeric not null,
    imputed_coverage numeric not null,
    missing_or_invalid_coverage numeric not null,
    metric_eligible_coverage numeric not null,
    actual_constituent_count integer not null,
    cohort_target_count integer not null,
    effective_constituent_count numeric,
    largest_constituent_weight numeric,
    top_five_concentration numeric,
    top_ten_concentration numeric,
    membership_overlap numeric,
    interval_lower numeric,
    interval_upper numeric,
    source_coverage jsonb not null default '{}'::jsonb,
    structured_reasons jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    primary key (run_id, market_id, metric_key, week_id),
    foreign key (run_id) references core.country_index_runs (run_id),
    foreign key (market_id, cohort_version)
        references core.country_cohorts (market_id, cohort_version)
);

create table if not exists core.country_metric_warnings (
    run_id text not null,
    market_id text not null,
    metric_key text not null,
    week_id date not null,
    warning_code text not null,
    warning_level text not null,
    warning_message text not null,
    affected_market_weight numeric,
    interval_width_contribution numeric,
    structured_reason jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    primary key (run_id, market_id, metric_key, week_id, warning_code),
    foreign key (run_id, market_id, metric_key, week_id)
        references core.country_weekly_metrics (run_id, market_id, metric_key, week_id)
);

create table if not exists marts.country_index_publications (
    run_id text not null,
    market_id text not null,
    metric_key text not null,
    week_id date not null,
    published_at timestamptz not null,
    is_current boolean not null default false,
    publication_metadata jsonb not null default '{}'::jsonb,
    primary key (run_id, market_id, metric_key, week_id),
    foreign key (run_id, market_id, metric_key, week_id)
        references core.country_weekly_metrics (run_id, market_id, metric_key, week_id)
);

create unique index if not exists country_index_publications_current_week_idx
    on marts.country_index_publications (market_id, metric_key, week_id)
    where is_current;

create schema if not exists core;
create schema if not exists etl;
create schema if not exists raw;
create schema if not exists staging;
create schema if not exists mart;

create table if not exists core.series_metadata (
    series_id text primary key,
    key text not null unique,
    category text not null,
    provider text not null,
    external_series_id text not null,
    label text not null,
    region text not null,
    frequency text not null,
    unit text not null,
    source_url text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists etl.series_checkpoints (
    series_id text primary key,
    last_successful_observation_date date,
    last_run_at timestamptz,
    last_run_status text not null default 'unknown'
);

create table if not exists etl.pipeline_runs (
    run_id text primary key,
    domain_key text not null,
    started_at timestamptz not null,
    finished_at timestamptz,
    status text not null,
    error_summary text
);

create table if not exists raw.series_observations (
    series_id text not null,
    observation_date date not null,
    value text not null,
    fetched_at timestamptz not null,
    primary key (series_id, observation_date)
);

create table if not exists staging.series_observations (
    series_id text not null,
    observation_date date not null,
    numeric_value numeric not null,
    category text not null,
    region text not null,
    frequency text not null,
    unit text not null,
    provider text not null,
    is_valid boolean not null default true,
    primary key (series_id, observation_date)
);

create table if not exists mart.taylor_rule_inputs (
    region text not null,
    as_of_date date not null,
    policy_rate numeric not null,
    inflation numeric not null,
    inflation_target numeric not null,
    neutral_rate numeric not null,
    slack_proxy numeric not null,
    implied_rate numeric not null,
    policy_gap numeric not null,
    policy_series_key text not null,
    policy_source_url text not null,
    inflation_series_key text not null,
    inflation_source_url text not null,
    slack_source_note text not null,
    primary key (region, as_of_date)
);

create table if not exists mart.macro_reference_metrics (
    region text primary key,
    headline_inflation numeric not null,
    headline_inflation_as_of_date date not null,
    core_inflation numeric not null,
    core_inflation_as_of_date date not null,
    policy_real_rate numeric not null,
    policy_real_rate_as_of_date date not null,
    market_real_rate numeric not null,
    market_real_rate_as_of_date date not null,
    output_gap numeric not null default 0,
    output_gap_as_of_date date not null default date '1970-01-01',
    gdp_growth_yoy_current numeric not null,
    gdp_growth_yoy_historical_average numeric not null,
    gdp_growth_yoy_gap numeric not null,
    gdp_growth_yoy_as_of_date date not null,
    gdp_growth_yoy_history_window text not null,
    gdp_growth_qoq_annualized_current numeric not null,
    gdp_growth_qoq_annualized_historical_average numeric not null,
    gdp_growth_qoq_annualized_gap numeric not null,
    gdp_growth_qoq_annualized_as_of_date date not null,
    gdp_growth_qoq_annualized_history_window text not null,
    headline_series_key text not null,
    headline_source_url text not null,
    core_series_key text not null,
    core_source_url text not null,
    market_real_rate_series_key text not null,
    market_real_rate_source_url text not null,
    output_gap_series_key text not null default '',
    output_gap_source_url text not null default '',
    gdp_series_key text not null,
    gdp_source_url text not null,
    policy_real_rate_note text not null
);

create table if not exists mart.currency_ppp_snapshots (
    pair_key text not null,
    base_month date not null,
    as_of_month date not null,
    base_spot numeric not null,
    current_spot numeric not null,
    implied_ppp numeric not null,
    deviation_pct numeric not null,
    trailing_12m_average_gap_pct numeric not null default 0,
    spot_series_key text not null,
    spot_source_url text not null,
    us_cpi_series_key text not null,
    us_cpi_source_url text not null,
    ea_cpi_series_key text not null,
    ea_cpi_source_url text not null,
    primary key (pair_key, base_month, as_of_month)
);

create table if not exists mart.currency_ppp_paths (
    pair_key text not null,
    base_month date not null,
    observation_month date not null,
    actual_spot numeric not null,
    implied_ppp numeric not null,
    primary key (pair_key, base_month, observation_month)
);

create table if not exists mart.currency_irp_snapshots (
    pair_key text not null,
    as_of_date date not null,
    tenor text not null,
    spot numeric not null,
    eur_rate numeric not null,
    usd_rate numeric not null,
    rate_spread numeric not null,
    cip_implied_forward numeric not null,
    observed_forward numeric,
    cip_basis_bps numeric,
    uip_implied_move_pct numeric not null,
    uip_implied_spot numeric not null,
    spot_series_key text not null,
    spot_source_url text not null,
    eur_rate_series_key text not null,
    eur_rate_source_url text not null,
    usd_rate_series_key text not null,
    usd_rate_source_url text not null,
    forward_series_key text,
    forward_source_url text,
    has_observed_forward boolean not null default false,
    primary key (pair_key, as_of_date, tenor)
);

create table if not exists mart.currency_data_availability (
    pair_key text not null,
    section_key text not null,
    item_key text not null,
    status text not null,
    detail text not null,
    as_of_date date,
    primary key (pair_key, section_key, item_key)
);

alter table mart.macro_reference_metrics add column if not exists output_gap numeric not null default 0;
alter table mart.macro_reference_metrics add column if not exists output_gap_as_of_date date not null default date '1970-01-01';
alter table mart.macro_reference_metrics add column if not exists output_gap_series_key text not null default '';
alter table mart.macro_reference_metrics add column if not exists output_gap_source_url text not null default '';
alter table mart.currency_ppp_snapshots add column if not exists trailing_12m_average_gap_pct numeric not null default 0;

-- Raw retention policy is intentionally deferred in v1.
-- Cleanup can be added later as scheduled maintenance work.

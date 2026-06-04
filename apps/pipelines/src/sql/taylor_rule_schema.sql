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

alter table mart.macro_reference_metrics add column if not exists output_gap numeric not null default 0;
alter table mart.macro_reference_metrics add column if not exists output_gap_as_of_date date not null default date '1970-01-01';
alter table mart.macro_reference_metrics add column if not exists output_gap_series_key text not null default '';
alter table mart.macro_reference_metrics add column if not exists output_gap_source_url text not null default '';

-- Raw retention policy is intentionally deferred in v1.
-- Cleanup can be added later as scheduled maintenance work.

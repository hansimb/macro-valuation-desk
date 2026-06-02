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

-- Raw retention policy is intentionally deferred in v1.
-- Cleanup can be added later as scheduled maintenance work.

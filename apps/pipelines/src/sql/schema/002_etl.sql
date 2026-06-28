create schema if not exists etl;

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

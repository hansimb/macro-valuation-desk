create schema if not exists core;
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
    is_imputed boolean not null default false,
    imputation_method text,
    imputation_note text,
    imputation_source_window text,
    primary key (series_id, observation_date)
);

alter table staging.series_observations add column if not exists is_imputed boolean not null default false;
alter table staging.series_observations add column if not exists imputation_method text;
alter table staging.series_observations add column if not exists imputation_note text;
alter table staging.series_observations add column if not exists imputation_source_window text;

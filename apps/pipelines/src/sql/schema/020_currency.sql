create table if not exists mart.currency_ppp_snapshots (
    pair_key text not null,
    base_month date not null,
    anchor_kind text not null default 'year',
    anchor_statistic text not null default 'average',
    anchor_window_code text,
    anchor_start_month date,
    anchor_end_month date,
    anchor_years_covered integer,
    base_year text,
    as_of_month date not null,
    base_spot numeric not null,
    current_spot numeric not null,
    implied_ppp numeric not null,
    deviation_pct numeric not null,
    trailing_12m_average_gap_pct numeric,
    spot_series_key text not null,
    spot_source_url text not null,
    us_cpi_series_key text not null,
    us_cpi_source_url text not null,
    ea_cpi_series_key text not null,
    ea_cpi_source_url text not null,
    primary key (pair_key, base_month, anchor_kind, anchor_statistic, as_of_month)
);

create table if not exists mart.currency_ppp_paths (
    pair_key text not null,
    base_month date not null,
    anchor_kind text not null default 'year',
    anchor_statistic text not null default 'average',
    anchor_window_code text,
    base_year text,
    observation_month date not null,
    actual_spot numeric not null,
    implied_ppp numeric not null,
    primary key (pair_key, base_month, anchor_kind, anchor_statistic, observation_month)
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
    uip_implied_move_pct numeric not null,
    uip_implied_spot numeric not null,
    spot_series_key text not null,
    spot_source_url text not null,
    eur_rate_series_key text not null,
    eur_rate_source_url text not null,
    usd_rate_series_key text not null,
    usd_rate_source_url text not null,
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

alter table mart.currency_ppp_snapshots add column if not exists trailing_12m_average_gap_pct numeric;
alter table mart.currency_ppp_snapshots alter column trailing_12m_average_gap_pct drop not null;
alter table mart.currency_ppp_snapshots add column if not exists anchor_kind text not null default 'year';
alter table mart.currency_ppp_snapshots add column if not exists anchor_statistic text not null default 'average';
alter table mart.currency_ppp_snapshots add column if not exists anchor_window_code text;
alter table mart.currency_ppp_snapshots add column if not exists anchor_start_month date;
alter table mart.currency_ppp_snapshots add column if not exists anchor_end_month date;
alter table mart.currency_ppp_snapshots add column if not exists anchor_years_covered integer;
alter table mart.currency_ppp_snapshots add column if not exists base_year text;
alter table mart.currency_ppp_paths add column if not exists anchor_kind text not null default 'year';
alter table mart.currency_ppp_paths add column if not exists anchor_statistic text not null default 'average';
alter table mart.currency_ppp_paths add column if not exists anchor_window_code text;
alter table mart.currency_ppp_paths add column if not exists base_year text;
alter table mart.currency_ppp_paths add column if not exists has_imputed_inputs boolean not null default false;
alter table mart.currency_ppp_paths add column if not exists imputation_note text;
alter table mart.currency_irp_snapshots drop column if exists observed_forward;
alter table mart.currency_irp_snapshots drop column if exists cip_basis_bps;
alter table mart.currency_irp_snapshots drop column if exists forward_series_key;
alter table mart.currency_irp_snapshots drop column if exists forward_source_url;
alter table mart.currency_irp_snapshots drop column if exists has_observed_forward;

do $$
begin
    if exists (
        select 1
        from pg_constraint
        where conname = 'currency_ppp_snapshots_pkey'
          and conrelid = 'mart.currency_ppp_snapshots'::regclass
    ) then
        alter table mart.currency_ppp_snapshots drop constraint currency_ppp_snapshots_pkey;
    end if;
end
$$;

alter table mart.currency_ppp_snapshots
    add constraint currency_ppp_snapshots_pkey
    primary key (pair_key, base_month, anchor_kind, anchor_statistic, as_of_month);

do $$
begin
    if exists (
        select 1
        from pg_constraint
        where conname = 'currency_ppp_paths_pkey'
          and conrelid = 'mart.currency_ppp_paths'::regclass
    ) then
        alter table mart.currency_ppp_paths drop constraint currency_ppp_paths_pkey;
    end if;
end
$$;

alter table mart.currency_ppp_paths
    add constraint currency_ppp_paths_pkey
    primary key (pair_key, base_month, anchor_kind, anchor_statistic, observation_month);

-- Raw retention policy is intentionally deferred in v1.
-- Cleanup can be added later as scheduled maintenance work.

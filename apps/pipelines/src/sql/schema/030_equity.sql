create table if not exists staging.equity_index_constituent_snapshots (
    universe_key text not null,
    as_of_date date not null,
    ticker text not null,
    company text not null,
    country_code text,
    country_name text,
    sector text not null,
    market_cap numeric not null,
    trailing_12m_revenue numeric not null,
    ps_ratio numeric,
    index_weight_pct numeric not null,
    average_daily_traded_value numeric not null,
    source_provider text not null,
    source_url text,
    fetched_at timestamptz not null default now(),
    primary key (universe_key, as_of_date, ticker)
);

create index if not exists equity_index_constituent_snapshots_universe_as_of_idx
    on staging.equity_index_constituent_snapshots (universe_key, as_of_date desc);

create table if not exists mart.highest_ps_section_summaries (
    section_key text primary key,
    as_of_date date,
    universe_key text not null,
    universe_label text not null,
    section_label text not null,
    benchmark_key text not null,
    benchmark_label text not null,
    average_ps_ratio numeric,
    top_basket_average_ps_ratio numeric,
    top_basket_index_weight_pct numeric,
    eligible_constituent_count integer not null,
    unavailable boolean not null default false
);

create table if not exists mart.highest_ps_section_rankings (
    section_key text not null,
    rank integer not null,
    ticker text not null,
    company text not null,
    country_code text not null,
    country_name text not null,
    sector text not null,
    ps_ratio numeric not null,
    sector_average_ps_ratio numeric not null,
    relative_to_sector_multiple numeric not null,
    index_weight_pct numeric not null,
    primary key (section_key, rank)
);

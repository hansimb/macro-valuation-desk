create schema if not exists raw;
create schema if not exists marts;

create table if not exists raw.equity_market_valuation_payloads (
    provider text not null,
    external_symbol text not null,
    fetched_at timestamptz not null,
    payload_json jsonb not null,
    created_at timestamptz not null default now(),
    primary key (provider, external_symbol, fetched_at)
);

create table if not exists marts.equity_market_valuation_snapshot (
    market_id text not null,
    region text not null,
    market_name text not null,
    measured_symbol text not null,
    measured_name text not null,
    measured_type text not null,
    provider text not null,
    source text not null,
    as_of_date date not null,
    trailing_pe numeric,
    price_to_book numeric,
    price_to_sales numeric,
    price_to_cash_flow numeric,
    dividend_yield_pct numeric,
    price_to_free_cash_flow numeric,
    price_to_cash_flow_method text not null,
    price_to_free_cash_flow_method text not null,
    missing_fields jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (market_id, as_of_date)
);

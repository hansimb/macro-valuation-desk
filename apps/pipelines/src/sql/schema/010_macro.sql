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

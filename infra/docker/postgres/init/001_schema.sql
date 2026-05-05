create schema if not exists raw;
create schema if not exists staging;
create schema if not exists warehouse;
create schema if not exists marts;

create table if not exists raw.macro_series (
    series text not null,
    value numeric not null,
    as_of date not null
);

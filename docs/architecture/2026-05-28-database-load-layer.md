# MVD Database / Load Layer

## Purpose

Describe the reusable database and load-layer architecture for `Macro Valuation Desk`.

This document focuses on:

- how prepared data is stored
- how storage layers are separated
- what the load step owns
- how serving and internal research access relate to stored data

## Role In The System

The database/load layer sits after the pipeline layer and before the API layer.

In the high-level flow:

`source -> pipeline -> postgres -> api -> web`

In ETL terms:

- the pipeline prepares data
- the load step writes it into the correct database layers

The load step is not a separate service by default.

It is a responsibility within the pipeline runtime.

## Core Principle

The database layer should separate:

- stable metadata
- raw landed observations
- cleaned observations
- analysis-ready datasets
- ETL runtime state

This keeps the system understandable, auditable, and reusable.

## Database Shape

The recommended v1 model is:

- one `PostgreSQL` database
- multiple schemas with clear responsibilities

Recommended schemas:

- `core`
- `etl`
- `raw`
- `staging`
- `mart`

## Schema Responsibilities

### `core`

Shared stable metadata.

This is where series-level metadata should live.

Example:

- `core.series_metadata`

### `etl`

Pipeline runtime state and ETL support structures.

Examples:

- `etl.series_checkpoints`
- `etl.pipeline_runs`

### `raw`

First landed standardized source output in database form.

This is `light raw`, not full provider JSON storage.

### `staging`

Technically cleaned and standardized observation data.

### `mart`

Use-case-oriented, analysis-ready, or serving-ready datasets.

This schema is allowed to be more denormalized for practical consumption.

## Load Layer Responsibility

The load step is responsible for:

- writing pipeline outputs to the correct schema
- keeping layer boundaries clean
- using safe write strategies
- supporting traceability and controlled reruns

The load step does not own:

- source fetching
- transformation logic
- analytical interpretation
- API response shaping

## Relationship Between Adapter Output And Raw

`raw` should stay close to the standardized adapter output.

The recommended v1 model is:

- metadata part goes to `core.series_metadata`
- observation part goes to `raw.series_observations`

This means `raw` is not a single JSON blob.

It is the standardized adapter output persisted in a relational model.

## Metadata Strategy

The recommended metadata strategy is:

- keep shared series metadata centralized in `core`
- avoid repeating full metadata in every observation row
- allow selected metadata to be copied into `mart` when serving simplicity benefits from it

This means lower layers stay more normalized, while `mart` may be selectively denormalized.

## Normalized Vs Denormalized

In this architecture:

- `normalized` means shared metadata is stored once and referenced
- `denormalized` means selected metadata is copied into usage-oriented output tables for easier queries and serving

Recommended pattern:

- `core`, `raw`, `staging` = more normalized
- `mart` = selectively denormalized where it improves use

## Example Data Layers

### `raw`

First standardized landed observations:

| key | category | provider | date | value | frequency | unit | source_url |
|---|---|---|---|---:|---|---|---|
| us_cpi_headline | inflation | fred | 2026-01-01 | 312.1 | monthly | index | https://fred.stlouisfed.org/series/CPIAUCSL |
| us_cpi_headline | inflation | fred | 2026-02-01 | 313.0 | monthly | index | https://fred.stlouisfed.org/series/CPIAUCSL |
| us_cpi_headline | inflation | fred | 2026-03-01 | 313.8 | monthly | index | https://fred.stlouisfed.org/series/CPIAUCSL |

### `staging`

Technically cleaned and validated observations:

| key | category | region | observation_date | numeric_value | frequency | unit | provider | is_valid |
|---|---|---|---|---:|---|---|---|---|
| us_cpi_headline | inflation | US | 2026-01-01 | 312.1 | monthly | index | fred | true |
| us_cpi_headline | inflation | US | 2026-02-01 | 313.0 | monthly | index | fred | true |
| us_cpi_headline | inflation | US | 2026-03-01 | 313.8 | monthly | index | fred | true |

### `mart`

Analysis-ready dataset example:

| region | as_of_date | policy_rate | inflation_rate | inflation_target | slack_proxy | implied_rate |
|---|---|---:|---:|---:|---:|---:|
| US | 2026-04-01 | 5.50 | 2.9 | 2.0 | 0.8 | 5.1 |
| EU | 2026-04-01 | 4.00 | 2.4 | 2.0 | 0.2 | 3.6 |

## `core.series_metadata` v1

The recommended v1 fields are:

- `series_id`
- `key`
- `category`
- `provider`
- `external_series_id`
- `label`
- `region`
- `frequency`
- `unit`
- `source_url`
- `created_at`
- `updated_at`

This table stores stable reusable metadata for series across the whole system.

## `raw.series_observations` v1

The recommended `raw` observation model is:

- `series_id`
- `observation_date`
- `value`
- `fetched_at`

This is intentionally close to the adapter output, but persisted in row form.

## `staging.series_observations` v1

The recommended `staging` observation model is structurally close to `raw`, but contains technically validated and standardized data.

The important principle is:

- `raw` keeps first landed standardized observations
- `staging` keeps cleaned trustworthy observations

## `mart` Strategy

`mart` should not be a single generic observation table.

Instead, `mart` should contain use-case-oriented tables or views.

Examples:

- `mart.taylor_rule_inputs`
- `mart.index_valuation_snapshots`
- `mart.index_valuation_history`
- `mart.macro_series_latest`

These are packaged datasets for analysis consumption and API serving.

## Load Behavior

Recommended default write strategy:

- `raw` = upsert
- `staging` = upsert
- `mart historical` = upsert
- `mart snapshot` = overwrite or upsert depending on table shape

The default principle is:

- `upsert` is the normal default
- `overwrite` is mainly for clearly snapshot-oriented mart tables

## Why Upsert Is Not Enough By Itself

Upsert prevents duplicates and supports corrections, but it does not by itself prevent unnecessary full-history work.

To avoid waste, the pipeline layer should also use:

- incremental fetch
- checkpoints
- reprocessing windows
- change detection

The database/load layer supports these, but does not own their orchestration logic.

## ETL Runtime State

The `etl` schema should support pipeline runtime needs.

Recommended v1 tables:

- `etl.series_checkpoints`
- `etl.pipeline_runs`

### `etl.series_checkpoints`

Recommended v1 fields:

- `series_id`
- `last_successful_observation_date`
- `last_run_at`
- `last_run_status`

This supports incremental continuation and controlled reruns.

### `etl.pipeline_runs`

Recommended v1 fields:

- `run_id`
- `domain_key`
- `started_at`
- `finished_at`
- `status`
- `error_summary`

This supports run visibility and debugging.

## Raw Retention

The recommended raw strategy is:

- keep `light raw`
- avoid storing full provider JSON by default
- apply retention policy over time

Retention is a database/data policy, while actual cleanup is typically performed through scheduled pipeline/orchestration work.

## API Relationship

Recommended access pattern:

- product API reads mainly from `mart`
- product API may use selected `core` metadata when needed
- product API should not normally read from `raw`
- product API should rarely read directly from `staging`

Recommended internal research access pattern:

- internal research may use `mart`
- internal research may also use `staging`
- internal research may use `core`
- `raw` is mainly for audit/debug/reprocessing cases

## Query Simplicity Principle

For lower layers, normalization is preferred.

For serving-oriented marts, denormalization is acceptable when it keeps API and frontend queries simpler.

This is why selected fields such as:

- `source_url`
- `label`

may be copied into `mart` outputs even if the canonical metadata lives in `core`.

## Database / Load Layer Summary

The reusable database/load design is:

- one PostgreSQL database
- schemas for `core`, `etl`, `raw`, `staging`, and `mart`
- normalized lower layers
- selectively denormalized mart layer
- load handled inside pipeline runtime
- ETL state stored separately from business metadata

## Next Planning Steps

The next architecture planning step after this document is:

1. API serving layer

## Short Implementation Steps

The database/load layer can later be implemented in small steps:

1. create schema layout
2. create `core.series_metadata`
3. create `etl.series_checkpoints`
4. create `etl.pipeline_runs`
5. create `raw.series_observations`
6. create `staging.series_observations`
7. create the first `mart` table
8. wire one ETL domain end to end into all layers

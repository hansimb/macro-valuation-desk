# MVD Recommended Future Stack

## Purpose

Capture the most relevant next-step data and analytics tooling candidates for MVD without committing to unnecessary platform complexity too early.

## Recommended Additions Later

### `dbt`

Best candidate for a later addition once the warehouse model grows beyond the current skeleton.

Why it may help:

- formalizes SQL transformations
- fits the `raw -> staging -> warehouse -> marts` model well
- improves testability and documentation of warehouse logic

Recommended timing:

- after the first real warehouse and marts layers start to grow

## Conditional Candidate

### `DuckDB`

Potentially useful, but not as the main source-of-truth database.

Good use cases:

- local analysis
- ad hoc data exploration
- CSV or Parquet inspection
- lightweight local research workflows

Important guardrail:

- do not let it replace PostgreSQL in the core product architecture
- use it only if it clearly improves local development or analysis workflows

## Not Recommended Now

### `Spark`

Too heavy for the current scale and product stage.

### `Kafka`

Not a good fit for a scheduled batch-oriented analytics product at this stage.

### `Airflow`

Not needed while `Prefect` already fills the orchestration role.

## Current Recommendation Order

1. `dbt`
2. `Polars`
3. `DuckDB`
4. `Pandas` as likely baseline pipeline utility

## Summary

The best near-future additions are the ones that reinforce the existing architecture:

- `dbt` for warehouse modeling
- `Polars` and likely some `Pandas` for richer pipeline transforms
- `DuckDB` only as a local helper, not as the main application database

Everything else should stay out unless the product shape changes materially.

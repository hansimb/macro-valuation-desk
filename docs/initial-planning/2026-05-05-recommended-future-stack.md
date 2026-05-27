# MVD Recommended Future Stack

## Purpose

Capture the most relevant future additions for the reusable MVD data platform without adding unnecessary complexity too early.

## Current Core Stack

The current architectural direction is:

- `Next.js` for web
- `Fastify` for API
- `Python` for data ingestion and preparation
- `PostgreSQL` for durable storage
- `Docker Compose` for local runtime

## Recommended Additions Later

### `dbt`

Strong candidate once warehouse modeling starts to grow.

Why it may help:

- formalizes transformation layers
- fits `raw -> staging -> mart` thinking
- improves warehouse documentation and testing

Recommended timing:

- after the first real reusable pipeline flows are in place

### `Polars`

Good candidate once transformation logic becomes heavier.

Why it may help:

- fast dataframe-style transforms
- useful for pipeline normalization and preparation work
- better fit than overusing plain ad hoc Python loops

Recommended timing:

- once multiple real source ingestions exist

## Conditional Candidate

### `DuckDB`

Useful as a local analysis helper, but not as the main application database.

Good use cases:

- ad hoc local analysis
- quick exploration of extracted datasets
- CSV or Parquet inspection

Guardrail:

- do not replace PostgreSQL with it in the core system

### `OpenBB`

Useful only as an optional helper inside the source layer.

Good use case:

- accelerating selected provider integrations

Guardrail:

- do not make OpenBB the architecture
- the reusable source layer must still own the internal data contract

## Not Recommended Now

### `Spark`

Too heavy for the current scale.

### `Kafka`

Not a good fit for the current batch-oriented data flow.

### `Airflow`

Not needed unless orchestration complexity grows far beyond the current stage.

## Summary

The best future additions are the ones that reinforce the reusable data platform:

- `dbt` for warehouse modeling
- `Polars` for richer transforms
- `DuckDB` for local analysis only
- `OpenBB` only as an optional source-layer helper

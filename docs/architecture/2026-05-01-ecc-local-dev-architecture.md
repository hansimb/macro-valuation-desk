# MVD Local Development Architecture

## Services

### Web

`apps/web` owns the user-facing Macro Valuation Desk shell, including the primary `Macro` and `Stock Markets` sections.

### API

`apps/api` is a Fastify service that reads prepared data from PostgreSQL and exposes stable product-facing routes.

### Pipelines

`apps/pipelines` contains Python pipeline code and Prefect-based orchestration. It is responsible for ingesting, normalizing, and loading data into PostgreSQL.

### Database

`postgres` is the source of truth and the durable store for the first vertical slice.

## Local Runtime Shape

The stack is designed to run through Docker Compose with separate containers for:

- `web`
- `api`
- `pipelines`
- `postgres`

This keeps the local environment close to the intended production service boundaries.

## First Macro Slice

The first skeleton slice flows like this:

1. a Prefect-backed pipeline prepares macro seed data
2. the data is loaded into `raw.macro_series`
3. the Fastify route `/macro/overview` reads or falls back to a stable seed response
4. the web `Macro` page consumes the API response

## Why This Matters

This foundation proves the repo structure, runtime boundaries, and data-serving model before deeper analytics and broader market coverage are added.

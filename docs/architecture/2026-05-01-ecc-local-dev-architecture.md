# MVD Local Development Architecture

## Purpose

Describe the current local runtime shape of `Macro Valuation Desk`.

This is the practical development setup, not the full reusable data-platform design.

## Services

### Web

`apps/web` owns the user-facing site shell and analysis pages.

It should remain a presentation layer, not a place where provider access or core data preparation logic lives.

### API

`apps/api` is the serving layer.

Its job is to read prepared data from PostgreSQL and expose stable product-facing routes for the web app and other consumers.

### Pipelines

`apps/pipelines` contains Python ingestion and preparation logic.

It is responsible for:

- calling the reusable data source layer
- ingesting source data
- normalizing it
- preparing analysis-ready datasets
- loading them into PostgreSQL

### Database

`postgres` is the durable system store and the main source of truth for application-facing data.

## Local Runtime Shape

The local stack is designed to run through Docker Compose with separate containers for:

- `web`
- `api`
- `pipelines`
- `postgres`

This keeps local development close to the intended long-term service boundaries.

## Current Direction

The intended flow is:

1. source layer fetches external data
2. pipelines ingest and standardize it
3. PostgreSQL stores prepared data
4. API serves it
5. web renders it

In short:

`source -> pipeline -> postgres -> api -> web`

## Notes

- the reusable data source architecture is designed separately from this document
- the API should normally read from PostgreSQL, not from live providers
- analysis pages should consume prepared data, not provider-specific payloads

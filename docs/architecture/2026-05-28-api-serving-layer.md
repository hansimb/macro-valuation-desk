# MVD API Serving Layer

## Purpose

Describe the serving-layer role of the API in `Macro Valuation Desk`.

This document is intentionally lighter than the source, pipeline, and database/load layer docs.

## Role In The System

The API sits between PostgreSQL and the web layer.

In the high-level flow:

`source -> pipeline -> postgres -> api -> web`

Its job is to serve prepared data, not to perform ETL work.

## Main Responsibility

The API is responsible for:

- exposing stable routes
- reading prepared data from PostgreSQL
- shaping database outputs into application-facing responses
- enforcing clear serving boundaries between the data platform and the frontend

## What The API Does Not Own

The API does not own:

- source/provider fetching
- ETL orchestration
- transformation logic that belongs in pipelines
- database loading
- frontend rendering logic

## Primary Data Access Pattern

The default serving pattern is:

- product API reads mainly from `mart`

The API may also read selected metadata from:

- `core`

But it should not normally read from:

- `raw`
- `staging`

## Why `mart` Is The Default

`mart` exists to provide ready-to-serve, use-case-oriented data.

This keeps the API:

- simpler
- lighter
- more stable
- less coupled to ETL internals

## Product API Vs Internal Research Access

Recommended separation:

- `product API` = public or app-facing, mart-first
- `internal research access` = broader, usually direct DB or separate internal tools

The product API should stay narrow and stable.

Broader exploratory access should not force the product API to become a general warehouse query layer.

## Response Shaping Principle

The API may reshape data for frontend use, but it should not recalculate major analytical logic.

Good API work:

- rename fields for client clarity
- combine a small amount of serving metadata
- package mart outputs for screens or analysis pages

Bad API work:

- recomputing ETL-derived metrics
- rebuilding marts on request
- reaching down into raw provider-like structures

## References And Metadata

If the frontend needs references such as `source_url`, the preferred pattern is:

- include them in `mart` when they are serving-critical
- use `core` metadata only when needed

This keeps API queries simpler.

## API Layer Summary

The API layer should be:

- mart-first
- serving-focused
- lightweight
- separate from ETL concerns
- stable for frontend consumption

## Short Implementation Steps

The API layer can later be implemented in small steps:

1. define route groups by product area
2. map each route to its primary mart source
3. shape mart outputs into frontend-facing contracts
4. add metadata joins only where clearly needed
5. keep internal research access separate from product-serving routes

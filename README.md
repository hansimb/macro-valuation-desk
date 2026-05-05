# Macro Valuation Desk

Macro Valuation Desk is a macro and valuation workspace for a value investor. This repository contains the first monorepo foundation for the web app, API, pipelines, shared contracts, and local infrastructure.

## Core Stack

- Next.js for the web shell
- Fastify for the product API
- Prefect for pipeline orchestration
- PostgreSQL as the source of truth
- Docker Compose for the local multi-service stack

## Repository Structure

```text
apps/
  web/
  api/
  pipelines/
packages/
  shared/
infra/
docs/
```

## Local Development

The project is designed around Docker Compose first. The intended local runtime shape is:

- `web` serves the Macro Valuation Desk UI
- `api` exposes product-facing endpoints backed by PostgreSQL
- `pipelines` owns ingestion and Prefect-driven flow execution
- `postgres` stores raw, staging, warehouse, and marts-oriented data

Local scripts:

- `npm run dev:db` starts PostgreSQL only in docker
- `npm run dev` starts `api` and `web` dev servers
- `npm run dev:pipeline` runs a pipeline flow once
- `npm run dev:stack` starts the full Compose stack

## First Vertical Slice

The initial end-to-end slice is a `Macro` overview flow:

1. pipelines prepare a macro seed payload
2. PostgreSQL stores macro series data
3. the Fastify API exposes `/macro/overview`
4. the web app reads that route for the Macro page

## Current Goal

The current milestone is a serious skeleton, not full feature breadth. The main focus is proving service boundaries, data flow, and a cloud-shaped local architecture before the product deepens.

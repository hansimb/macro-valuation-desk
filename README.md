# Macro Valuation Desk

Macro Valuation Desk is a local-first research workspace for macro, currency, and equity valuation analysis. The repository is organized as a monorepo with a web app, product API, data pipelines, shared contracts, documentation, and local infrastructure.

The project is intentionally built around reusable analysis surfaces rather than one-off pages. Current work includes macro dashboards, Taylor-rule style policy analysis, currency valuation tools, and equity return-expectation workflows.

## Stack

- `apps/web`: Next.js UI for analysis pages and interactive calculators
- `apps/api`: Fastify API for product-facing data routes
- `apps/pipelines`: Python pipeline code for ingestion, transforms, and database loading
- `packages/shared`: shared TypeScript contracts
- `infra`: local infrastructure configuration
- `docs`: architecture notes, product plans, and agent-facing implementation guidance

## Local Development

Install dependencies from the repository root:

```bash
npm install
```

Common commands:

```bash
npm run dev:db       # start PostgreSQL only
npm run dev          # start API and web dev servers
npm run dev:web      # start the web app
npm run dev:api      # start the API
npm run dev:pipeline # run the pipeline entrypoint
npm run dev:stack    # start the compose stack
npm test             # run Vitest suites
```

Market valuation snapshots use Yahoo Finance quote summary data by default and do not require an API key:

```powershell
cd apps/pipelines
python -m src.flows.equity_market_valuation_flow
```

The paid EODHD adapter remains available in code, but it is not the default local-development source.

## Runtime Shape

The local stack is designed around clear service boundaries:

- the web app presents analysis workflows and browser-local inputs where appropriate
- the API serves product data from the database
- the pipeline layer fetches, transforms, and loads source data
- PostgreSQL stores raw, staging, warehouse, and mart-style datasets

## Development Notes

Prefer small, testable changes that preserve the service boundaries above. Keep long-lived implementation detail in `docs/` instead of overloading this README with feature-specific status, so the front page can remain stable as the product evolves.

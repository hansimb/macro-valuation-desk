# Repo Map For Agents

Macro Valuation Desk is a monorepo for a macro and valuation workspace.

## Structure

- `apps/web`: Next.js user interface.
- `apps/api`: Fastify product API.
- `apps/pipelines`: Prefect and Python data ingestion, transforms, and loads.
- `packages/shared`: Shared TypeScript contracts used across app boundaries.
- `docs`: Product, architecture, analysis, deployment, and agent notes.
- `infra`: Local and deployment infrastructure.

## System Flow

The main runtime flow is:

```text
source -> pipeline -> postgres -> api -> web
```

## Default Reading Order For Analysis Changes

1. `docs/agents/features/<feature>.md`, if it exists.
2. Shared contract in `packages/shared`.
3. API route in `apps/api`.
4. Pipeline transform/load in `apps/pipelines`, if the data shape changes.
5. Web page and components in `apps/web`.
6. Targeted tests for the changed boundary.

## Do Not Read First

Avoid starting with build output, caches, generated artifacts, dependency folders, coverage reports, or package manager lockfiles unless the task is specifically about dependencies or generated output.

## Important Rule

Do not add fake fallback data to live analysis paths. If live analysis data is missing or invalid, surface that state explicitly through the real data/API flow.

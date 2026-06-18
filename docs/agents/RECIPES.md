# Agent Recipes

Use these recipes to keep searches small and edits aligned with the repo flow.

## Frontend Analysis Change

1. Read the relevant feature note in `docs/agents/features/<feature>.md`, if it exists.
2. Read the shared contract that defines the data shape.
3. Read the API response shape used by the page.
4. Edit the focused page/component files in `apps/web`.
5. Run targeted frontend or contract tests.

Do not invent fallback analysis values in the UI. Show loading, empty, or error states from real API state.

## Backend/API Change

1. Read the shared contract first.
2. Read the route and service code in `apps/api`.
3. Check the SQL/query boundary used by the route.
4. Update API code and the contract together when the response shape changes.
5. Run targeted API and shared-contract tests.

Keep API responses honest: missing source data should be represented explicitly, not replaced with fake live-analysis data.

## Pipeline Transform Change

1. Read the target shared contract and the expected API shape.
2. Read the pipeline transform/load code in `apps/pipelines`.
3. Read only the relevant SQL schema or load target.
4. Update transform, load, and tests for the changed data shape.
5. Run targeted pipeline tests.

Prefer preserving source lineage and explicit null/missing states over manufactured values.

## Full-Stack Analysis Feature Change

1. Read `docs/agents/features/<feature>.md`, if it exists.
2. Read the shared contract.
3. Read the API route.
4. Read pipeline transform/load code if the data shape changes.
5. Read the web page/components.
6. Make the smallest cross-boundary change that keeps `source -> pipeline -> postgres -> api -> web` consistent.
7. Run targeted tests for every touched boundary.

Do not start by scanning build folders, caches, generated artifacts, or dependency directories.

## Debugging Failing Test

1. Read the failing test and its assertion.
2. Read the smallest implementation unit directly under test.
3. Trace one boundary outward only if the failure requires it.
4. Reproduce the failure with the narrowest test command.
5. Make the smallest fix and rerun the same targeted test.
6. Broaden verification only when the changed behavior crosses boundaries.

Avoid speculative rewrites. Let the failing assertion and real data flow guide the search.

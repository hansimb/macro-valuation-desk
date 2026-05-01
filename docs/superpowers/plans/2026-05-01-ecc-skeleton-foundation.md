# MVR Desk Skeleton Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first end-to-end Macro Valuation Research Desk skeleton with a cloud-shaped local architecture, including web, API, pipelines, PostgreSQL, and one thin working data flow.

**Architecture:** MVR Desk uses a lean monorepo with separate services for the web UI, product API, and Python pipelines. Docker Compose boots the local system, PostgreSQL acts as the source of truth, Prefect orchestrates the data layer, and the UI/API contracts establish clean product boundaries from the start.

**Tech Stack:** Next.js, TypeScript, Chakra UI, Node.js, Fastify, Python, Prefect, PostgreSQL, Docker Compose, pnpm or npm workspaces, pytest, Vitest

---

## File Structure Map

### New directories

- `apps/web/`
- `apps/api/`
- `apps/pipelines/`
- `packages/shared/`
- `infra/compose/`
- `infra/docker/`
- `docs/architecture/`

### Expected responsibility split

- `apps/web`: UI shell, theme, route layout, section pages
- `apps/api`: health route, product data route, DB read layer
- `apps/pipelines`: Prefect flows, source adapter, transform, load
- `packages/shared`: shared response contracts and schema notes
- `infra/compose`: local stack definition
- `docs/architecture`: architecture notes that sit closer to implementation

### Expected early files

- `package.json`
- `pnpm-workspace.yaml` or npm workspace config in `package.json`
- `docker-compose.yml`
- `apps/web/package.json`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/macro/page.tsx`
- `apps/web/src/app/stock-markets/page.tsx`
- `apps/web/src/features/theme/system.ts`
- `apps/api/package.json`
- `apps/api/src/server.ts`
- `apps/api/src/routes/health.ts`
- `apps/api/src/routes/macro-overview.ts`
- `apps/api/src/lib/db.ts`
- `apps/pipelines/pyproject.toml`
- `apps/pipelines/src/flows/macro_seed_flow.py`
- `apps/pipelines/src/tasks/fetch_seed_data.py`
- `apps/pipelines/src/tasks/load_macro_seed.py`
- `apps/pipelines/src/lib/db.py`
- `infra/docker/postgres/init/001_schema.sql`
- `packages/shared/src/contracts/macro-overview.ts`

## Task 1: Establish the Monorepo Skeleton

**Files:**
- Create: `package.json`
- Create: `pnpm-workspace.yaml` or workspace equivalents
- Create: `apps/web/package.json`
- Create: `apps/api/package.json`
- Create: `packages/shared/package.json`
- Create: `README.md`

- [ ] **Step 1: Write the failing workspace structure test**

Create a simple repo contract test file such as `tests/workspace-structure.test.ts` that asserts the expected top-level folders and package files exist.

```ts
import { existsSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("workspace structure", () => {
  it("contains the expected service roots", () => {
    expect(existsSync("apps/web/package.json")).toBe(true);
    expect(existsSync("apps/api/package.json")).toBe(true);
    expect(existsSync("packages/shared/package.json")).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/workspace-structure.test.ts`
Expected: FAIL because the workspace files do not exist yet

- [ ] **Step 3: Write the minimal workspace setup**

Add workspace manifests and minimal package definitions so the repo is bootstrappable and the test can pass.

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/workspace-structure.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add package.json pnpm-workspace.yaml apps/web/package.json apps/api/package.json packages/shared/package.json tests/workspace-structure.test.ts README.md
git commit -m "feat: add mvr desk monorepo skeleton"
```

## Task 2: Add Docker Compose Local Infrastructure

**Files:**
- Create: `docker-compose.yml`
- Create: `infra/docker/postgres/init/001_schema.sql`
- Create: `infra/compose/.env.example`
- Test: `tests/docker-compose-contract.test.ts`

- [ ] **Step 1: Write the failing infra contract test**

Create a test that reads `docker-compose.yml` as text and verifies service names for `web`, `api`, `pipelines`, and `postgres` appear.

```ts
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("docker compose contract", () => {
  it("defines the core services", () => {
    const compose = readFileSync("docker-compose.yml", "utf8");
    expect(compose).toContain("web:");
    expect(compose).toContain("api:");
    expect(compose).toContain("pipelines:");
    expect(compose).toContain("postgres:");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/docker-compose-contract.test.ts`
Expected: FAIL because `docker-compose.yml` does not exist yet

- [ ] **Step 3: Write the minimal compose stack**

Define:

- `postgres` with persistent volume and init SQL
- `api` container
- `web` container
- `pipelines` container
- shared network and environment placeholders

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/docker-compose-contract.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml infra/docker/postgres/init/001_schema.sql infra/compose/.env.example tests/docker-compose-contract.test.ts
git commit -m "feat: add mvr desk local docker compose stack"
```

## Task 3: Build the Web Shell and Theme Foundation

**Files:**
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/app/macro/page.tsx`
- Create: `apps/web/src/app/stock-markets/page.tsx`
- Create: `apps/web/src/features/theme/system.ts`
- Create: `apps/web/src/features/theme/provider.tsx`
- Test: `apps/web/tests/navigation-shell.test.tsx`

- [ ] **Step 1: Write the failing UI shell test**

Create a test asserting the home shell renders links for `Macro` and `Stock Markets`.

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "../src/app/page";

describe("MVR Desk home shell", () => {
  it("renders the primary sections", () => {
    render(<HomePage />);
    expect(screen.getByText("Macro")).toBeInTheDocument();
    expect(screen.getByText("Stock Markets")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --workspace apps/web test -- navigation-shell.test.tsx`
Expected: FAIL because the page and theme files do not exist yet

- [ ] **Step 3: Write the minimal web shell**

Implement:

- Chakra provider wiring
- light and dark theme tokens
- a polished landing shell
- first-class routes for `Macro` and `Stock Markets`

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --workspace apps/web test -- navigation-shell.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "feat: add mvr desk web shell and theme foundation"
```

## Task 4: Create the API Skeleton with Shared Contracts

**Files:**
- Create: `packages/shared/src/contracts/macro-overview.ts`
- Create: `apps/api/src/server.ts`
- Create: `apps/api/src/routes/health.ts`
- Create: `apps/api/src/routes/macro-overview.ts`
- Create: `apps/api/src/lib/db.ts`
- Test: `apps/api/tests/macro-overview-route.test.ts`

- [ ] **Step 1: Write the failing API test**

Create a route test that expects `/health` to return `200` and `/macro/overview` to return a typed payload with at least one metric field.

```ts
import { describe, expect, it } from "vitest";

describe("macro overview route", () => {
  it("returns a stable contract", async () => {
    const response = await app.inject({ method: "GET", url: "/macro/overview" });
    expect(response.statusCode).toBe(200);
    expect(response.json()).toHaveProperty("metrics");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --workspace apps/api test -- macro-overview-route.test.ts`
Expected: FAIL because the server and route files do not exist yet

- [ ] **Step 3: Write the minimal API implementation**

Implement:

- Fastify server bootstrap
- health route
- a placeholder macro overview route
- DB client setup
- response type contract shared with the frontend

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --workspace apps/api test -- macro-overview-route.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api packages/shared
git commit -m "feat: add mvr desk api skeleton and shared contracts"
```

## Task 5: Wire the Pipelines Service with Prefect

**Files:**
- Create: `apps/pipelines/pyproject.toml`
- Create: `apps/pipelines/src/flows/macro_seed_flow.py`
- Create: `apps/pipelines/src/tasks/fetch_seed_data.py`
- Create: `apps/pipelines/src/tasks/load_macro_seed.py`
- Create: `apps/pipelines/src/lib/db.py`
- Test: `apps/pipelines/tests/test_macro_seed_flow.py`

- [ ] **Step 1: Write the failing pipeline test**

Create a pytest test that imports the flow and asserts it returns a non-empty result summary.

```python
from src.flows.macro_seed_flow import run_macro_seed_flow

def test_macro_seed_flow_returns_summary():
    result = run_macro_seed_flow()
    assert result["rows_loaded"] >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/pipelines/tests/test_macro_seed_flow.py -v`
Expected: FAIL because the flow does not exist yet

- [ ] **Step 3: Write the minimal Prefect pipeline**

Implement:

- one Prefect flow
- one fetch task with hard-coded or fixture seed data
- one load task that writes a tiny macro seed dataset into PostgreSQL
- one returned summary payload

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/pipelines/tests/test_macro_seed_flow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines
git commit -m "feat: add mvr desk prefect pipeline skeleton"
```

## Task 6: Connect the End-to-End Vertical Slice

**Files:**
- Modify: `infra/docker/postgres/init/001_schema.sql`
- Modify: `apps/api/src/routes/macro-overview.ts`
- Modify: `apps/web/src/app/macro/page.tsx`
- Test: `tests/ecc-end-to-end-contract.test.ts`

- [ ] **Step 1: Write the failing end-to-end contract test**

Create a contract test that checks:

- the seed flow target table exists in schema SQL
- the API route reads from that domain table
- the macro page references the API route

```ts
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("end-to-end macro slice contract", () => {
  it("connects pipeline, api, and web around macro overview", () => {
    expect(readFileSync("infra/docker/postgres/init/001_schema.sql", "utf8")).toContain("macro_series");
    expect(readFileSync("apps/api/src/routes/macro-overview.ts", "utf8")).toContain("macro_series");
    expect(readFileSync("apps/web/src/app/macro/page.tsx", "utf8")).toContain("/macro/overview");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/ecc-end-to-end-contract.test.ts`
Expected: FAIL because the cross-layer slice is not wired yet

- [ ] **Step 3: Implement the minimal vertical slice**

Wire:

- one schema table such as `macro_series`
- one seed flow write
- one API read
- one web page fetch and render

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/ecc-end-to-end-contract.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/docker/postgres/init/001_schema.sql apps/api/src/routes/macro-overview.ts apps/web/src/app/macro/page.tsx tests/ecc-end-to-end-contract.test.ts
git commit -m "feat: wire mvr desk macro vertical slice"
```

## Task 7: Document Developer Workflow and Architecture Notes

**Files:**
- Create: `docs/architecture/2026-05-01-ecc-local-dev-architecture.md`
- Modify: `README.md`
- Test: `tests/documentation-contract.test.ts`

- [ ] **Step 1: Write the failing documentation contract test**

Create a test that asserts the README mentions `Docker Compose`, `Prefect`, `Fastify`, and `PostgreSQL`.

```ts
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("documentation contract", () => {
  it("describes the core stack", () => {
    const readme = readFileSync("README.md", "utf8");
    expect(readme).toContain("Docker Compose");
    expect(readme).toContain("Prefect");
    expect(readme).toContain("Fastify");
    expect(readme).toContain("PostgreSQL");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/documentation-contract.test.ts`
Expected: FAIL because the workflow documentation is not complete yet

- [ ] **Step 3: Write the minimal docs**

Document:

- service responsibilities
- how to start the stack
- where the first vertical slice lives
- how pipelines, API, and web connect

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/documentation-contract.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md docs/architecture/2026-05-01-ecc-local-dev-architecture.md tests/documentation-contract.test.ts
git commit -m "docs: add mvr desk architecture and developer workflow notes"
```

## Spec Coverage Check

- The monorepo architecture is implemented by Tasks 1 and 2.
- The product shell and dual-section navigation are implemented by Task 3.
- The separate API service is implemented by Task 4.
- Python pipelines with Prefect are implemented by Task 5.
- The direct pipeline-to-Postgres and API-to-web flow is proven by Task 6.
- The human-facing onboarding and architecture understanding are reinforced by Task 7.

## Placeholder Scan

No task intentionally contains `TBD`, `TODO`, or deferred implementation language in place of a real step. All tasks describe concrete files, verification commands, and expected outcomes.

## Type Consistency Check

- `Macro` is named consistently across web, API, and pipeline examples.
- `macro overview` remains the first vertical slice across all layers.
- PostgreSQL remains the single source of truth in all tasks.
- Prefect appears only in the pipelines service and not in the API layer.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-01-ecc-skeleton-foundation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

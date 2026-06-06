# Analysis Planning Guide For Agents

This file restates the analysis-planning rules in a process-oriented form for agent use.

Use it together with `docs/analysis/README.md`, not as a replacement for it.

## Default Behavior

Follow these rules by default.

Do not re-ask for them and do not deviate from them unless the user or developer explicitly tells you to.

## Planning Goal

When planning a new analysis in MVD, the goal is to produce one serious analysis-specific master plan that:

- defines the analytical question clearly
- keeps methodology open and inspectable
- fits the approved architecture
- supports reusable data and pipeline design
- avoids fake outputs and hardcoded shortcuts

## Required Mental Model

Always think in this system flow:

`source -> pipeline -> postgres -> api -> web`

This means:

- source fetches raw external data
- pipeline validates, standardizes, derives, and prepares reusable datasets
- postgres stores durable prepared layers
- api serves stable product-facing shapes
- web presents the final analysis

Do not blur these responsibilities.

## Planning Workflow

When starting analysis planning, use this order:

1. define the question the analysis answers
2. define the theory and reasoning in plain language
3. define the formula or analytical framework
4. define the required raw inputs
5. define which inputs are observed, assumed, proxied, and derived
6. define the expected analysis outputs
7. define how the prepared data should flow through pipeline, database, api, and web
8. define implementation phases

Do not jump straight into data-source trivia or UI details before the analytical model itself is clear.

## Theory First Rule

Every analysis block should follow this order:

1. short theory / reasoning
2. explicit formula or framework
3. explicit formula-term explanations
4. data inputs and assumptions
5. numerical analysis or output
6. references

If the page shows a compact formula, always open every important symbol or term in plain language directly on the page.

Do not assume the formula is self-explanatory.

The same rule applies whether the page has one method block or several related method blocks.

## Open Methodology Rule

The user must be able to inspect how the analysis works.

Do not hide methodology behind:

- black-box labels
- unexplained composite scores
- magic internal transforms
- silent proxy substitutions

State openly:

- what the model is trying to measure
- why the method is economically relevant
- what formula is used
- what data is required
- what assumptions or proxies exist
- what the output can and cannot mean

## No Fake Fallback Rule

Never use:

- placeholder outputs
- hardcoded fake values
- fake example datasets in live analysis flows
- silent fallback series that pretend to be real data

If required data is unavailable, the affected output should not appear.

Missing data must be handled honestly.

## Reuse And Scope Discipline

Start narrow if needed, but do not bake narrow v1 scope unnecessarily into the architecture.

Prefer:

- reusable source adapters
- reusable domain-first pipeline outputs
- reusable prepared database layers
- stable API contracts

Avoid:

- analysis-specific monolithic ETL unless truly required
- provider-specific logic in API or web
- hardcoding the first geography or pair deeply into system structure

## Naming Rule

Use the standard analysis naming pattern:

- `<analysis-name>-master-plan.md`

If the product analysis is expected to broaden later, prefer a broad analysis name instead of hardcoding the first geography, region, or currency pair into every artifact name.

Do not reopen naming discussion unless the user explicitly asks to.

## Architecture Compliance

Before finalizing a new analysis plan, check it against the architecture docs under `docs/architecture/`.

Especially preserve these rules:

- `source -> pipeline -> postgres -> api -> web`
- pipeline owns transforms and preparation
- API serves prepared data, not provider payloads
- pipeline is domain-first by default
- UI may look unified even when backend layers remain modular

If a plan conflicts with the architecture, revise the plan instead of hand-waving the conflict away.

## Master Plan Expectations

Each analysis master plan should cover:

1. Goal
2. Core question
3. Why the analysis matters
4. Variable map
5. Formula or analytical framework
6. Data needs
7. Assumptions
8. User interaction model
9. Interpretation model
10. References plan
11. Phase-by-phase implementation path

## Phase Design Rule

Implementation should proceed in small phases.

If one analysis page contains multiple related methodologies, implement one methodology at a time while leaving behind reusable shared architecture.

Do not solve all source, pipeline, database, API, and UI complexity at once.

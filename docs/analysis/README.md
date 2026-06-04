# Analysis Docs

This directory is the home for analysis-specific planning and development work.

It exists for both humans and agents.

The purpose of this directory is not to create a large number of small documents for every analysis.

The default model is:

- one shared `README.md` for analysis guidelines
- one analysis-specific master plan per analysis

## Core Principle

Each analysis should begin with a single master plan document.

That master plan should describe:

- what the analysis is trying to answer
- what variables it needs
- what assumptions it uses
- what the user should be able to do
- how the analysis should behave in the app
- how the work should be implemented in small phases

The master plan should not try to fully document all system architecture in one place.

System-level architecture work should be handled later, phase by phase, through the needs exposed by the analysis master plan.

## What Goes Here

Recommended contents of this directory:

- `README.md`
- `<analysis-name>-master-plan.md`

Example:

- `taylor-rule-master-plan.md`

Naming should follow the same pattern consistently.

If the product-facing analysis is still intended to stay broad or expandable, prefer the broad analysis name rather than hardcoding the first covered geography, region, or pair into every artifact name.

Do not ask for naming variations again unless the user explicitly wants to revisit the convention.

If an analysis later becomes large enough to justify extra documentation, that should happen only after the master plan has exposed a clear need for it.

## Macro Analysis Guidelines

These are the default rules for macro analysis work in MVD.

Agents should follow these defaults without re-asking for them and should not deviate without explicit user or developer approval.

### 1. Data First

The analysis should be built around data, formulas, tables, and scenario outputs.

Text should stay short and only explain the most important interpretation.

The page should feel closer to a research worksheet than a long article.

### 2. Clear Method

Every analysis page must make its method explicit:

- the short theory or reasoning behind the framework
- what is being measured
- which formula or framework is used
- which inputs come from real data
- which inputs are assumptions
- what the output means

If a formula exists, show it clearly on the page.

Theory and reasoning should appear before the formula, and the formula should appear before the numerical analysis output.

Preferred section flow inside an analysis block:

1. short theory / reasoning
2. explicit formula or framework
3. data inputs and assumptions
4. analysis output
5. references

This is the default `theory first` rule for MVD analysis work.

### 3. Minimal User Inputs

Only parameters that are genuinely assumption-driven should be user-adjustable.

Anything that should come from real data must be fixed to real data, not exposed as a free control.

Default values for adjustable inputs should be economically defensible and documented.

### 4. Scenario Structure

Where scenario analysis is useful, prefer a small preset set such as:

- `dovish`
- `base`
- `hawkish`

Do not create overly complex dashboards for v1 analysis pages.

### 4.5. No Fake Fallbacks

Do not use placeholder outputs, hardcoded fallback values, fake example data, or silent substitute series in product analysis flows.

If real required data is unavailable, the affected analysis output should simply not appear rather than pretending the system has an answer.

Missing data should be handled honestly in architecture and implementation, not hidden through UI filler.

### 5. References Required

Every analysis page must end with references.

References should include:

- methodology or theory sources
- primary data sources
- any important proxy or assumption source

### 6. Honest Proxies

If an ideal variable is not available, a proxy can be used, but it must be stated explicitly.

Do not hide substitutions.

### 7. Keep Pages Narrow

Each analysis page should answer one clear question.

If the page starts trying to answer several different macro questions at once, split it into separate analyses.

If a single page intentionally contains multiple tightly related methods inside one analysis, each method block must still keep its own clear internal structure:

- theory first
- formula second
- data and outputs after that
- references at the end of the block

### 8. Full-Stack Means Full-Stack

Analysis planning in this directory is full-stack planning.

That means the master plan should consider:

- source and ingestion implications
- pipeline preparation and reuse
- database/load shape
- API serving shape
- final web analysis behavior

This does not mean pipeline or data architecture should collapse into one monolithic analysis-specific blob.

The UI may present as one coherent analysis page while pipeline, database, and API responsibilities remain modular and reusable.

### 9. Follow Architecture Docs

When creating or expanding an analysis, refer to the documents under `docs/architecture/` and follow their rules.

Especially important:

- `source -> pipeline -> postgres -> api -> web`
- pipeline responsibilities stay in the pipeline layer
- API serves prepared data rather than raw provider payloads
- reusable prepared data is preferred over one-off analysis shortcuts
- domain-first pipeline design is preferred over analysis-first ETL coupling

Do not invent analysis plans that conflict with architecture rules unless the user or developer explicitly approves the exception.

### 10. Reuse First, Hardcoding Last

Analysis plans should prefer reusable building blocks and avoid hardcoding the first supported geography, country set, currency pair, or region deep into the architecture unless that scope is explicitly meant to be permanent.

It is acceptable for v1 scope to start narrow.

It is not acceptable to spread that narrowness as avoidable hardcoding across pipelines, schemas, API contracts, and product structure.

### 11. Open Methodology

MVD analysis should be explicit and inspectable.

The methodology should not be hidden behind black-box outputs, unexplained scores, or unexplained transformations.

The user should be able to see:

- the theory in short plain language
- the formula or decision framework
- the required data inputs
- the distinction between direct observations and derived outputs
- the final interpretation limits

If the analysis uses a proxy, smoothing rule, base-period choice, or simplifying assumption, that should be stated openly.

## What A Master Plan Must Cover

Each analysis master plan should cover these sections in one document:

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

## Phase-First Working Style

The analysis master plan should be used to break implementation into small, careful phases.

Example style:

- Phase A: analysis variable map
- Phase B: reusable data source architecture
- Phase C: first raw ingestion for one USA series
- Phase D: first EU series
- Phase E: normalization layer
- Phase F: analysis input mart
- Phase G: API endpoint
- Phase H: analysis page

Within that phased work, implement one methodology at a time when an analysis contains multiple methodological sections.

The point is to keep delivery incremental while still building reusable shared architecture underneath.

These phases are not all solved at once.

They are worked through one by one, with system design decisions made only when that phase is being addressed.

## Working Rule

If there is uncertainty, prefer:

- simpler interaction
- fewer controls
- stronger defaults
- clearer methodology
- more visible references
- smaller implementation steps

This directory should remain the easiest place for both humans and agents to understand how MVD analyses are planned and expanded over time.

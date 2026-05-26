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

If an analysis later becomes large enough to justify extra documentation, that should happen only after the master plan has exposed a clear need for it.

## Macro Analysis Guidelines

These are the default rules for macro analysis work in MVD.

### 1. Data First

The analysis should be built around data, formulas, tables, and scenario outputs.

Text should stay short and only explain the most important interpretation.

The page should feel closer to a research worksheet than a long article.

### 2. Clear Method

Every analysis page must make its method explicit:

- what is being measured
- which formula or framework is used
- which inputs come from real data
- which inputs are assumptions
- what the output means

If a formula exists, show it clearly on the page.

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

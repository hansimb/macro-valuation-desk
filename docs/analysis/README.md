# Analysis Docs

This directory is the home for analysis-specific planning and development work.

It exists for both humans and agents.

When a new analysis is started, its design, assumptions, data choices, and implementation notes should be documented here before deeper implementation begins.

## What Goes Here

Each analysis should get its own markdown document in this directory.

Recommended naming:

- `YYYY-MM-DD-<analysis-name>-design.md` for the design/spec
- optional follow-up files later if the analysis becomes large

Example:

- `2026-05-26-taylor-rule-design.md`

## Macro Analysis Guidelines

These are the default rules for macro analysis work in MVD.

### 1. Data First

The analysis should be built around data, tables, formulas, and scenario outputs.

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

## Required Sections For A New Analysis Doc

Every new analysis design doc should cover:

1. Goal
2. Why this analysis matters
3. Page structure
4. Formula or framework
5. Inputs from real data
6. Inputs from assumptions
7. User-adjustable parameters
8. Scenario design
9. Interpretation rules
10. References plan
11. Implementation notes

## Working Rule

If there is uncertainty, prefer:

- simpler interaction
- fewer controls
- stronger defaults
- clearer methodology
- more visible references

This directory should become the canonical place to understand how MVD analyses are designed and expanded over time.

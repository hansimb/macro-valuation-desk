# Taylor Rule Master Plan

## Goal

Build the first serious macro analysis in MVD around the Taylor Rule.

The goal is not to produce a placeholder page quickly.

The goal is to build this analysis carefully enough that it teaches the right full-stack system lessons:

- how analysis variables are defined
- how reusable data sourcing should work
- how pipelines feed analysis inputs
- how API and UI layers consume prepared data

## Core Question

What policy rate does a Taylor Rule style framework imply for `USA` and `EU` under a small number of disciplined assumptions?

## Why This Analysis Matters

Taylor Rule is a strong first analysis for MVD because it combines:

- macroeconomic theory
- observable public data
- explicit assumptions
- scenario comparison
- structured interpretation

It is also a good first analysis because it forces the project to connect data engineering and economic reasoning instead of faking either one.

## Variable Map

The analysis needs a clear variable map before any implementation begins.

Expected core variables:

- current policy rate
- inflation measure
- inflation target
- output gap or a proxy for slack/activity
- neutral real rate `r*`
- Taylor-implied rate
- policy gap between actual and implied rate

This variable map should be refined first in implementation.

## Formula / Framework

The page should use a Taylor Rule style formula and show it clearly.

Baseline family:

`i = r* + pi + a(pi - pi*) + b(output gap)`

The final displayed formula must be explicit on the page.

The analysis must also state clearly:

- which terms come from real data
- which terms come from assumptions
- which terms may use proxies

## Data Needs

The analysis requires real data for the variables that should not be user-adjustable.

At minimum, real data will be needed for:

- USA policy rate
- EU policy rate
- USA inflation
- EU inflation
- inflation targets where applicable
- a defensible slack/activity variable or proxy

How those are sourced, ingested, normalized, and served should be worked out phase by phase during implementation.

## Assumptions

The analysis should minimize free assumptions.

The main assumption-driven variable is expected to be:

- `r*`

Possibly one more assumption-based parameter can be exposed later, but only if there is a strong reason.

The user should not be allowed to freely override values that should come from real data.

## User Interaction Model

The page should be both:

- a short analysis
- a controlled scenario tool

The preferred interaction model is:

- show `USA` and `EU` together
- load a default `base` scenario
- provide preset scenarios such as `dovish`, `base`, `hawkish`
- allow only minimal assumption adjustment

The page should not become a broad sandbox or generic calculator.

## Interpretation Model

Interpretation should stay short and disciplined.

The analysis should not present the Taylor Rule as absolute truth.

It should present the result as:

- a rule-based benchmark
- sensitive to assumptions
- useful for comparing policy stance

Text should remain brief and secondary to the data outputs.

## References Plan

The final page must end with references.

References should include:

- Taylor Rule methodology source(s)
- policy rate sources
- inflation sources
- output gap / proxy sources
- any meaningful `r*` framing source

## Implementation Philosophy

This analysis should be implemented in small, careful phases.

The master plan should drive that process.

The point is not to solve data sourcing, pipeline architecture, database design, API shape, and UI behavior all at once.

The point is to uncover and solve them phase by phase through the needs of this analysis.

## Implementation Phases

### Phase A: Analysis Variable Map

Lock the exact variables the analysis needs and define which are:

- data-driven
- assumption-driven
- derived

### Phase B: Reusable Data Source Architecture

Design how analysis data sources should be approached so they are reusable beyond one page.

This includes deciding where direct provider access is appropriate and where helper layers such as OpenBB may help.

### Phase C: First Raw Ingestion For One USA Series

Implement one real raw ingestion path for a USA variable.

The goal is to learn the full ingestion path on a small surface area first.

### Phase D: First EU Series

Repeat the ingestion path for one EU variable and compare differences in source structure and normalization needs.

### Phase E: Normalization Layer

Create the first reusable normalization step that turns raw source-specific series into analysis-ready standardized inputs.

### Phase F: Taylor Input Mart

Build the prepared Taylor Rule input layer that the serving layer can read cleanly.

### Phase G: API Endpoint

Expose a clean product-facing endpoint for the Taylor Rule page.

The API should read prepared data, not raw source data.

### Phase H: Analysis Page

Only after the earlier phases are understood should the final interactive analysis page be built.

## Scope Guard

This analysis should not grow in v1 into:

- a general macro dashboard
- a large central-bank simulator
- a free-form economic modeling lab
- a one-off hardcoded page disconnected from reusable data architecture

## Working Rule

If there is uncertainty, prefer:

- smaller phases
- more explicit variable definitions
- less UI complexity
- more reusable data handling
- more visible methodology

This master plan is the top-level guide for implementing Taylor Rule analysis as a real full-stack system in MVD.

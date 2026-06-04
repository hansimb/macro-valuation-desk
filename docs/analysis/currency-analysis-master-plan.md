# Currency Analysis Master Plan

## Goal

Build a serious `Currency Analysis` for MVD around `EUR/USD`.

The goal is not to create a generic FX dashboard or a shallow market commentary page.

The goal is to build a disciplined full-stack analysis that teaches the right system lessons:

- how currency-analysis variables are defined
- how reusable source and pipeline components support multiple methods
- how prepared datasets feed analysis outputs
- how API and UI layers present open methodology without black-box scoring

## Core Question

How should `EUR/USD` be interpreted when viewed through:

- relative purchasing power parity
- interest rate parity

The analysis should answer whether `EUR/USD` looks rich or cheap versus a long-run inflation anchor and whether money-market rate differentials plus forward pricing support or contradict the spot level.

## Why This Analysis Matters

Currency analysis is a strong next analysis for MVD because it connects:

- macro price-level logic
- interest-rate logic
- observable market pricing
- explicit formula-driven interpretation
- reusable cross-layer data handling

It is also a good systems exercise because it requires the project to separate:

- raw macro and market inputs
- reusable prepared datasets
- methodology-specific derived outputs
- product-facing interpretation

without collapsing pipelines or API responses into one-off analysis shortcuts.

## Analysis Scope

`v1` of `Currency Analysis` contains `2` sections:

- `1.0 Relative Purchasing Power Parity`
- `2.0 Interest Rate Parity`

`Real rate differential` is not a standalone section in this analysis.

It may later be used as supporting reference context where relevant.

`Taylor-implied policy differential` is out of scope for this version.

It may be reconsidered later as a separate extension only after the first `PPP` and `IRP` analysis path is working cleanly.

## Theory-First Rule For This Page

Each section of the page must follow this order:

1. short theory / reasoning
2. explicit formula
3. visible data inputs
4. analysis outputs
5. short takeaway
6. references

The page should feel like an open research worksheet.

It should not hide the model behind a composite score or opaque narrative summary.

## Variable Map

The analysis needs a clear variable map before implementation begins.

### Shared Variables

- current `EUR/USD` spot rate
- historical `EUR/USD` monthly spot history
- observation dates
- methodology metadata

### `1.0 Relative PPP` Variables

- user-selected `base month`
- `EUR/USD` spot at base month
- `US CPI` monthly index level
- `Euro Area CPI` monthly index level
- relative-PPP implied `EUR/USD` path
- current relative-PPP implied `EUR/USD`
- current spot vs PPP deviation in percent

### `2.0 IRP` Variables

- current `EUR/USD` spot rate
- tenor set: `3M`, `6M`, `12M`
- `EUR` tenor-specific money-market / gov-bill proxy rate
- `USD` tenor-specific money-market / gov-bill proxy rate
- tenor-specific rate spread
- tenor-specific `CIP` implied forward
- tenor-specific observed forward, if reliable data exists
- tenor-specific `CIP` gap / basis, only when observed forward exists
- `UIP` theoretical expected move or expected future spot framing

## Formula / Framework

## `1.0 Relative Purchasing Power Parity`

This section uses only the relative-PPP formulation as the active model.

The working model is:

`PPP_t = S_base * (CPI_US_t / CPI_US_base) / (CPI_EA_t / CPI_EA_base)`

Where:

- `PPP_t` = implied `EUR/USD` fair-value level at time `t`
- `S_base` = observed `EUR/USD` spot at the user-selected base month
- `CPI_US_t` = `US CPI` index at time `t`
- `CPI_US_base` = `US CPI` index at the base month
- `CPI_EA_t` = `Euro Area CPI` index at time `t`
- `CPI_EA_base` = `Euro Area CPI` index at the base month

Interpretation:

- if spot is above the implied PPP level, `EUR/USD` is rich versus that inflation anchor
- if spot is below the implied PPP level, `EUR/USD` is cheap versus that inflation anchor

This is a valuation anchor, not a timing model.

## `2.0 Interest Rate Parity`

This section shows both `CIP` and `UIP`, but treats `CIP` as the main analytical anchor.

### `CIP`

Main formula:

`F = S * ((1 + r_EUR) / (1 + r_USD))`

For interpretation, the page may also show the approximation:

`(F - S) / S ~= r_EUR - r_USD`

Where:

- `F` = implied forward for a given tenor
- `S` = current spot
- `r_EUR` = tenor-matched `EUR` money-market / gov-bill proxy
- `r_USD` = tenor-matched `USD` money-market / gov-bill proxy

The analysis should compare:

- spot
- tenor-specific rate spread
- `CIP` implied forward
- observed forward, only if reliable observed forward data is available

### `UIP`

`UIP` is included as a smaller theoretical sub-section.

Its role is to show the expectation-based framework without treating it as a stronger market anchor than `CIP`.

The section should state clearly that `UIP` is a theoretical uncovered-return relationship and not a claim that future spot must follow the implied path mechanically.

## Data Needs

The analysis requires real source data for all non-assumption-driven values.

### Shared Data Needs

- `EUR/USD` spot history at monthly frequency for `PPP`
- current `EUR/USD` spot for `IRP`

### `PPP` Data Needs

- monthly `US CPI` index level
- monthly `Euro Area CPI` index level

The page should expose the selected base month openly.

The model should use monthly index levels directly, not year-over-year inflation rates.

### `IRP` Data Needs

- current or latest available `EUR` tenor-specific market-rate proxies for `3M`, `6M`, `12M`
- current or latest available `USD` tenor-specific market-rate proxies for `3M`, `6M`, `12M`
- observed forward data for `EUR/USD` at `3M`, `6M`, `12M`, if reliable and reasonably available

If an observed forward series is not reliable or not available for a tenor, that tenor's observed-forward comparison should not be shown.

No fake or substitute forward values should be inserted to complete the display.

## Assumptions

This analysis should keep assumptions narrow and visible.

### `PPP` Assumptions

- the user-selected base month is a chosen methodological anchor, not an objective truth
- monthly `CPI` index levels are an acceptable proxy for relative price-level evolution

### `IRP` Assumptions

- tenor-specific money-market / gov-bill proxies are acceptable practical stand-ins for parity calculations in `v1`
- `CIP` is the primary market-anchored framework
- `UIP` is interpretive and theoretical, not a hard prediction model

## User Interaction Model

The page should be one coherent `Currency Analysis` view, not multiple disconnected mini-products.

### `PPP` Interaction

The user should be able to:

- choose a `base month`
- see the resulting relative-PPP implied path
- compare spot vs implied fair value

The section should include:

- short theory text
- formula
- visible data inputs
- a summary view of current spot vs PPP implied level
- a main chart for spot vs PPP implied path
- a short takeaway
- references

### `IRP` Interaction

The section should include:

- short theory text
- `CIP` and `UIP` formulas
- a main `CIP` tenor table for `3M`, `6M`, `12M`
- a smaller `UIP` sub-section below the `CIP` table
- a short takeaway
- references

The `CIP` table should be the main display element for this section.

Tabs are not the preferred primary structure because tenor comparison should remain visible side by side.

## Interpretation Model

Interpretation should stay short and disciplined.

The page should not pretend that either framework predicts precise near-term FX moves.

### `PPP`

`PPP` should be framed as:

- a long-run valuation anchor
- sensitive to base-month choice
- useful for comparing current spot to inflation-adjusted fair value logic

### `IRP`

`IRP` should be framed as:

- a market-pricing and no-arbitrage anchor for forwards
- a tenor-sensitive comparison across `3M`, `6M`, and `12M`
- informative about whether spot, rates, and forwards tell a coherent story

### Takeaways

Each major section should end with a short takeaway block.

The takeaway should summarize the main interpretive result in a few sentences without pretending to be a magical trading signal.

## References Plan

The final page must end each section with references.

References should include:

- PPP methodology references
- IRP methodology references
- primary CPI data sources
- primary spot and forward data sources
- rate-proxy source references
- any proxy justification used in `IRP`

## Full-Stack Implementation Philosophy

This is a full-stack analysis plan.

That means implementation must consider:

- source-layer access
- pipeline preparation
- database/load design
- API serving shape
- final web presentation

At the same time, this should not become one analysis-specific monolith.

The UI may look like one integrated page while source, pipeline, database, and API layers stay modular and reusable.

The architecture must continue to follow:

`source -> pipeline -> postgres -> api -> web`

and remain aligned with the rules under `docs/architecture/`.

## Implementation Phases

### Phase A: Currency Variable Map

Lock the exact inputs and outputs for:

- `PPP`
- `IRP`
- shared spot and metadata handling

Define which fields are:

- observed
- user-selected
- proxied
- derived

### Phase B: Source And Availability Review

Confirm realistic source paths for:

- `EUR/USD` spot history
- `US CPI`
- `Euro Area CPI`
- `EUR` tenor-specific rates
- `USD` tenor-specific rates
- observed `EUR/USD` forward data for `3M`, `6M`, `12M`

The purpose is to verify what is genuinely available before implementation starts pretending it exists.

### Phase C: Reusable Source-Layer Coverage

Implement or extend source-layer adapters only for the raw data required.

This should produce reusable fetch capability for:

- macro price-level series
- FX spot series
- market-rate series
- forward-rate series where supported

### Phase D: Staging Contracts

Create the first reusable staging rules for:

- monthly CPI index levels
- monthly FX spot history
- tenor-specific rate observations
- observed forward quotes if available

The goal is technical standardization, not analysis-specific interpretation yet.

### Phase E: Analytical Transform For `PPP`

Build the first `PPP` analytical transform on top of staged:

- `EUR/USD` spot history
- `US CPI`
- `Euro Area CPI`

This transform should prepare the series needed for base-month-relative `PPP` path calculations without pushing provider-specific logic into serving layers.

### Phase F: Analytical Transform For `IRP`

Build the `IRP` analytical transform on top of staged:

- current spot
- tenor-specific `EUR` rates
- tenor-specific `USD` rates
- observed forwards when available

This transform should prepare `CIP` and `UIP` inputs cleanly enough for serving.

### Phase G: Currency Analysis Mart

Create prepared mart-level structures for:

- `PPP` analysis data
- `IRP` analysis data
- availability metadata needed to suppress missing outputs honestly

The mart should be product-facing in purpose but still reusable by the API.

### Phase H: API Endpoint

Expose a clean `Currency Analysis` route that:

- reads prepared mart data
- exposes `PPP` and `IRP` blocks in stable shapes
- respects missing-data rules without fake completion

The API should not fetch providers directly and should not reproduce pipeline logic.

### Phase I: Web Analysis Page

Build the final `Currency Analysis` page only after the earlier phases are understood.

The page should:

- present theory first
- show formulas clearly
- expose data inputs visibly
- render the `PPP` chart and `IRP` table cleanly
- show short takeaways
- end each section with references

## Scope Guard

This analysis should not grow in `v1` into:

- a multi-pair FX platform
- a generic macro dashboard
- a black-box currency score
- a one-off hardcoded page disconnected from reusable architecture
- a fake-complete parity analysis built on missing market data

## Working Rule

If there is uncertainty, prefer:

- open methodology
- fewer hidden assumptions
- more visible source limitations
- more reusable prepared data
- less UI gimmickry
- smaller implementation phases

This master plan is the top-level guide for implementing `Currency Analysis` as a real full-stack `EUR/USD` analysis in MVD.

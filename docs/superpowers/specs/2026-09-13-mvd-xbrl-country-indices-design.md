# MVD XBRL Country Indices Design

**Date:** 2026-09-13

## Purpose

Replace issuer-published ETF valuation proxies with MVD country indices calculated from company-level regulatory filings and market prices. The system must produce transparent, historically comparable weekly P/E, P/B, P/S, P/CF, exact P/FCF, and dividend-yield observations with explicit coverage, concentration, freshness, uncertainty, methodology, and source lineage.

The first supported filing jurisdictions are the United States, Japan, South Korea, Taiwan, the United Kingdom, and EU/EEA countries whose data passes the same automated availability and quality gates. There is no global aggregate index in this design.

## Product principles

1. A company belongs to the country of its primary equity listing. Legal domicile does not determine the country index.
2. Each country is calculated independently. EU/EEA is a source family, not a combined index.
3. Published country samples target 75–80% of the eligible local equity market capitalization.
4. Historical comparisons use a stable cohort and constituent count within a cohort version.
5. Regulatory XBRL facts are the authority for company fundamentals.
6. Prices come through a replaceable provider interface. Development data must never be represented as commercially licensed production data.
7. Missing or weak data does not disappear. The product publishes the estimate with an uncertainty band, warning level, and reasons when calculation remains mathematically valid.
8. Every number is reproducible from versioned source observations, calculation rules, and cohort membership.

## Supported filing sources

| Jurisdiction | Primary source | Expected history | Filing frequency |
|---|---|---:|---|
| United States | SEC EDGAR XBRL APIs and bulk archives | approximately 2009 onward | quarterly and annual |
| Japan | EDINET XBRL and API v2 | 2008 onward | quarterly, semiannual, and annual as filed |
| South Korea | DART/OpenDART XBRL and bulk downloads | 2007–2011 onward depending on taxonomy | quarterly and annual |
| Taiwan | MOPS XBRL downloads | 2010 onward | quarterly and annual |
| EU/EEA | ESEF filings from national mechanisms and an interchangeable archive adapter | principally 2021 onward | primarily annual |
| United Kingdom | UKSEF/FCA NSM and Companies House iXBRL | mixed older iXBRL; consistent listed-company structured reporting principally from 2021 | primarily annual |

Each adapter emits the same canonical objects and preserves the source document unchanged or by content-addressed reference. Adding a jurisdiction must not change downstream calculation code.

## System architecture

```text
regulatory filing adapters     price adapters       exchange/universe adapters
            |                       |                         |
            v                       v                         v
       raw source store       raw price store          security master
            |                       |                         |
            +-----------+-----------+-------------------------+
                        v
              canonical observations
                        |
                        v
             point-in-time fundamentals
                        |
                        v
           cohort construction and versioning
                        |
                        v
               daily country valuations
                        |
                        v
          weekly aggregation and uncertainty
                        |
                        v
             immutable publication version
                        |
                  API and web UI
```

The pipeline is divided into restartable stages. A failed provider or country can be retried without refetching completed immutable inputs. Publication switches atomically from the previous complete run to the new complete run.

## Adapter contracts

### Filing adapter

Every filing adapter supports discovery by filing date, immutable document retrieval, filer identity, taxonomy identity, reporting period, acceptance/publication timestamp, amendment relationship, and extraction of raw facts with their contexts and units.

Canonical facts retain:

- source jurisdiction, registry, filing ID, document URL, and content hash;
- company and security identifiers available from the filing;
- taxonomy, concept name, context, dimensions, units, decimals, and original value;
- period start/end or instant date;
- filing publication/acceptance timestamp and amendment timestamp;
- consolidated versus separate accounts and continuing versus discontinued operations where tagged.

### Price adapter

`PriceProvider` supplies daily unadjusted close, split-adjusted close, trading currency, trading date, corporate-action adjustment metadata, provider timestamp, and license classification for a security identifier.

Two configurations are required:

- `development`: an explicitly non-production adapter may be used to validate calculations and coverage;
- `production`: publication is disabled unless the configured source is approved for the intended commercial derived-data use.

Raw prices are never exposed through the product API. The adapter boundary allows the provider to be replaced without changing canonical fundamentals or index calculation.

### Universe adapter

The universe adapter supplies primary listings, security type, exchange, trading currency, active dates, share class, issuer relationship, and delisting or corporate-action state. Funds, ETFs, preferred shares, depositary receipts when the primary ordinary share is already represented, shell companies, and duplicate share classes are excluded by deterministic rules.

## Canonical financial model

The normalization layer maps jurisdiction-specific taxonomies into versioned concepts:

- revenue;
- net income attributable to common owners;
- common equity attributable to common owners;
- operating cash flow;
- capital expenditure paid in cash;
- common dividends paid;
- basic and diluted weighted-average shares;
- period-end shares outstanding;
- reporting currency.

Every canonical value records whether it was reported directly, derived from cumulative periods, converted between units or currencies, carried forward as the latest valid point-in-time observation, or unavailable.

Flow facts use trailing twelve months. Four discrete quarters are summed when available. A discrete quarter may be derived from cumulative filings, for example `Q2 = H1 - Q1` and `Q4 = FY - 9M`. Stock facts such as equity use the latest valid reported instant. No filing can affect a valuation date earlier than its publication or acceptance timestamp.

Maximum age is part of the metric definition and warning model. A carried-forward observation remains usable while it is the latest report the issuer was required to have published. Late or unusually old filings add staleness uncertainty rather than silently changing the cohort.

## Country cohorts

For each country and cohort effective date:

1. Build the complete eligible primary-listing universe.
2. Calculate each company's market capitalization using the security price and point-in-time shares outstanding.
3. Sort descending by market capitalization.
4. Select a stable constituent count whose cumulative market capitalization is within the 75–80% target band.
5. If discrete company weights make the band impossible, choose the closest cohort at or above 75% and attach a persistent coverage-band warning.
6. Freeze membership and constituent count for the cohort version.

Cohorts are reconstituted annually. Between annual reviews, changes are limited to delistings, mergers, bankruptcies, invalid securities, and other events that make a constituent impossible to retain. A forced replacement keeps the constituent count constant where an eligible replacement exists and creates a new minor cohort version.

The 75–80% band is the formation target. During the year, 72.5–82.5% is the operating tolerance that preserves the stable cohort. Moving outside that tolerance produces a coverage warning. If coverage remains outside it for two consecutive published weeks, an exceptional reconstitution creates a new cohort version. The outgoing and incoming cohorts are both calculated on the transition week so the UI can separate the membership effect from market movement.

For every historical comparison, the API identifies the cohort version. A cohort transition is measured on an overlap date using both the outgoing and incoming cohorts, and its estimated valuation impact is stored as a bridge. The UI marks cohort boundaries instead of presenting them as ordinary market movement.

## Valuation calculations

Daily calculations aggregate company numerators and denominators; they never average company-level valuation multiples.

```text
P/E       = aggregate market capitalization / aggregate TTM common net income
P/B       = aggregate market capitalization / aggregate latest common equity
P/S       = aggregate market capitalization / aggregate TTM revenue
P/CF      = aggregate market capitalization / aggregate TTM operating cash flow
P/FCF     = aggregate market capitalization / aggregate (TTM operating cash flow - TTM cash capex)
Div yield = aggregate TTM common dividends / aggregate market capitalization
```

Losses and negative cash flows remain in aggregate denominators. If an aggregate denominator is zero or negative, the multiple is not economically meaningful and is returned as unavailable with the exact reason. Exact P/FCF always uses reported cash from operations minus cash capital expenditure; it is never substituted with a provider multiple.

Metric applicability is explicit. P/CF and P/FCF exclude industries where regulatory cash-flow presentation makes the measure structurally non-comparable, especially banks and insurers. P/S for those industries is also reported only when the canonical revenue definition is comparable. Each metric therefore reports both whole-cohort coverage and eligible-scope coverage.

## Weekly observations

The pipeline gathers filings continually or daily. The official valuation product is weekly and is published on Monday after weekend processing.

For each country:

1. Calculate a point-in-time aggregate valuation for every completed local trading day in the preceding Monday–Friday week.
2. Use that day's closing prices, foreign-exchange conversion, share state, and only filings published by that day's cutoff.
3. Retain all daily aggregate values for audit and diagnostics.
4. Publish the median of the valid daily aggregate values as the weekly headline.
5. Require at least three valid trading-day observations; otherwise publish an unavailable weekly state with reasons.
6. Publish the weekly minimum, maximum, median, observation count, and actual local valuation dates.

The median limits the influence of a one-day price spike or bad close without applying a backward-looking smoothing model. A filing released during the week enters only the daily observations after its publication cutoff.

## Coverage and comparability

Each daily and weekly observation records:

- actual constituent count and fixed cohort target count;
- market coverage of the cohort;
- direct reported-fact coverage by market-cap weight;
- valid carried-forward coverage by market-cap weight;
- missing or invalid coverage by market-cap weight;
- metric-eligible coverage;
- largest constituent weight;
- top-five and top-ten concentration;
- effective constituent count `1 / sum(weight_i^2)`;
- membership overlap with the prior cohort.

The cohort is never silently reduced to companies with convenient data. Metrics use the fixed cohort and expose missingness. When a current or valid carried-forward fact is missing, the published point estimate uses the median of the multiple-imputation distribution for that constituent so its weight does not disappear. The observation is explicitly labeled partly estimated, and the imputed weight and interval contribution are reported. Historical charts retain observations with warnings so the user can see data-quality changes, but comparisons and rankings are disabled when uncertainty is high or experimental.

## Uncertainty model

The product reports a sensitivity interval, not a classical random-sample confidence interval. The cohort is capitalization-selected and therefore is not a random sample.

The uncertainty engine combines:

1. **Missing-fact sensitivity:** multiple imputations drawn from point-in-time distributions for the same country, industry, size band, and metric. The median imputation keeps the fixed constituent in the published point estimate, while the full distribution determines its uncertainty contribution. Imputed values never count as reported or carried-forward source coverage.
2. **Staleness sensitivity:** historical filing-to-filing changes for comparable companies scale the uncertainty assigned to old carried-forward facts.
3. **Concentration sensitivity:** leave-one-out and leave-top-group calculations measure how much dominant constituents change the aggregate.
4. **Cohort-transition sensitivity:** dual calculation on cohort overlap dates measures membership effects.
5. **Coverage sensitivity:** historically observed fundamentals for companies outside the selected cohort estimate the plausible effect of the omitted market-cap tail when available.

The engine uses deterministic seeded simulations and stores the model version, inputs, number of draws, median, lower and upper percentiles, and component contributions. Initial intervals are labeled `experimental` until backtesting supplies enough realized filing revisions and cohort transitions to calibrate them.

Warning levels are `low`, `moderate`, `high`, and `experimental`. Warning reasons are structured codes with human-readable explanations, affected market-cap weight, and estimated contribution to interval width. A high or experimental observation remains visible, but country rankings and precise cross-country claims are suppressed.

## Data-quality and failure behavior

A calculation can produce `complete`, `warning`, `unavailable`, or `failed`:

- `complete`: all hard invariants pass and uncertainty is low;
- `warning`: calculation is valid but coverage, concentration, staleness, cohort transition, or source quality widens uncertainty;
- `unavailable`: the value is not mathematically or methodologically meaningful, including a non-positive denominator or fewer than three daily observations;
- `failed`: a required calculation stage did not complete.

Provider failures preserve the previous published run. They do not delete history or publish partial rows as the latest version. Weekend retries occur through Saturday and Sunday. Monday publication points only to a fully validated immutable run.

## Storage boundaries

The database separates:

- immutable raw filing documents and facts;
- security identity and listing history;
- daily raw/normalized prices and corporate actions;
- canonical financial facts and derivation lineage;
- point-in-time company fundamentals;
- versioned country cohorts and memberships;
- daily aggregate valuations;
- weekly published observations;
- uncertainty simulation summaries and warning reasons;
- source and methodology references.

Existing ETF/issuer snapshots remain historical legacy data during migration but are not mixed with MVD-calculated series. New tables and API fields use an explicit methodology identifier so no chart can splice provider and MVD methodologies without labeling the break.

## API and user experience

The market overview has separate regional sections and one row per available country. A row shows weekly metrics, actual company count, effective company count, market coverage, fundamental coverage, uncertainty level, and the latest valuation week. Metrics unavailable for every visible country are hidden from the overview.

Selecting a row opens the country page with:

- weekly historical charts for every available metric;
- weekly range and sensitivity interval;
- coverage, effective count, and concentration history;
- cohort changes and bridge impacts;
- warning timeline and structured reasons;
- fundamental freshness distribution;
- formula, inclusion rules, source registries, price methodology, and methodology version;
- links from claims and source rows to the exact regulatory references.

The UI describes the weekly headline as the median of daily country-level aggregate valuations, not a Friday close and not an average of company multiples.

## Delivery sequence and feasibility gates

The work is split into independently reviewable increments:

1. Prove one full historical path for the United States and one non-US taxonomy using official XBRL data.
2. Validate a development price adapter and quantify symbol, corporate-action, delisting, and history coverage.
3. Block production publication until a price source permits the intended commercial derived-data use.
4. Build canonical point-in-time facts and metric calculations.
5. Build stable cohorts, daily aggregates, weekly medians, and coverage diagnostics.
6. Add the experimental uncertainty model and calibration storage.
7. Expose versioned API contracts and country pages.
8. Add EDINET, OpenDART, MOPS, ESEF, and UKSEF adapters one at a time, promoting a country only after automated quality gates pass.
9. Retire issuer-proxy presentation only after replacement MVD series pass reconciliation and UI acceptance checks.

Every increment is committed atomically with its relevant tests and documentation. Pipeline, API, shared-contract, UI, and documentation changes are not mixed unless they form one inseparable independently testable boundary.

## Acceptance criteria

- A published weekly metric can be traced to daily aggregate values, cohort membership, company fundamentals, raw XBRL facts, prices, FX observations, and methodology versions.
- No filing is used before its public acceptance or publication time.
- Weekly headline values equal the median of at least three valid daily country aggregates.
- Country cohorts remain stable within a cohort version and target 75–80% market coverage.
- A cohort outside the 72.5–82.5% operating tolerance is warned immediately and reconstituted with an overlap bridge after two consecutive published weeks outside the tolerance.
- Coverage, actual and effective company counts, concentration, freshness, sensitivity interval, warning level, and warning reasons accompany every published observation.
- Missing or stale company data never causes silent constituent substitution.
- Model-imputed facts remain explicitly separate from reported and carried-forward coverage and contribute visibly to the sensitivity interval.
- Exact P/FCF uses cash from operations minus cash capital expenditure.
- A failed or partial weekend run cannot replace the previous complete publication.
- The UI presents methodology and source references with the metric they support.
- Commercial production publication cannot run with a development-only price adapter.

# Macro Product Design

## Goal

Define the macro-side product philosophy, information architecture, feature shape, and first-pass analysis framework for Macro Valuation Desk so the product can create genuine expert-level value through high-signal macro analysis instead of broad but shallow data coverage.

## Product Position

Macro Valuation Desk on the macro side is not a generic data terminal and not a broad macro data library.

Its purpose is to help a serious user form a fast, robust view of the global macro environment by focusing on the small set of economic drivers that matter most for the larger cycle, inflation path, financing conditions, and real-economy direction.

The macro product should feel useful even to a strong economist because it prioritizes:

- theoretical seriousness
- transparent methodology
- leading or transmission-sensitive indicators
- disciplined selection over data abundance
- consistent global framing

## Core Philosophy

The macro product follows a strict `Pareto-first` philosophy.

It should not try to track everything. It should track only a small set of macro drivers with the strongest theoretical and empirical importance for understanding the broader economic environment.

The goal is not quantity. The goal is quality and signal density.

This means the product is designed around the following principles:

- `Pareto-first`: follow the 1 percent of macro inputs that explain the largest share of the big picture
- `Causal-first`: prefer drivers and transmission channels over headline reporting
- `Leading-first`: prefer indicators that move early or sit close to the causal chain
- `Theory-backed`: every included metric must have a clear economic rationale
- `Transparent`: no black boxes, hidden scoring logic, or unexplained composites
- `Global but consistent`: use the same analytic framework across major market regions where data quality permits

The macro experience should not tell the user what to think. It should present the most meaningful data, the interpretation framework, and the methodological background clearly enough that an expert user can form their own judgment quickly.

## What The Product Is Not

The macro product should not become:

- a giant repository of every available macro series
- a dashboard that optimizes for number of charts
- a beginner explainer product
- a black-box signal engine that outputs opinions without showing the mechanism
- a region-by-region research suite with separate country logic for every area

## User Model

The macro product assumes an expert or near-expert user.

That means:

- the user already knows how to read macro charts
- the user does not need simplified "translation" into basic language
- the user does benefit from a cleaner structure, stronger indicator selection, and explicit methodological framing
- the user wants to know why a given series matters, whether it leads or lags, and what caveats apply

## Geographic Scope

The macro product aims to give a fast view of the global economy rather than only one domestic economy.

The main recurring regions are:

- `USA`
- `Euro Area`
- `China`
- `Asia ex-China`

These are not separate product modules. They are parallel views inside the same macro framework.

The intent is not to build a heavy region-comparison tool. Instead:

- the same analytic structure should be reused across these regions
- charts may show multiple regional time series together when useful
- if a relevant data series is not available with acceptable quality for a region, it can be omitted for that region
- the framework should stay simple and robust rather than forcing artificial parity

## World Data Rule

The label `World` must be handled carefully and honestly.

`World` should appear only in the headline section, where it can use externally sourced world-level macro data from credible institutions such as IMF-style sources when available.

The product must not label internally derived regional averages, medians, or blended signals as `World`.

If the system computes a normalized median or similar aggregate from `USA`, `Euro Area`, `China`, and `Asia ex-China`, that output is an internal product analysis construct, not a literal world statistic. It should be presented as such and never misrepresented.

## Product Structure

The macro main page should have three layers.

### 1. Headline Layer

The first layer gives a concise but reasonably broad current-state view.

This layer should support a dropdown such as:

- `World`
- `USA`
- `Euro Area`
- `China`
- `Asia ex-China`

Headline cards can be relatively comprehensive as long as they remain compact and readable.

Typical values may include:

- GDP growth
- CPI
- policy rate
- unemployment or another anchor labor measure
- other foundational context metrics if they earn their place

Each headline statistic should show:

- the main level prominently
- a smaller `MoM`, `YoY`, or equivalent change figure beside it where relevant
- optional short directionality context if it improves readability

This layer exists for orientation, not for the deepest value creation.

### 2. Driver Analysis Layer

Below the headline layer, the macro page should show the product's true center of gravity:

- `6 driving economic analysis areas`

Each driver area should appear as its own box or card with:

- a compact signal summary
- one or more small charts or sparklines
- a quick sense of direction or state
- room for an internally derived normalized signal if useful

This normalized signal can be based on the product's own internal aggregation logic across regional series, but it should be framed as an internal analysis aid rather than a literal macro statistic.

### 3. Drilldown Layer

Each driver area should be openable into a deeper analysis view.

That deeper view should contain:

- the full chart set for the driver
- methodology notes
- economic rationale
- source information
- update frequency
- caveats and weaknesses
- explanation of whether the indicator is leading, coincident, or lagging

The drilldown is where the product earns trust.

## Design Inspiration

The product may draw inspiration from sites such as `longtermtrends.net` in the sense of making chart-based research accessible and navigable.

However, Macro Valuation Desk should differ in important ways:

- more robust and methodologically serious
- more focused on macro real economy and transmission mechanisms
- less centered on stock-market-derived narrative charts
- more explicit about theory, data quality, and caveats

## Priority Driver Areas

The initial design should work around six driver families.

These are not yet final frozen data definitions. They are the current highest-priority analysis categories.

### 1. Liquidity and Money Impulse

This area focuses on money and credit dynamics that can influence demand, inflation, and financial conditions with a lag.

Why it matters:

- it sits close to deep macro causality
- it is more informative than many headline indicators
- it helps frame future pressure rather than only present conditions

### 2. Credit Conditions and Financing Stress

This area tracks the availability and pricing of financing, credit tightness, and stress in the funding environment.

Why it matters:

- credit transmission is one of the central links between policy and the real economy
- financial tightening often matters before lagging macro damage becomes obvious

### 3. Price Pressure Pipeline

This area examines where inflation pressure is being created, transmitted, or relieved before it fully appears in headline inflation measures.

Why it matters:

- the product should not stop at reporting CPI
- it should map the upstream and transmission-side forces behind inflation
- this is high priority and should rank above some more familiar but lower-signal categories

### 4. Consumer Behavior and Demand Resilience

This area tracks the resilience or weakening of household demand and related cyclical sensitivity.

Why it matters:

- consumption is central to many economies
- consumer behavior can reveal whether macro resilience is broadening or fading
- selective cyclical demand series may add earlier information than lagging output data

### 5. Industrial and Trade Pulse

This area captures the industrial cycle, goods demand, export sensitivity, and external trade momentum.

Why it matters:

- it is especially relevant for the global cycle
- it often turns earlier than slower aggregate output measures
- it is important across Europe, China, and Asia ex-China in particular

### 6. Housing and Construction Transmission

This area captures the interest-rate-sensitive housing and construction channel.

Why it matters:

- it is a classic transmission path from rates to real activity
- it can be highly useful in some major economies
- it may be less uniform across regions and should therefore be handled with realism about data quality and comparability

## Robustness View On The Six Drivers

Not all six categories are equally easy to measure in a timely and consistently leading way.

Current design view:

- strongest foundational candidates: `Liquidity and Money Impulse`, `Credit Conditions and Financing Stress`, `Price Pressure Pipeline`
- strong but more data-sensitive categories: `Consumer Behavior and Demand Resilience`, `Industrial and Trade Pulse`
- theoretically valuable but potentially less uniform across regions: `Housing and Construction Transmission`

This prioritization should influence implementation sequencing, but not remove the lower-ranked categories from the design framework.

## Candidate Metrics Per Driver

The plan should record candidate metrics without freezing the final implementation set too early.

For each driver area, the design should preserve:

- `3 strongest candidate metrics`
- `2 extra candidate metrics`

These are idea slots, not final commitments. Final metric selection must be done carefully during implementation based on data availability, update frequency, regional comparability, and methodological quality.

### 1. Liquidity and Money Impulse

Strong candidates:

- broad money growth `YoY`
- real broad money growth `YoY`
- credit impulse or private sector credit growth `YoY`

Extra candidates:

- central bank balance sheet liquidity proxy
- real policy liquidity spread proxy

### 2. Credit Conditions and Financing Stress

Strong candidates:

- bank lending standards
- corporate credit spreads
- bank loan growth or private credit growth

Extra candidates:

- high-yield versus investment-grade stress spread proxy
- financial conditions subcomponent with transparent construction

### 3. Price Pressure Pipeline

Strong candidates:

- producer price inflation or similar upstream price series
- wage growth proxy
- import price or commodity pass-through proxy

Extra candidates:

- shelter or housing-cost transmission proxy
- core goods versus services pressure split

### 4. Consumer Behavior and Demand Resilience

Strong candidates:

- consumer confidence
- real retail sales growth
- auto sales or auto demand proxy

Extra candidates:

- discretionary spending proxy
- household savings or spending-capacity proxy

### 5. Industrial and Trade Pulse

Strong candidates:

- manufacturing new orders
- export orders or export growth
- inventory or orders-balance proxy

Extra candidates:

- freight or logistics activity proxy
- industrial production momentum

### 6. Housing and Construction Transmission

Strong candidates:

- building permits
- housing starts or construction starts
- mortgage or housing finance cost proxy

Extra candidates:

- homebuilder sentiment or construction confidence proxy
- property sales or turnover proxy

## Composite And Internal Signal Rules

The product may create internal normalized signals, composite views, or medians when helpful for navigation and summary.

However, these must follow strict rules:

- they must be explicitly identified as internal analysis constructs
- their components must be visible
- their normalization logic must be explainable
- any weighting or smoothing must be transparent
- they must never be confused with official world-level macro statistics

## Methodology Transparency Requirements

For every important chart or metric, the product should make it possible to inspect:

- what the series measures
- why it matters economically
- where it sits in the causal chain
- whether it is leading, coincident, or lagging
- how often it updates
- what its main limitations are
- whether it is revision-sensitive
- where the data comes from

This transparency is a core product requirement, not an optional documentation nicety.

## Product Value Proposition

The macro side of Macro Valuation Desk should create value by making the global macro picture faster to understand, more theoretically grounded, and more analytically usable than standard broad-data dashboards.

Its advantage should come from:

- disciplined indicator selection
- clearer macro driver hierarchy
- better organization of transmission channels
- transparent internal methodology
- global framing without fake precision

The product should feel like a serious macro research workspace, not just a nicer chart gallery.

## Out Of Scope For This Design

This design does not yet finalize:

- the exact data source for every metric
- the final formulas for internal normalized signals
- the exact chart-library implementation
- the complete API contract for every driver box and drilldown
- the equity or stock-markets side of the product

Those belong to the next planning and implementation layers.

## Design Outcome

If executed well, this macro design gives Macro Valuation Desk a clear identity:

- expert-facing
- high-signal
- theory-backed
- globally aware
- methodologically honest
- focused on the small number of macro forces that actually matter most

# Stock Market Product Design

## Goal

Define the stock-market-side product philosophy, information architecture, valuation framework, and first-pass market coverage for Macro Valuation Desk so the product can assess broad equity-market valuation risk more seriously than simple country P/E dashboards.

## Product Position

The stock market side of Macro Valuation Desk should act as a `Global Equity Valuation Desk`.

Its job is to help the user understand whether broad equity-market risk is currently low, moderate, or high by examining the valuation level of major market indexes through multiple lenses rather than a single headline multiple.

The product should help with:

- broad market timing context
- valuation-aware risk management
- long-horizon allocation framing
- historical context for major indexes
- disciplined cross-market valuation research

It should not try to become a single-stock valuation tool.

## Core Philosophy

The central philosophy is:

`Valuation is multidimensional.`

No serious valuation view should rely on one ratio alone.

The product must therefore avoid reducing a market to a single raw `P/E` figure or a simplistic `cheap / fair / expensive` label. A broad market can look cheap on one metric, rich on another, cycle-distorted on a third, and reasonable relative to bonds or GDP. The system should preserve that structure instead of flattening it away.

This leads to the following principles:

- `Multidimensional valuation`: use multiple valuation families, not one headline ratio
- `History first`: current values are not meaningful without historical context
- `Structure over simplification`: separate earnings-based, book-based, sales-based, cash-flow-based, and macro-relative valuation views
- `Methodological honesty`: always state whether the measured object is a cash index, benchmark index, or ETF proxy
- `No fake precision`: avoid turning a complex valuation reality into an overconfident single "truth number"
- `Overview plus drilldown`: allow fast scanning at the top level, while keeping deeper chart-based research one click away

## What The Product Is Not

The stock-market product should not become:

- a country P/E ranking page with thin methodology
- a one-metric heatmap
- a black-box market score engine
- a pseudo-forecasting model that pretends to know precise future returns
- a copy of WorldPE with more columns but the same weak assumptions

## User Model

The intended user is an expert or serious market participant.

That means:

- the user is comfortable reading valuation ratios and long historical charts
- the user does not need beginner-level simplification
- the user does need rigorous structure, historical framing, and methodological transparency
- the product should support the user's own judgment rather than replace it

## Measurement Object Rule

The product must be explicit about what it measures.

Where possible, the preferred object is the actual broad market index. If some valuation fields are only available through a representative ETF or fund proxy, that fact must be stated clearly in the methodology.

The UI may visually suggest a country through a flag, but the analytics must still be tied to the actual underlying measured object:

- index name
- ticker or abbreviation
- whether the metric comes from the index, an index family, or an ETF proxy

This is an important correction relative to weaker country-valuation sites that speak about countries while actually measuring ETF structures.

## Main Product Promise

For each covered market index, the product should provide a robust valuation research frame built around:

- current valuation level
- historical valuation context
- earnings-based versus book-based valuation
- cycle-smoothed valuation
- macro-relative valuation
- forward return or risk framing, used carefully and without pseudo-precision

This is the backbone of every serious index or ETF analysis page in the product.

## Valuation Framework

### 1. Current And Historical Valuation Level

Current values should always be shown together with historical context.

That means the product should not simply show today's metrics. It should show:

- the current level
- the long-run time series
- historical percentiles
- possible z-score style positioning
- historical ranges
- relation to earlier peaks, troughs, and normal valuation zones

Without this layer, current valuation figures are low-information.

### 2. Earnings-Based, Book-Based, Sales-Based, And Cash-Flow-Based Valuation

The product should make these valuation families explicit rather than blending them invisibly.

This includes:

- earnings-based valuation
- book-based valuation
- sales-based valuation
- cash-flow-based valuation
- payout-oriented valuation

The point is to preserve structure. Different markets can look very different depending on whether the lens is profits, balance sheet, sales, free cash flow, or shareholder payout.

### 3. Cycle-Smoothed Valuation

This layer exists to reduce the distortion caused by temporary earnings booms or earnings collapses.

The key example is:

- `CAPE / Shiller P/E`

Potential later extensions may include other medium- or long-horizon real-earnings smoothing variants.

This is essential because a normal trailing `P/E` can look misleadingly low during peak margins or misleadingly high during recession-driven earnings weakness.

### 4. Macro-Relative Valuation

The product should also show how valuation relates to the macro and discount-rate environment rather than only to its own history.

This layer may include:

- earnings yield versus government bond yield
- equity risk premium style framing
- Buffett indicator
- possible valuation versus nominal growth or real-rate context

This is one of the most valuable differentiators of the product because it places market valuation into the broader cost-of-capital environment.

### 5. Forward Return Or Risk Framing

The product should be cautious here.

It should not begin with a sophisticated expected-return engine that produces precise long-run return forecasts. That would create fragile pseudo-accuracy.

Instead, the product can provide measured framing such as:

- historically elevated valuations have often implied thinner long-run return asymmetry
- historically compressed valuations have often implied better long-run asymmetry
- thin or rich equity risk premium regimes can change risk framing materially

This should remain a framing layer rather than a precise prediction layer.

## Core Valuation Metrics

The first-pass core set of raw valuation metrics should be:

- `P/E`
- `forward P/E`
- `P/B`
- `dividend yield`
- `price-to-sales`
- `free cash flow yield`
- `CAPE`

These seven metrics are sufficient for the overview-level valuation position logic.

## Additional Important Metrics

The design should also plan for additional metrics and contextual analyses outside the seven-metric overview core:

- `EV/EBIT`
- `EV/EBITDA`
- `Buffett indicator`
- `earnings yield vs government bond yield`
- `equity risk premium`

These are important and should appear in deeper analysis views, but they do not need to be part of the initial overview-position construction.

## Historical Valuation Position

The product should use an overview construct called:

`Historical Valuation Position`

This is intentionally not called a score in the user-facing product.

### Why It Exists

The top-level map and summary views need a single navigation-friendly logic for color and quick reading. A carefully constrained historical valuation position is acceptable if it is honest about what it measures.

### What It Means

Historical Valuation Position should mean only this:

- where the market's current valuation sits relative to its own historical valuation distribution across the selected core valuation metrics

It does **not** mean:

- fair value
- a buy or sell signal
- expected return
- a complete scientific summary of the market

### Construction Rules

The construction should follow strict limits:

- use only the seven core raw valuation metrics
- use historical positioning logic rather than raw level comparison alone
- keep the methodology inspectable
- do not merge in macro-relative metrics at this stage
- treat it as an overview-layer aid, not the final analysis

### Suggested Qualitative States

The user-facing representation can use five qualitative states:

- `Historically Compressed`
- `Moderately Compressed`
- `Historically Neutral`
- `Moderately Elevated`
- `Historically Elevated`

This is more honest and more useful than `cheap / fair / expensive`.

## Product Structure

The stock-market main page should be a hybrid of:

- efficient navigation inspired by simple country-valuation sites
- deeper research structure inspired by serious chart-driven analysis sites

### 1. Map Layer

The top of the page can use a world map interface inspired by the usability of country-valuation sites.

However, the map should not inherit their simplistic logic.

The map should:

- use country flags or country shapes as navigation aids
- color markets by `Historical Valuation Position`
- open tooltips on hover
- let the user move quickly into a market drilldown

Each tooltip should show:

- flag only for country identity
- index or ETF name
- abbreviation or ticker
- current valuation metrics snapshot
- qualitative historical valuation position

The map is a UI/navigation layer, not the full analysis.

### 2. Summary Table Layer

Below the map, the main page should show a structured summary table.

This table is not primarily for ranking countries against one another. It is a fast navigation and snapshot layer.

Suggested content:

- flag
- index or ETF name
- abbreviation
- current valuation summary values
- valuation position label
- link or click path to detailed analysis

The product should avoid overly simplistic "cheap / expensive" columns.

### 3. Drilldown Analysis Layer

When the user opens a specific market, the product should move from overview to full research view.

That research view should follow a top-down sequence:

- broad valuation picture
- structural valuation framing
- cycle-smoothed valuation
- macro-relative valuation
- full historical chart detail

This keeps the design aligned with the idea that analysis should move from the big picture toward more index-specific detail.

## Detailed Market Page Structure

Each market page should contain sections such as:

### 1. Valuation Snapshot

- current values for the main metrics
- historical valuation position
- short methodological notes

### 2. Raw Valuation History

- historical `P/E`
- historical `forward P/E`
- historical `P/B`
- historical `dividend yield`
- historical `price-to-sales`
- historical `free cash flow yield`

### 3. Cycle-Smoothed Valuation

- `CAPE`
- possible long-horizon smoothed earnings views later

### 4. Macro-Relative Valuation

- earnings yield versus bond yield
- equity risk premium framing
- Buffett indicator

### 5. Methodology

- what is being measured
- whether the source is index-native or ETF-proxy-based
- update frequency
- limitations and caveats

## No User-Facing Summary Score

The product should not expose a generic all-purpose valuation score.

The only acceptable aggregation layer is the narrowly defined `Historical Valuation Position`, and even that should be treated as:

- a navigation and overview aid
- not the main analysis itself

This avoids black-box behavior and preserves the credibility of the product.

## Covered Markets

The product should maintain a larger master list for future coverage, even if implementation starts with a smaller subset.

### Recommended Shortlist

- `USA: S&P 500 / SPX`
- `USA: Nasdaq Composite / IXIC`
- `USA: FT Wilshire 5000 / FTW5000`
- `Europe: STOXX Europe 600 / SXXP`
- `Finland: OMX Helsinki 25 / OMXH25`
- `Sweden: OMX Stockholm 30 / OMXS30`
- `Norway: OBX Index / OBX`
- `Denmark: OMX Copenhagen 25 / OMXC25`
- `Germany: DAX / DAX`
- `France: CAC 40 / CAC 40`
- `United Kingdom: FTSE 100 / FTSE 100`
- `Switzerland: Swiss Market Index / SMI`
- `Netherlands: AEX Index / AEX`
- `Italy: FTSE MIB / FTSEMIB`
- `Spain: IBEX 35 / IBEX`
- `Japan: Nikkei 225 / N225`
- `China: CSI 300 / CSI300`
- `Hong Kong: Hang Seng Index / HSI`
- `South Korea: KOSPI / KOSPI`
- `Taiwan: Taiwan Weighted Index / TAIEX`
- `India: NIFTY 50 / NIFTY`
- `Australia: S&P/ASX 200 / ASX 200`

### Master List Extensions

The broader design can also leave room for:

- `Japan: TOPIX / TOPIX`
- `India: BSE SENSEX / SENSEX`
- `China: Shanghai Composite / SSE Composite`

These may be useful later, but the shortlist above is strong enough to define the product shape clearly.

## Design Inspiration

The product can borrow selected interaction patterns from `WorldPE`-style sites:

- fast world map navigation
- quick top-level table browsing
- easy market selection

It can also borrow from `Longtermtrends`-style research experiences:

- chart-first drilldown
- long historical context
- explanatory framing around charts

But Macro Valuation Desk should improve on both by:

- using many valuation lenses instead of one
- showing better methodology
- avoiding false country-level simplifications
- distinguishing overview constructs from real analysis

## Product Value Proposition

The stock-market side of Macro Valuation Desk should create value by showing whether a major equity market is expensive, compressed, mixed, or cycle-distorted through a richer, more historically grounded and more macro-aware framework than simple market P/E dashboards.

Its advantage should come from:

- multidimensional valuation
- historical context everywhere
- cycle-smoothed analysis
- macro-relative analysis
- honest handling of measurement objects
- strong drilldown research depth

## Out Of Scope For This Design

This design does not yet finalize:

- the exact pipeline source for every valuation metric
- the exact formula for the Historical Valuation Position
- the exact weighting or normalization method for metric aggregation
- the exact charting library or frontend implementation
- single-stock analysis
- a broad emerging-markets or frontier-markets product scope

Those belong to later planning and implementation layers.

## Design Outcome

If executed well, this product becomes more than a nicer country valuation table.

It becomes a serious global equity valuation workspace that helps the user judge broad market risk through multiple valuation dimensions, deep history, cycle-aware framing, and macro-relative context.

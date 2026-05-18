# MVD UI Refresh Design

## Goal

Refresh the `Macro Valuation Desk` web UI so it feels sharp, modern, and product-grade rather than generic or overly rounded. The refreshed UI should borrow the structural strengths of `../pro-site-cms` while adapting them to a more serious macro and equity research product shell.

## Design Direction

- Style direction: `Editorial terminal luxury`
- Layout approach: `Structural copy, stronger product shell`
- Theme count: `one theme only`
- Default tone: dark, sharp, high-contrast, restrained
- Accent direction: `icy blue-green`

The UI must avoid the usual AI-generated product look:

- no oversized rounded cards
- no soft purple gradients
- no generic SaaS dashboard feel
- no visual clutter pretending to be sophistication

Instead, the product should feel:

- editorial
- institutional
- high-signal
- modern but restrained
- interesting enough to invite deeper exploration

## Reference Project Reuse

The UI should deliberately reuse structure and code patterns from `pro-site-cms` where that helps consistency and speed:

- top navigation structure
- mobile drawer navigation
- container rhythm and page spacing
- footer composition
- sharp token philosophy
- background atmosphere treatment

However, the resulting product should not feel like a CMS or content site. It should feel like a research workspace.

## Global Shell

### Navigation

Use a thin top navigation bar inspired by `pro-site-cms`.

Required items:

- `Home`
- `Macro`
- `Equity Markets`

Behavior:

- active route is highlighted with the icy blue-green accent
- desktop uses inline navigation
- mobile uses a drawer menu
- branding stays compact and serious rather than logo-heavy

### Footer

Add a simple but polished footer.

Required content:

- navigation links
- short product description
- one small extra product-status or methodology-oriented detail

The footer should feel intentional, not decorative.

### Theme

Use a single dark theme only.

Theme principles:

- sharp or near-sharp radii
- subtle border system
- restrained glow in the page background
- strong typography hierarchy
- minimal accent usage

The accent should be an icy blue-green distinct from the green used in `pro-site-cms`.

## Page Designs

### Home

The home page should follow a `hybrid` structure:

1. strong hero
2. immediate intelligence strip
3. curated section entries

#### Home Hero

The hero should quickly establish MVD as a serious workspace for macro and equity-market context. It should feel like the beginning of a high-end research product, not a marketing landing page.

#### Intelligence Strip

Immediately below the hero, show compact placeholder insight blocks with fast, interesting, high-signal snippets from both macro and equity domains.

This layer exists to:

- create quick interest
- show that the product contains real analytical depth
- pull the user into deeper browsing

#### Curated Section Entries

Below the intelligence strip, add entry sections for:

- `Macro`
- `Equity Markets`

Each entry should explain why that section matters and create curiosity without turning into a sales pitch.

### Macro

The `Macro` page should follow the product design doc structure and use placeholders that match the intended long-term product shape.

It should have three layers:

1. `Headline layer`
2. `Driver analysis layer`
3. `Drilldown-oriented layer`

#### Headline Layer

Show a compact current-state view with placeholder macro context for:

- GDP growth
- CPI
- policy rate
- labor anchor

Also reserve a region selector concept for:

- `World`
- `USA`
- `Euro Area`
- `China`
- `Asia ex-China`

This can be presented as a visual control placeholder even if the real data logic is not implemented yet.

#### Driver Analysis Layer

Show the six driver families from the macro product plan:

- `Liquidity and Money Impulse`
- `Credit Conditions and Financing Stress`
- `Price Pressure Pipeline`
- `Consumer Behavior and Demand Resilience`
- `Industrial and Trade Pulse`
- `Housing and Construction Transmission`

Each driver block should include:

- compact summary
- placeholder signal language
- small placeholder sparkline or chart-like region
- short methodology framing

This is the true center of gravity of the macro page.

#### Drilldown-Oriented Layer

Below the driver grid, add a structure that signals what deeper analysis will later contain:

- full chart sets
- methodology notes
- causal rationale
- source information
- caveats
- update frequency

The point is not full implementation now. The point is making the future product shape legible already in the placeholder phase.

### Equity Markets

The third page should be renamed consistently to `Equity Markets`.

This page should preserve the serious broad-market valuation philosophy from the existing stock-markets work, but be adapted into the new shell.

Core sections:

- overview framing
- valuation lens families
- market coverage shortlist
- page structure / workflow
- methodology posture

The visual tone should match the new shell and feel more institutional than generic.

## Component Strategy

Introduce a small reusable site-shell layer rather than leaving each page to build its own outer structure.

Recommended pieces:

- shared navigation component
- shared mobile nav drawer
- shared footer
- shared page container / shell wrapper
- reusable insight/stat card primitives
- reusable section heading pattern

Keep components focused and avoid oversized files.

## Content Strategy For Placeholders

Placeholder content should still feel intelligent and curated.

That means:

- no lorem ipsum
- no fake generic analytics labels
- no vague "powerful insights" wording

Placeholder text should instead sound like real product language:

- disciplined
- analytical
- theory-aware
- concise

## Responsive Behavior

The product must work well on mobile and desktop from the start.

Minimum expectations:

- nav collapses cleanly into a drawer
- hero content reflows without losing hierarchy
- intelligence strip stacks well on mobile
- macro driver grid becomes readable at narrow widths
- footer remains tidy on small screens

## Implementation Scope For This Phase

This phase should implement:

- one unified dark theme
- refreshed navigation and footer
- new home page structure
- refreshed macro page placeholders based on the macro product design
- renamed and restyled `Equity Markets` page
- mobile compatibility

This phase should not implement:

- final mathematical models
- final macro formulas
- full charting system
- real drilldown workflows
- complete data-driven insight engine

Those will be designed later after the shell and page structure are in place.

## Testing And Verification

Implementation should preserve or extend tests for:

- navigation rendering
- correct route labels including `Equity Markets`
- page rendering for home, macro, and equity pages
- shell-level layout expectations where practical

Visual verification should also be done in-browser after implementation.

## Outcome

If executed correctly, this refresh should make MVD feel like a serious modern macro and valuation workspace:

- visually sharper
- less generic
- more memorable
- more curiosity-inducing
- better aligned with eventual deep research workflows

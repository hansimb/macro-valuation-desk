# Frontend Agent Prompt: Market Valuation Integration

You are the frontend agent for Macro Valuation Desk. The backend now exposes global equity market valuation snapshots through:

```text
GET /equity-markets/valuations
```

Use the shared contract:

```text
packages/shared/src/contracts/equity-market-valuation.ts
```

Treat that shared contract as the source of truth. Do not modify it unless the backend/API contract is intentionally changed in the same task.

## Goal

Integrate the market valuation API into the existing Equity Markets area. Build a usable overview that helps the user scan broad market valuation levels across countries and regions.

## Existing Frontend Context

Start by reading:

- `docs/agents/REPO-MAP.md`
- `docs/product/2026-05-12-stock-market-product-design.md`
- `apps/web/src/app/equity-markets/page.tsx`
- `apps/web/src/app/equity-markets/[market]/page.tsx`
- `apps/web/src/features/site-shell/mvd-data.ts`
- `apps/web/tests/stock-markets-page.test.tsx`

Follow existing Next.js App Router and Chakra UI v3 patterns.

## Required Behavior

Render market valuation snapshots from the API:

- response-level latest as-of date from `asOf`;
- market name;
- region;
- measured object symbol;
- measured object name;
- measured object type;
- per-market as-of date from `market.asOf`;
- source URL from `market.sourceUrl`;
- P/E from `market.metrics.trailingPe`;
- P/B from `market.metrics.priceToBook`;
- P/S from `market.metrics.priceToSales`;
- P/CF proxy from `market.metrics.priceToCashFlow`;
- dividend yield from `market.metrics.dividendYieldPct`.

The top-level `asOf` is the latest available valuation date across all returned markets. Each market row still has its own `market.asOf`, and those dates may differ by provider symbol.

When `markets` is empty, render an explicit missing-data state. Do not add fake fallback valuation data.

## Methodology Requirements

Be precise in labels:

- `priceToCashFlow` is a `P/CF proxy`.
- `priceToFreeCashFlow` is exact P/FCF only when its value is not null.
- Exact P/FCF remains a distinct API field; omit its separate UI column under the current display scope. Never relabel P/CF as exact P/FCF.

Make the measured object visible. The user must be able to see whether the data describes an ETF proxy or an index-native series.

Follow [the analysis UI instructions, section 12](../../analysis/FOR-AGENTS-UI-BUILD-INSTRUCTIONS.md#12-references-must-match-the-taylor-style). Build one reference registry from `references`, deduplicate by source identity, and append any missing row-level `sourceUrl` using row metadata. Render compact numbered citations beside measured objects and matching academic-style references with institution/provider, ETF or series title, and online URL. Do not render a separate `Sources` column, generic `Row source` links, or a plain link list.

Current UI scope (2026-09-12): omit the separate Exact P/FCF column; retain the P/CF proxy only when data is available. Hide any metric column with no available values across the returned markets. Use a responsive layout that fits without horizontal scrolling while retaining measured-object identity, per-row dates, and citations.

## Testing Requirements

Add or update web tests that verify:

- the Equity Markets page renders populated API data;
- the page renders the empty-data state when `markets` is empty;
- P/CF is labeled as a proxy;
- the separate exact P/FCF column is omitted;
- wholly unavailable metric columns are hidden, while zero counts as available;
- measured ETF/index proxy metadata is visible.
- response-level `asOf` and per-market `market.asOf` can both render without being treated as the same thing.
- numbered row citations match descriptive references, including repeated source URLs and row URLs absent from `references`;
- desktop and narrow-screen layouts fit without horizontal scrolling, including long reference URLs.

Run:

```powershell
npm.cmd run test --workspace @mvd/web -- stock-markets-page.test.tsx
```

If the Equity Markets implementation lives under a more specific test file after your changes, run that focused file instead or in addition.

Then run:

```powershell
npm.cmd test
```

## Commit Policy

Use atomic commits. Recommended commit:

```powershell
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add apps/web docs/agents
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "feat: integrate market valuation overview"
```

Only include frontend integration files and tests in that commit.

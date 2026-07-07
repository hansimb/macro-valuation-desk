# Frontend Agent Prompt: Market Valuation Integration

You are the frontend agent for Macro Valuation Desk. The backend now exposes global equity market valuation snapshots through:

```text
GET /equity-markets/valuations
```

Use the shared contract:

```text
packages/shared/src/contracts/equity-market-valuation.ts
```

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

- market name;
- region;
- measured object symbol;
- measured object name;
- measured object type;
- as-of date;
- P/E;
- P/B;
- P/S;
- P/CF proxy;
- exact P/FCF when available;
- dividend yield.

When `markets` is empty, render an explicit missing-data state. Do not add fake fallback valuation data.

## Methodology Requirements

Be precise in labels:

- `priceToCashFlow` is a `P/CF proxy`.
- `priceToFreeCashFlow` is exact P/FCF only when its value is not null.
- If exact P/FCF is null, show it as unavailable rather than silently substituting P/CF.

Make the measured object visible. The user must be able to see whether the data describes an ETF proxy or an index-native series.

## Testing Requirements

Add or update web tests that verify:

- the Equity Markets page renders populated API data;
- the page renders the empty-data state when `markets` is empty;
- P/CF is labeled as a proxy;
- exact P/FCF is shown as unavailable when null;
- measured ETF/index proxy metadata is visible.

Run:

```powershell
npm.cmd run test --workspace @mvd/web -- stock-markets-page.test.tsx
```

Then run:

```powershell
npm.cmd test
```

## Commit Policy

Use atomic commits. Recommended commit:

```powershell
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add apps/web packages/shared docs/agents
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "feat: integrate market valuation overview"
```

Only include frontend integration files and tests in that commit.

# Return Expectation Market Cap Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add shares-times-price market cap input and clearer earnings-yield diagnostics to the stock return expectation calculator.

**Architecture:** Keep the change inside the existing calculator client component and page test. Extend `CalculatorState.common` with a market cap input mode, shares outstanding, and share price; centralize effective market cap calculation in helper functions used by earnings and FCF calculations.

**Tech Stack:** Next.js App Router, React 19, Chakra UI v3, Vitest, Testing Library.

---

### Task 1: Commit Design Documents

**Files:**
- Create: `docs/superpowers/specs/2026-07-03-return-expectation-market-cap-input-design.md`
- Create: `docs/superpowers/plans/2026-07-03-return-expectation-market-cap-input.md`

- [ ] **Step 1: Commit docs**

Run:

```bash
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add docs/superpowers/specs/2026-07-03-return-expectation-market-cap-input-design.md docs/superpowers/plans/2026-07-03-return-expectation-market-cap-input.md
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "docs: plan return expectation market cap input"
```

Expected: commit succeeds with only the two documentation files.

### Task 2: Add Failing Tests

**Files:**
- Modify: `apps/web/tests/equity-return-expectation-page.test.tsx`

- [ ] **Step 1: Write market cap mode test**

Add a test that switches the earnings model to `Shares x price`, enters `100` shares and `10` share price, enters `80` net income, and verifies:

- Calculated market capitalization shows `1000`.
- Earnings yield shows `8.00%`.
- Implied P/E shows `12.5x`.
- Switching to FCF uses the same calculated market cap for FCF yield.

- [ ] **Step 2: Write earnings diagnostics and FCF isolation test**

Add assertions that the market-cap based earnings input path shows `Earnings yield = net income / market capitalization`, `Calculated Earnings Yield`, and `Calculated P/E`. Extend the FCF assertion to verify the formula text `Expected return = free cash flow yield + FCF growth` remains visible and EPS/revenue controls are absent.

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```bash
npm.cmd run test --workspace @mvd/web -- equity-return-expectation-page.test.tsx
```

Expected: the new tests fail because `Shares x price` and the diagnostics do not exist yet.

### Task 3: Implement Market Cap Input

**Files:**
- Modify: `apps/web/src/features/equity/return-expectation-client.tsx`

- [ ] **Step 1: Extend state**

Add `marketCapMode: "direct" | "shares"` plus `sharesOutstanding` and `sharePrice` to `CalculatorState.common`, defaulting to direct mode and empty values.

- [ ] **Step 2: Add helpers**

Add helpers:

- `calculatedMarketCap(state)` returns direct market cap or shares times price.
- `marketCapInputNote(state)` returns the visible source note for metric summary cards.

- [ ] **Step 3: Update calculations**

Use `calculatedMarketCap(state)` in `earningsYieldPct`, `impliedEarningsPe`, `fcfYieldPct`, and `impliedPriceToFcf`.

- [ ] **Step 4: Render inputs and diagnostics**

In earnings and FCF market-cap input sections, add segmented buttons for `Market cap input` and `Shares x price`. Render shares and price fields when shares mode is selected. In earnings market-cap mode, render a compact diagnostics block with formula, calculated earnings yield, and calculated P/E.

- [ ] **Step 5: Run focused tests**

Run:

```bash
npm.cmd run test --workspace @mvd/web -- equity-return-expectation-page.test.tsx
```

Expected: all tests in the file pass.

- [ ] **Step 6: Commit feature**

Run:

```bash
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add apps/web/src/features/equity/return-expectation-client.tsx apps/web/tests/equity-return-expectation-page.test.tsx
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "feat: add shares-based market cap input"
```

Expected: commit succeeds with only the calculator and test changes.

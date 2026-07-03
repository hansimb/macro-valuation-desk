# Return Expectation Metric Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single metric summary section to the stock return expectation calculator with yield metrics and historical growth metrics derived from current inputs.

**Architecture:** Keep the implementation inside `apps/web/src/features/equity/return-expectation-client.tsx`, matching the existing large-component pattern. Add small row-building helpers near the existing comparison helpers, then render one Chakra surface between `Result` and `Return Expectation Methods`.

**Tech Stack:** Next.js App Router, React 19, Chakra UI v3, Vitest, Testing Library.

---

### Task 1: Document Design

**Files:**
- Create: `docs/superpowers/specs/2026-07-03-return-expectation-metric-summary-design.md`
- Create: `docs/superpowers/plans/2026-07-03-return-expectation-metric-summary.md`

- [ ] **Step 1: Commit the approved design and plan**

Run:

```bash
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add docs/superpowers/specs/2026-07-03-return-expectation-metric-summary-design.md docs/superpowers/plans/2026-07-03-return-expectation-metric-summary.md
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "docs: plan return expectation metric summary"
```

Expected: commit succeeds with only the two documentation files.

### Task 2: Add Failing Coverage

**Files:**
- Modify: `apps/web/tests/equity-return-expectation-page.test.tsx`

- [ ] **Step 1: Add a failing test**

Add a test that fills dividend, earnings, EPS, revenue, and FCF historical inputs, then expects:

- `Metric Summary` to be after `Result`.
- `Metric Summary` to be before `Return Expectation Methods`.
- `Yield Metrics` and `Historical Growth Metrics` to be present.
- `Dividend Yield`, `Earnings Yield`, `FCF Yield`, `EPS Growth History`, `Revenue Growth History`, `Dividend Growth History`, and `FCF Growth History` to be present.

- [ ] **Step 2: Run the focused test**

Run:

```bash
npm run test --workspace @mvd/web -- equity-return-expectation-page.test.tsx
```

Expected: the new test fails because `Metric Summary` does not exist yet.

### Task 3: Implement Metric Summary

**Files:**
- Modify: `apps/web/src/features/equity/return-expectation-client.tsx`

- [ ] **Step 1: Add metric summary row helpers**

Add a row type and helpers that call existing functions:

- `dividendYieldPct`
- `earningsYieldPct`
- `fcfYieldPct`
- `impliedEarningsPe`
- `impliedPriceToFcf`
- `averageHistoricalGrowth`
- `fcfHistoricalGrowthPct`

- [ ] **Step 2: Render the summary**

Render one `Box` after the `Result` box and before the comparison section. Inside it, render two internal `Stack` groups with headings `Yield Metrics` and `Historical Growth Metrics`, each using `AnalysisMetricCard` tiles.

- [ ] **Step 3: Run the focused test**

Run:

```bash
npm run test --workspace @mvd/web -- equity-return-expectation-page.test.tsx
```

Expected: all tests in that file pass.

- [ ] **Step 4: Commit the feature**

Run:

```bash
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' add apps/web/tests/equity-return-expectation-page.test.tsx apps/web/src/features/equity/return-expectation-client.tsx
git -c safe.directory='C:/Users/IMBERI/Desktop/dev/projects2/macro-valuation-desk' commit -m "feat: add return expectation metric summary"
```

Expected: commit succeeds with only the test and component changes.

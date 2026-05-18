# MVD UI Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the MVD web shell and core pages into a sharper single-theme research product UI with shared navigation, footer, and stronger macro/equity placeholders.

**Architecture:** Reuse the structural patterns from `pro-site-cms` by introducing a small site-shell layer inside `apps/web`, then rebuild `Home`, `Macro`, and `Equity Markets` on top of that shell. Keep pages mostly server-rendered, push route-aware nav into client components, and preserve Chakra v3 tokens as the single styling system.

**Tech Stack:** Next.js App Router, React 19, Chakra UI v3, Vitest, Testing Library

---

### Task 1: Lock the new route labels and shared shell expectations in tests

**Files:**
- Modify: `apps/web/tests/navigation-shell.test.tsx`
- Modify: `apps/web/tests/stock-markets-page.test.tsx`
- Create: `apps/web/tests/macro-page.test.tsx`

- [ ] **Step 1: Write the failing test updates for Home and Equity Markets**

```tsx
import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "../src/app/page";
import EquityMarketsPage from "../src/app/equity-markets/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("MVD home shell", () => {
  it("renders the primary sections", () => {
    render(
      <ThemeProvider>
        <HomePage />
      </ThemeProvider>
    );

    expect(screen.getByText("Macro")).toBeInTheDocument();
    expect(screen.getByText("Equity Markets")).toBeInTheDocument();
  });
});

describe("Equity Markets page", () => {
  it("renders the valuation overview draft structure", () => {
    render(
      <ThemeProvider>
        <EquityMarketsPage />
      </ThemeProvider>
    );

    expect(screen.getByRole("heading", { name: "Equity Markets" })).toBeInTheDocument();
    expect(screen.getByText("Historical valuation position")).toBeInTheDocument();
    expect(screen.getByText("Valuation lens families")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Add a failing Macro page test that locks the new placeholder structure**

```tsx
import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import MacroPage from "../src/app/macro/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("Macro page", () => {
  it("renders the macro driver workspace structure", async () => {
    const page = await MacroPage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: "Macro" })).toBeInTheDocument();
    expect(screen.getByText("Headline layer")).toBeInTheDocument();
    expect(screen.getByText("Driver analysis")).toBeInTheDocument();
    expect(screen.getByText("Liquidity and Money Impulse")).toBeInTheDocument();
    expect(screen.getByText("Housing and Construction Transmission")).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run the targeted test files to verify failure**

Run: `npx.cmd vitest run apps/web/tests/navigation-shell.test.tsx apps/web/tests/stock-markets-page.test.tsx apps/web/tests/macro-page.test.tsx --config apps/web/vitest.config.ts`
Expected: FAIL because the route names, file paths, and new macro placeholder content do not exist yet.

- [ ] **Step 4: Commit the red tests once they exist if the team wants ultra-strict red/green history**

```bash
git add apps/web/tests/navigation-shell.test.tsx apps/web/tests/stock-markets-page.test.tsx apps/web/tests/macro-page.test.tsx
git commit -m "test: lock mvd ui refresh shell expectations"
```

### Task 2: Introduce the shared MVD shell and single-theme tokens

**Files:**
- Modify: `apps/web/src/features/theme/system.ts`
- Modify: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/features/site-shell/navigation.tsx`
- Create: `apps/web/src/features/site-shell/mobile-nav.tsx`
- Create: `apps/web/src/features/site-shell/footer.tsx`
- Create: `apps/web/src/features/site-shell/layout-shell.tsx`

- [ ] **Step 1: Expand the theme tokens toward the sharper single-theme shell**

```tsx
import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

export const mvdThemeConfig = defineConfig({
  globalCss: {
    html: { colorPalette: "accent" },
    body: { bg: "canvas", color: "text", margin: "0", letterSpacing: "0" },
    "::selection": { bg: "accent", color: "black" }
  },
  theme: {
    tokens: {
      colors: {
        accent: { value: "#7dd3d8" },
        canvas: { value: "#050816" },
        edge: { value: "#1a2236" },
        muted: { value: "#8b97b3" },
        surface: { value: "#0a1224" },
        surfaceRaised: { value: "#101a31" },
        text: { value: "#eef2ff" }
      },
      fonts: {
        body: { value: "var(--font-sans), sans-serif" },
        heading: { value: "var(--font-serif), serif" }
      },
      radii: {
        panel: { value: "6px" },
        control: { value: "4px" },
        sharp: { value: "0" }
      }
    },
    semanticTokens: {
      colors: {
        "bg.panel": { value: "{colors.surface}" },
        "bg.panel.raised": { value: "{colors.surfaceRaised}" },
        "fg.default": { value: "{colors.text}" },
        "fg.muted": { value: "{colors.muted}" },
        "border.default": { value: "{colors.edge}" }
      }
    }
  }
});
```

- [ ] **Step 2: Build the route-aware desktop navigation**

```tsx
"use client";

import NextLink from "next/link";
import { usePathname } from "next/navigation";
import { Flex, Link } from "@chakra-ui/react";

const navigation = [
  { href: "/", label: "Home" },
  { href: "/macro", label: "Macro" },
  { href: "/equity-markets", label: "Equity Markets" }
];

export function SiteNavigation() {
  const pathname = usePathname();

  return (
    <Flex align="center" gap={{ base: 2, md: 5 }}>
      {navigation.map((item) => {
        const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
        return (
          <Link asChild color={active ? "accent" : "fg.muted"} key={item.href} _hover={{ color: "accent" }}>
            <NextLink href={item.href}>{item.label}</NextLink>
          </Link>
        );
      })}
    </Flex>
  );
}
```

- [ ] **Step 3: Build the mobile drawer and footer, then mount the shell in layout**

```tsx
export function LayoutShell({ children }: { children: React.ReactNode }) {
  return (
    <Box minH="100vh" bg="canvas" color="text" position="relative">
      <Container maxW="6xl" px={{ base: 4, md: 6 }} py={{ base: 4, md: 6 }} position="relative" zIndex={1}>
        <Flex as="nav" align="center" borderBottomWidth="1px" borderColor="border.default" justify="space-between" pb={4}>
          {/* brand, desktop nav, mobile nav */}
        </Flex>
        <Box as="main" py={{ base: 8, md: 12 }}>{children}</Box>
        <SiteFooter />
      </Container>
    </Box>
  );
}
```

- [ ] **Step 4: Run typecheck to validate the shell compiles**

Run: `npx.cmd tsc -p apps/web/tsconfig.json --noEmit`
Expected: PASS

- [ ] **Step 5: Commit the shell foundation**

```bash
git add apps/web/src/features/theme/system.ts apps/web/src/app/layout.tsx apps/web/src/features/site-shell
git commit -m "feat: add mvd research shell foundation"
```

### Task 3: Rebuild the Home page into the hybrid editorial-product structure

**Files:**
- Modify: `apps/web/src/app/page.tsx`

- [ ] **Step 1: Replace the current Home page with a hero plus intelligence strip**

```tsx
const insightStrip = [
  { eyebrow: "Macro", title: "Credit is tight before damage is obvious", detail: "Financing stress usually matters before lagging growth data admits it." },
  { eyebrow: "Equity", title: "Valuation breadth matters more than one multiple", detail: "Broad-market pricing needs history, composition, and discount-rate context." },
  { eyebrow: "Method", title: "Signal density over dashboard sprawl", detail: "The product will stay narrow on purpose and go deeper where the causal chain is strongest." }
];
```

- [ ] **Step 2: Add curated section entries for Macro and Equity Markets**

```tsx
const sectionEntries = [
  {
    href: "/macro",
    title: "Macro",
    description: "Follow the six driver families that shape the cycle, inflation path, financing conditions, and real-economy direction."
  },
  {
    href: "/equity-markets",
    title: "Equity Markets",
    description: "Read broad market valuation through multiple lenses before narrowing the field into deeper market research."
  }
];
```

- [ ] **Step 3: Run the Home shell test**

Run: `npx.cmd tsc -p apps/web/tsconfig.json --noEmit`
Expected: PASS

- [ ] **Step 4: Commit the Home page refresh**

```bash
git add apps/web/src/app/page.tsx apps/web/tests/navigation-shell.test.tsx
git commit -m "feat: refresh mvd home page shell"
```

### Task 4: Rebuild the Macro page around the product-design placeholder layers

**Files:**
- Modify: `apps/web/src/app/macro/page.tsx`

- [ ] **Step 1: Keep the existing API fetch but restructure the page into headline, driver, and drilldown layers**

```tsx
const regions = ["World", "USA", "Euro Area", "China", "Asia ex-China"];

const drivers = [
  { title: "Liquidity and Money Impulse", summary: "Money and credit conditions still matter before the headline economy catches up.", cue: "Liquidity pulse stabilizing" },
  { title: "Credit Conditions and Financing Stress", summary: "The financing channel is often where policy becomes real economic pressure.", cue: "Credit stress elevated" },
  { title: "Price Pressure Pipeline", summary: "Inflation should be read upstream, not only at the CPI print.", cue: "Pipeline cooling unevenly" },
  { title: "Consumer Behavior and Demand Resilience", summary: "Demand resilience helps reveal whether the cycle is broadening or tiring.", cue: "Consumer resilience narrowing" },
  { title: "Industrial and Trade Pulse", summary: "Goods demand and export sensitivity still anchor the global cycle.", cue: "Trade pulse mixed" },
  { title: "Housing and Construction Transmission", summary: "Housing remains one of the clearest rate-sensitive transmission paths.", cue: "Construction drag persistent" }
];
```

- [ ] **Step 2: Add a drilldown-oriented methodology section**

```tsx
const drilldownBlocks = [
  "Full chart sets",
  "Causal rationale",
  "Source and update notes",
  "Caveats and revision risk"
];
```

- [ ] **Step 3: Run the Macro test and typecheck**

Run: `npx.cmd tsc -p apps/web/tsconfig.json --noEmit`
Expected: PASS

- [ ] **Step 4: Commit the Macro page rebuild**

```bash
git add apps/web/src/app/macro/page.tsx apps/web/tests/macro-page.test.tsx
git commit -m "feat: rebuild macro workspace placeholders"
```

### Task 5: Rename and restyle Stock Markets into Equity Markets

**Files:**
- Create: `apps/web/src/app/equity-markets/page.tsx`
- Modify: `apps/web/tests/stock-markets-page.test.tsx`

- [ ] **Step 1: Move the current market philosophy into the renamed Equity Markets page**

```tsx
const valuationLenses = [
  { title: "Earnings-based", detail: "Use earnings multiples carefully and keep cycle distortion explicit." },
  { title: "Balance-sheet based", detail: "Asset-heavy markets need a different valuation framing than capital-light ones." },
  { title: "Sales and cash flow", detail: "Sales and cash flow metrics help when margins distort the picture." },
  { title: "Macro-relative", detail: "Market valuation should also be read against discount rates and equity risk premium logic." }
];
```

- [ ] **Step 2: Update the headline and section labels to the final names**

```tsx
<Heading as="h1" size={{ base: "2xl", md: "3xl" }}>
  Equity Markets
</Heading>
```

- [ ] **Step 3: Run the Equity Markets test and typecheck**

Run: `npx.cmd tsc -p apps/web/tsconfig.json --noEmit`
Expected: PASS

- [ ] **Step 4: Commit the route rename and restyle**

```bash
git add apps/web/src/app/equity-markets/page.tsx apps/web/tests/stock-markets-page.test.tsx
git commit -m "feat: rename stock markets to equity markets"
```

### Task 6: Final verification and cleanup

**Files:**
- Modify: `apps/web/tests/root-layout.test.tsx`
- Modify: `apps/web/src/features/theme/provider.tsx`
- Modify: `apps/web/src/features/theme/emotion-registry.tsx`

- [ ] **Step 1: Make sure the existing Chakra SSR fix still matches the new shell**

```tsx
expect(element.type).toBe(EmotionRegistry);
expect(element.props.lang).toBe("en");
```

- [ ] **Step 2: Run the web verification set**

Run: `npx.cmd tsc -p apps/web/tsconfig.json --noEmit`
Expected: PASS

Run: `npx.cmd next build`
Expected: either PASS or the same known workspace-root/readlink issue already seen in this environment, with no new component-level TypeScript failures.

- [ ] **Step 3: Commit the integrated UI refresh**

```bash
git add apps/web/src apps/web/tests
git commit -m "feat: implement mvd ui refresh"
```

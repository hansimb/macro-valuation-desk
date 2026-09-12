import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import EquityMarketsPage from "../src/app/equity-markets/page";
import MarketValuationPage from "../src/app/equity-markets/market-valuation/page";
import { ThemeProvider } from "../src/features/theme/provider";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
describe("Market valuation page", () => {
  it("is discoverable from the equity analysis registry", () => {
    render(
      <ThemeProvider>
        <EquityMarketsPage />
      </ThemeProvider>,
    );

    expect(screen.getByRole("link", { name: /Market Valuation Dashboard/i })).toBeInTheDocument();
    expect(screen.getByText(/API-backed overview of broad equity valuation ratios/i)).toBeInTheDocument();
  });

  it.each([
    ["ishares.com", "BlackRock iShares"],
    ["ssga.com", "State Street SPDR"],
  ])("keeps sparse zero metrics and cites issuer sources for %s", async (host, institution) => {
    const row = {
      marketId: "one", marketName: "Market one", region: "EU", measuredSymbol: "ONE",
      measuredName: "First index", measuredType: "index", provider: "issuer_pages",
      sourceUrl: `https://www.${host}/one`, asOf: "2026-07-06", missingFields: [],
      metrics: {
        trailingPe: { value: null, method: "unavailable" },
        priceToBook: { value: null, method: "unavailable" },
        priceToSales: { value: null, method: "unavailable" },
        priceToCashFlow: { value: null, method: "unavailable" },
        priceToFreeCashFlow: { value: null, method: "unavailable" },
        dividendYieldPct: { value: null, method: "unavailable" },
      },
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({
      asOf: "2026-07-07", references: [{ label: "Methodology", url: "https://example.com/method" }, { label: "Duplicate", url: "https://example.com/method" }], markets: [row, {
        ...row, marketId: "two", marketName: "Market two",
        metrics: { ...row.metrics, dividendYieldPct: { value: "0", method: "provider" } },
      }],
    }) }));
    render(<ThemeProvider>{await MarketValuationPage()}</ThemeProvider>);
    expect(screen.queryByRole("columnheader", { hidden: true, name: "P/E" })).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { hidden: true, name: "P/B" })).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { hidden: true, name: "P/S" })).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { hidden: true, name: "P/CF proxy" })).not.toBeInTheDocument();
    expect(screen.getByRole("columnheader", { hidden: true, name: "Dividend yield" })).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "[2]" })).toHaveLength(2);
    expect(screen.getByRole("link", { name: `[2] ${institution}, "First index (ONE)." [Online]. Available: https://www.${host}/one.` })).toHaveAttribute("href", `https://www.${host}/one`);
    expect(screen.getAllByRole("link", { name: /\[1\] example.com, "Methodology."/ })).toHaveLength(1);
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.getAllByText("Valuation as of 2026-07-06")).toHaveLength(2);
  });

  it("renders API-backed valuation data instead of placeholder seed rows", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          asOf: "2026-07-07",
          markets: [
            {
              marketId: "finland_large_cap",
              region: "FI",
              marketName: "Finland large cap",
              measuredSymbol: "EFNL.US",
              measuredName: "iShares MSCI Finland ETF",
              measuredType: "ETF",
              provider: "eodhd",
              sourceUrl: "https://eodhd.com/api/fundamentals/EFNL.US",
              asOf: "2026-07-06",
              metrics: {
                trailingPe: { value: "18.20", method: "provider_price_prospective_earnings" },
                priceToBook: { value: "2.10", method: "provider_price_to_book" },
                priceToSales: { value: "1.70", method: "provider_price_to_sales" },
                priceToCashFlow: { value: "11.30", method: "provider_price_to_cash_flow_proxy" },
                priceToFreeCashFlow: { value: "10.90", method: "provider_exact_price_to_free_cash_flow" },
                dividendYieldPct: { value: "2.45", method: "provider_dividend_yield_factor" },
              },
              missingFields: [],
            },
          ],
          references: [],
        }),
      }),
    );

    const page = await MarketValuationPage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("table", { name: "Market valuation overview" })).toBeInTheDocument();
    expect(screen.getByText("Finland large cap")).toBeInTheDocument();
    expect(screen.getByText("EFNL.US")).toBeInTheDocument();
    expect(screen.getByText("11.30")).toBeInTheDocument();
    expect(screen.queryByText("10.90")).not.toBeInTheDocument();
    expect(screen.queryByText("Placeholder data only")).not.toBeInTheDocument();
    expect(screen.queryByText("Do not use these values for analysis")).not.toBeInTheDocument();
  });
});

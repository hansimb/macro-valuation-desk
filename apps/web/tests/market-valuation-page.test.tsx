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
    expect(screen.getByText("10.90")).toBeInTheDocument();
    expect(screen.queryByText("Placeholder data only")).not.toBeInTheDocument();
    expect(screen.queryByText("Do not use these values for analysis")).not.toBeInTheDocument();
  });
});

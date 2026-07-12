import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import EquityMarketsPage from "../src/app/equity-markets/page";
import MarketValuationPage from "../src/app/equity-markets/market-valuation/page";
import { ThemeProvider } from "../src/features/theme/provider";

const valuationPayload = {
  asOf: "2026-07-07",
  markets: [
    {
      marketId: "us_total_market",
      region: "US",
      marketName: "United States broad market",
      measuredSymbol: "VTI.US",
      measuredName: "Vanguard Total Stock Market ETF",
      measuredType: "ETF",
      provider: "eodhd",
      sourceUrl: "https://eodhd.com/api/fundamentals/VTI.US",
      asOf: "2026-07-05",
      metrics: {
        trailingPe: { value: "22.10", method: "provider_price_prospective_earnings" },
        priceToBook: { value: "3.80", method: "provider_price_to_book" },
        priceToSales: { value: "2.60", method: "provider_price_to_sales" },
        priceToCashFlow: { value: "14.40", method: "provider_price_to_cash_flow_proxy" },
        priceToFreeCashFlow: {
          value: null,
          method: "unavailable_exact_pfcf_not_in_provider_snapshot",
        },
        dividendYieldPct: { value: "1.35", method: "provider_dividend_yield_factor" },
      },
      missingFields: ["price_to_free_cash_flow"],
    },
  ],
  references: [
    {
      label: "EODHD fundamentals",
      url: "https://eodhd.com/financial-apis/stock-etf-fundamental-data-feeds/",
    },
  ],
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function renderMarketValuationPage() {
  const page = await MarketValuationPage();

  render(<ThemeProvider>{page}</ThemeProvider>);
}

describe("Equity Markets page", () => {
  it("renders an analysis registry page that mirrors the macro landing-page structure", () => {
    render(
      <ThemeProvider>
        <EquityMarketsPage />
      </ThemeProvider>
    );

    expect(screen.getByRole("heading", { name: "Equity Markets" })).toBeInTheDocument();
    expect(screen.getByText("Equity Workspace")).toBeInTheDocument();
    expect(screen.getByText("Analysis")).toBeInTheDocument();
    expect(screen.queryByText("No analysis yet")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Market Valuation Dashboard/i })).toBeInTheDocument();
    expect(screen.getByText(/API-backed overview of broad equity valuation ratios across major regions/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Stock Return Expectation/i })).toBeInTheDocument();
    expect(screen.getByText(/Frontend-only calculator for dividend, earnings-yield, and free-cash-flow return models/i)).toBeInTheDocument();
  });

  it("renders populated market valuation API data with methodology-specific labels", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => valuationPayload,
      }),
    );

    await renderMarketValuationPage();

    expect(screen.getByRole("heading", { name: "Market Valuation Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Latest valuation date: 2026-07-07")).toBeInTheDocument();
    expect(screen.getByText("Row as of 2026-07-05")).toBeInTheDocument();
    expect(screen.getByText("United States broad market")).toBeInTheDocument();
    expect(screen.getByText("US")).toBeInTheDocument();
    expect(screen.getByText("VTI.US")).toBeInTheDocument();
    expect(screen.getByText("Vanguard Total Stock Market ETF")).toBeInTheDocument();
    expect(screen.getByText("ETF proxy")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "P/CF proxy" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Exact P/FCF" })).toBeInTheDocument();
    expect(screen.getByText("14.40")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "EODHD fundamentals" })).toHaveAttribute(
      "href",
      "https://eodhd.com/financial-apis/stock-etf-fundamental-data-feeds/",
    );
    expect(screen.getByRole("link", { name: "Row source" })).toHaveAttribute(
      "href",
      "https://eodhd.com/api/fundamentals/VTI.US",
    );
    expect(screen.queryByText("Placeholder data only")).not.toBeInTheDocument();
  });

  it("renders an explicit empty market valuation state without fallback rows", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ asOf: null, markets: [], references: [] }),
      }),
    );

    await renderMarketValuationPage();

    expect(screen.getByText("Live market valuation data is unavailable right now.")).toBeInTheDocument();
    expect(screen.getByText("Run the market valuation pipeline to populate ETF and index valuation snapshots.")).toBeInTheDocument();
    expect(screen.queryByText("United States broad market")).not.toBeInTheDocument();
    expect(screen.queryByText("Placeholder")).not.toBeInTheDocument();
  });
});

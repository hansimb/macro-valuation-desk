import React from "react";
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import EquityMarketsPage from "../src/app/equity-markets/page";
import MarketValuationPage from "../src/app/equity-markets/market-valuation/page";
import { marketValuationRows } from "../src/features/equity/market-valuation-placeholder-data";
import { ThemeProvider } from "../src/features/theme/provider";

afterEach(() => {
  cleanup();
});

function renderMarketValuationPage() {
  render(
    <ThemeProvider>
      <MarketValuationPage />
    </ThemeProvider>,
  );
}

describe("Market valuation page", () => {
  it("is discoverable from the equity analysis registry", () => {
    render(
      <ThemeProvider>
        <EquityMarketsPage />
      </ThemeProvider>,
    );

    expect(screen.getByRole("link", { name: /Market Valuation Dashboard/i })).toBeInTheDocument();
    expect(screen.getByText(/Placeholder interface for weighted index and ETF valuation ratios/i)).toBeInTheDocument();
  });

  it("renders a visibly placeholder-only market valuation workspace", () => {
    renderMarketValuationPage();

    expect(screen.getByRole("heading", { name: "Market Valuation Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Placeholder data only")).toBeInTheDocument();
    expect(screen.getByText(/Do not use these values for analysis/i)).toBeInTheDocument();
    expect(screen.getByText("Backend handoff")).toBeInTheDocument();
    expect(screen.getByText(/Replace this dataset with API-backed weighted index\/ETF metrics before launch/i)).toBeInTheDocument();

    const table = screen.getByRole("table", { name: "Placeholder market valuation matrix" });
    expect(within(table).getByText("Region")).toBeInTheDocument();
    expect(within(table).getByText("P/E")).toBeInTheDocument();
    expect(within(table).getByText("P/B")).toBeInTheDocument();
    expect(within(table).getByText("P/S")).toBeInTheDocument();
    expect(within(table).getByText("P/FCF")).toBeInTheDocument();
    expect(within(table).getByText("Dividend yield")).toBeInTheDocument();
    expect(within(table).getByText("USA")).toBeInTheDocument();
    expect(within(table).getByText("Finland")).toBeInTheDocument();
    expect(within(table).getAllByText("Placeholder").length).toBeGreaterThan(3);
  });

  it("keeps every seeded row explicitly marked as placeholder data", () => {
    expect(marketValuationRows.length).toBeGreaterThan(8);
    expect(marketValuationRows.every((row) => row.isPlaceholder)).toBe(true);
    expect(marketValuationRows.every((row) => row.sourceStatus === "placeholder")).toBe(true);
  });
});

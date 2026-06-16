import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HighestPsRankingPage from "../src/app/equity-markets/highest-ps-ranking/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("Highest P/S ranking page", () => {
  it("renders a placeholder analysis route with explicit demo framing", async () => {
    const page = await HighestPsRankingPage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: "Highest P/S Stocks" })).toBeInTheDocument();
    expect(screen.getByText("Equity Valuation")).toBeInTheDocument();
    expect(screen.getByText(/This demo version previews the analysis shape with placeholder rows only/i)).toBeInTheDocument();
    expect(screen.getByText(/P\/S = market capitalization \/ revenue/i)).toBeInTheDocument();
    expect(screen.getByText(/Rank the universe by price-to-sales and inspect which names sit at the extreme top end/i)).toBeInTheDocument();
    expect(screen.getByText("Reference Valuation Context")).toBeInTheDocument();
    expect(screen.getByText(/These benchmark values are placeholder reference context only/i)).toBeInTheDocument();
    expect(screen.getByText("S&P 500 Average P/S")).toBeInTheDocument();
    expect(screen.getByText("STOXX Europe 600 Average P/S")).toBeInTheDocument();
    expect(screen.getByText("3.1x")).toBeInTheDocument();
    expect(screen.getByText("1.9x")).toBeInTheDocument();
    expect(screen.getByText("USA benchmark")).toBeInTheDocument();
    expect(screen.getByText("Europe benchmark")).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: "Benchmark" })).not.toBeInTheDocument();
    const rankHeader = screen.getByRole("columnheader", { name: "Rank" });
    const countryHeader = screen.getByRole("columnheader", { name: "Country" });
    const tickerHeader = screen.getByRole("columnheader", { name: "Ticker" });
    expect(rankHeader.compareDocumentPosition(countryHeader) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(countryHeader.compareDocumentPosition(tickerHeader) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByText("SNOW")).toBeInTheDocument();
    expect(screen.getByText("CRWD")).toBeInTheDocument();
    expect(screen.getByText("PLTR")).toBeInTheDocument();
    expect(screen.getAllByText(/US/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Placeholder demo data only. This table will be removed once the live full-stack ranking is ready/i)).toBeInTheDocument();
  });
});

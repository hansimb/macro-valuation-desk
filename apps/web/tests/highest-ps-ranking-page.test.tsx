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
    expect(screen.getByText("SNOW")).toBeInTheDocument();
    expect(screen.getByText("CRWD")).toBeInTheDocument();
    expect(screen.getByText("PLTR")).toBeInTheDocument();
    expect(screen.getByText(/Placeholder demo data only. This table will be removed once the live full-stack ranking is ready/i)).toBeInTheDocument();
  });
});

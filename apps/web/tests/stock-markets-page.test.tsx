import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import EquityMarketsPage from "../src/app/equity-markets/page";
import { ThemeProvider } from "../src/features/theme/provider";

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
    expect(screen.getByRole("link", { name: /Highest P\/S Stocks/i })).toBeInTheDocument();
    expect(screen.getByText(/Separate U\.S\. and Europe leaderboards for the highest price-to-sales names in major large-cap indices/i)).toBeInTheDocument();
    expect(screen.getByText(/Theory-first comparison of top multiple baskets, benchmark averages, and index-weight concentration/i)).toBeInTheDocument();
  });
});

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import EquityMarketsPage from "../src/app/equity-markets/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("Equity Markets page", () => {
  it("renders the standardized market table without placeholder detail text", () => {
    render(
      <ThemeProvider>
        <EquityMarketsPage />
      </ThemeProvider>
    );

    expect(screen.getByRole("heading", { name: "Index Valuations" })).toBeInTheDocument();
    expect(screen.getByText("Equity market index valuation analysis")).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Market" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Ticker" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Valuation posture" })).toBeInTheDocument();
    expect(screen.getByText("S&P 500")).toBeInTheDocument();
    expect(screen.getByText("OMX Helsinki 25")).toBeInTheDocument();
    expect(screen.getByText("🇺🇸 S&P 500")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /S&P 500/i })).toBeInTheDocument();
    expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
  });
});

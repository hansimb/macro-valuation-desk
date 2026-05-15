import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import StockMarketsPage from "../src/app/stock-markets/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("Stock Markets page", () => {
  it("renders the valuation overview draft structure", () => {
    render(
      <ThemeProvider>
        <StockMarketsPage />
      </ThemeProvider>
    );

    expect(screen.getByRole("heading", { name: "Stock Markets" })).toBeInTheDocument();
    expect(screen.getByText("Historical Valuation Position")).toBeInTheDocument();
    expect(screen.getByText("Core metric families")).toBeInTheDocument();
    expect(screen.getByText("Coverage shortlist")).toBeInTheDocument();
    expect(screen.getByText("Methodology posture")).toBeInTheDocument();
  });
});

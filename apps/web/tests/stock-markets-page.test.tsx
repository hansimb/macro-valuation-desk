import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import EquityMarketsPage from "../src/app/equity-markets/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("Equity Markets page", () => {
  it("renders an empty-state card when the equity analysis registry is empty", () => {
    render(
      <ThemeProvider>
        <EquityMarketsPage />
      </ThemeProvider>
    );

    expect(screen.getByRole("heading", { name: "Equity market index valuation analysis" })).toBeInTheDocument();
    expect(screen.getByText("Global Equity Valuation")).toBeInTheDocument();
    expect(screen.getByText("No analysis yet")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: "Market" })).not.toBeInTheDocument();
    expect(screen.queryByText("S&P 500")).not.toBeInTheDocument();
  });
});

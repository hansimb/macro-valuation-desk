import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import EquityMarketsPage from "../src/app/equity-markets/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("Equity Markets page", () => {
  it("renders the valuation overview draft structure", () => {
    render(
      <ThemeProvider>
        <EquityMarketsPage />
      </ThemeProvider>
    );

    expect(screen.getByRole("heading", { name: "Equity Markets" })).toBeInTheDocument();
    expect(screen.getByText("Historical valuation position")).toBeInTheDocument();
    expect(screen.getByText("Valuation lens families")).toBeInTheDocument();
    expect(screen.getByText("Coverage shortlist")).toBeInTheDocument();
    expect(screen.getByText("Methodology posture")).toBeInTheDocument();
  });
});

import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import HighestPsRankingPage from "../src/app/equity-markets/highest-ps-ranking/page";
import { ThemeProvider } from "../src/features/theme/provider";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Highest P/S ranking page", () => {
  it("shows an unavailable-data notice instead of rendering placeholder benchmark or ranking data when the API fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const page = await HighestPsRankingPage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: "Highest P/S Stocks" })).toBeInTheDocument();
    expect(screen.getByText("Equity Valuation")).toBeInTheDocument();
    expect(screen.getByText(/Top-50 ranking view for the most sales-expensive stocks in the selected live universe/i)).toBeInTheDocument();
    expect(screen.getByText("Live highest P/S ranking data is unavailable right now.")).toBeInTheDocument();
    expect(screen.getByText("Start the API and run the equity ranking pipeline to populate current values.")).toBeInTheDocument();
    expect(screen.queryByText("Reference Valuation Context")).not.toBeInTheDocument();
    expect(screen.queryByText("S&P 500 Average P/S")).not.toBeInTheDocument();
    expect(screen.queryByText("STOXX Europe 600 Average P/S")).not.toBeInTheDocument();
    expect(screen.queryByText("Ranking")).not.toBeInTheDocument();
    expect(screen.queryByText("SNOW")).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: "Rank" })).not.toBeInTheDocument();
  });
});

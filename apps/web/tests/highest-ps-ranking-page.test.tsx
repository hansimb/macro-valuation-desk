import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import HighestPsRankingPage from "../src/app/equity-markets/highest-ps-ranking/page";
import { ThemeProvider } from "../src/features/theme/provider";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Highest P/S ranking page", () => {
  it("falls back to a temporary mock preview when live section data is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const page = await HighestPsRankingPage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: "Highest P/S Stocks" })).toBeInTheDocument();
    expect(screen.getByText("Equity Valuation")).toBeInTheDocument();
    expect(screen.getByText(/Two-track valuation view for the highest price-to-sales leaders in U\.S\. and European large-cap indices/i)).toBeInTheDocument();
    expect(screen.getByText(/Temporary mock preview for the two-section design/i)).toBeInTheDocument();
    expect(screen.getAllByText("USA High P/S Leaders").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Europe High P/S Leaders").length).toBeGreaterThan(0);
    expect(screen.getByText("SNOW")).toBeInTheDocument();
    expect(screen.getAllByText("ASML").length).toBeGreaterThan(0);
  });

  it("renders separate USA and Europe analysis blocks and keeps unavailable sections isolated", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          asOf: "2026-06-17",
          sections: [
            {
              key: "usa",
              label: "USA High P/S Leaders",
              universeKey: "sp500",
              asOf: "2026-06-17",
              unavailable: false,
              benchmark: {
                key: "sp500",
                label: "S&P 500",
                averagePsRatio: "3.1x",
                topBasketAveragePsRatio: "18.4x",
                topBasketIndexWeightPct: "9.2%",
                eligibleConstituentCount: 468,
              },
              ranking: [
                {
                  rank: 1,
                  ticker: "SNOW",
                  company: "Snowflake",
                  countryCode: "US",
                  countryName: "United States",
                  sector: "Software",
                  psRatio: "22.4x",
                  sectorAveragePsRatio: "8.1x",
                  relativeToSectorMultiple: "2.8x",
                  indexWeightPct: "0.22%",
                },
              ],
            },
            {
              key: "europe",
              label: "Europe High P/S Leaders",
              universeKey: "stoxx600",
              asOf: null,
              unavailable: true,
              benchmark: {
                key: "stoxx600",
                label: "STOXX Europe 600",
                averagePsRatio: null,
                topBasketAveragePsRatio: null,
                topBasketIndexWeightPct: null,
                eligibleConstituentCount: 0,
              },
              ranking: [],
            },
          ],
          references: [
            { label: "S&P 500 constituents" },
            { label: "STOXX Europe 600 constituents" },
          ],
        }),
      }),
    );

    const page = await HighestPsRankingPage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getAllByText("USA High P/S Leaders").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Europe High P/S Leaders").length).toBeGreaterThan(0);
    expect(screen.getByText(/Sector-relative high-P\/S names inside the S&P 500 eligible large-cap universe/i)).toBeInTheDocument();
    expect(screen.getByText(/Live section data for Europe High P\/S Leaders is unavailable right now\./i)).toBeInTheDocument();
    expect(screen.getByText("3.1x")).toBeInTheDocument();
    expect(screen.getByText("18.4x")).toBeInTheDocument();
    expect(screen.getByText("9.2%")).toBeInTheDocument();
    expect(screen.getByText("468")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Sector Avg P/S" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Rel. to Sector" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Index Weight" })).toBeInTheDocument();
    expect(screen.getByText("SNOW")).toBeInTheDocument();
    expect(screen.getByText("United States")).toBeInTheDocument();
    expect(screen.getByText("0.22%")).toBeInTheDocument();
    expect(screen.queryByText("Not available")).not.toBeInTheDocument();
  });
});

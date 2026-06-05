import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import CurrencyAnalysisPage from "../src/app/macro/currency-analysis/page";
import { ThemeProvider } from "../src/features/theme/provider";

const payload = {
  asOf: "2026-05-30",
  ppp: {
    availableBaseMonths: ["2026-01-01", "2026-02-01"],
    selectedBaseMonth: "2026-01-01",
    summary: {
      baseMonth: "2026-01-01",
      asOf: "2026-02-01",
      baseSpot: "1.1000",
      currentSpot: "1.2000",
      impliedPpp: "1.1109",
      deviationPct: "8.02",
    },
    path: [
      { observationMonth: "2026-01-01", actualSpot: "1.1000", impliedPpp: "1.1000" },
      { observationMonth: "2026-02-01", actualSpot: "1.2000", impliedPpp: "1.1109" },
    ],
    references: [
      { label: "EUR/USD spot", url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A" },
      { label: "US CPI index", url: "https://fred.stlouisfed.org/series/CPIAUCSL" },
      { label: "Euro Area CPI index", url: "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST" },
    ],
  },
  irp: {
    cipRows: [
      {
        tenor: "3M",
        asOf: "2026-05-30",
        spot: "1.1400",
        eurRate: "2.00",
        usdRate: "4.00",
        rateSpread: "-2.00",
        cipImpliedForward: "1.1344",
        hasObservedForward: false,
      },
      {
        tenor: "6M",
        asOf: "2026-05-30",
        spot: "1.1400",
        eurRate: "2.10",
        usdRate: "4.10",
        rateSpread: "-2.00",
        cipImpliedForward: "1.1288",
        hasObservedForward: false,
      },
    ],
    uip: {
      rows: [
        { tenor: "3M", impliedMovePct: "-0.50", impliedSpot: "1.1343" },
        { tenor: "6M", impliedMovePct: "-1.00", impliedSpot: "1.1286" },
      ],
    },
    references: [
      { label: "EUR/USD spot", url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A" },
      { label: "EUR 3M rate", url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR" },
      { label: "USD 3M rate", url: "https://fred.stlouisfed.org/series/DTB3" },
    ],
  },
  availability: [
    {
      sectionKey: "ppp",
      itemKey: "relative_ppp",
      status: "available",
      detail: "PPP snapshots and paths available.",
      asOfDate: "2026-02-01",
    },
  ],
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Currency Analysis page", () => {
  it("renders theory-first PPP and IRP sections from API data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const page = await CurrencyAnalysisPage({
      searchParams: Promise.resolve({ baseMonth: "2026-01-01" }),
    });

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: /Currency Analysis/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Relative Purchasing Power Parity/i })).toBeInTheDocument();
    expect(screen.getByText(/Relative PPP treats EUR\/USD as a long-run valuation relationship/i)).toBeInTheDocument();
    expect(screen.getByText(/PPP_t = S_base/i)).toBeInTheDocument();
    expect(screen.getAllByText("2026-01-01").length).toBeGreaterThan(0);
    expect(screen.getAllByText("1.1109").length).toBeGreaterThan(0);
    expect(screen.getByText(/Relative PPP suggests EUR\/USD is trading 8.02% above/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Interest Rate Parity/i })).toBeInTheDocument();
    expect(screen.getByText(/Interest rate parity links spot, tenor-specific rates, and forwards/i)).toBeInTheDocument();
    expect(screen.getByText(/F = S \* \(\(1 \+ r_EUR\) \/ \(1 \+ r_USD\)\)/i)).toBeInTheDocument();
    expect(screen.getAllByText("3M").length).toBeGreaterThan(0);
    expect(screen.getAllByText("6M").length).toBeGreaterThan(0);
    expect(screen.getByText("UIP Subsection")).toBeInTheDocument();
    expect(screen.getByText(/Across the visible tenors, EUR rates sit below USD rates/i)).toBeInTheDocument();
    expect(screen.queryByText("Live currency analysis data is unavailable right now.")).not.toBeInTheDocument();
  });

  it("shows an explicit unavailable-data notice instead of rendering fallback numbers when the API fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const page = await CurrencyAnalysisPage({});

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByText("Live currency analysis data is unavailable right now.")).toBeInTheDocument();
    expect(screen.getByText("Start the API and run the currency analysis pipeline to populate current values.")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /Relative Purchasing Power Parity/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /Interest Rate Parity/i })).not.toBeInTheDocument();
  });
});

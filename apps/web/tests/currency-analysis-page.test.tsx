import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import CurrencyAnalysisPage from "../src/app/macro/currency-analysis/page";
import { ThemeProvider } from "../src/features/theme/provider";

const pushMock = vi.fn();

vi.mock("next/navigation", async (importOriginal) => {
  const actual = await importOriginal<typeof import("next/navigation")>();

  return {
    ...actual,
    useRouter: () => ({
      push: pushMock,
    }),
  };
});

const payload = {
  asOf: "2026-05-30",
  ppp: {
    availableBaseYears: ["2025", "2026"],
    selectedBaseYear: "2025",
    summary: {
      baseYear: "2025",
      asOf: "2026-02-01",
      baseSpot: "1.1000",
      currentSpot: "1.2000",
      impliedPpp: "1.1109",
      deviationPct: "8.02",
      trailing12mAverageGapPct: "6.40",
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
  pushMock.mockReset();
  vi.unstubAllGlobals();
});

describe("Currency Analysis page", () => {
  it("renders a PPP-only analysis with a Taylor-style formula block, dropdown base month, and academic references", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const page = await CurrencyAnalysisPage({
      searchParams: Promise.resolve({ baseYear: "2025" }),
    });

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: /Currency Analysis/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /1.0 Relative Purchasing Power Parity/i })).toBeInTheDocument();
    expect(screen.getByText(/Relative PPP treats EUR\/USD as a long-run valuation relationship/i)).toBeInTheDocument();
    expect(screen.getByText(/PPP_t = S_0/i)).toBeInTheDocument();
    expect(screen.getByText(/Base-period spot exchange rate \(here: annual-average EUR\/USD in the selected base year\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Home-country price level at time t \(here: U\.S\. CPI index at observation month t\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Foreign-country price level in the base period \(here: annual-average euro area CPI index in the selected base year\)/i)).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: /PPP base-year average/i })).toBeInTheDocument();
    expect(screen.getAllByText("2025").length).toBeGreaterThan(0);
    expect(screen.getAllByText("1.1109").length).toBeGreaterThan(0);
    expect(screen.getByText(/The latest market spot sits 8.02% above the PPP-implied fair-value anchor/i)).toBeInTheDocument();
    expect(screen.getByText(/These values are computed from the selected base-year average and the latest month where spot and both CPI series overlap/i)).toBeInTheDocument();
    expect(screen.getByText(/Each row compares the observed EUR\/USD spot with the PPP-implied level generated from the selected base-year average/i)).toBeInTheDocument();
    expect(screen.getByText("6.40%")).toBeInTheDocument();
    expect(screen.queryByText("Snapshot")).not.toBeInTheDocument();
    expect(screen.queryByText("Recent Path Excerpt")).not.toBeInTheDocument();
    expect(screen.getByText(/\[1\] European Central Bank, Data Portal, "EUR\/USD spot"\. \[Online\]\. Available:/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /Interest Rate Parity/i })).not.toBeInTheDocument();
    expect(screen.queryByText("UIP Subsection")).not.toBeInTheDocument();
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

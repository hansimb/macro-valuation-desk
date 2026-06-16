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
    availableWindowOptions: [
      { code: "3Y", label: "3Y", yearsCovered: 3 },
      { code: "5Y", label: "5Y", yearsCovered: 5 },
      { code: "10Y", label: "10Y", yearsCovered: 10 },
      { code: "20Y", label: "20Y", yearsCovered: 20 },
      { code: "MAX", label: "MAX", yearsCovered: 26 },
    ],
    availableBaseYears: ["2025", "2026"],
    selectedAnchorKind: "window",
    selectedAnchorStatistic: "average",
    selectedWindowCode: "10Y",
    selectedBaseYear: "2025",
    summary: {
      anchorKind: "window",
      anchorStatistic: "average",
      anchorLabel: "10-year average anchor",
      anchorWindowCode: "10Y",
      anchorStartMonth: "2016-05-01",
      anchorEndMonth: "2026-04-01",
      anchorYearsCovered: 10,
      baseYear: null,
      asOf: "2026-02-01",
      baseSpot: "1.1000",
      currentSpot: "1.2000",
      impliedPpp: "1.1109",
      deviationPct: "8.02",
      trailing12mAverageGapPct: "6.40",
    },
    path: [
      { observationMonth: "2026-01-01", actualSpot: "1.1000", impliedPpp: "1.1000", hasImputedInputs: false },
      {
        observationMonth: "2026-02-01",
        actualSpot: "1.2000",
        impliedPpp: "1.1109",
        hasImputedInputs: true,
        imputationNote: "Filled using +/- 6 month median assumption.",
      },
    ],
    spotHistory: [
      { observationMonth: "2016-01-01", actualSpot: "1.0500" },
      { observationMonth: "2017-01-01", actualSpot: "1.0600" },
      { observationMonth: "2018-01-01", actualSpot: "1.0700" },
      { observationMonth: "2019-01-01", actualSpot: "1.0800" },
      { observationMonth: "2020-01-01", actualSpot: "1.0900" },
      { observationMonth: "2021-01-01", actualSpot: "1.1000" },
      { observationMonth: "2022-01-01", actualSpot: "1.1100" },
      { observationMonth: "2023-01-01", actualSpot: "1.1200" },
      { observationMonth: "2024-01-01", actualSpot: "1.1300" },
      { observationMonth: "2025-01-01", actualSpot: "1.1400" },
      { observationMonth: "2026-01-01", actualSpot: "1.1500" },
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
      searchParams: Promise.resolve({ anchorKind: "window", anchorStatistic: "average", windowCode: "10Y", baseYear: "2025" }),
    });

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: /Currency Analysis/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /1.0 Relative Purchasing Power Parity/i })).toBeInTheDocument();
    expect(screen.getByText(/Relative PPP treats EUR\/USD as a long-run valuation relationship/i)).toBeInTheDocument();
    expect(screen.getByText(/PPP_t = S_0/i)).toBeInTheDocument();
    expect(screen.getByText(/Base-period spot exchange rate \(here: the selected long-run anchor value for EUR\/USD under the chosen rule\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Home-country price level at time t \(here: U\.S\. CPI index at observation month t\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Foreign-country price level in the base period \(here: the selected long-run anchor value for euro-area CPI under the chosen rule\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/10-year average anchor/i).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /Average/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Median/i })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "MAX" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("combobox", { name: /Single-year anchor/i })).toBeInTheDocument();
    expect(screen.getAllByText("2025").length).toBeGreaterThan(0);
    expect(screen.getAllByText("1.1109").length).toBeGreaterThan(0);
    expect(screen.getByText(/The latest market spot sits 8.02% above the PPP-implied fair-value anchor/i)).toBeInTheDocument();
    expect(screen.getByText(/These values are computed from the selected long-run anchor and the latest month where spot and both CPI series overlap/i)).toBeInTheDocument();
    expect(screen.getByText(/Historical Spot Context/i)).toBeInTheDocument();
    expect(screen.getByText(/Observed EUR\/USD spot history with the selected long-run anchor spot shown as a reference line/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Historical EUR\/USD spot context/i)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "10Y" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "20Y" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "MAX" }).length).toBeGreaterThan(1);
    expect(screen.getByText(/X-axis: yearly marks. Y-axis: observed EUR\/USD spot/i)).toBeInTheDocument();
    expect(screen.getByText(/Hover the line to inspect month and spot/i)).toBeInTheDocument();
    expect(screen.getByText(/Each row compares the observed EUR\/USD spot with the PPP-implied level generated from the selected anchor rule/i)).toBeInTheDocument();
    expect(screen.getByText(/Rows marked with \* use at least one filled observation based on a \+\/- 6 month median assumption/i)).toBeInTheDocument();
    expect(screen.getByText("2026-02-01*")).toBeInTheDocument();
    expect(screen.getByText(/Available windows: 3Y \(3Y covered\), 5Y \(5Y covered\), 10Y \(10Y covered\), 20Y \(20Y covered\), MAX \(26Y covered\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Active anchor sample: 2016-05-01 to 2026-04-01 \(10 years covered\)/i)).toBeInTheDocument();
    expect(screen.getByText("6.40%")).toBeInTheDocument();
    expect(screen.queryByText("Snapshot")).not.toBeInTheDocument();
    expect(screen.queryByText("Recent Path Excerpt")).not.toBeInTheDocument();
    expect(screen.getAllByText(/\[1\] European Central Bank, Data Portal, "EUR\/USD spot"\. \[Online\]\. Available:/).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /2.0 Interest Rate Parity/i })).toBeInTheDocument();
    expect(screen.getByText(/Covered interest parity links spot, tenor-matched interest rates, and forwards/i)).toBeInTheDocument();
    expect(screen.queryByText("CIP exact")).not.toBeInTheDocument();
    expect(screen.queryByText("Carry approximation")).not.toBeInTheDocument();
    expect(screen.getByText(/F = S x \(\(1 \+ r_EUR x T\) \/ \(1 \+ r_USD x T\)\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Start from the live spot and tenor rates \(S, rEUR, rUSD, T\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Use the formula to calculate the tenor-matched forward anchor \(F\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Read UIP separately as a theoretical expected-spot lens \(E\[ST\]\)/i)).toBeInTheDocument();
    expect(screen.getByText(/CIP-implied forward/i)).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: /Observed forward/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: /CIP gap/i })).not.toBeInTheDocument();
    expect(screen.getAllByText("3M").length).toBeGreaterThan(0);
    expect(screen.getAllByText("6M").length).toBeGreaterThan(0);
    expect(screen.getAllByText("1.1400").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2.00%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("4.00%").length).toBeGreaterThan(0);
    expect(screen.queryByText("Not available")).not.toBeInTheDocument();
    expect(screen.queryByText("Not shown")).not.toBeInTheDocument();
    expect(screen.getByText(/UIP is shown as a theoretical expected-spot framing/i)).toBeInTheDocument();
    expect(screen.getByText(/Observed forwards are shown only when a reliable forward series is present/i)).toBeInTheDocument();
    expect(screen.queryByText("Live currency analysis data is unavailable right now.")).not.toBeInTheDocument();
  });

  it("renders IRP when PPP data is unavailable but IRP mart rows exist", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ...payload,
          ppp: {
            ...payload.ppp,
            availableWindowOptions: [],
            availableBaseYears: [],
            selectedAnchorKind: null,
            selectedWindowCode: null,
            selectedBaseYear: null,
            summary: null,
            path: [],
            spotHistory: [],
            references: [],
          },
        }),
      }),
    );

    const page = await CurrencyAnalysisPage({});

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: /2.0 Interest Rate Parity/i })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /1.0 Relative Purchasing Power Parity/i })).not.toBeInTheDocument();
    expect(screen.queryByText("Live currency analysis data is unavailable right now.")).not.toBeInTheDocument();
  });

  it("does not render the IRP analysis section when IRP mart rows are missing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ...payload,
          irp: {
            cipRows: [],
            uip: {
              rows: [],
            },
            references: [],
          },
          availability: [
            ...payload.availability,
            {
              sectionKey: "irp",
              itemKey: "3M",
              status: "unavailable",
              detail: "Required spot or tenor rate inputs are unavailable.",
              asOfDate: null,
            },
            {
              sectionKey: "irp",
              itemKey: "6M",
              status: "unavailable",
              detail: "Required spot or tenor rate inputs are unavailable.",
              asOfDate: null,
            },
            {
              sectionKey: "irp",
              itemKey: "12M",
              status: "unavailable",
              detail: "Required spot or tenor rate inputs are unavailable.",
              asOfDate: null,
            },
          ],
        }),
      }),
    );

    const page = await CurrencyAnalysisPage({});

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.queryByRole("heading", { name: /2.0 Interest Rate Parity/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/IRP tenor outputs are unavailable/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/EUR rates use compounded euro short-term average rate tenor proxies/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/EUR 3M rate/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/USD 12M rate/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Live currency analysis data is unavailable right now.")).not.toBeInTheDocument();
  });

  it("does not render the IRP analysis section when IRP rows contain invalid zero-valued market data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ...payload,
          ppp: {
            ...payload.ppp,
            availableWindowOptions: [],
            availableBaseYears: [],
            selectedAnchorKind: null,
            selectedWindowCode: null,
            selectedBaseYear: null,
            summary: null,
            path: [],
            spotHistory: [],
            references: [],
          },
          irp: {
            ...payload.irp,
            cipRows: [
              {
                tenor: "3M",
                asOf: "2026-05-30",
                spot: "0.0000",
                eurRate: "0.00",
                usdRate: "0.00",
                rateSpread: "0.00",
                cipImpliedForward: "0.0000",
                hasObservedForward: false,
              },
            ],
            uip: {
              rows: [],
            },
          },
        }),
      }),
    );

    const page = await CurrencyAnalysisPage({});

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.queryByRole("heading", { name: /2.0 Interest Rate Parity/i })).not.toBeInTheDocument();
    expect(screen.queryByText("0.0000")).not.toBeInTheDocument();
    expect(screen.queryByText("0.00%")).not.toBeInTheDocument();
    expect(screen.queryByText("Not available")).not.toBeInTheDocument();
    expect(screen.queryByText("Not shown")).not.toBeInTheDocument();
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

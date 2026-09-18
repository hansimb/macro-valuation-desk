import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import EquityMarketsPage from "../src/app/equity-markets/page";
import MarketValuationPage from "../src/app/equity-markets/market-valuation/page";
import { ThemeProvider } from "../src/features/theme/provider";

const metric = (key: string, value: string | null, overrides: Record<string, unknown> = {}) => ({
  metricKey: key, value, weeklyMin: value, weeklyMax: value,
  status: value === null ? "unavailable" : "experimental", method: `aggregate_${key}`, formula: `aggregate ${key}`,
  sensitivity: { point: value, lower: value, upper: value, status: "experimental", model: "v1", intervalLabel: "95% interval", reason: null, draws: 1000, components: [] },
  coverage: { wholeCohort: { market: "0.764", reported: "0.67", carriedForward: "0.12", imputed: "0.08", missingOrInvalid: "0.13" }, eligibleScope: { market: "0.764", eligible: "0.91" }, formationMarket: "0.781", currentMarket: "0.764" },
  constituents: { actualCount: 321, targetCount: 325, effectiveCount: "87.45", largestWeight: "0.071", topFiveConcentration: "0.229", topTenConcentration: "0.351", membershipOverlap: "0.98" },
  cohort: { version: "us-largecap-v12", effectiveDate: "2026-09-01" }, valuation: { week: "2026-09-07", dates: ["2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"], dailyObservationCount: 5 },
  warnings: [], methodologyVersion: "mvd-country-index-v1", referenceIds: ["methodology:mvd-country-index-v1", "source:sec"], ...overrides,
});

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("Market valuation page", () => {
  it("is discoverable from the equity analysis registry", () => {
    render(<ThemeProvider><EquityMarketsPage /></ThemeProvider>);
    expect(screen.getByRole("link", { name: /Market Valuation Dashboard/i })).toBeInTheDocument();
  });

  it("renders a fully clickable MVD country row with diagnostics and no ETF identity", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({
      asOf: "2026-09-07", regions: [{ region: "North America", markets: [{ marketId: "us", marketName: "United States", latestWeek: "2026-09-07", publication: { runId: "run-us", publishedAt: "2026-09-14T02:00:00Z", methodologyVersion: "mvd-country-index-v1" }, metrics: {
        pe: metric("pe", "21.35", { warnings: [{ code: "concentration", level: "warning", message: "Dominant constituents widen the interval.", affectedMarketWeight: "0.071", intervalWidthContribution: "0.42", reason: { code: "concentration" } }] }),
        pb: metric("pb", "4.20"), pfcf: metric("pfcf", null),
      } }] }], markets: [], references: [{ id: "source:sec", label: "SEC company facts", url: "https://data.sec.gov/submissions/" }],
    }) }));
    render(<ThemeProvider>{await MarketValuationPage()}</ThemeProvider>);

    expect(screen.getByRole("link", { name: /United States valuation history/i })).toHaveAttribute("href", "/equity-markets/market-valuation/us");
    expect(screen.getByText("321 / 325")).toBeInTheDocument();
    expect(screen.getByText("87.45")).toBeInTheDocument();
    expect(screen.getByText("76.4%")).toBeInTheDocument();
    expect(screen.getByText("67.0%")).toBeInTheDocument();
    expect(screen.getByLabelText("Warning: Dominant constituents widen the interval.")).toBeInTheDocument();
    expect(screen.queryByText(/ETF proxy/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/SPY|iShares|SPDR/)).not.toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "P/E" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "P/B" })).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: "Exact P/FCF" })).not.toBeInTheDocument();
  });

  it("renders an explicit unavailable state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ asOf: null, regions: [], markets: [], references: [] }) }));
    render(<ThemeProvider>{await MarketValuationPage()}</ThemeProvider>);
    expect(screen.getByText("Live market valuation data is unavailable right now.")).toBeInTheDocument();
    expect(screen.getByText("Run the MVD country valuation pipeline to publish weekly observations.")).toBeInTheDocument();
    expect(screen.queryByText(/ETF and index valuation snapshots/i)).not.toBeInTheDocument();
  });

  it("renders diagnostics without metric columns when every country metric is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({
      asOf: "2026-09-07", regions: [{ region: "North America", markets: [{ marketId: "us", marketName: "United States", latestWeek: "2026-09-07", publication: { runId: "run-us", publishedAt: "2026-09-14T02:00:00Z", methodologyVersion: "v1" }, metrics: { pe: metric("pe", null) } }] }], markets: [], references: [],
    }) }));
    render(<ThemeProvider>{await MarketValuationPage()}</ThemeProvider>);
    expect(screen.getByRole("link", { name: /United States valuation history/i })).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: "P/E" })).not.toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Companies" })).toBeInTheDocument();
  });
});

import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import MarketValuationHistoryPage from "../src/app/equity-markets/market-valuation/[marketId]/page";
import { ThemeProvider } from "../src/features/theme/provider";

const metric = (week: string, value: string, overrides: Record<string, unknown> = {}) => ({
  metricKey: "pe", value, weeklyMin: "20.90", weeklyMax: "21.80", status: "experimental",
  method: "aggregate_market_capitalization_divided_by_aggregate_ttm_common_net_income", formula: "aggregate market capitalization / aggregate TTM common net income",
  sensitivity: { point: value, lower: "19.80", upper: "23.10", status: "experimental", model: "mvd-country-index-v1", intervalLabel: "95% sensitivity interval", reason: null, draws: 1000, components: [] },
  coverage: { wholeCohort: { market: "0.764", reported: "0.67", carriedForward: "0.12", imputed: "0.08", missingOrInvalid: "0.13" }, eligibleScope: { market: "0.764", eligible: "0.91" }, formationMarket: "0.781", currentMarket: "0.764" },
  constituents: { actualCount: 321, targetCount: 325, effectiveCount: "87.45", largestWeight: "0.071", topFiveConcentration: "0.229", topTenConcentration: "0.351", membershipOverlap: "0.98" },
  cohort: { version: "us-largecap-v12", effectiveDate: "2026-09-01" }, valuation: { week, dates: [week, "2026-09-08", "2026-09-09"], dailyObservationCount: 3 }, warnings: [], methodologyVersion: "mvd-country-index-v1", referenceIds: ["methodology:mvd-country-index-v1", "source:sec", "source:prices"], ...overrides,
});

const response = { marketId: "us", marketName: "United States", region: "North America", observations: [
  { valuation: { week: "2026-08-31", dates: ["2026-08-31", "2026-09-01", "2026-09-02"], dailyObservationCount: 3 }, publication: { runId: "run-1", publishedAt: "2026-09-07T02:00:00Z", methodologyVersion: "mvd-country-index-v1" }, metrics: { pe: metric("2026-08-31", "20.75", { cohort: { version: "us-largecap-v11", effectiveDate: "2026-06-01" } }) } },
  { valuation: { week: "2026-09-07", dates: ["2026-09-07", "2026-09-08", "2026-09-09"], dailyObservationCount: 3 }, publication: { runId: "run-2", publishedAt: "2026-09-14T02:00:00Z", methodologyVersion: "mvd-country-index-v1" }, metrics: { pe: metric("2026-09-07", "21.35") } },
], references: [
  { id: "methodology:mvd-country-index-v1", label: "MVD country index methodology mvd-country-index-v1", url: null },
  { id: "source:sec", label: "U.S. Securities and Exchange Commission, Companyfacts API", url: "https://data.sec.gov/api/xbrl/companyfacts/" },
  { id: "source:prices", label: "Development price adapter, adjusted close history", url: "https://query1.finance.yahoo.com/" },
] };

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("Market valuation history page", () => {
  it("explains and charts the weekly country valuation history with exact lineage", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => response }));
    render(<ThemeProvider>{await MarketValuationHistoryPage({ params: Promise.resolve({ marketId: "us" }) })}</ThemeProvider>);
    expect(screen.getByRole("heading", { name: "United States valuation history" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /United States valuation history/i })).toHaveAttribute("href", "/equity-markets/market-valuation/us");
    expect(screen.getAllByText(/median of the daily aggregate country values/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/development price adapter/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("20.90–21.80").length).toBeGreaterThan(0);
    expect(screen.getAllByText("19.80–23.10").length).toBeGreaterThan(0);
    expect(screen.getByText(/Cohort boundary: us-largecap-v12 effective 2026-09-01/i)).toBeInTheDocument();
    expect(screen.getByText(/Published 2026-09-14/i)).toBeInTheDocument();
    expect(screen.getByText("aggregate market capitalization / aggregate TTM common net income")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "United States P/E weekly valuation history" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "United States P/E history data" })).toBeInTheDocument();
    expect(screen.getAllByText("Daily range").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /U.S. Securities and Exchange Commission, Companyfacts API/ })).toHaveAttribute("href", "https://data.sec.gov/api/xbrl/companyfacts/");
    expect(screen.getByRole("link", { name: /Development price adapter, adjusted close history/ })).toHaveAttribute("href", "https://query1.finance.yahoo.com/");
  });

  it("shows an unavailable state when the market has no observations in the selected range", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ ...response, observations: [] }) }));
    render(<ThemeProvider>{await MarketValuationHistoryPage({ params: Promise.resolve({ marketId: "us" }) })}</ThemeProvider>);
    expect(screen.getByText("Valuation history is unavailable for this market.")).toBeInTheDocument();
  });

  it("shows an unavailable state when observations contain no available metric values", async () => {
    const unavailableMetric = { ...metric("2026-09-07", "21.35"), value: null, weeklyMin: null, weeklyMax: null, status: "unavailable" };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ ...response, observations: [{ ...response.observations[1], metrics: { pe: unavailableMetric } }] }) }));
    render(<ThemeProvider>{await MarketValuationHistoryPage({ params: Promise.resolve({ marketId: "us" }) })}</ThemeProvider>);
    expect(screen.getByText("Valuation history is unavailable for this market.")).toBeInTheDocument();
    expect(screen.queryByRole("img", { name: /weekly valuation history/i })).not.toBeInTheDocument();
  });
});

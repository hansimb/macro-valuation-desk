import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";

import TaylorRulePage from "../src/app/macro/taylor-rule/page";
import { ThemeProvider } from "../src/features/theme/provider";

const payload = {
  asOf: "2026-05-01",
  formula: "i = r* + pi + 0.5(pi - pi*) + 0.5(slack)",
  assumptions: {
    neutralRate: "1.00",
    inflationTarget: "2.00",
    slackProxy: "0.00",
    inflationWeight: "0.50",
    slackWeight: "0.50"
  },
  regions: [
    {
      region: "EU",
      asOf: "2026-05-01",
      policyRate: "2.25",
      inflation: "2.10",
      target: "2.00",
      neutralRate: "1.00",
      slackProxy: "0.00",
      impliedRate: "3.15",
      policyGap: "-0.90",
      sourceNames: ["ECB", "FRED"],
      references: {
        policySeriesKey: "eu_policy_rate",
        policySourceUrl: "https://data.ecb.europa.eu/data/datasets/FM/FM.D.U2.EUR.4F.KR.DFR.LEV",
        inflationSeriesKey: "eu_hicp_headline",
        inflationSourceUrl: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR",
        slackSourceNote: "Assumed neutral slack proxy in v1"
      },
      referenceMetrics: {
        headlineInflation: { value: "2.10", asOf: "2026-04-01" },
        coreInflation: { value: "2.30", asOf: "2026-04-01" },
        policyRealRate: { value: "0.15", asOf: "2026-04-01", note: "Policy real rate = policy rate minus headline inflation." },
        marketRealRate: { value: "0.46", asOf: "2026-04-01" },
        outputGap: { value: "-0.49", asOf: "2026-01-01" },
        gdpGrowthYoy: {
          current: "1.20",
          historicalAverage: "1.60",
          gap: "-0.40",
          asOf: "2026-01-01",
          historyWindow: "2000-01-01 to 2026-01-01"
        },
        gdpGrowthQoqAnnualized: {
          current: "0.80",
          historicalAverage: "1.40",
          gap: "-0.60",
          asOf: "2026-01-01",
          historyWindow: "2000-01-01 to 2026-01-01"
        }
      }
    },
    {
      region: "US",
      asOf: "2026-05-01",
      policyRate: "4.50",
      inflation: "2.90",
      target: "2.00",
      neutralRate: "1.00",
      slackProxy: "0.00",
      impliedRate: "4.35",
      policyGap: "0.15",
      sourceNames: ["FRED"],
      references: {
        policySeriesKey: "us_policy_rate",
        policySourceUrl: "https://fred.stlouisfed.org/series/DFEDTARU",
        inflationSeriesKey: "us_cpi_headline",
        inflationSourceUrl: "https://fred.stlouisfed.org/series/CPIAUCSL",
        slackSourceNote: "Assumed neutral slack proxy in v1"
      },
      referenceMetrics: {
        headlineInflation: { value: "2.90", asOf: "2026-04-01" },
        coreInflation: { value: "3.10", asOf: "2026-04-01" },
        policyRealRate: { value: "1.60", asOf: "2026-04-01", note: "Policy real rate = policy rate minus headline inflation." },
        marketRealRate: { value: "2.10", asOf: "2026-04-01" },
        outputGap: { value: "-0.11", asOf: "2026-01-01" },
        gdpGrowthYoy: {
          current: "2.40",
          historicalAverage: "2.10",
          gap: "0.30",
          asOf: "2026-01-01",
          historyWindow: "2000-01-01 to 2026-01-01"
        },
        gdpGrowthQoqAnnualized: {
          current: "2.80",
          historicalAverage: "2.20",
          gap: "0.60",
          asOf: "2026-01-01",
          historyWindow: "2000-01-01 to 2026-01-01"
        }
      }
    }
  ],
  references: [
    {
      label: "EU policy rate",
      url: "https://data.ecb.europa.eu/data/datasets/FM/FM.D.U2.EUR.4F.KR.DFR.LEV"
    },
    {
      label: "US policy rate",
      url: "https://fred.stlouisfed.org/series/DFEDTARU"
    }
  ]
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Taylor Rule page", () => {
  it("renders per-region assumptions, results, and academic-style references from API data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload
      })
    );

    const page = await TaylorRulePage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: /Taylor Rule/i })).toBeInTheDocument();
    expect(screen.getByText("Implied nominal policy rate from the rule.")).toBeInTheDocument();
    expect(screen.getByText("Neutral real rate assumption.")).toBeInTheDocument();
    expect(screen.getByText("Current inflation rate.")).toBeInTheDocument();
    expect(screen.getByText("Inflation target.")).toBeInTheDocument();
    expect(screen.getByText("Slack or output-gap proxy.")).toBeInTheDocument();
    expect(screen.getAllByText("US").length).toBeGreaterThan(0);
    expect(screen.getAllByText("EU").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "EU" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "USA" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "EU assumptions" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "USA assumptions" })).toBeInTheDocument();
    expect(screen.getAllByText("CPI").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Core CPI").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Policy real rate").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Market real rate").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Output gap").length).toBeGreaterThan(0);
    expect(screen.getAllByText("GDP YoY growth").length).toBeGreaterThan(0);
    expect(screen.getAllByText("GDP YoY Avg").length).toBeGreaterThan(0);
    expect(screen.queryByText("GDP q/q ann. growth")).not.toBeInTheDocument();
    expect(screen.getByText("Source: ECB, FRED")).toBeInTheDocument();
    expect(screen.getByText("Source: FRED")).toBeInTheDocument();
    expect(screen.getByText(/Interpretation: EU screens easier than the rule benchmark by 0.90 percentage points\./)).toBeInTheDocument();
    expect(screen.getByText(/Interpretation: US screens tighter than the rule benchmark by 0.15 percentage points\./)).toBeInTheDocument();
    expect(screen.getByText(/European Central Bank, Data Portal, "EU policy rate"/)).toBeInTheDocument();
    expect(screen.getByText(/Federal Reserve Bank of St\. Louis, FRED, "US policy rate"/)).toBeInTheDocument();
    expect(screen.queryByText("Assumed neutral slack proxy in v1")).not.toBeInTheDocument();
  });

  it("adjusts region assumptions in 0.25 point steps", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload
      })
    );

    const page = await TaylorRulePage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    const euNeutralIncrease = screen.getByRole("button", { name: "Increase EU neutral rate" });
    fireEvent.click(euNeutralIncrease);

    expect(screen.getAllByText("1.25").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Interpretation: EU screens easier than the rule benchmark by 1.15 percentage points\./)
    ).toBeInTheDocument();

    const euSlackDecrease = screen.getByRole("button", { name: "Decrease EU slack proxy" });
    fireEvent.click(euSlackDecrease);

    expect(screen.getAllByText("-0.25").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Interpretation: EU screens easier than the rule benchmark by 1.03 percentage points\./)
    ).toBeInTheDocument();
  });

  it("switches a region calculation between headline and core CPI", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload
      })
    );

    const page = await TaylorRulePage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    fireEvent.click(screen.getAllByRole("button", { name: "Core CPI" })[0]);

    expect(screen.getAllByText(/Core CPI/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Interpretation: EU screens easier than the rule benchmark by 1.20 percentage points\./)).toBeInTheDocument();
  });

  it("shows an explicit unavailable-data notice instead of rendering fallback numbers when the API fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const page = await TaylorRulePage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByText("Live Taylor Rule data is unavailable right now.")).toBeInTheDocument();
    expect(screen.getByText("Start the API and run the Taylor Rule pipeline to populate current values.")).toBeInTheDocument();
    expect(screen.queryByText("European Central Bank, Data Portal, \"EU policy rate\"")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "USA" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "EU assumptions" })).not.toBeInTheDocument();
  });
});

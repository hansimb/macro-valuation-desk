import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

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
      references: {
        policySeriesKey: "eu_policy_rate",
        policySourceUrl: "https://data.ecb.europa.eu/data/datasets/FM/FM.D.U2.EUR.4F.KR.DFR.LEV",
        inflationSeriesKey: "eu_hicp_headline",
        inflationSourceUrl: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR",
        slackSourceNote: "Assumed neutral slack proxy in v1"
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
      references: {
        policySeriesKey: "us_policy_rate",
        policySourceUrl: "https://fred.stlouisfed.org/series/DFEDTARU",
        inflationSeriesKey: "us_cpi_headline",
        inflationSourceUrl: "https://fred.stlouisfed.org/series/CPIAUCSL",
        slackSourceNote: "Assumed neutral slack proxy in v1"
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
  vi.unstubAllGlobals();
});

describe("Taylor Rule page", () => {
  it("renders the formula, compact symbol guide, region comparison, and references from API data", async () => {
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
    expect(screen.getByText("US")).toBeInTheDocument();
    expect(screen.getByText("EU")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Base" })).toBeInTheDocument();
    expect(screen.getByText("EU policy rate")).toBeInTheDocument();
    expect(screen.getByText("US policy rate")).toBeInTheDocument();
  });
});

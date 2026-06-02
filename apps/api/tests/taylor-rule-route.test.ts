import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const queryMock = vi.fn();

vi.mock("../src/lib/db", () => ({
  getDbPool: () => ({
    query: queryMock
  })
}));

import { buildServer } from "../src/server";

describe("taylor rule route", () => {
  const app = buildServer();

  beforeAll(async () => {
    await app.ready();
  });

  afterAll(async () => {
    await app.close();
  });

  beforeEach(() => {
    queryMock.mockReset();
  });

  it("returns a two-region comparison contract when mart data exists", async () => {
    queryMock.mockResolvedValue({
      rows: [
        {
          region: "EU",
          as_of_date: "2026-05-01",
          policy_rate: "2.25",
          inflation: "2.10",
          inflation_target: "2.00",
          neutral_rate: "1.00",
          slack_proxy: "0.00",
          implied_rate: "3.15",
          policy_gap: "-0.90",
          policy_series_key: "eu_policy_rate",
          policy_source_url: "https://data.ecb.europa.eu/data/datasets/FM/FM.D.U2.EUR.4F.KR.DFR.LEV",
          inflation_series_key: "eu_hicp_headline",
          inflation_source_url: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR",
          slack_source_note: "Assumed neutral slack proxy in v1"
        },
        {
          region: "US",
          as_of_date: "2026-05-01",
          policy_rate: "4.50",
          inflation: "2.90",
          inflation_target: "2.00",
          neutral_rate: "1.00",
          slack_proxy: "0.00",
          implied_rate: "4.35",
          policy_gap: "0.15",
          policy_series_key: "us_policy_rate",
          policy_source_url: "https://fred.stlouisfed.org/series/DFEDTARU",
          inflation_series_key: "us_cpi_headline",
          inflation_source_url: "https://fred.stlouisfed.org/series/CPIAUCSL",
          slack_source_note: "Assumed neutral slack proxy in v1"
        }
      ]
    });

    const response = await app.inject({ method: "GET", url: "/macro/taylor-rule" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
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
          label: "EU inflation",
          url: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR"
        },
        {
          label: "US policy rate",
          url: "https://fred.stlouisfed.org/series/DFEDTARU"
        },
        {
          label: "US inflation",
          url: "https://fred.stlouisfed.org/series/CPIAUCSL"
        },
        {
          label: "Slack proxy",
          note: "Assumed neutral slack proxy in v1"
        }
      ]
    });
  });

  it("returns an empty but stable contract when mart data is missing", async () => {
    queryMock.mockResolvedValue({ rows: [] });

    const response = await app.inject({ method: "GET", url: "/macro/taylor-rule" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toMatchObject({
      asOf: null,
      regions: [],
      references: []
    });
  });
});

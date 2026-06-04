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
          slack_source_note: "Assumed neutral slack proxy in v1",
          headline_inflation: "2.10",
          headline_inflation_as_of_date: "2026-04-01",
          core_inflation: "2.30",
          core_inflation_as_of_date: "2026-04-01",
          policy_real_rate: "0.15",
          policy_real_rate_as_of_date: "2026-04-01",
          market_real_rate: "0.46",
          market_real_rate_as_of_date: "2026-04-01",
          output_gap: "-0.49",
          output_gap_as_of_date: "2026-01-01",
          gdp_growth_yoy_current: "4.06",
          gdp_growth_yoy_historical_average: "4.06",
          gdp_growth_yoy_gap: "0.00",
          gdp_growth_yoy_as_of_date: "2026-01-01",
          gdp_growth_yoy_history_window: "2026-01-01",
          gdp_growth_qoq_annualized_current: "4.04",
          gdp_growth_qoq_annualized_historical_average: "4.04",
          gdp_growth_qoq_annualized_gap: "0.00",
          gdp_growth_qoq_annualized_as_of_date: "2026-01-01",
          gdp_growth_qoq_annualized_history_window: "2025-04-01 to 2026-01-01",
          headline_series_key: "eu_hicp_headline",
          headline_source_url: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR",
          core_series_key: "eu_hicp_core",
          core_source_url: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.XEFUN0.4D0.ANR",
          market_real_rate_series_key: "eu_market_real_rate",
          market_real_rate_source_url: "https://data.ecb.europa.eu/data/datasets/FM/FM.M.U2.EUR.4F.BB.R_U2_10Y.YLDA",
          output_gap_series_key: "eu_output_gap",
          output_gap_source_url: "https://db.nomics.world/AMECO/AVGDGP/EA20.1.0.0.0.AVGDGP",
          gdp_series_key: "eu_real_gdp",
          gdp_source_url: "https://data.ecb.europa.eu/data/datasets/MNA/MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
          policy_real_rate_note: "Policy real rate = policy rate minus headline inflation."
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
          slack_source_note: "Assumed neutral slack proxy in v1",
          headline_inflation: "3.00",
          headline_inflation_as_of_date: "2026-04-01",
          core_inflation: "3.00",
          core_inflation_as_of_date: "2026-04-01",
          policy_real_rate: "1.50",
          policy_real_rate_as_of_date: "2026-04-01",
          market_real_rate: "2.10",
          market_real_rate_as_of_date: "2026-04-01",
          output_gap: "-0.11",
          output_gap_as_of_date: "2026-01-01",
          gdp_growth_yoy_current: "4.06",
          gdp_growth_yoy_historical_average: "4.06",
          gdp_growth_yoy_gap: "0.00",
          gdp_growth_yoy_as_of_date: "2026-01-01",
          gdp_growth_yoy_history_window: "2026-01-01",
          gdp_growth_qoq_annualized_current: "4.04",
          gdp_growth_qoq_annualized_historical_average: "4.04",
          gdp_growth_qoq_annualized_gap: "0.00",
          gdp_growth_qoq_annualized_as_of_date: "2026-01-01",
          gdp_growth_qoq_annualized_history_window: "2025-04-01 to 2026-01-01",
          headline_series_key: "us_cpi_headline",
          headline_source_url: "https://fred.stlouisfed.org/series/CPIAUCSL",
          core_series_key: "us_cpi_core",
          core_source_url: "https://fred.stlouisfed.org/series/CPILFESL",
          market_real_rate_series_key: "us_market_real_rate",
          market_real_rate_source_url: "https://data.ecb.europa.eu/data/datasets/FM/FM.M.US.USD.4F.BB.R_US10YT_RR.YLDA",
          output_gap_series_key: "us_output_gap",
          output_gap_source_url: "https://db.nomics.world/AMECO/AVGDGP/USA.1.0.0.0.AVGDGP",
          gdp_series_key: "us_real_gdp",
          gdp_source_url: "https://fred.stlouisfed.org/series/GDPC1",
          policy_real_rate_note: "Policy real rate = policy rate minus headline inflation."
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
          sourceNames: ["ECB", "AMECO"],
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
            policyRealRate: {
              value: "0.15",
              asOf: "2026-04-01",
              note: "Policy real rate = policy rate minus headline inflation."
            },
            marketRealRate: { value: "0.46", asOf: "2026-04-01" },
            outputGap: { value: "-0.49", asOf: "2026-01-01" },
            gdpGrowthYoy: {
              current: "4.06",
              historicalAverage: "4.06",
              gap: "0.00",
              asOf: "2026-01-01",
              historyWindow: "2026-01-01"
            },
            gdpGrowthQoqAnnualized: {
              current: "4.04",
              historicalAverage: "4.04",
              gap: "0.00",
              asOf: "2026-01-01",
              historyWindow: "2025-04-01 to 2026-01-01"
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
          sourceNames: ["FRED", "ECB", "AMECO"],
          references: {
            policySeriesKey: "us_policy_rate",
            policySourceUrl: "https://fred.stlouisfed.org/series/DFEDTARU",
            inflationSeriesKey: "us_cpi_headline",
            inflationSourceUrl: "https://fred.stlouisfed.org/series/CPIAUCSL",
            slackSourceNote: "Assumed neutral slack proxy in v1"
          },
          referenceMetrics: {
            headlineInflation: { value: "3.00", asOf: "2026-04-01" },
            coreInflation: { value: "3.00", asOf: "2026-04-01" },
            policyRealRate: {
              value: "1.50",
              asOf: "2026-04-01",
              note: "Policy real rate = policy rate minus headline inflation."
            },
            marketRealRate: { value: "2.10", asOf: "2026-04-01" },
            outputGap: { value: "-0.11", asOf: "2026-01-01" },
            gdpGrowthYoy: {
              current: "4.06",
              historicalAverage: "4.06",
              gap: "0.00",
              asOf: "2026-01-01",
              historyWindow: "2026-01-01"
            },
            gdpGrowthQoqAnnualized: {
              current: "4.04",
              historicalAverage: "4.04",
              gap: "0.00",
              asOf: "2026-01-01",
              historyWindow: "2025-04-01 to 2026-01-01"
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
          label: "EU inflation",
          url: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR"
        },
        {
          label: "EU core inflation",
          url: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.XEFUN0.4D0.ANR"
        },
        {
          label: "EU market real rate",
          url: "https://data.ecb.europa.eu/data/datasets/FM/FM.M.U2.EUR.4F.BB.R_U2_10Y.YLDA"
        },
        {
          label: "EU output gap",
          url: "https://db.nomics.world/AMECO/AVGDGP/EA20.1.0.0.0.AVGDGP"
        },
        {
          label: "EU GDP growth proxy",
          url: "https://data.ecb.europa.eu/data/datasets/MNA/MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N"
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
          label: "US core inflation",
          url: "https://fred.stlouisfed.org/series/CPILFESL"
        },
        {
          label: "US market real rate",
          url: "https://data.ecb.europa.eu/data/datasets/FM/FM.M.US.USD.4F.BB.R_US10YT_RR.YLDA"
        },
        {
          label: "US output gap",
          url: "https://db.nomics.world/AMECO/AVGDGP/USA.1.0.0.0.AVGDGP"
        },
        {
          label: "US GDP growth proxy",
          url: "https://fred.stlouisfed.org/series/GDPC1"
        },
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

  it("omits reference metrics when the joined reference-metrics row is missing", async () => {
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
          slack_source_note: "Assumed neutral slack proxy in v1",
          headline_inflation: null,
          headline_inflation_as_of_date: null,
          core_inflation: null,
          core_inflation_as_of_date: null,
          policy_real_rate: null,
          policy_real_rate_as_of_date: null,
          market_real_rate: null,
          market_real_rate_as_of_date: null,
          output_gap: null,
          output_gap_as_of_date: null,
          gdp_growth_yoy_current: null,
          gdp_growth_yoy_historical_average: null,
          gdp_growth_yoy_gap: null,
          gdp_growth_yoy_as_of_date: null,
          gdp_growth_yoy_history_window: null,
          gdp_growth_qoq_annualized_current: null,
          gdp_growth_qoq_annualized_historical_average: null,
          gdp_growth_qoq_annualized_gap: null,
          gdp_growth_qoq_annualized_as_of_date: null,
          gdp_growth_qoq_annualized_history_window: null,
          headline_series_key: null,
          headline_source_url: null,
          core_series_key: null,
          core_source_url: null,
          market_real_rate_series_key: null,
          market_real_rate_source_url: null,
          output_gap_series_key: null,
          output_gap_source_url: null,
          gdp_series_key: null,
          gdp_source_url: null,
          policy_real_rate_note: null
        }
      ]
    });

    const response = await app.inject({ method: "GET", url: "/macro/taylor-rule" });
    const body = response.json();

    expect(response.statusCode).toBe(200);
    expect(body.regions).toHaveLength(1);
    expect(body.regions[0].sourceNames).toEqual(["ECB"]);
    expect(body.regions[0]).not.toHaveProperty("referenceMetrics");
  });
});

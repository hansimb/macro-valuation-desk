import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const queryMock = vi.fn();

vi.mock("../src/lib/db", () => ({
  getDbPool: () => ({
    query: queryMock,
  }),
}));

import { buildServer } from "../src/server";

const sourceCoverage = {
  references: [
    {
      id: "sec-companyfacts",
      label: "SEC company facts API",
      url: "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
    },
  ],
  sensitivity: {
    point_estimate: "21.345678901234567890",
    status: "experimental",
    model: "seeded_multiple_imputation_v1",
    draws: 1000,
    components: [{ code: "concentration", interval_width_contribution: "0.42", available: true }],
  },
};

const publishedPe = {
  market_id: "us",
  market_name: "United States",
  region: "North America",
  metric_key: "pe",
  week_id: "2026-09-07",
  published_at: "2026-09-14T02:00:00.000Z",
  run_id: "country-index-us-20260914",
  methodology_version: "mvd-country-index-v1",
  cohort_version: "2026-09-07",
  metric_value: "21.345678901234567890",
  weekly_min_value: "20.10",
  weekly_max_value: "22.40",
  valuation_dates: ["2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"],
  daily_observation_count: 5,
  metric_status: "warning",
  formation_market_coverage: "0.781",
  current_market_coverage: "0.764",
  reported_fact_coverage: "0.67",
  carried_forward_coverage: "0.12",
  imputed_coverage: "0.08",
  missing_or_invalid_coverage: "0.13",
  metric_eligible_coverage: "0.91",
  actual_constituent_count: 321,
  cohort_target_count: 325,
  effective_constituent_count: "87.45",
  largest_constituent_weight: "0.071",
  top_five_concentration: "0.229",
  top_ten_concentration: "0.351",
  membership_overlap: "0.98",
  interval_lower: "19.90",
  interval_upper: "23.80",
  source_coverage: sourceCoverage,
  structured_reasons: ["concentration", "missing_fact"],
  warnings: [
    {
      warning_code: "concentration",
      warning_level: "experimental",
      warning_message: "Dominant constituents widen the sensitivity interval.",
      affected_market_weight: "0.071",
      interval_width_contribution: "0.42",
      structured_reason: { code: "concentration", component: { available: true } },
    },
  ],
};

describe("equity market valuations route", () => {
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

  it("returns only latest atomically published MVD metrics and keeps numeric values as strings", async () => {
    queryMock.mockResolvedValue({
      rows: [
        publishedPe,
        {
          ...publishedPe,
          metric_key: "pfcf",
          metric_value: null,
          weekly_min_value: null,
          weekly_max_value: null,
          metric_status: "unavailable",
          structured_reasons: ["non_positive_denominator"],
          warnings: [],
        },
      ],
    });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations" });

    expect(response.statusCode).toBe(200);
    const [sql, values] = queryMock.mock.calls[0] as [string, unknown[] | undefined];
    expect(sql).toContain("marts.country_index_publications");
    expect(sql).toContain("core.country_weekly_metrics");
    expect(sql).toContain("core.country_index_runs");
    expect(sql).toContain("publication.is_current = true");
    expect(sql).toContain("run.run_status = 'completed'");
    expect(sql).toContain("row_number() over (partition by weekly.market_id, weekly.metric_key");
    expect(sql).not.toContain("equity_market_valuation_snapshot");
    expect(sql).not.toContain("raw.");
    expect(sql).not.toContain("staging.");
    expect(values ?? []).toEqual([]);
    expect(response.json()).toEqual({
      asOf: "2026-09-07",
      regions: [
        {
          region: "North America",
          markets: [
            {
              marketId: "us",
              marketName: "United States",
              latestWeek: "2026-09-07",
              publication: { runId: "country-index-us-20260914", publishedAt: "2026-09-14T02:00:00.000Z" },
              metrics: {
                pe: {
                  metricKey: "pe",
                  value: "21.345678901234567890",
                  weeklyMin: "20.10",
                  weeklyMax: "22.40",
                  status: "warning",
                  method: "aggregate_market_capitalization_divided_by_aggregate_ttm_common_net_income",
                  formula: "aggregate market capitalization / aggregate TTM common net income",
                  sensitivity: {
                    point: "21.345678901234567890",
                    lower: "19.90",
                    upper: "23.80",
                    status: "experimental",
                    model: "seeded_multiple_imputation_v1",
                    draws: 1000,
                    components: [{ code: "concentration", intervalWidthContribution: "0.42", available: true }],
                  },
                  coverage: {
                    wholeCohort: {
                      market: "0.764",
                      reported: "0.67",
                      carriedForward: "0.12",
                      imputed: "0.08",
                      missingOrInvalid: "0.13",
                    },
                    eligibleScope: { market: "0.764", eligible: "0.91" },
                    formationMarket: "0.781",
                    currentMarket: "0.764",
                  },
                  constituents: {
                    actualCount: 321,
                    targetCount: 325,
                    effectiveCount: "87.45",
                    largestWeight: "0.071",
                    topFiveConcentration: "0.229",
                    topTenConcentration: "0.351",
                    membershipOverlap: "0.98",
                  },
                  cohort: { version: "2026-09-07", effectiveDate: "2026-09-07" },
                  valuation: {
                    week: "2026-09-07",
                    dates: ["2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"],
                    dailyObservationCount: 5,
                  },
                  warnings: [
                    {
                      code: "concentration",
                      level: "experimental",
                      message: "Dominant constituents widen the sensitivity interval.",
                      affectedMarketWeight: "0.071",
                      intervalWidthContribution: "0.42",
                      reason: { code: "concentration", component: { available: true } },
                    },
                    {
                      code: "missing_fact",
                      level: "warning",
                      message: "missing_fact",
                      affectedMarketWeight: null,
                      intervalWidthContribution: null,
                      reason: { code: "missing_fact" },
                    },
                  ],
                  methodologyVersion: "mvd-country-index-v1",
                  referenceIds: ["methodology:mvd-country-index-v1", "sec-companyfacts"],
                },
                pfcf: expect.objectContaining({
                  value: null,
                  weeklyMin: null,
                  weeklyMax: null,
                  status: "unavailable",
                  warnings: [expect.objectContaining({ code: "non_positive_denominator" })],
                }),
              },
            },
          ],
        },
      ],
      references: [
        {
          id: "methodology:mvd-country-index-v1",
          label: "MVD country index methodology mvd-country-index-v1",
          url: null,
        },
        {
          id: "sec-companyfacts",
          label: "SEC company facts API",
          url: "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
        },
      ],
    });
  });

  it("deduplicates repeated metric rows selected by the SQL window and source references", async () => {
    queryMock.mockResolvedValue({
      rows: [
        publishedPe,
        { ...publishedPe, metric_value: "999.99" },
        { ...publishedPe, metric_key: "pb", metric_value: "4.20", source_coverage: sourceCoverage },
      ],
    });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations" });

    expect(response.statusCode).toBe(200);
    expect(Object.keys(response.json().regions[0].markets[0].metrics)).toEqual(["pe", "pb"]);
    expect(response.json().regions[0].markets[0].metrics.pe.value).toBe("21.345678901234567890");
    expect(response.json().references).toHaveLength(2);
  });

  it("returns an empty MVD overview when no published observation exists", async () => {
    queryMock.mockResolvedValue({ rows: [] });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({ asOf: null, regions: [], references: [] });
  });
});

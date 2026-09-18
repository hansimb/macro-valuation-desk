import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const queryMock = vi.fn();

vi.mock("../src/lib/db", () => ({
  getDbPool: () => ({
    query: queryMock,
  }),
}));

import { buildServer } from "../src/server";

const sourceCoverage = {
  sensitivity: {
    interval_label: "experimental seeded sensitivity interval",
    status: "experimental",
    reason: null,
    model_version: "mvd-country-index-v1",
    seed: "us-pe-20260907",
    point_estimate: "21.345678901234567890",
    lower: "19.70",
    upper: "24.10",
    draws: 1000,
    components: [{ code: "concentration", interval_width_contribution: "0.42", available: true }],
    warnings: [{ code: "staleness", reason: "late filing acceptance" }],
  },
  references: [{ id: "price-feed", label: "Primary price feed", url: "https://prices.example.test/us" }],
};

const unavailableSourceCoverage = {
  sensitivity: {
    interval_label: "unavailable sensitivity interval",
    status: "unavailable",
    reason: "non_positive_denominator_in_sensitivity_draw",
    model_version: "mvd-country-index-v1",
    seed: "us-pfcf-20260907",
    point_estimate: null,
    lower: null,
    upper: null,
    draws: 1000,
    components: [{ code: "denominator", interval_width_contribution: null, available: false }],
    warnings: [{ code: "non_positive_denominator", reason: "non-positive denominator" }],
  },
};

const runSourceCoverage = {
  references: [
    { id: "price-feed", label: "Primary price feed", url: "https://prices.example.test/us" },
    { id: "price-feed", label: "Conflicting price feed", url: "https://prices.example.test/conflict" },
  ],
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
  cohort_version: "us-largecap-v12",
  cohort_effective_date: "2026-09-01",
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
  source_coverage: JSON.stringify(sourceCoverage),
  run_source_coverage: runSourceCoverage,
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
          interval_lower: "0.01",
          interval_upper: "999.99",
          source_coverage: unavailableSourceCoverage,
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
    expect(response.json()).toMatchObject({
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
                    lower: "19.70",
                    upper: "24.10",
                    status: "experimental",
                    model: "mvd-country-index-v1",
                    intervalLabel: "experimental seeded sensitivity interval",
                    reason: null,
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
                  cohort: { version: "us-largecap-v12", effectiveDate: "2026-09-01" },
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
                  referenceIds: [
                    "methodology:mvd-country-index-v1",
                    "source:price-feed",
                    expect.stringMatching(/^source:price-feed:[a-z0-9]+$/),
                  ],
                },
                pfcf: {
                  metricKey: "pfcf",
                  value: null,
                  weeklyMin: null,
                  weeklyMax: null,
                  status: "unavailable",
                  method: "aggregate_market_capitalization_divided_by_aggregate_ttm_free_cash_flow",
                  formula: "aggregate market capitalization / aggregate TTM free cash flow",
                  sensitivity: {
                    point: null,
                    lower: null,
                    upper: null,
                    status: "unavailable",
                    model: "mvd-country-index-v1",
                    intervalLabel: "unavailable sensitivity interval",
                    reason: "non_positive_denominator_in_sensitivity_draw",
                    draws: 1000,
                    components: [{ code: "denominator", intervalWidthContribution: null, available: false }],
                  },
                  coverage: expect.any(Object),
                  constituents: expect.any(Object),
                  cohort: { version: "us-largecap-v12", effectiveDate: "2026-09-01" },
                  valuation: expect.any(Object),
                  warnings: [expect.objectContaining({ code: "non_positive_denominator" })],
                  methodologyVersion: "mvd-country-index-v1",
                  referenceIds: [
                    "methodology:mvd-country-index-v1",
                    "source:price-feed",
                    expect.stringMatching(/^source:price-feed:[a-z0-9]+$/),
                  ],
                },
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
          id: "source:price-feed",
          label: "Primary price feed",
          url: "https://prices.example.test/us",
        },
        {
          id: expect.stringMatching(/^source:price-feed:[a-z0-9]+$/),
          label: "Conflicting price feed",
          url: "https://prices.example.test/conflict",
        },
      ],
      markets: [
        expect.objectContaining({
          marketId: "us",
          marketName: "United States",
          asOf: "2026-09-07",
          metrics: expect.objectContaining({
            trailingPe: expect.objectContaining({ value: "21.345678901234567890" }),
            priceToFreeCashFlow: expect.objectContaining({ value: null }),
          }),
        }),
      ],
    });

    expect(response.json().regions[0].markets[0].metrics.pe.referenceIds).toEqual([
      "methodology:mvd-country-index-v1",
      "source:price-feed",
      expect.stringMatching(/^source:price-feed:[a-z0-9]+$/),
    ]);
    expect(new Set(response.json().regions[0].markets[0].metrics.pe.referenceIds).size).toBe(
      response.json().regions[0].markets[0].metrics.pe.referenceIds.length,
    );
  });

  it("uses one coherent market publication snapshot instead of mixing latest metric pointers", async () => {
    queryMock.mockResolvedValue({
      rows: [
        { ...publishedPe, run_id: "run-new", week_id: "2026-09-14", published_at: "2026-09-21T02:00:00.000Z", metric_value: "22.00" },
        { ...publishedPe, run_id: "run-old", week_id: "2026-09-07", metric_key: "pe", metric_value: "21.00" },
        { ...publishedPe, run_id: "run-old", week_id: "2026-09-07", metric_key: "pb", metric_value: "4.20" },
      ],
    });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations" });

    expect(response.statusCode).toBe(200);
    expect(response.json().regions[0].markets[0].publication).toEqual({
      runId: "run-new",
      publishedAt: "2026-09-21T02:00:00.000Z",
      methodologyVersion: "mvd-country-index-v1",
    });
    expect(Object.keys(response.json().regions[0].markets[0].metrics)).toEqual(["pe"]);
    expect(response.json().regions[0].markets[0].metrics.pe.value).toBe("22.00");
  });

  it("treats invalid persisted JSON as empty structured data instead of inventing references or warnings", async () => {
    queryMock.mockResolvedValue({
      rows: [
        {
          ...publishedPe,
          source_coverage: "{not-json",
          run_source_coverage: 42,
          structured_reasons: "{\"code\":\"not-an-array\"}",
          warnings: "not-json",
        },
      ],
    });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations" });

    expect(response.statusCode).toBe(200);
    expect(response.json().regions[0].markets[0].metrics.pe.warnings).toEqual([]);
    expect(response.json().regions[0].markets[0].metrics.pe.referenceIds).toEqual(["methodology:mvd-country-index-v1"]);
    expect(response.json().references).toEqual([
      { id: "methodology:mvd-country-index-v1", label: "MVD country index methodology mvd-country-index-v1", url: null },
    ]);
  });

  it("normalizes a stringified nested sensitivity payload without conflating its persisted fields", async () => {
    queryMock.mockResolvedValue({
      rows: [
        {
          ...publishedPe,
          source_coverage: JSON.stringify({
            sensitivity: JSON.stringify({
              status: "unavailable",
              reason: "non_positive_denominator_in_sensitivity_draw",
              model_version: "configured-sensitivity-method-v7",
              interval_label: "unavailable sensitivity interval",
              point_estimate: null,
              lower: null,
              upper: null,
              draws: 250,
              components: [],
            }),
          }),
        },
      ],
    });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations" });

    expect(response.statusCode).toBe(200);
    expect(response.json().regions[0].markets[0].metrics.pe.sensitivity).toEqual({
      point: null,
      lower: null,
      upper: null,
      status: "unavailable",
      model: "configured-sensitivity-method-v7",
      intervalLabel: "unavailable sensitivity interval",
      reason: "non_positive_denominator_in_sensitivity_draw",
      draws: 250,
      components: [],
    });
  });

  it("returns an empty MVD overview when no published observation exists", async () => {
    queryMock.mockResolvedValue({ rows: [] });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({ asOf: null, regions: [], markets: [], references: [] });
  });
});

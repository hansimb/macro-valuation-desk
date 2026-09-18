import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const queryMock = vi.fn();

vi.mock("../src/lib/db", () => ({
  getDbPool: () => ({
    query: queryMock,
  }),
}));

import { buildServer } from "../src/server";

const historyRow = {
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
  metric_value: "21.30",
  weekly_min_value: "20.10",
  weekly_max_value: "22.40",
  valuation_dates: ["2026-09-07", "2026-09-08", "2026-09-09"],
  daily_observation_count: 3,
  metric_status: "complete",
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
  interval_lower: "20.00",
  interval_upper: "22.50",
  source_coverage: {
    sensitivity: {
      interval_label: "experimental seeded sensitivity interval",
      status: "experimental",
      reason: null,
      model_version: "mvd-country-index-v1",
      point_estimate: "21.30",
      lower: "20.05",
      upper: "22.55",
      draws: 1000,
      components: [],
    },
  },
  structured_reasons: [],
  warnings: [],
};

describe("equity market valuation history route", () => {
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

  it("uses parameterized inclusive date filters and returns weekly observations in ascending order", async () => {
    queryMock.mockResolvedValue({
      rows: [historyRow, { ...historyRow, week_id: "2026-09-14", metric_value: "21.80" }],
    });

    const response = await app.inject({
      method: "GET",
      url: "/equity-markets/valuations/us?from=2026-09-07&to=2026-09-14",
    });

    expect(response.statusCode).toBe(200);
    const [sql, values] = queryMock.mock.calls[0] as [string, unknown[]];
    expect(sql).toContain("marts.country_index_publications");
    expect(sql).toContain("core.country_weekly_metrics");
    expect(sql).toContain("core.country_index_runs");
    expect(sql).toContain("ranked.market_id = $1");
    expect(sql).toContain("ranked.week_id >= $2::date");
    expect(sql).toContain("ranked.week_id <= $3::date");
    expect(sql).toContain("order by ranked.week_id asc, ranked.run_id asc, ranked.methodology_version asc, ranked.metric_key asc");
    expect(sql).not.toContain("raw.");
    expect(sql).not.toContain("staging.");
    expect(values).toEqual(["us", "2026-09-07", "2026-09-14"]);
    expect(response.json().marketId).toBe("us");
    expect(response.json().observations.map((observation: { valuation: { week: string } }) => observation.valuation.week)).toEqual([
      "2026-09-07",
      "2026-09-14",
    ]);
    expect(response.json().observations[0].metrics.pe.value).toBe("21.30");
    expect(response.json().observations[0].publication).toEqual({
      runId: "country-index-us-20260914",
      publishedAt: "2026-09-14T02:00:00.000Z",
      methodologyVersion: "mvd-country-index-v1",
    });
    expect(response.json().observations[0].metrics.pe.cohort.effectiveDate).toBe("2026-09-01");
    expect(response.json().observations[0].metrics.pe.sensitivity).toMatchObject({
      status: "experimental",
      model: "mvd-country-index-v1",
      intervalLabel: "experimental seeded sensitivity interval",
      point: "21.30",
      lower: "20.05",
      upper: "22.55",
      reason: null,
      draws: 1000,
    });
    expect(response.json().references).toEqual([
      { id: "methodology:mvd-country-index-v1", label: "MVD country index methodology mvd-country-index-v1", url: null },
    ]);
  });

  it("keeps same-week publications from different runs and methodologies as separate observations", async () => {
    queryMock.mockResolvedValue({
      rows: [
        { ...historyRow, run_id: "run-a", methodology_version: "mvd-country-index-v1", metric_value: "21.30" },
        { ...historyRow, run_id: "run-b", methodology_version: "mvd-country-index-v2", metric_value: "22.10" },
      ],
    });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations/us" });

    expect(response.statusCode).toBe(200);
    expect(response.json().observations).toHaveLength(2);
    expect(response.json().observations.map((observation: { publication: { runId: string; methodologyVersion: string } }) => observation.publication)).toEqual([
      { runId: "run-a", publishedAt: "2026-09-14T02:00:00.000Z", methodologyVersion: "mvd-country-index-v1" },
      { runId: "run-b", publishedAt: "2026-09-14T02:00:00.000Z", methodologyVersion: "mvd-country-index-v2" },
    ]);
    expect(response.json().observations.map((observation: { metrics: { pe: { value: string } } }) => observation.metrics.pe.value)).toEqual([
      "21.30",
      "22.10",
    ]);
  });

  it("passes hostile market text only as a query parameter when it matches the public id shape", async () => {
    const marketId = "us-2026-drop-table";
    queryMock.mockResolvedValue({ rows: [] }).mockResolvedValueOnce({ rows: [] }).mockResolvedValueOnce({ rows: [{ market_exists: false }] });

    const response = await app.inject({ method: "GET", url: `/equity-markets/valuations/${marketId}` });

    expect(response.statusCode).toBe(404);
    const [historySql, historyValues] = queryMock.mock.calls[0] as [string, unknown[]];
    const [existsSql, existsValues] = queryMock.mock.calls[1] as [string, unknown[]];
    expect(historySql).toContain("ranked.market_id = $1");
    expect(historySql).not.toContain(marketId);
    expect(historyValues).toEqual([marketId]);
    expect(existsSql).toContain("publication.market_id = $1");
    expect(existsSql).not.toContain(marketId);
    expect(existsValues).toEqual([marketId]);
  });

  it("keeps a known published market with an empty date window distinct from an unknown market", async () => {
    queryMock.mockResolvedValueOnce({ rows: [] }).mockResolvedValueOnce({ rows: [{ market_exists: true }] });

    const empty = await app.inject({ method: "GET", url: "/equity-markets/valuations/us?from=2020-01-01&to=2020-01-31" });

    expect(empty.statusCode).toBe(200);
    expect(empty.json()).toMatchObject({ marketId: "us", observations: [], references: [] });

    queryMock.mockResolvedValueOnce({ rows: [] }).mockResolvedValueOnce({ rows: [{ market_exists: false }] });

    const unknown = await app.inject({ method: "GET", url: "/equity-markets/valuations/xx" });

    expect(unknown.statusCode).toBe(404);
  });

  it.each([
    "/equity-markets/valuations/us?from=bad",
    "/equity-markets/valuations/us?to=2026-02-30",
    "/equity-markets/valuations/us?from=2026-09-14&to=2026-09-07",
    "/equity-markets/valuations/USA",
    "/equity-markets/valuations/us;drop-table",
  ])("rejects invalid market or date input: %s", async (url) => {
    const response = await app.inject({ method: "GET", url });

    expect(response.statusCode).toBe(400);
    expect(queryMock).not.toHaveBeenCalled();
  });
});

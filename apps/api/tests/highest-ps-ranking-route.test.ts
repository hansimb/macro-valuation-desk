import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const queryMock = vi.fn();

vi.mock("../src/lib/db", () => ({
  getDbPool: () => ({
    query: queryMock,
  }),
}));

import { buildServer } from "../src/server";

describe("highest ps ranking route", () => {
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

  it("returns the USA section with benchmark context and sector-relative ranking rows", async () => {
    queryMock
      .mockResolvedValueOnce({
        rows: [
          {
            section_key: "usa",
            as_of_date: "2026-06-15",
            universe_key: "sp500",
            universe_label: "S&P 500",
            section_label: "USA High P/S Leaders",
            benchmark_key: "sp500",
            benchmark_label: "S&P 500 Average P/S",
            average_ps_ratio: "3.80",
            top_basket_average_ps_ratio: "11.40",
            top_basket_index_weight_pct: "18.20",
            eligible_constituent_count: 182,
            unavailable: false,
          },
        ],
      })
      .mockResolvedValueOnce({
        rows: [
          {
            section_key: "usa",
            rank: 1,
            ticker: "NVDA",
            company: "NVIDIA",
            country_code: "US",
            country_name: "United States",
            sector: "Information Technology",
            ps_ratio: "24.10",
            sector_average_ps_ratio: "8.00",
            relative_to_sector_multiple: "3.01",
            index_weight_pct: "6.10",
          },
        ],
      });

    const response = await app.inject({ method: "GET", url: "/equity/highest-ps-ranking" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      asOf: "2026-06-15",
      sections: [
        {
          key: "usa",
          label: "USA High P/S Leaders",
          universeKey: "sp500",
          asOf: "2026-06-15",
          unavailable: false,
          benchmark: {
            key: "sp500",
            label: "S&P 500 Average P/S",
            averagePsRatio: "3.80",
            topBasketAveragePsRatio: "11.40",
            topBasketIndexWeightPct: "18.20",
            eligibleConstituentCount: 182,
          },
          ranking: [
            {
              rank: 1,
              ticker: "NVDA",
              company: "NVIDIA",
              countryCode: "US",
              countryName: "United States",
              sector: "Information Technology",
              psRatio: "24.10",
              sectorAveragePsRatio: "8.00",
              relativeToSectorMultiple: "3.01",
              indexWeightPct: "6.10",
            },
          ],
        },
      ],
      references: [],
    });
  });

  it("returns an unavailable section instead of fake values when no live rows exist", async () => {
    queryMock
      .mockResolvedValueOnce({
        rows: [
          {
            section_key: "usa",
            as_of_date: null,
            universe_key: "sp500",
            universe_label: "S&P 500",
            section_label: "USA High P/S Leaders",
            benchmark_key: "sp500",
            benchmark_label: "S&P 500 Average P/S",
            average_ps_ratio: null,
            top_basket_average_ps_ratio: null,
            top_basket_index_weight_pct: null,
            eligible_constituent_count: 0,
            unavailable: true,
          },
        ],
      })
      .mockResolvedValueOnce({ rows: [] });

    const response = await app.inject({ method: "GET", url: "/equity/highest-ps-ranking" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      asOf: null,
      sections: [
        {
          key: "usa",
          label: "USA High P/S Leaders",
          universeKey: "sp500",
          asOf: null,
          unavailable: true,
          benchmark: {
            key: "sp500",
            label: "S&P 500 Average P/S",
            averagePsRatio: null,
            topBasketAveragePsRatio: null,
            topBasketIndexWeightPct: null,
            eligibleConstituentCount: 0,
          },
          ranking: [],
        },
      ],
      references: [],
    });
  });
});

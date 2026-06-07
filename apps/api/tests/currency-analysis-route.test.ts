import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const queryMock = vi.fn();

vi.mock("../src/lib/db", () => ({
  getDbPool: () => ({
    query: queryMock
  })
}));

import { buildServer } from "../src/server";

describe("currency analysis route", () => {
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

  it("returns PPP and IRP blocks when mart data exists", async () => {
    queryMock
      .mockResolvedValueOnce({
        rows: [
          {
            pair_key: "eurusd",
            base_month: "2025-01-01",
            as_of_month: "2026-02-01",
            base_spot: "1.1000",
            current_spot: "1.2000",
            implied_ppp: "1.1109",
            deviation_pct: "8.02",
            trailing_12m_average_gap_pct: "6.40",
            spot_series_key: "eurusd_spot_monthly",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            us_cpi_series_key: "us_cpi_index",
            us_cpi_source_url: "https://fred.stlouisfed.org/series/CPIAUCSL",
            ea_cpi_series_key: "ea_cpi_index",
            ea_cpi_source_url: "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
          },
          {
            pair_key: "eurusd",
            base_month: "2026-02-01",
            as_of_month: "2026-02-01",
            base_spot: "1.2000",
            current_spot: "1.2000",
            implied_ppp: "1.2000",
            deviation_pct: "0.00",
            trailing_12m_average_gap_pct: "0.00",
            spot_series_key: "eurusd_spot_monthly",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            us_cpi_series_key: "us_cpi_index",
            us_cpi_source_url: "https://fred.stlouisfed.org/series/CPIAUCSL",
            ea_cpi_series_key: "ea_cpi_index",
            ea_cpi_source_url: "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
          },
        ]
      })
      .mockResolvedValueOnce({
        rows: [
          {
            pair_key: "eurusd",
            base_month: "2025-01-01",
            observation_month: "2026-01-01",
            actual_spot: "1.1000",
            implied_ppp: "1.1000",
          },
          {
            pair_key: "eurusd",
            base_month: "2026-01-01",
            observation_month: "2026-02-01",
            actual_spot: "1.2000",
            implied_ppp: "1.1109",
          },
        ]
      })
      .mockResolvedValueOnce({
        rows: [
          {
            pair_key: "eurusd",
            as_of_date: "2026-05-30",
            tenor: "3M",
            spot: "1.1400",
            eur_rate: "2.00",
            usd_rate: "4.00",
            rate_spread: "-2.00",
            cip_implied_forward: "1.1344",
            observed_forward: null,
            cip_basis_bps: null,
            uip_implied_move_pct: "-0.50",
            uip_implied_spot: "1.1343",
            spot_series_key: "eurusd_spot_daily",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
            eur_rate_series_key: "eur_3m_rate",
            eur_rate_source_url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR",
            usd_rate_series_key: "usd_3m_rate",
            usd_rate_source_url: "https://fred.stlouisfed.org/series/DTB3",
            forward_series_key: null,
            forward_source_url: null,
            has_observed_forward: false,
          },
          {
            pair_key: "eurusd",
            as_of_date: "2026-05-30",
            tenor: "6M",
            spot: "1.1400",
            eur_rate: "2.10",
            usd_rate: "4.10",
            rate_spread: "-2.00",
            cip_implied_forward: "1.1288",
            observed_forward: null,
            cip_basis_bps: null,
            uip_implied_move_pct: "-1.00",
            uip_implied_spot: "1.1286",
            spot_series_key: "eurusd_spot_daily",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
            eur_rate_series_key: "eur_6m_rate",
            eur_rate_source_url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF40.CR",
            usd_rate_series_key: "usd_6m_rate",
            usd_rate_source_url: "https://fred.stlouisfed.org/series/DTB6",
            forward_series_key: null,
            forward_source_url: null,
            has_observed_forward: false,
          },
        ]
      })
      .mockResolvedValueOnce({
        rows: [
          {
            section_key: "ppp",
            item_key: "relative_ppp",
            status: "available",
            detail: "PPP snapshots and paths available.",
            as_of_date: "2026-02-01",
          },
          {
            section_key: "irp",
            item_key: "3M",
            status: "partial",
            detail: "Observed forward unavailable; CIP-only comparison returned.",
            as_of_date: "2026-05-30",
          },
        ]
      });

    const response = await app.inject({ method: "GET", url: "/macro/currency-analysis?baseYear=2025" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      asOf: "2026-05-30",
      ppp: {
        availableBaseYears: ["2025", "2026"],
        selectedBaseYear: "2025",
        summary: {
          baseYear: "2025",
          asOf: "2026-02-01",
          baseSpot: "1.1000",
          currentSpot: "1.2000",
          impliedPpp: "1.1109",
          deviationPct: "8.02",
          trailing12mAverageGapPct: "6.40",
        },
        path: [
          { observationMonth: "2026-01-01", actualSpot: "1.1000", impliedPpp: "1.1000" },
          { observationMonth: "2026-02-01", actualSpot: "1.2000", impliedPpp: "1.1109" },
        ],
        references: [
          { label: "EUR/USD spot", url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A" },
          { label: "US CPI index", url: "https://fred.stlouisfed.org/series/CPIAUCSL" },
          { label: "Euro Area CPI index", url: "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST" },
        ],
      },
      irp: {
        cipRows: [
          {
            tenor: "3M",
            asOf: "2026-05-30",
            spot: "1.1400",
            eurRate: "2.00",
            usdRate: "4.00",
            rateSpread: "-2.00",
            cipImpliedForward: "1.1344",
            hasObservedForward: false,
          },
          {
            tenor: "6M",
            asOf: "2026-05-30",
            spot: "1.1400",
            eurRate: "2.10",
            usdRate: "4.10",
            rateSpread: "-2.00",
            cipImpliedForward: "1.1288",
            hasObservedForward: false,
          },
        ],
        uip: {
          rows: [
            { tenor: "3M", impliedMovePct: "-0.50", impliedSpot: "1.1343" },
            { tenor: "6M", impliedMovePct: "-1.00", impliedSpot: "1.1286" },
          ],
        },
        references: [
          { label: "EUR/USD spot", url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A" },
          { label: "EUR 3M rate", url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR" },
          { label: "USD 3M rate", url: "https://fred.stlouisfed.org/series/DTB3" },
          { label: "EUR 6M rate", url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF40.CR" },
          { label: "USD 6M rate", url: "https://fred.stlouisfed.org/series/DTB6" },
        ],
      },
      availability: [
        {
          sectionKey: "ppp",
          itemKey: "relative_ppp",
          status: "available",
          detail: "PPP snapshots and paths available.",
          asOfDate: "2026-02-01",
        },
        {
          sectionKey: "irp",
          itemKey: "3M",
          status: "partial",
          detail: "Observed forward unavailable; CIP-only comparison returned.",
          asOfDate: "2026-05-30",
        },
      ],
    });
  });

  it("returns an empty but stable contract when mart data is missing", async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] });

    const response = await app.inject({ method: "GET", url: "/macro/currency-analysis" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      asOf: null,
      ppp: {
        availableBaseYears: [],
        selectedBaseYear: null,
        summary: null,
        path: [],
        references: [],
      },
      irp: {
        cipRows: [],
        uip: { rows: [] },
        references: [],
      },
      availability: [],
    });
  });
});

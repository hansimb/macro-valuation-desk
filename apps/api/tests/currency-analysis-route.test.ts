import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const queryMock = vi.fn();

vi.mock("../src/lib/db", () => ({
  getDbPool: () => ({
    query: queryMock,
  }),
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

  it("returns PPP from mart snapshots and paths using window-code anchors", async () => {
    queryMock
      .mockResolvedValueOnce({
        rows: [
          {
            anchor_kind: "window",
            anchor_statistic: "average",
            anchor_window_code: "10Y",
            anchor_start_month: "2016-05-01",
            anchor_end_month: "2026-04-01",
            anchor_years_covered: 10,
            base_year: null,
            base_month: "2016-05-01",
            as_of_month: "2026-04-01",
            base_spot: "1.1000",
            current_spot: "1.2000",
            implied_ppp: "1.1109",
            deviation_pct: "8.02",
            trailing_12m_average_gap_pct: "6.40",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            us_cpi_source_url: "https://fred.stlouisfed.org/series/CPIAUCSL",
            ea_cpi_source_url: "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
          },
          {
            anchor_kind: "window",
            anchor_statistic: "average",
            anchor_window_code: "20Y",
            anchor_start_month: "2006-05-01",
            anchor_end_month: "2026-04-01",
            anchor_years_covered: 20,
            base_year: null,
            base_month: "2006-05-01",
            as_of_month: "2026-04-01",
            base_spot: "1.0800",
            current_spot: "1.2000",
            implied_ppp: "1.0900",
            deviation_pct: "10.09",
            trailing_12m_average_gap_pct: "7.10",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            us_cpi_source_url: "https://fred.stlouisfed.org/series/CPIAUCSL",
            ea_cpi_source_url: "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
          },
          {
            anchor_kind: "window",
            anchor_statistic: "average",
            anchor_window_code: "MAX",
            anchor_start_month: "1999-12-01",
            anchor_end_month: "2026-04-01",
            anchor_years_covered: 26,
            base_year: null,
            base_month: "1999-12-01",
            as_of_month: "2026-04-01",
            base_spot: "1.0500",
            current_spot: "1.2000",
            implied_ppp: "1.0700",
            deviation_pct: "12.15",
            trailing_12m_average_gap_pct: "8.30",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            us_cpi_source_url: "https://fred.stlouisfed.org/series/CPIAUCSL",
            ea_cpi_source_url: "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
          },
          {
            anchor_kind: "year",
            anchor_statistic: "average",
            anchor_window_code: null,
            anchor_start_month: "2025-01-01",
            anchor_end_month: "2025-12-01",
            anchor_years_covered: 1,
            base_year: "2025",
            base_month: "2025-01-01",
            as_of_month: "2026-04-01",
            base_spot: "1.1200",
            current_spot: "1.2000",
            implied_ppp: "1.1150",
            deviation_pct: "7.62",
            trailing_12m_average_gap_pct: "5.90",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            us_cpi_source_url: "https://fred.stlouisfed.org/series/CPIAUCSL",
            ea_cpi_source_url: "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
          },
        ],
      })
      .mockResolvedValueOnce({
        rows: [
          {
            anchor_kind: "window",
            anchor_statistic: "average",
            anchor_window_code: "20Y",
            base_year: null,
            base_month: "2006-05-01",
            observation_month: "2026-03-01",
            actual_spot: "1.1800",
            implied_ppp: "1.0850",
            has_imputed_inputs: false,
            imputation_note: null,
          },
          {
            anchor_kind: "window",
            anchor_statistic: "average",
            anchor_window_code: "20Y",
            base_year: null,
            base_month: "2006-05-01",
            observation_month: "2026-04-01",
            actual_spot: "1.2000",
            implied_ppp: "1.0900",
            has_imputed_inputs: true,
            imputation_note: "Filled using +/- 6 month median assumption.",
          },
        ],
      })
      .mockResolvedValueOnce({
        rows: [
          {
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
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
            eur_rate_source_url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR",
            usd_rate_source_url: "https://fred.stlouisfed.org/series/DTB3",
            forward_source_url: null,
            has_observed_forward: false,
          },
        ],
      })
      .mockResolvedValueOnce({
        rows: [
          {
            section_key: "ppp",
            item_key: "relative_ppp",
            status: "available",
            detail: "PPP snapshots and paths available.",
            as_of_date: "2026-04-01",
          },
        ],
      });

    const response = await app.inject({
      method: "GET",
      url: "/macro/currency-analysis?anchorKind=window&anchorStatistic=average&windowCode=20Y&baseYear=2025",
    });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      asOf: "2026-05-30",
      ppp: {
        availableWindowOptions: [
          { code: "10Y", label: "10Y", yearsCovered: 10 },
          { code: "20Y", label: "20Y", yearsCovered: 20 },
          { code: "MAX", label: "MAX", yearsCovered: 26 },
        ],
        availableBaseYears: ["2025"],
        selectedAnchorKind: "window",
        selectedAnchorStatistic: "average",
        selectedWindowCode: "20Y",
        selectedBaseYear: "2025",
        summary: {
          anchorKind: "window",
          anchorStatistic: "average",
          anchorLabel: "20-year average anchor",
          anchorWindowCode: "20Y",
          anchorStartMonth: "2006-05-01",
          anchorEndMonth: "2026-04-01",
          anchorYearsCovered: 20,
          baseYear: null,
          asOf: "2026-04-01",
          baseSpot: "1.0800",
          currentSpot: "1.2000",
          impliedPpp: "1.0900",
          deviationPct: "10.09",
          trailing12mAverageGapPct: "7.10",
        },
        path: [
          { observationMonth: "2026-03-01", actualSpot: "1.1800", impliedPpp: "1.0850", hasImputedInputs: false },
          {
            observationMonth: "2026-04-01",
            actualSpot: "1.2000",
            impliedPpp: "1.0900",
            hasImputedInputs: true,
            imputationNote: "Filled using +/- 6 month median assumption.",
          },
        ],
        spotHistory: [
          { observationMonth: "2026-03-01", actualSpot: "1.1800" },
          { observationMonth: "2026-04-01", actualSpot: "1.2000" },
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
        ],
        uip: {
          rows: [{ tenor: "3M", impliedMovePct: "-0.50", impliedSpot: "1.1343" }],
        },
        references: [
          { label: "EUR/USD spot", url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A" },
          { label: "EUR 3M rate", url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR" },
          { label: "USD 3M rate", url: "https://fred.stlouisfed.org/series/DTB3" },
        ],
      },
      availability: [
        {
          sectionKey: "ppp",
          itemKey: "relative_ppp",
          status: "available",
          detail: "PPP snapshots and paths available.",
          asOfDate: "2026-04-01",
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
        availableWindowOptions: [],
        availableBaseYears: [],
        selectedAnchorKind: null,
        selectedAnchorStatistic: "average",
        selectedWindowCode: null,
        selectedBaseYear: null,
        summary: null,
        path: [],
        spotHistory: [],
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

  it("returns IRP rows and UIP rows in matching tenor order", async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({
        rows: [
          {
            as_of_date: "2026-05-30",
            tenor: "12M",
            spot: "1.1400",
            eur_rate: "2.20",
            usd_rate: "4.20",
            rate_spread: "-2.00",
            cip_implied_forward: "1.1181",
            observed_forward: null,
            cip_basis_bps: null,
            uip_implied_move_pct: "-2.00",
            uip_implied_spot: "1.1172",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
            eur_rate_source_url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF57.CR",
            usd_rate_source_url: "https://fred.stlouisfed.org/series/DTB1YR",
            forward_source_url: null,
            has_observed_forward: false,
          },
          {
            as_of_date: "2026-05-30",
            tenor: "3M",
            spot: "1.1400",
            eur_rate: "2.00",
            usd_rate: "4.00",
            rate_spread: "-2.00",
            cip_implied_forward: "1.1344",
            observed_forward: "1.1330",
            cip_basis_bps: "-11.90",
            uip_implied_move_pct: "-0.50",
            uip_implied_spot: "1.1343",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
            eur_rate_source_url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR",
            usd_rate_source_url: "https://fred.stlouisfed.org/series/DTB3",
            forward_source_url: "https://example.com/verified-forward-source",
            has_observed_forward: true,
          },
          {
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
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
            eur_rate_source_url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF40.CR",
            usd_rate_source_url: "https://fred.stlouisfed.org/series/DTB6",
            forward_source_url: null,
            has_observed_forward: false,
          },
        ],
      })
      .mockResolvedValueOnce({ rows: [] });

    const response = await app.inject({ method: "GET", url: "/macro/currency-analysis" });

    expect(response.statusCode).toBe(200);
    expect(response.json().irp.cipRows).toEqual([
      {
        tenor: "3M",
        asOf: "2026-05-30",
        spot: "1.1400",
        eurRate: "2.00",
        usdRate: "4.00",
        rateSpread: "-2.00",
        cipImpliedForward: "1.1344",
        observedForward: "1.1330",
        cipBasisBps: "-11.90",
        hasObservedForward: true,
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
      {
        tenor: "12M",
        asOf: "2026-05-30",
        spot: "1.1400",
        eurRate: "2.20",
        usdRate: "4.20",
        rateSpread: "-2.00",
        cipImpliedForward: "1.1181",
        hasObservedForward: false,
      },
    ]);
    expect(response.json().irp.uip.rows).toEqual([
      { tenor: "3M", impliedMovePct: "-0.50", impliedSpot: "1.1343" },
      { tenor: "6M", impliedMovePct: "-1.00", impliedSpot: "1.1286" },
      { tenor: "12M", impliedMovePct: "-2.00", impliedSpot: "1.1172" },
    ]);
  });

  it("labels yearly median anchors correctly", async () => {
    queryMock
      .mockResolvedValueOnce({
        rows: [
          {
            anchor_kind: "year",
            anchor_statistic: "median",
            anchor_window_code: null,
            anchor_start_month: "2025-01-01",
            anchor_end_month: "2025-12-01",
            anchor_years_covered: 1,
            base_year: "2025",
            base_month: "2025-01-01",
            as_of_month: "2026-04-01",
            base_spot: "1.1200",
            current_spot: "1.2000",
            implied_ppp: "1.1150",
            deviation_pct: "7.62",
            trailing_12m_average_gap_pct: "5.90",
            spot_source_url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
            us_cpi_source_url: "https://fred.stlouisfed.org/series/CPIAUCSL",
            ea_cpi_source_url: "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
          },
        ],
      })
      .mockResolvedValueOnce({
        rows: [
          {
            anchor_kind: "year",
            anchor_statistic: "median",
            anchor_window_code: null,
            base_year: "2025",
            base_month: "2025-01-01",
            observation_month: "2026-04-01",
            actual_spot: "1.2000",
            implied_ppp: "1.1150",
            has_imputed_inputs: false,
            imputation_note: null,
          },
        ],
      })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] });

    const response = await app.inject({
      method: "GET",
      url: "/macro/currency-analysis?anchorKind=year&anchorStatistic=median&baseYear=2025",
    });

    expect(response.statusCode).toBe(200);
    expect(response.json().ppp.summary.anchorLabel).toBe("2025 median base-year anchor");
    expect(response.json().ppp.spotHistory).toEqual([{ observationMonth: "2026-04-01", actualSpot: "1.2000" }]);
  });
});

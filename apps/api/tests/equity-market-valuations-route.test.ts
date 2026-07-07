import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const queryMock = vi.fn();

vi.mock("../src/lib/db", () => ({
  getDbPool: () => ({
    query: queryMock,
  }),
}));

import { buildServer } from "../src/server";

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

  it("maps populated mart rows to the frontend contract with deduped references", async () => {
    queryMock.mockResolvedValue({
      rows: [
        {
          market_id: "sp500",
          region: "US",
          market_name: "S&P 500",
          measured_symbol: "SPY.US",
          measured_name: "SPDR S&P 500 ETF Trust",
          measured_type: "etf",
          provider: "eodhd",
          source_url: "https://eodhd.com/financial-summary/SPY.US",
          as_of: "2026-07-06",
          trailing_pe: "24.50",
          price_to_book: "4.80",
          price_to_sales: "3.10",
          price_to_cash_flow: "16.20",
          price_to_free_cash_flow: null,
          dividend_yield_pct: "1.28",
          price_to_cash_flow_method: "provider_price_to_cash_flow",
          price_to_free_cash_flow_method: "unavailable",
          missing_fields: ["price_to_free_cash_flow"],
        },
        {
          market_id: "nasdaq100",
          region: "US",
          market_name: "Nasdaq 100",
          measured_symbol: "QQQ.US",
          measured_name: "Invesco QQQ Trust",
          measured_type: "etf",
          provider: "eodhd",
          source_url: "https://eodhd.com/financial-summary/SPY.US",
          as_of: "2026-07-05",
          trailing_pe: "31.40",
          price_to_book: "7.20",
          price_to_sales: "5.80",
          price_to_cash_flow: "22.10",
          price_to_free_cash_flow: "25.90",
          dividend_yield_pct: "0.66",
          price_to_cash_flow_method: "provider_operating_cash_flow_proxy",
          price_to_free_cash_flow_method: "provider_free_cash_flow",
          missing_fields: [],
        },
      ],
    });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations" });

    expect(response.statusCode).toBe(200);
    expect(queryMock).toHaveBeenCalledWith(expect.stringContaining("from marts.equity_market_valuation_snapshot"));
    expect(queryMock).toHaveBeenCalledWith(expect.stringContaining("order by region asc, market_name asc"));
    expect(response.json()).toEqual({
      asOf: "2026-07-06",
      markets: [
        {
          marketId: "sp500",
          region: "US",
          marketName: "S&P 500",
          measuredSymbol: "SPY.US",
          measuredName: "SPDR S&P 500 ETF Trust",
          measuredType: "etf",
          provider: "eodhd",
          sourceUrl: "https://eodhd.com/financial-summary/SPY.US",
          asOf: "2026-07-06",
          metrics: {
            trailingPe: { value: "24.50", method: "provider_trailing_pe" },
            priceToBook: { value: "4.80", method: "provider_price_to_book" },
            priceToSales: { value: "3.10", method: "provider_price_to_sales" },
            priceToCashFlow: { value: "16.20", method: "provider_price_to_cash_flow" },
            priceToFreeCashFlow: { value: null, method: "unavailable" },
            dividendYieldPct: { value: "1.28", method: "provider_dividend_yield" },
          },
          missingFields: ["price_to_free_cash_flow"],
        },
        {
          marketId: "nasdaq100",
          region: "US",
          marketName: "Nasdaq 100",
          measuredSymbol: "QQQ.US",
          measuredName: "Invesco QQQ Trust",
          measuredType: "etf",
          provider: "eodhd",
          sourceUrl: "https://eodhd.com/financial-summary/SPY.US",
          asOf: "2026-07-05",
          metrics: {
            trailingPe: { value: "31.40", method: "provider_trailing_pe" },
            priceToBook: { value: "7.20", method: "provider_price_to_book" },
            priceToSales: { value: "5.80", method: "provider_price_to_sales" },
            priceToCashFlow: { value: "22.10", method: "provider_operating_cash_flow_proxy" },
            priceToFreeCashFlow: { value: "25.90", method: "provider_free_cash_flow" },
            dividendYieldPct: { value: "0.66", method: "provider_dividend_yield" },
          },
          missingFields: [],
        },
      ],
      references: [
        {
          label: "S&P 500 valuation source",
          url: "https://eodhd.com/financial-summary/SPY.US",
        },
      ],
    });
  });

  it("returns an empty stable contract when the valuation mart is empty", async () => {
    queryMock.mockResolvedValue({ rows: [] });

    const response = await app.inject({ method: "GET", url: "/equity-markets/valuations" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      asOf: null,
      markets: [],
      references: [],
    });
  });
});

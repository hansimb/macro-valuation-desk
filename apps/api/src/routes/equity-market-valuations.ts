import type { FastifyInstance } from "fastify";

import type { EquityMarketValuationsResponse } from "../../../../packages/shared/src/contracts/equity-market-valuation";
import { getDbPool } from "../lib/db";

interface EquityMarketValuationSnapshotRow {
  market_id: string;
  region: string;
  market_name: string;
  measured_symbol: string;
  measured_name: string;
  measured_type: string;
  provider: string;
  source_url: string;
  as_of: string;
  trailing_pe: string | null;
  price_to_book: string | null;
  price_to_sales: string | null;
  price_to_cash_flow: string | null;
  price_to_free_cash_flow: string | null;
  dividend_yield_pct: string | null;
  price_to_cash_flow_method: string;
  price_to_free_cash_flow_method: string;
  missing_fields: string[] | null;
}

function uniqueReferences(rows: EquityMarketValuationSnapshotRow[]) {
  const seenUrls = new Set<string>();

  return rows.flatMap((row) => {
    if (seenUrls.has(row.source_url)) {
      return [];
    }

    seenUrls.add(row.source_url);
    return [
      {
        label: `${row.market_name} valuation source`,
        url: row.source_url,
      },
    ];
  });
}

export async function registerEquityMarketValuationsRoute(app: FastifyInstance) {
  app.get("/equity-markets/valuations", async (): Promise<EquityMarketValuationsResponse> => {
    const result = await getDbPool().query<EquityMarketValuationSnapshotRow>(`
      select
        market_id,
        region,
        market_name,
        measured_symbol,
        measured_name,
        measured_type,
        provider,
        source_url,
        as_of::text as as_of,
        trailing_pe::text,
        price_to_book::text,
        price_to_sales::text,
        price_to_cash_flow::text,
        price_to_free_cash_flow::text,
        dividend_yield_pct::text,
        price_to_cash_flow_method,
        price_to_free_cash_flow_method,
        missing_fields
      from marts.equity_market_valuation_snapshot
      order by region asc, market_name asc
    `);

    if (result.rows.length === 0) {
      return {
        asOf: null,
        markets: [],
        references: [],
      };
    }

    const markets = result.rows.map((row) => ({
      marketId: row.market_id,
      region: row.region,
      marketName: row.market_name,
      measuredSymbol: row.measured_symbol,
      measuredName: row.measured_name,
      measuredType: row.measured_type,
      provider: row.provider,
      sourceUrl: row.source_url,
      asOf: row.as_of,
      metrics: {
        trailingPe: { value: row.trailing_pe, method: "provider_trailing_pe" },
        priceToBook: { value: row.price_to_book, method: "provider_price_to_book" },
        priceToSales: { value: row.price_to_sales, method: "provider_price_to_sales" },
        priceToCashFlow: { value: row.price_to_cash_flow, method: row.price_to_cash_flow_method },
        priceToFreeCashFlow: { value: row.price_to_free_cash_flow, method: row.price_to_free_cash_flow_method },
        dividendYieldPct: { value: row.dividend_yield_pct, method: "provider_dividend_yield" },
      },
      missingFields: row.missing_fields ?? [],
    }));

    return {
      asOf: markets[0]?.asOf ?? null,
      markets,
      references: uniqueReferences(result.rows),
    };
  });
}

export interface EquityMarketValuationMetric {
  value: string | null;
  method: string;
}

export interface EquityMarketValuationRow {
  marketId: string;
  region: string;
  marketName: string;
  measuredSymbol: string;
  measuredName: string;
  measuredType: string;
  provider: string;
  sourceUrl: string;
  asOf: string;
  metrics: {
    trailingPe: EquityMarketValuationMetric;
    priceToBook: EquityMarketValuationMetric;
    priceToSales: EquityMarketValuationMetric;
    priceToCashFlow: EquityMarketValuationMetric;
    priceToFreeCashFlow: EquityMarketValuationMetric;
    dividendYieldPct: EquityMarketValuationMetric;
  };
  missingFields: string[];
}

export interface EquityMarketValuationReference {
  label: string;
  url: string;
}

export interface EquityMarketValuationsResponse {
  asOf: string | null;
  markets: EquityMarketValuationRow[];
  references: EquityMarketValuationReference[];
}

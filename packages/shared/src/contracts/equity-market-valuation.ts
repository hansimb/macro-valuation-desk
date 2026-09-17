export interface EquityMarketValuationReference {
  id: string;
  label: string;
  url: string | null;
}

export interface EquityMarketValuationSensitivityComponent {
  code: string;
  intervalWidthContribution: string | null;
  available: boolean | null;
}

export interface EquityMarketValuationSensitivity {
  point: string | null;
  lower: string | null;
  upper: string | null;
  status: string;
  model: string | null;
  draws: number | null;
  components: EquityMarketValuationSensitivityComponent[];
}

export interface EquityMarketValuationCoverage {
  wholeCohort: {
    market: string;
    reported: string | null;
    carriedForward: string | null;
    imputed: string | null;
    missingOrInvalid: string | null;
  };
  eligibleScope: {
    market: string;
    eligible: string;
  };
  formationMarket: string;
  currentMarket: string;
}

export interface EquityMarketValuationConstituents {
  actualCount: number;
  targetCount: number;
  effectiveCount: string | null;
  largestWeight: string | null;
  topFiveConcentration: string | null;
  topTenConcentration: string | null;
  membershipOverlap: string | null;
}

export interface EquityMarketValuationWarning {
  code: string;
  level: string;
  message: string;
  affectedMarketWeight: string | null;
  intervalWidthContribution: string | null;
  reason: Record<string, unknown>;
}

export interface EquityMarketValuationMetric {
  metricKey: string;
  value: string | null;
  weeklyMin: string | null;
  weeklyMax: string | null;
  status: string;
  method: string;
  formula: string;
  sensitivity: EquityMarketValuationSensitivity;
  coverage: EquityMarketValuationCoverage;
  constituents: EquityMarketValuationConstituents;
  cohort: {
    version: string;
    effectiveDate: string;
  };
  valuation: {
    week: string;
    dates: string[];
    dailyObservationCount: number;
  };
  warnings: EquityMarketValuationWarning[];
  methodologyVersion: string;
  referenceIds: string[];
}

export interface EquityMarketValuationMarketOverview {
  marketId: string;
  marketName: string;
  latestWeek: string;
  publication: {
    runId: string;
    publishedAt: string;
  };
  metrics: Record<string, EquityMarketValuationMetric>;
}

export interface EquityMarketValuationRegionOverview {
  region: string;
  markets: EquityMarketValuationMarketOverview[];
}

export interface EquityMarketValuationsResponse {
  asOf: string | null;
  regions: EquityMarketValuationRegionOverview[];
  references: EquityMarketValuationReference[];
}

export interface EquityMarketValuationHistoryObservation {
  valuation: {
    week: string;
    dates: string[];
    dailyObservationCount: number;
  };
  publication: {
    runId: string;
    publishedAt: string;
  };
  metrics: Record<string, EquityMarketValuationMetric>;
}

export interface EquityMarketValuationHistoryResponse {
  marketId: string;
  marketName: string;
  region: string;
  observations: EquityMarketValuationHistoryObservation[];
  references: EquityMarketValuationReference[];
}

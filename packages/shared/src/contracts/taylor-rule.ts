export interface TaylorRuleAssumptions {
  neutralRate: string;
  inflationTarget: string;
  slackProxy: string;
  inflationWeight: string;
  slackWeight: string;
}

export interface TaylorRuleRegionReferences {
  policySeriesKey: string;
  policySourceUrl: string;
  inflationSeriesKey: string;
  inflationSourceUrl: string;
  slackSourceNote: string;
}

export interface TaylorRuleMetricPoint {
  value: string;
  asOf: string;
}

export interface TaylorRuleGrowthMetric {
  current: string;
  historicalAverage: string;
  gap: string;
  asOf: string;
  historyWindow: string;
}

export interface TaylorRulePolicyRealRateMetric extends TaylorRuleMetricPoint {
  note: string;
}

export interface TaylorRuleReferenceMetrics {
  headlineInflation: TaylorRuleMetricPoint;
  coreInflation: TaylorRuleMetricPoint;
  policyRealRate: TaylorRulePolicyRealRateMetric;
  marketRealRate: TaylorRuleMetricPoint;
  gdpGrowthYoy: TaylorRuleGrowthMetric;
  gdpGrowthQoqAnnualized: TaylorRuleGrowthMetric;
}

export interface TaylorRuleRegionComparison {
  region: string;
  asOf: string;
  policyRate: string;
  inflation: string;
  target: string;
  neutralRate: string;
  slackProxy: string;
  impliedRate: string;
  policyGap: string;
  references: TaylorRuleRegionReferences;
  referenceMetrics?: TaylorRuleReferenceMetrics;
}

export interface TaylorRuleReferenceItem {
  label: string;
  url?: string;
  note?: string;
}

export interface TaylorRuleResponse {
  asOf: string | null;
  formula: string;
  assumptions: TaylorRuleAssumptions;
  regions: TaylorRuleRegionComparison[];
  references: TaylorRuleReferenceItem[];
}

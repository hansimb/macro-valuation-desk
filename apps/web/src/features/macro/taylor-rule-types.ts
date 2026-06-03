export type TaylorRuleAssumptions = {
  neutralRate: string;
  inflationTarget: string;
  slackProxy: string;
  inflationWeight: string;
  slackWeight: string;
};

export type TaylorRuleRegionReferences = {
  policySeriesKey: string;
  policySourceUrl: string;
  inflationSeriesKey: string;
  inflationSourceUrl: string;
  slackSourceNote: string;
};

export type TaylorRuleMetricPoint = {
  value: string;
  asOf: string;
};

export type TaylorRuleGrowthMetric = {
  current: string;
  historicalAverage: string;
  gap: string;
  asOf: string;
  historyWindow: string;
};

export type TaylorRulePolicyRealRateMetric = TaylorRuleMetricPoint & {
  note: string;
};

export type TaylorRuleReferenceMetrics = {
  headlineInflation: TaylorRuleMetricPoint;
  coreInflation: TaylorRuleMetricPoint;
  policyRealRate: TaylorRulePolicyRealRateMetric;
  marketRealRate: TaylorRuleMetricPoint;
  gdpGrowthYoy: TaylorRuleGrowthMetric;
  gdpGrowthQoqAnnualized: TaylorRuleGrowthMetric;
};

export type TaylorRuleRegionComparison = {
  region: string;
  asOf: string;
  policyRate: string;
  inflation: string;
  target: string;
  neutralRate: string;
  slackProxy: string;
  impliedRate: string;
  policyGap: string;
  sourceNames: string[];
  references: TaylorRuleRegionReferences;
  referenceMetrics?: TaylorRuleReferenceMetrics;
};

export type TaylorRuleReferenceItem = {
  label: string;
  url?: string;
  note?: string;
};

export type TaylorRulePageData = {
  asOf: string | null;
  formula: string;
  assumptions: TaylorRuleAssumptions;
  regions: TaylorRuleRegionComparison[];
  references: TaylorRuleReferenceItem[];
};

export const emptyTaylorRulePageData: TaylorRulePageData = {
  asOf: null,
  formula: "i = r* + pi + 0.5(pi - pi*) + 0.5(slack)",
  assumptions: {
    neutralRate: "1.00",
    inflationTarget: "2.00",
    slackProxy: "0.00",
    inflationWeight: "0.50",
    slackWeight: "0.50"
  },
  regions: [],
  references: []
};

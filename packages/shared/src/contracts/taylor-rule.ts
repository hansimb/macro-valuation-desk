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

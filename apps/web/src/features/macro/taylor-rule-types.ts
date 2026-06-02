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
  references: TaylorRuleRegionReferences;
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

export const fallbackTaylorRulePageData: TaylorRulePageData = {
  asOf: "2026-05-01",
  formula: "i = r* + pi + 0.5(pi - pi*) + 0.5(slack)",
  assumptions: {
    neutralRate: "1.00",
    inflationTarget: "2.00",
    slackProxy: "0.00",
    inflationWeight: "0.50",
    slackWeight: "0.50"
  },
  regions: [
    {
      region: "EU",
      asOf: "2026-05-01",
      policyRate: "2.25",
      inflation: "2.10",
      target: "2.00",
      neutralRate: "1.00",
      slackProxy: "0.00",
      impliedRate: "3.15",
      policyGap: "-0.90",
      references: {
        policySeriesKey: "eu_policy_rate",
        policySourceUrl: "https://data.ecb.europa.eu/data/datasets/FM/FM.D.U2.EUR.4F.KR.DFR.LEV",
        inflationSeriesKey: "eu_hicp_headline",
        inflationSourceUrl: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR",
        slackSourceNote: "Assumed neutral slack proxy in v1"
      }
    },
    {
      region: "US",
      asOf: "2026-05-01",
      policyRate: "4.50",
      inflation: "2.90",
      target: "2.00",
      neutralRate: "1.00",
      slackProxy: "0.00",
      impliedRate: "4.35",
      policyGap: "0.15",
      references: {
        policySeriesKey: "us_policy_rate",
        policySourceUrl: "https://fred.stlouisfed.org/series/DFEDTARU",
        inflationSeriesKey: "us_cpi_headline",
        inflationSourceUrl: "https://fred.stlouisfed.org/series/CPIAUCSL",
        slackSourceNote: "Assumed neutral slack proxy in v1"
      }
    }
  ],
  references: [
    {
      label: "EU policy rate",
      url: "https://data.ecb.europa.eu/data/datasets/FM/FM.D.U2.EUR.4F.KR.DFR.LEV"
    },
    {
      label: "EU inflation",
      url: "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR"
    },
    {
      label: "US policy rate",
      url: "https://fred.stlouisfed.org/series/DFEDTARU"
    },
    {
      label: "US inflation",
      url: "https://fred.stlouisfed.org/series/CPIAUCSL"
    },
    {
      label: "Slack proxy",
      note: "Assumed neutral slack proxy in v1"
    }
  ]
};

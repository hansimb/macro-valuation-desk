export type MacroAnalysisEntry = {
  slug: string;
  title: string;
  summary: string;
  cue: string;
  eyebrow: string;
};

export type EquityMarketAnalysisEntry = {
  slug: string;
  flagEmoji: string;
  region: string;
  market: string;
  ticker: string;
  pe: string;
  cape: string;
  pb: string;
  posture: string;
  eyebrow: string;
  summary: string;
  methodologyNote: string;
};

export type EquityAnalysisEntry = {
  slug: string;
  title: string;
  summary: string;
  cue: string;
  eyebrow: string;
};

export const macroAnalyses: MacroAnalysisEntry[] = [
  {
    slug: "currency-analysis",
    title: "Currency Analysis",
    summary: "Open-methodology EUR/USD analysis through relative purchasing power parity.",
    cue: "Theory-first PPP workup with a selectable base month and transparent valuation path.",
    eyebrow: "Macro FX"
  },
  {
    slug: "taylor-rule",
    title: "Taylor Rule",
    summary: "Rule-based policy benchmark for the U.S. and euro area using real policy-rate and inflation inputs.",
    cue: "Rule-based policy benchmark with minimal assumption controls and scenario presets.",
    eyebrow: "Macro policy"
  }
];

export const equityAnalyses: EquityAnalysisEntry[] = [
  {
    slug: "highest-ps-ranking",
    title: "Highest P/S Stocks",
    summary: "Top-50 ranking view for the most sales-expensive stocks in the S&P 500 universe.",
    cue: "Shows only live data and stays hidden until the ranking mart and benchmark inputs are available.",
    eyebrow: "Valuation Ranking"
  }
];

export const equityMarketAnalyses: EquityMarketAnalysisEntry[] = [];

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
    slug: "return-expectation",
    title: "Stock Return Expectation",
    summary: "Frontend-only calculator for dividend, earnings-yield, and free-cash-flow return models.",
    cue: "Enter company metrics manually and compare Gordon, earnings-yield, and FCF-yield return assumptions.",
    eyebrow: "Return Calculator"
  },
  {
    slug: "highest-ps-ranking",
    title: "Highest P/S Stocks",
    summary: "Separate U.S. and Europe leaderboards for the highest price-to-sales names in major large-cap indices.",
    cue: "Theory-first comparison of top multiple baskets, benchmark averages, and index-weight concentration.",
    eyebrow: "Valuation Ranking"
  }
];

export const equityMarketAnalyses: EquityMarketAnalysisEntry[] = [];

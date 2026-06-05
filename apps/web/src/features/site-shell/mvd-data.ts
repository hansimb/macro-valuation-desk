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

export const macroAnalyses: MacroAnalysisEntry[] = [
  {
    slug: "currency-analysis",
    title: "Currency Analysis",
    summary: "Open-methodology EUR/USD analysis through relative PPP and interest rate parity.",
    cue: "Theory-first PPP and IRP workup with selectable base month and tenor-based parity table.",
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

export const equityMarketAnalyses: EquityMarketAnalysisEntry[] = [];

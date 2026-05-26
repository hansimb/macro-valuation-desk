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

export const macroAnalyses: MacroAnalysisEntry[] = [];

export const equityMarketAnalyses: EquityMarketAnalysisEntry[] = [];

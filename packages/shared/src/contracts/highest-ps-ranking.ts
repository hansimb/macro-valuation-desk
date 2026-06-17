export interface HighestPsRankingReferenceBenchmark {
  key: "sp500" | "stoxx600";
  label: string;
  regionLabel: string;
  averagePsRatio: string;
}

export interface HighestPsRankingRow {
  rank: number;
  ticker: string;
  company: string;
  countryCode: string;
  countryFlag: string;
  sector: string;
  psRatio: string;
}

export interface HighestPsRankingResponse {
  asOf: string | null;
  universeLabel: string | null;
  ranking: HighestPsRankingRow[];
  referenceBenchmarks: HighestPsRankingReferenceBenchmark[];
}

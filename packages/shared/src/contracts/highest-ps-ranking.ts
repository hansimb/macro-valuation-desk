export interface HighestPsRankingReferenceItem {
  label: string;
  url?: string;
}

export interface HighestPsRankingSectionBenchmark {
  key: "sp500" | "stoxx600";
  label: string;
  averagePsRatio: string | null;
  topBasketAveragePsRatio: string | null;
  topBasketIndexWeightPct: string | null;
  eligibleConstituentCount: number;
}

export interface HighestPsRankingSectionRow {
  rank: number;
  ticker: string;
  company: string;
  countryCode: string;
  countryName: string;
  sector: string;
  psRatio: string;
  sectorAveragePsRatio: string;
  relativeToSectorMultiple: string;
  indexWeightPct: string;
}

export interface HighestPsRankingSection {
  key: "usa" | "europe";
  label: string;
  universeKey: "sp500" | "stoxx600";
  asOf: string | null;
  unavailable: boolean;
  benchmark: HighestPsRankingSectionBenchmark;
  ranking: HighestPsRankingSectionRow[];
}

export interface HighestPsRankingResponse {
  asOf: string | null;
  sections: HighestPsRankingSection[];
  references: HighestPsRankingReferenceItem[];
}

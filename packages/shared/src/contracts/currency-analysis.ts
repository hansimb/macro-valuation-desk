export interface CurrencyAnalysisReferenceItem {
  label: string;
  url?: string;
  note?: string;
}

export type CurrencyAnalysisPppAnchorKind = "window" | "year";
export type CurrencyAnalysisPppAnchorStatistic = "average" | "median";
export type CurrencyAnalysisPppWindowCode = "3Y" | "5Y" | "10Y" | "20Y" | "MAX";

export interface CurrencyAnalysisPppWindowOption {
  code: CurrencyAnalysisPppWindowCode;
  label: string;
  yearsCovered: number;
}

export interface CurrencyAnalysisPppSummary {
  anchorKind: CurrencyAnalysisPppAnchorKind;
  anchorStatistic: CurrencyAnalysisPppAnchorStatistic;
  anchorLabel: string;
  anchorWindowCode: CurrencyAnalysisPppWindowCode | null;
  anchorStartMonth: string;
  anchorEndMonth: string;
  anchorYearsCovered: number | null;
  baseYear: string | null;
  asOf: string;
  baseSpot: string;
  currentSpot: string;
  impliedPpp: string;
  deviationPct: string;
  trailing12mAverageGapPct: string | null;
}

export interface CurrencyAnalysisPppPathPoint {
  observationMonth: string;
  actualSpot: string;
  impliedPpp: string;
  hasImputedInputs: boolean;
  imputationNote?: string;
}

export interface CurrencyAnalysisPppBlock {
  availableWindowOptions: CurrencyAnalysisPppWindowOption[];
  availableBaseYears: string[];
  selectedAnchorKind: CurrencyAnalysisPppAnchorKind | null;
  selectedAnchorStatistic: CurrencyAnalysisPppAnchorStatistic;
  selectedWindowCode: CurrencyAnalysisPppWindowCode | null;
  selectedBaseYear: string | null;
  summary: CurrencyAnalysisPppSummary | null;
  path: CurrencyAnalysisPppPathPoint[];
  references: CurrencyAnalysisReferenceItem[];
}

export interface CurrencyAnalysisIrpCipRow {
  tenor: string;
  asOf: string;
  spot: string;
  eurRate: string;
  usdRate: string;
  rateSpread: string;
  cipImpliedForward: string;
  observedForward?: string;
  cipBasisBps?: string;
  hasObservedForward: boolean;
}

export interface CurrencyAnalysisIrpUipRow {
  tenor: string;
  impliedMovePct: string;
  impliedSpot: string;
}

export interface CurrencyAnalysisIrpBlock {
  cipRows: CurrencyAnalysisIrpCipRow[];
  uip: {
    rows: CurrencyAnalysisIrpUipRow[];
  };
  references: CurrencyAnalysisReferenceItem[];
}

export interface CurrencyAnalysisAvailabilityItem {
  sectionKey: string;
  itemKey: string;
  status: string;
  detail: string;
  asOfDate: string | null;
}

export interface CurrencyAnalysisResponse {
  asOf: string | null;
  ppp: CurrencyAnalysisPppBlock;
  irp: CurrencyAnalysisIrpBlock;
  availability: CurrencyAnalysisAvailabilityItem[];
}

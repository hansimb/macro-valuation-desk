export interface CurrencyAnalysisReferenceItem {
  label: string;
  url?: string;
  note?: string;
}

export interface CurrencyAnalysisPppSummary {
  baseYear: string;
  asOf: string;
  baseSpot: string;
  currentSpot: string;
  impliedPpp: string;
  deviationPct: string;
  trailing12mAverageGapPct: string;
}

export interface CurrencyAnalysisPppPathPoint {
  observationMonth: string;
  actualSpot: string;
  impliedPpp: string;
}

export interface CurrencyAnalysisPppBlock {
  availableBaseYears: string[];
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

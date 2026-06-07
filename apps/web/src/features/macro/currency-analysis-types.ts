import type { CurrencyAnalysisResponse } from "../../../../../packages/shared/src/contracts/currency-analysis";

export type CurrencyAnalysisPageData = CurrencyAnalysisResponse;

export const emptyCurrencyAnalysisPageData: CurrencyAnalysisPageData = {
  asOf: null,
  ppp: {
    availableWindowOptions: [],
    availableBaseYears: [],
    selectedAnchorKind: null,
    selectedAnchorStatistic: "average",
    selectedWindowCode: null,
    selectedBaseYear: null,
    summary: null,
    path: [],
    references: [],
  },
  irp: {
    cipRows: [],
    uip: {
      rows: [],
    },
    references: [],
  },
  availability: [],
};

import type { HighestPsRankingResponse } from "../../../../../packages/shared/src/contracts/highest-ps-ranking";

export type HighestPsRankingPageData = HighestPsRankingResponse;

export const emptyHighestPsRankingPageData: HighestPsRankingPageData = {
  asOf: null,
  universeLabel: null,
  ranking: [],
  referenceBenchmarks: [],
};

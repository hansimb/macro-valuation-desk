import type {
  HighestPsRankingResponse,
  HighestPsRankingSection,
} from "../../../../../packages/shared/src/contracts/highest-ps-ranking";

export type HighestPsRankingPageData = HighestPsRankingResponse;

export const emptyHighestPsRankingPageData: HighestPsRankingPageData = {
  asOf: null,
  sections: [],
  references: [],
};

export function hasRenderableHighestPsSection(section: HighestPsRankingSection) {
  return (
    !section.unavailable
    && section.ranking.length > 0
    && section.benchmark.averagePsRatio !== null
    && section.benchmark.topBasketAveragePsRatio !== null
    && section.benchmark.topBasketIndexWeightPct !== null
    && section.benchmark.eligibleConstituentCount > 0
  );
}

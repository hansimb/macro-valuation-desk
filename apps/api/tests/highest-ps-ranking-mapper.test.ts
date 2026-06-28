import { describe, expect, it } from "vitest";

import {
  mapHighestPsRankingResponse,
  type HighestPsSectionRankingRow,
  type HighestPsSectionSummaryRow,
} from "../src/features/highest-ps-ranking/mapper";

describe("highest ps ranking mapper", () => {
  it("maps mart rows to the shared highest P/S ranking contract", () => {
    const summaries: HighestPsSectionSummaryRow[] = [
      {
        section_key: "usa",
        as_of_date: "2026-06-15",
        universe_key: "sp500",
        universe_label: "S&P 500",
        section_label: "USA High P/S Leaders",
        benchmark_key: "sp500",
        benchmark_label: "S&P 500 Average P/S",
        average_ps_ratio: "3.80",
        top_basket_average_ps_ratio: "11.40",
        top_basket_index_weight_pct: "18.20",
        eligible_constituent_count: 182,
        unavailable: false,
      },
    ];
    const rankings: HighestPsSectionRankingRow[] = [
      {
        section_key: "usa",
        rank: 1,
        ticker: "NVDA",
        company: "NVIDIA",
        country_code: "US",
        country_name: "United States",
        sector: "Information Technology",
        ps_ratio: "24.10",
        sector_average_ps_ratio: "8.00",
        relative_to_sector_multiple: "3.01",
        index_weight_pct: "6.10",
      },
    ];

    expect(mapHighestPsRankingResponse(summaries, rankings)).toEqual({
      asOf: "2026-06-15",
      sections: [
        {
          key: "usa",
          label: "USA High P/S Leaders",
          universeKey: "sp500",
          asOf: "2026-06-15",
          unavailable: false,
          benchmark: {
            key: "sp500",
            label: "S&P 500 Average P/S",
            averagePsRatio: "3.80",
            topBasketAveragePsRatio: "11.40",
            topBasketIndexWeightPct: "18.20",
            eligibleConstituentCount: 182,
          },
          ranking: [
            {
              rank: 1,
              ticker: "NVDA",
              company: "NVIDIA",
              countryCode: "US",
              countryName: "United States",
              sector: "Information Technology",
              psRatio: "24.10",
              sectorAveragePsRatio: "8.00",
              relativeToSectorMultiple: "3.01",
              indexWeightPct: "6.10",
            },
          ],
        },
      ],
      references: [],
    });
  });
});

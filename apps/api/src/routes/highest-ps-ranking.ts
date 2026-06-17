import type { FastifyInstance } from "fastify";

import type { HighestPsRankingResponse, HighestPsRankingSection } from "../../../../packages/shared/src/contracts/highest-ps-ranking";
import { getDbPool } from "../lib/db";

interface HighestPsSectionSummaryRow {
  section_key: "usa" | "europe";
  as_of_date: string | null;
  universe_key: "sp500" | "stoxx600";
  universe_label: string;
  section_label: string;
  benchmark_key: "sp500" | "stoxx600";
  benchmark_label: string;
  average_ps_ratio: string | null;
  top_basket_average_ps_ratio: string | null;
  top_basket_index_weight_pct: string | null;
  eligible_constituent_count: number;
  unavailable: boolean;
}

interface HighestPsSectionRankingRow {
  section_key: "usa" | "europe";
  rank: number;
  ticker: string;
  company: string;
  country_code: string;
  country_name: string;
  sector: string;
  ps_ratio: string;
  sector_average_ps_ratio: string;
  relative_to_sector_multiple: string;
  index_weight_pct: string;
}

export async function registerHighestPsRankingRoute(app: FastifyInstance) {
  app.get("/equity/highest-ps-ranking", async (): Promise<HighestPsRankingResponse> => {
    const summariesResult = await getDbPool().query<HighestPsSectionSummaryRow>(`
      select
        section_key,
        as_of_date::text,
        universe_key,
        universe_label,
        section_label,
        benchmark_key,
        benchmark_label,
        average_ps_ratio::text,
        top_basket_average_ps_ratio::text,
        top_basket_index_weight_pct::text,
        eligible_constituent_count,
        unavailable
      from mart.highest_ps_section_summaries
      order by section_key asc
    `);

    const rankingResult = await getDbPool().query<HighestPsSectionRankingRow>(`
      select
        section_key,
        rank,
        ticker,
        company,
        country_code,
        country_name,
        sector,
        ps_ratio::text,
        sector_average_ps_ratio::text,
        relative_to_sector_multiple::text,
        index_weight_pct::text
      from mart.highest_ps_section_rankings
      order by section_key asc, rank asc
    `);

    const rankingsBySection = rankingResult.rows.reduce(
      (collection, row) => {
        const key = row.section_key;
        collection[key] ??= [];
        collection[key].push({
          rank: row.rank,
          ticker: row.ticker,
          company: row.company,
          countryCode: row.country_code,
          countryName: row.country_name,
          sector: row.sector,
          psRatio: row.ps_ratio,
          sectorAveragePsRatio: row.sector_average_ps_ratio,
          relativeToSectorMultiple: row.relative_to_sector_multiple,
          indexWeightPct: row.index_weight_pct,
        });
        return collection;
      },
      {} as Record<string, HighestPsRankingSection["ranking"]>,
    );

    const sections: HighestPsRankingSection[] = summariesResult.rows.map((row) => ({
      key: row.section_key,
      label: row.section_label,
      universeKey: row.universe_key,
      asOf: row.as_of_date,
      unavailable: row.unavailable,
      benchmark: {
        key: row.benchmark_key,
        label: row.benchmark_label,
        averagePsRatio: row.average_ps_ratio,
        topBasketAveragePsRatio: row.top_basket_average_ps_ratio,
        topBasketIndexWeightPct: row.top_basket_index_weight_pct,
        eligibleConstituentCount: row.eligible_constituent_count,
      },
      ranking: rankingsBySection[row.section_key] ?? [],
    }));

    return {
      asOf: sections.find((section) => section.asOf !== null)?.asOf ?? null,
      sections,
      references: [],
    };
  });
}

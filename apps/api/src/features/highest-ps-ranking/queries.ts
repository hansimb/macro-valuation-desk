import { getDbPool } from "../../lib/db";
import type { HighestPsSectionRankingRow, HighestPsSectionSummaryRow } from "./mapper";

export async function readHighestPsRankingRows() {
  const pool = getDbPool();
  const summariesResult = await pool.query<HighestPsSectionSummaryRow>(`
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

  const rankingResult = await pool.query<HighestPsSectionRankingRow>(`
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

  return {
    summaries: summariesResult.rows,
    rankings: rankingResult.rows,
  };
}

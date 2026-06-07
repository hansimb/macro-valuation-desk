import type { FastifyInstance } from "fastify";

import type {
  CurrencyAnalysisAvailabilityItem,
  CurrencyAnalysisIrpCipRow,
  CurrencyAnalysisPppAnchorKind,
  CurrencyAnalysisPppAnchorStatistic,
  CurrencyAnalysisReferenceItem,
  CurrencyAnalysisResponse,
} from "../../../../packages/shared/src/contracts/currency-analysis";
import { getDbPool } from "../lib/db";

interface PppInputRow {
  series_id: string;
  observation_date: string;
  numeric_value: string;
  source_url: string;
}

interface IrpSnapshotRow {
  as_of_date: string;
  tenor: string;
  spot: string;
  eur_rate: string;
  usd_rate: string;
  rate_spread: string;
  cip_implied_forward: string;
  observed_forward: string | null;
  cip_basis_bps: string | null;
  uip_implied_move_pct: string;
  uip_implied_spot: string;
  spot_source_url: string;
  eur_rate_source_url: string;
  usd_rate_source_url: string;
  forward_source_url: string | null;
  has_observed_forward: boolean;
}

interface AvailabilityRow {
  section_key: string;
  item_key: string;
  status: string;
  detail: string;
  as_of_date: string | null;
}

const WINDOW_OPTIONS = [3, 5, 10, 20, 30] as const;
type WindowOption = (typeof WINDOW_OPTIONS)[number];

function uniqueReferences(references: CurrencyAnalysisReferenceItem[]) {
  return references.filter(
    (reference, index, collection) =>
      collection.findIndex((candidate) => candidate.label === reference.label && candidate.url === reference.url) === index,
  );
}

function tenorRank(tenor: string) {
  return { "3M": 1, "6M": 2, "12M": 3 }[tenor] ?? 99;
}

function parseAnchorStatistic(value: unknown): CurrencyAnalysisPppAnchorStatistic {
  return value === "median" ? "median" : "average";
}

function parseAnchorKind(value: unknown): CurrencyAnalysisPppAnchorKind | null {
  if (value === "window" || value === "year") {
    return value;
  }
  return null;
}

function parseWindowYears(value: unknown): WindowOption | null {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  return WINDOW_OPTIONS.includes(parsed as WindowOption) ? (parsed as WindowOption) : null;
}

function formatPrice(value: number) {
  return value.toFixed(4);
}

function formatPercent(value: number) {
  return value.toFixed(2);
}

function mean(values: number[]) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function median(values: number[]) {
  const sorted = [...values].sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 1) {
    return sorted[middle]!;
  }
  return (sorted[middle - 1]! + sorted[middle]!) / 2;
}

function aggregate(values: number[], statistic: CurrencyAnalysisPppAnchorStatistic) {
  return statistic === "median" ? median(values) : mean(values);
}

function yearOf(value: string) {
  return value.slice(0, 4);
}

function buildAnchorLabel(
  anchorKind: CurrencyAnalysisPppAnchorKind,
  statistic: CurrencyAnalysisPppAnchorStatistic,
  selectedWindowYears: number | null,
  selectedBaseYear: string | null,
) {
  if (anchorKind === "window" && selectedWindowYears !== null) {
    return `${selectedWindowYears}-year ${statistic} anchor`;
  }

  if (anchorKind === "year" && selectedBaseYear !== null) {
    return `${selectedBaseYear} ${statistic} base-year anchor`;
  }

  return `${statistic} PPP anchor`;
}

export async function registerCurrencyAnalysisRoute(app: FastifyInstance) {
  app.get("/macro/currency-analysis", async (request): Promise<CurrencyAnalysisResponse> => {
    const query = (request.query as Record<string, unknown> | undefined) ?? {};
    const requestedBaseYear = typeof query.baseYear === "string" ? query.baseYear : null;
    const requestedAnchorKind = parseAnchorKind(query.anchorKind);
    const requestedAnchorStatistic = parseAnchorStatistic(query.anchorStatistic);
    const requestedWindowYears = parseWindowYears(query.windowYears);

    const pppInputsResult = await getDbPool().query<PppInputRow>(
      `
        select
          staging.series_id,
          staging.observation_date::text,
          staging.numeric_value::text,
          metadata.source_url
        from staging.series_observations as staging
        join core.series_metadata as metadata
          on metadata.series_id = staging.series_id
        where staging.series_id = any($1::text[])
          and staging.is_valid = true
        order by staging.observation_date asc, staging.series_id asc
      `,
      [["eurusd_spot_monthly", "us_cpi_index", "ea_cpi_index"]],
    );

    const pppRowsBySeries = new Map<string, Map<string, PppInputRow>>();
    for (const row of pppInputsResult.rows) {
      if (!pppRowsBySeries.has(row.series_id)) {
        pppRowsBySeries.set(row.series_id, new Map());
      }
      pppRowsBySeries.get(row.series_id)!.set(row.observation_date, row);
    }

    const spotRows = pppRowsBySeries.get("eurusd_spot_monthly") ?? new Map<string, PppInputRow>();
    const usCpiRows = pppRowsBySeries.get("us_cpi_index") ?? new Map<string, PppInputRow>();
    const eaCpiRows = pppRowsBySeries.get("ea_cpi_index") ?? new Map<string, PppInputRow>();
    const commonMonths = [...spotRows.keys()].filter((month) => usCpiRows.has(month) && eaCpiRows.has(month)).sort();

    const availableBaseYears = Array.from(new Set(commonMonths.map(yearOf)));
    const availableWindowYears: WindowOption[] = WINDOW_OPTIONS.filter((years) => commonMonths.length >= years * 12);
    const defaultBaseYear = availableBaseYears[availableBaseYears.length - 1] ?? null;
    const selectedBaseYear = requestedBaseYear && availableBaseYears.includes(requestedBaseYear) ? requestedBaseYear : defaultBaseYear;

    const defaultWindowYears =
      (availableWindowYears.includes(10) ? 10 : null) ??
      availableWindowYears[availableWindowYears.length - 1] ??
      null;
    const selectedWindowYears =
      requestedWindowYears !== null && availableWindowYears.includes(requestedWindowYears)
        ? requestedWindowYears
        : defaultWindowYears;

    const selectedAnchorKind =
      requestedAnchorKind === "year" && selectedBaseYear !== null
        ? "year"
        : selectedWindowYears !== null
          ? "window"
          : selectedBaseYear !== null
            ? "year"
            : null;

    let pppSummary: CurrencyAnalysisResponse["ppp"]["summary"] = null;
    let pppPath: CurrencyAnalysisResponse["ppp"]["path"] = [];
    let pppReferences: CurrencyAnalysisReferenceItem[] = [];

    if (commonMonths.length > 0 && selectedAnchorKind !== null) {
      const latestMonth = commonMonths[commonMonths.length - 1]!;
      const anchorMonths =
        selectedAnchorKind === "window" && selectedWindowYears !== null
          ? commonMonths.slice(-selectedWindowYears * 12)
          : commonMonths.filter((month) => yearOf(month) === selectedBaseYear);

      if (anchorMonths.length > 0) {
        const anchorStartMonth = anchorMonths[0]!;
        const anchorEndMonth = anchorMonths[anchorMonths.length - 1]!;
        const baseSpot = aggregate(anchorMonths.map((month) => Number.parseFloat(spotRows.get(month)!.numeric_value)), requestedAnchorStatistic);
        const baseUsCpi = aggregate(anchorMonths.map((month) => Number.parseFloat(usCpiRows.get(month)!.numeric_value)), requestedAnchorStatistic);
        const baseEaCpi = aggregate(anchorMonths.map((month) => Number.parseFloat(eaCpiRows.get(month)!.numeric_value)), requestedAnchorStatistic);
        const pathMonths =
          selectedAnchorKind === "window"
            ? commonMonths.filter((month) => month >= anchorStartMonth)
            : commonMonths.filter((month) => month >= anchorStartMonth);

        pppPath = pathMonths.map((observationMonth) => {
          const actualSpot = Number.parseFloat(spotRows.get(observationMonth)!.numeric_value);
          const currentUsCpi = Number.parseFloat(usCpiRows.get(observationMonth)!.numeric_value);
          const currentEaCpi = Number.parseFloat(eaCpiRows.get(observationMonth)!.numeric_value);
          const impliedPpp = baseSpot * (currentUsCpi / baseUsCpi) / (currentEaCpi / baseEaCpi);

          return {
            observationMonth,
            actualSpot: formatPrice(actualSpot),
            impliedPpp: formatPrice(impliedPpp),
          };
        });

        const latestPathRow = pppPath[pppPath.length - 1]!;
        const latestSpot = Number.parseFloat(latestPathRow.actualSpot);
        const impliedLatest = Number.parseFloat(latestPathRow.impliedPpp);
        const trailing12Rows = pppPath.slice(-12);
        const trailing12AverageGap =
          trailing12Rows.length === 0
            ? 0
            : mean(
                trailing12Rows.map((row) => ((Number.parseFloat(row.actualSpot) / Number.parseFloat(row.impliedPpp)) - 1) * 100),
              );

        pppSummary = {
          anchorKind: selectedAnchorKind,
          anchorStatistic: requestedAnchorStatistic,
          anchorLabel: buildAnchorLabel(selectedAnchorKind, requestedAnchorStatistic, selectedWindowYears, selectedBaseYear),
          anchorStartMonth,
          anchorEndMonth,
          anchorYears: selectedAnchorKind === "window" ? selectedWindowYears : null,
          baseYear: selectedAnchorKind === "year" ? selectedBaseYear : null,
          asOf: latestMonth,
          baseSpot: formatPrice(baseSpot),
          currentSpot: formatPrice(latestSpot),
          impliedPpp: formatPrice(impliedLatest),
          deviationPct: formatPercent(((latestSpot / impliedLatest) - 1) * 100),
          trailing12mAverageGapPct: formatPercent(trailing12AverageGap),
        };

        pppReferences = uniqueReferences([
          { label: "EUR/USD spot", url: spotRows.get(latestMonth)?.source_url },
          { label: "US CPI index", url: usCpiRows.get(latestMonth)?.source_url },
          { label: "Euro Area CPI index", url: eaCpiRows.get(latestMonth)?.source_url },
        ]);
      }
    }

    const irpSnapshotsResult = await getDbPool().query<IrpSnapshotRow>(`
      select
        as_of_date::text,
        tenor,
        spot::text,
        eur_rate::text,
        usd_rate::text,
        rate_spread::text,
        cip_implied_forward::text,
        observed_forward::text,
        cip_basis_bps::text,
        uip_implied_move_pct::text,
        uip_implied_spot::text,
        spot_source_url,
        eur_rate_source_url,
        usd_rate_source_url,
        forward_source_url,
        has_observed_forward
      from mart.currency_irp_snapshots
      where pair_key = 'eurusd'
      order by as_of_date asc, tenor asc
    `);

    const availabilityResult = await getDbPool().query<AvailabilityRow>(`
      select
        section_key,
        item_key,
        status,
        detail,
        as_of_date::text
      from mart.currency_data_availability
      where pair_key = 'eurusd'
      order by section_key asc, item_key asc
    `);

    const cipRows: CurrencyAnalysisIrpCipRow[] = [...irpSnapshotsResult.rows]
      .sort((left, right) => tenorRank(left.tenor) - tenorRank(right.tenor))
      .map((row) => ({
        tenor: row.tenor,
        asOf: row.as_of_date,
        spot: row.spot,
        eurRate: row.eur_rate,
        usdRate: row.usd_rate,
        rateSpread: row.rate_spread,
        cipImpliedForward: row.cip_implied_forward,
        ...(row.observed_forward ? { observedForward: row.observed_forward } : {}),
        ...(row.cip_basis_bps ? { cipBasisBps: row.cip_basis_bps } : {}),
        hasObservedForward: row.has_observed_forward,
      }));

    const availability: CurrencyAnalysisAvailabilityItem[] = availabilityResult.rows.map((row) => ({
      sectionKey: row.section_key,
      itemKey: row.item_key,
      status: row.status,
      detail: row.detail,
      asOfDate: row.as_of_date,
    }));

    const irpReferences = uniqueReferences(
      irpSnapshotsResult.rows.flatMap((row) => {
        const items: CurrencyAnalysisReferenceItem[] = [
          { label: "EUR/USD spot", url: row.spot_source_url },
          { label: `EUR ${row.tenor} rate`, url: row.eur_rate_source_url },
          { label: `USD ${row.tenor} rate`, url: row.usd_rate_source_url },
        ];
        if (row.forward_source_url) {
          items.push({ label: `EUR/USD ${row.tenor} forward`, url: row.forward_source_url });
        }
        return items;
      }),
    );

    return {
      asOf: irpSnapshotsResult.rows[0]?.as_of_date ?? pppSummary?.asOf ?? null,
      ppp: {
        availableWindowYears,
        availableBaseYears,
        selectedAnchorKind,
        selectedAnchorStatistic: requestedAnchorStatistic,
        selectedWindowYears,
        selectedBaseYear,
        summary: pppSummary,
        path: pppPath,
        references: pppReferences,
      },
      irp: {
        cipRows,
        uip: {
          rows: cipRows.map((row, index) => ({
            tenor: row.tenor,
            impliedMovePct: irpSnapshotsResult.rows[index]?.uip_implied_move_pct ?? "",
            impliedSpot: irpSnapshotsResult.rows[index]?.uip_implied_spot ?? "",
          })),
        },
        references: irpReferences,
      },
      availability,
    };
  });
}

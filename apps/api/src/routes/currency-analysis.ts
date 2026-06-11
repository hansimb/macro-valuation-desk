import type { FastifyInstance } from "fastify";

import type {
  CurrencyAnalysisAvailabilityItem,
  CurrencyAnalysisIrpCipRow,
  CurrencyAnalysisPppAnchorKind,
  CurrencyAnalysisPppAnchorStatistic,
  CurrencyAnalysisPppWindowCode,
  CurrencyAnalysisReferenceItem,
  CurrencyAnalysisResponse,
} from "../../../../packages/shared/src/contracts/currency-analysis";
import { getDbPool } from "../lib/db";

interface PppSnapshotRow {
  anchor_kind: CurrencyAnalysisPppAnchorKind;
  anchor_statistic: CurrencyAnalysisPppAnchorStatistic;
  anchor_window_code: CurrencyAnalysisPppWindowCode | null;
  anchor_start_month: string;
  anchor_end_month: string;
  anchor_years_covered: number | null;
  base_year: string | null;
  base_month: string;
  as_of_month: string;
  base_spot: string;
  current_spot: string;
  implied_ppp: string;
  deviation_pct: string;
  trailing_12m_average_gap_pct: string | null;
  spot_source_url: string;
  us_cpi_source_url: string;
  ea_cpi_source_url: string;
}

interface PppPathRow {
  anchor_kind: CurrencyAnalysisPppAnchorKind;
  anchor_statistic: CurrencyAnalysisPppAnchorStatistic;
  anchor_window_code: CurrencyAnalysisPppWindowCode | null;
  base_year: string | null;
  base_month: string;
  observation_month: string;
  actual_spot: string;
  implied_ppp: string;
  has_imputed_inputs: boolean;
  imputation_note: string | null;
}

interface PppSpotHistoryRow {
  observationMonth: string;
  actualSpot: string;
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

const WINDOW_CODE_ORDER: CurrencyAnalysisPppWindowCode[] = ["3Y", "5Y", "10Y", "20Y", "MAX"];

const IRP_PROXY_REFERENCES: CurrencyAnalysisReferenceItem[] = [
  { label: "EUR/USD spot", url: "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A" },
  { label: "EUR 3M rate", url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR" },
  { label: "EUR 6M rate", url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF40.CR" },
  { label: "EUR 12M rate", url: "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF57.CR" },
  { label: "USD 3M rate", url: "https://fred.stlouisfed.org/series/DTB3" },
  { label: "USD 6M rate", url: "https://fred.stlouisfed.org/series/DTB6" },
  { label: "USD 12M rate", url: "https://fred.stlouisfed.org/series/DTB1YR" },
];

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

function parseWindowCode(value: unknown): CurrencyAnalysisPppWindowCode | null {
  if (value === "3Y" || value === "5Y" || value === "10Y" || value === "20Y" || value === "MAX") {
    return value;
  }
  return null;
}

function buildAnchorLabel(
  anchorKind: CurrencyAnalysisPppAnchorKind,
  statistic: CurrencyAnalysisPppAnchorStatistic,
  selectedWindowCode: CurrencyAnalysisPppWindowCode | null,
  anchorYearsCovered: number | null,
  selectedBaseYear: string | null,
) {
  if (anchorKind === "window" && selectedWindowCode !== null) {
    if (selectedWindowCode === "MAX") {
      return `MAX ${statistic} anchor${anchorYearsCovered ? ` (${anchorYearsCovered} years covered)` : ""}`;
    }
    return `${selectedWindowCode.replace("Y", "-year")} ${statistic} anchor`;
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
    const requestedWindowCode = parseWindowCode(query.windowCode);

    const pppSnapshotsResult = await getDbPool().query<PppSnapshotRow>(
      `
        select
          anchor_kind,
          anchor_statistic,
          anchor_window_code,
          anchor_start_month::text,
          anchor_end_month::text,
          anchor_years_covered,
          base_year,
          base_month::text,
          as_of_month::text,
          base_spot::text,
          current_spot::text,
          implied_ppp::text,
          deviation_pct::text,
          trailing_12m_average_gap_pct::text,
          spot_source_url,
          us_cpi_source_url,
          ea_cpi_source_url
        from mart.currency_ppp_snapshots
        where pair_key = 'eurusd'
        order by as_of_month asc, anchor_kind asc, anchor_statistic asc, coalesce(anchor_window_code, ''), coalesce(base_year, '')
      `,
    );

    const pppPathsResult = await getDbPool().query<PppPathRow>(
      `
        select
          anchor_kind,
          anchor_statistic,
          anchor_window_code,
          base_year,
          base_month::text,
          observation_month::text,
          actual_spot::text,
          implied_ppp::text,
          has_imputed_inputs,
          imputation_note
        from mart.currency_ppp_paths
        where pair_key = 'eurusd'
        order by observation_month asc, anchor_kind asc, anchor_statistic asc, coalesce(anchor_window_code, ''), coalesce(base_year, '')
      `,
    );

    const snapshotRows = pppSnapshotsResult.rows;
    const pathRows = pppPathsResult.rows;

    const snapshotsForStatistic = snapshotRows.filter((row) => row.anchor_statistic === requestedAnchorStatistic);
    const yearSnapshots = snapshotsForStatistic.filter((row) => row.anchor_kind === "year" && row.base_year !== null);
    const windowSnapshots = snapshotsForStatistic.filter((row) => row.anchor_kind === "window" && row.anchor_window_code !== null);

    const availableBaseYears = Array.from(new Set(yearSnapshots.map((row) => row.base_year!))).sort();
    const availableWindowOptions = WINDOW_CODE_ORDER.map((code) => {
      const snapshot = windowSnapshots.find((row) => row.anchor_window_code === code);
      if (!snapshot) {
        return null;
      }

      return {
        code,
        label: code,
        yearsCovered: snapshot.anchor_years_covered ?? 0,
      };
    }).filter((option): option is NonNullable<typeof option> => option !== null);

    const defaultBaseYear = availableBaseYears[availableBaseYears.length - 1] ?? null;
    const selectedBaseYear = requestedBaseYear && availableBaseYears.includes(requestedBaseYear) ? requestedBaseYear : defaultBaseYear;

    const defaultWindowCode =
      (availableWindowOptions.some((option) => option.code === "10Y") ? "10Y" : null) ??
      availableWindowOptions[availableWindowOptions.length - 1]?.code ??
      null;
    const selectedWindowCode =
      requestedWindowCode !== null && availableWindowOptions.some((option) => option.code === requestedWindowCode)
        ? requestedWindowCode
        : defaultWindowCode;

    const selectedAnchorKind =
      requestedAnchorKind === "year" && selectedBaseYear !== null
        ? "year"
        : selectedWindowCode !== null
          ? "window"
          : selectedBaseYear !== null
            ? "year"
            : null;

    let pppSummary: CurrencyAnalysisResponse["ppp"]["summary"] = null;
    let pppPath: CurrencyAnalysisResponse["ppp"]["path"] = [];
    const pppSpotHistory = Array.from(
      pathRows.reduce((history, row) => {
        if (!history.has(row.observation_month)) {
          history.set(row.observation_month, {
            observationMonth: row.observation_month,
            actualSpot: row.actual_spot,
          });
        }
        return history;
      }, new Map<string, PppSpotHistoryRow>()),
    ).map(([, row]) => ({
      observationMonth: row.observationMonth,
      actualSpot: row.actualSpot,
    }));
    let pppReferences: CurrencyAnalysisReferenceItem[] = [];

    let selectedSnapshot: PppSnapshotRow | undefined;
    if (selectedAnchorKind === "window" && selectedWindowCode !== null) {
      selectedSnapshot = windowSnapshots.find((row) => row.anchor_window_code === selectedWindowCode);
    } else if (selectedAnchorKind === "year" && selectedBaseYear !== null) {
      selectedSnapshot = yearSnapshots.find((row) => row.base_year === selectedBaseYear);
    }

    if (selectedSnapshot) {
      pppPath = pathRows
        .filter(
          (row) =>
            row.anchor_kind === selectedSnapshot!.anchor_kind &&
            row.anchor_statistic === selectedSnapshot!.anchor_statistic &&
            row.base_month === selectedSnapshot!.base_month &&
            row.anchor_window_code === selectedSnapshot!.anchor_window_code &&
            row.base_year === selectedSnapshot!.base_year,
        )
        .map((row) => ({
          observationMonth: row.observation_month,
          actualSpot: row.actual_spot,
          impliedPpp: row.implied_ppp,
          hasImputedInputs: row.has_imputed_inputs,
          ...(row.imputation_note ? { imputationNote: row.imputation_note } : {}),
        }));

      pppSummary = {
        anchorKind: selectedSnapshot.anchor_kind,
        anchorStatistic: selectedSnapshot.anchor_statistic,
        anchorLabel: buildAnchorLabel(
          selectedSnapshot.anchor_kind,
          selectedSnapshot.anchor_statistic,
          selectedSnapshot.anchor_window_code,
          selectedSnapshot.anchor_years_covered,
          selectedSnapshot.base_year,
        ),
        anchorWindowCode: selectedSnapshot.anchor_window_code,
        anchorStartMonth: selectedSnapshot.anchor_start_month,
        anchorEndMonth: selectedSnapshot.anchor_end_month,
        anchorYearsCovered: selectedSnapshot.anchor_years_covered,
        baseYear: selectedSnapshot.base_year,
        asOf: selectedSnapshot.as_of_month,
        baseSpot: selectedSnapshot.base_spot,
        currentSpot: selectedSnapshot.current_spot,
        impliedPpp: selectedSnapshot.implied_ppp,
        deviationPct: selectedSnapshot.deviation_pct,
        trailing12mAverageGapPct: selectedSnapshot.trailing_12m_average_gap_pct,
      };

      pppReferences = uniqueReferences([
        { label: "EUR/USD spot", url: selectedSnapshot.spot_source_url },
        { label: "US CPI index", url: selectedSnapshot.us_cpi_source_url },
        { label: "Euro Area CPI index", url: selectedSnapshot.ea_cpi_source_url },
      ]);
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

    const sortedIrpRows = [...irpSnapshotsResult.rows].sort((left, right) => tenorRank(left.tenor) - tenorRank(right.tenor));

    const cipRows: CurrencyAnalysisIrpCipRow[] = sortedIrpRows.map((row) => ({
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

    const irpReferencesFromRows = uniqueReferences(
      sortedIrpRows.flatMap((row) => {
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
    const hasIrpAvailability = availability.some((item) => item.sectionKey === "irp");
    const irpReferences =
      irpReferencesFromRows.length > 0 ? irpReferencesFromRows : hasIrpAvailability ? IRP_PROXY_REFERENCES : [];

    return {
      asOf: irpSnapshotsResult.rows[0]?.as_of_date ?? pppSummary?.asOf ?? null,
      ppp: {
        availableWindowOptions,
        availableBaseYears,
        selectedAnchorKind,
        selectedAnchorStatistic: requestedAnchorStatistic,
        selectedWindowCode,
        selectedBaseYear,
        summary: pppSummary,
        path: pppPath,
        spotHistory: pppSpotHistory,
        references: pppReferences,
      },
      irp: {
        cipRows,
        uip: {
          rows: sortedIrpRows.map((row) => ({
            tenor: row.tenor,
            impliedMovePct: row.uip_implied_move_pct,
            impliedSpot: row.uip_implied_spot,
          })),
        },
        references: irpReferences,
      },
      availability,
    };
  });
}

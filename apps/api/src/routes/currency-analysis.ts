import type { FastifyInstance } from "fastify";

import type {
  CurrencyAnalysisAvailabilityItem,
  CurrencyAnalysisIrpCipRow,
  CurrencyAnalysisReferenceItem,
  CurrencyAnalysisResponse,
} from "../../../../packages/shared/src/contracts/currency-analysis";
import { getDbPool } from "../lib/db";

interface PppSnapshotRow {
  base_month: string;
  as_of_month: string;
  base_spot: string;
  current_spot: string;
  implied_ppp: string;
  deviation_pct: string;
  spot_source_url: string;
  us_cpi_source_url: string;
  ea_cpi_source_url: string;
}

interface PppPathRow {
  observation_month: string;
  actual_spot: string;
  implied_ppp: string;
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

function uniqueReferences(references: CurrencyAnalysisReferenceItem[]) {
  return references.filter(
    (reference, index, collection) =>
      collection.findIndex((candidate) => candidate.label === reference.label && candidate.url === reference.url) === index
  );
}

function tenorRank(tenor: string) {
  return { "3M": 1, "6M": 2, "12M": 3 }[tenor] ?? 99;
}

export async function registerCurrencyAnalysisRoute(app: FastifyInstance) {
  app.get("/macro/currency-analysis", async (request): Promise<CurrencyAnalysisResponse> => {
    const requestedBaseMonth =
      typeof (request.query as Record<string, unknown> | undefined)?.baseMonth === "string"
        ? String((request.query as Record<string, unknown>).baseMonth)
        : null;

    const pppSnapshotsResult = await getDbPool().query<PppSnapshotRow>(`
      select
        base_month::text,
        as_of_month::text,
        base_spot::text,
        current_spot::text,
        implied_ppp::text,
        deviation_pct::text,
        spot_source_url,
        us_cpi_source_url,
        ea_cpi_source_url
      from mart.currency_ppp_snapshots
      where pair_key = 'eurusd'
      order by base_month asc
    `);

    const availableBaseMonths = pppSnapshotsResult.rows.map((row) => row.base_month);
    const selectedBaseMonth =
      requestedBaseMonth && availableBaseMonths.includes(requestedBaseMonth)
        ? requestedBaseMonth
        : availableBaseMonths[0] ?? null;

    const pppPathsResult =
      selectedBaseMonth === null
        ? { rows: [] as PppPathRow[] }
        : await getDbPool().query<PppPathRow>(
            `
              select
                observation_month::text,
                actual_spot::text,
                implied_ppp::text
              from mart.currency_ppp_paths
              where pair_key = 'eurusd'
                and base_month = $1::date
              order by observation_month asc
            `,
            [selectedBaseMonth]
          );

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

    const pppSummary =
      selectedBaseMonth === null
        ? null
        : pppSnapshotsResult.rows.find((row) => row.base_month === selectedBaseMonth) ?? null;

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

    const pppReferences =
      pppSummary === null
        ? []
        : uniqueReferences([
            { label: "EUR/USD spot", url: pppSummary.spot_source_url },
            { label: "US CPI index", url: pppSummary.us_cpi_source_url },
            { label: "Euro Area CPI index", url: pppSummary.ea_cpi_source_url },
          ]);

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
      })
    );

    return {
      asOf: irpSnapshotsResult.rows[0]?.as_of_date ?? pppSummary?.as_of_month ?? null,
      ppp: {
        availableBaseMonths,
        selectedBaseMonth,
        summary:
          pppSummary === null
            ? null
            : {
                baseMonth: pppSummary.base_month,
                asOf: pppSummary.as_of_month,
                baseSpot: pppSummary.base_spot,
                currentSpot: pppSummary.current_spot,
                impliedPpp: pppSummary.implied_ppp,
                deviationPct: pppSummary.deviation_pct,
              },
        path: pppPathsResult.rows.map((row) => ({
          observationMonth: row.observation_month,
          actualSpot: row.actual_spot,
          impliedPpp: row.implied_ppp,
        })),
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

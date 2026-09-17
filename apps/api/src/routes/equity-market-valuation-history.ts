import type { FastifyInstance, FastifyReply, FastifyRequest } from "fastify";

import type {
  EquityMarketValuationHistoryObservation,
  EquityMarketValuationHistoryResponse,
  EquityMarketValuationMetric,
} from "../../../../packages/shared/src/contracts/equity-market-valuation";
import { getDbPool } from "../lib/db";
import {
  emptyReferenceState,
  metricFromRow,
  PUBLISHED_COUNTRY_INDEX_METRICS_SELECT,
  type PublishedCountryIndexMetricRow,
} from "./equity-market-valuations";

interface HistoryParams {
  marketId: string;
}

interface HistoryQuery {
  from?: string;
  to?: string;
}

interface MarketExistsRow {
  market_exists: boolean;
}

const MARKET_ID_PATTERN = /^[a-z][a-z0-9-]{1,63}$/;
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

const MARKET_METADATA: Record<string, { marketName: string; region: string }> = {
  us: { marketName: "United States", region: "North America" },
};

function validDate(value: string): boolean {
  if (!DATE_PATTERN.test(value)) {
    return false;
  }

  const [yearText, monthText, dayText] = value.split("-");
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const date = new Date(Date.UTC(year, month - 1, day));

  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

function badRequest(reply: FastifyReply, message: string) {
  return reply.code(400).send({ error: "Bad Request", message });
}

function toIsoString(value: string | Date): string {
  return value instanceof Date ? value.toISOString() : value;
}

function toDateString(value: string | Date): string {
  return value instanceof Date ? value.toISOString().slice(0, 10) : value;
}

function metadataFor(row: PublishedCountryIndexMetricRow | undefined, marketId: string) {
  const fallback = MARKET_METADATA[marketId] ?? { marketName: marketId.toUpperCase(), region: "Other" };

  return {
    marketName: row?.market_name ?? fallback.marketName,
    region: row?.region ?? fallback.region,
  };
}

function historySql(hasFrom: boolean, hasTo: boolean): string {
  const predicates = ["ranked.market_id = $1"];
  if (hasFrom) {
    predicates.push(`ranked.week_id >= $${predicates.length + 1}::date`);
  }
  if (hasTo) {
    predicates.push(`ranked.week_id <= $${predicates.length + 1}::date`);
  }

  return `
    ${PUBLISHED_COUNTRY_INDEX_METRICS_SELECT}
    where ${predicates.join(" and ")}
    order by ranked.week_id asc, ranked.metric_key asc
  `;
}

async function marketExists(marketId: string): Promise<boolean> {
  const result = await getDbPool().query<MarketExistsRow>(
    `
      select exists (
        select 1
        from marts.country_index_publications as publication
        join core.country_weekly_metrics as weekly
          on weekly.run_id = publication.run_id
         and weekly.market_id = publication.market_id
         and weekly.metric_key = publication.metric_key
         and weekly.week_id = publication.week_id
        join core.country_index_runs as run
          on run.run_id = weekly.run_id
         and run.methodology_version = weekly.methodology_version
        where publication.market_id = $1
          and publication.is_current = true
          and run.run_status = 'completed'
          and run.completed_at is not null
      ) as market_exists
    `,
    [marketId],
  );

  return result.rows[0]?.market_exists === true;
}

export async function registerEquityMarketValuationHistoryRoute(app: FastifyInstance) {
  app.get(
    "/equity-markets/valuations/:marketId",
    async (
      request: FastifyRequest<{ Params: HistoryParams; Querystring: HistoryQuery }>,
      reply,
    ): Promise<EquityMarketValuationHistoryResponse | FastifyReply> => {
      const { marketId } = request.params;
      const { from, to } = request.query;

      if (!MARKET_ID_PATTERN.test(marketId)) {
        return badRequest(reply, "marketId must use lowercase letters, digits, and hyphens");
      }
      if (from !== undefined && !validDate(from)) {
        return badRequest(reply, "from must be a real YYYY-MM-DD date");
      }
      if (to !== undefined && !validDate(to)) {
        return badRequest(reply, "to must be a real YYYY-MM-DD date");
      }
      if (from !== undefined && to !== undefined && from > to) {
        return badRequest(reply, "from must be on or before to");
      }

      const values: string[] = [marketId];
      if (from !== undefined) {
        values.push(from);
      }
      if (to !== undefined) {
        values.push(to);
      }

      const result = await getDbPool().query<PublishedCountryIndexMetricRow>(historySql(from !== undefined, to !== undefined), values);

      if (result.rows.length === 0 && !(await marketExists(marketId))) {
        return reply.code(404).send({ error: "Not Found", message: "No published valuation history exists for this market" });
      }

      const referenceState = emptyReferenceState();
      const observations = new Map<string, EquityMarketValuationHistoryObservation>();

      for (const row of result.rows) {
        const week = toDateString(row.week_id);
        const observation =
          observations.get(week) ??
          {
            valuation: {
              week,
              dates: row.valuation_dates.map(toDateString),
              dailyObservationCount: row.daily_observation_count,
            },
            publication: { runId: row.run_id, publishedAt: toIsoString(row.published_at) },
            metrics: {} as Record<string, EquityMarketValuationMetric>,
          };

        if (!(row.metric_key in observation.metrics)) {
          observation.metrics[row.metric_key] = metricFromRow(row, referenceState);
        }

        observations.set(week, observation);
      }

      const metadata = metadataFor(result.rows[0], marketId);
      return {
        marketId,
        marketName: metadata.marketName,
        region: metadata.region,
        observations: Array.from(observations.values()),
        references: referenceState.references,
      };
    },
  );
}

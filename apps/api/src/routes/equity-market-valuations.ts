import type { FastifyInstance } from "fastify";

import type {
  EquityMarketValuationMetric,
  EquityMarketValuationReference,
  EquityMarketValuationsResponse,
} from "../../../../packages/shared/src/contracts/equity-market-valuation";
import { getDbPool } from "../lib/db";

export interface PublishedCountryIndexMetricRow {
  market_id: string;
  market_name?: string | null;
  region?: string | null;
  metric_key: string;
  week_id: string | Date;
  published_at: string | Date;
  run_id: string;
  methodology_version: string;
  cohort_version: string;
  metric_value: string | null;
  weekly_min_value: string | null;
  weekly_max_value: string | null;
  valuation_dates: Array<string | Date>;
  daily_observation_count: number;
  metric_status: string;
  formation_market_coverage: string;
  current_market_coverage: string;
  reported_fact_coverage: string | null;
  carried_forward_coverage: string | null;
  imputed_coverage: string | null;
  missing_or_invalid_coverage: string | null;
  metric_eligible_coverage: string;
  actual_constituent_count: number;
  cohort_target_count: number;
  effective_constituent_count: string | null;
  largest_constituent_weight: string | null;
  top_five_concentration: string | null;
  top_ten_concentration: string | null;
  membership_overlap: string | null;
  interval_lower: string | null;
  interval_upper: string | null;
  source_coverage: Record<string, unknown> | null;
  run_source_coverage?: Record<string, unknown> | null;
  structured_reasons: unknown[] | null;
  warnings: unknown[] | null;
}

interface MarketMetadata {
  marketName: string;
  region: string;
}

interface MutableReferenceState {
  references: EquityMarketValuationReference[];
  seenReferenceIds: Set<string>;
}

const MARKET_METADATA: Record<string, MarketMetadata> = {
  us: { marketName: "United States", region: "North America" },
};

const METRIC_METHODS: Record<string, { method: string; formula: string }> = {
  pe: {
    method: "aggregate_market_capitalization_divided_by_aggregate_ttm_common_net_income",
    formula: "aggregate market capitalization / aggregate TTM common net income",
  },
  pb: {
    method: "aggregate_market_capitalization_divided_by_aggregate_common_equity",
    formula: "aggregate market capitalization / aggregate common equity",
  },
  ps: {
    method: "aggregate_market_capitalization_divided_by_aggregate_ttm_revenue",
    formula: "aggregate market capitalization / aggregate TTM revenue",
  },
  pcf: {
    method: "aggregate_market_capitalization_divided_by_aggregate_ttm_operating_cash_flow",
    formula: "aggregate market capitalization / aggregate TTM operating cash flow",
  },
  pfcf: {
    method: "aggregate_market_capitalization_divided_by_aggregate_ttm_free_cash_flow",
    formula: "aggregate market capitalization / aggregate TTM free cash flow",
  },
  dividend_yield: {
    method: "aggregate_ttm_common_dividends_divided_by_aggregate_market_capitalization",
    formula: "aggregate TTM common dividends / aggregate market capitalization",
  },
};

export const PUBLISHED_COUNTRY_INDEX_METRICS_SELECT = `
  select
    ranked.market_id,
    ranked.metric_key,
    ranked.week_id::text as week_id,
    ranked.published_at,
    ranked.run_id,
    ranked.methodology_version,
    ranked.cohort_version,
    ranked.metric_value::text as metric_value,
    ranked.weekly_min_value::text as weekly_min_value,
    ranked.weekly_max_value::text as weekly_max_value,
    ranked.valuation_dates,
    ranked.daily_observation_count,
    ranked.metric_status,
    ranked.formation_market_coverage::text as formation_market_coverage,
    ranked.current_market_coverage::text as current_market_coverage,
    ranked.reported_fact_coverage::text as reported_fact_coverage,
    ranked.carried_forward_coverage::text as carried_forward_coverage,
    ranked.imputed_coverage::text as imputed_coverage,
    ranked.missing_or_invalid_coverage::text as missing_or_invalid_coverage,
    ranked.metric_eligible_coverage::text as metric_eligible_coverage,
    ranked.actual_constituent_count,
    ranked.cohort_target_count,
    ranked.effective_constituent_count::text as effective_constituent_count,
    ranked.largest_constituent_weight::text as largest_constituent_weight,
    ranked.top_five_concentration::text as top_five_concentration,
    ranked.top_ten_concentration::text as top_ten_concentration,
    ranked.membership_overlap::text as membership_overlap,
    ranked.interval_lower::text as interval_lower,
    ranked.interval_upper::text as interval_upper,
    ranked.source_coverage,
    ranked.run_source_coverage,
    ranked.structured_reasons,
    ranked.warnings
  from (
    select
      weekly.market_id,
      weekly.metric_key,
      weekly.week_id,
      publication.published_at,
      weekly.run_id,
      weekly.methodology_version,
      weekly.cohort_version,
      weekly.metric_value,
      weekly.weekly_min_value,
      weekly.weekly_max_value,
      weekly.valuation_dates,
      weekly.daily_observation_count,
      weekly.metric_status,
      cohort.achieved_market_coverage as formation_market_coverage,
      weekly.market_coverage as current_market_coverage,
      weekly.reported_fact_coverage,
      weekly.carried_forward_coverage,
      weekly.imputed_coverage,
      weekly.missing_or_invalid_coverage,
      weekly.metric_eligible_coverage,
      weekly.actual_constituent_count,
      weekly.cohort_target_count,
      weekly.effective_constituent_count,
      weekly.largest_constituent_weight,
      weekly.top_five_concentration,
      weekly.top_ten_concentration,
      weekly.membership_overlap,
      weekly.interval_lower,
      weekly.interval_upper,
      weekly.source_coverage,
      run.source_coverage as run_source_coverage,
      weekly.structured_reasons,
      coalesce(warning_bundle.warnings, '[]'::jsonb) as warnings,
      row_number() over (partition by weekly.market_id, weekly.metric_key order by weekly.week_id desc, publication.published_at desc, weekly.run_id desc) as latest_metric_rank
    from marts.country_index_publications as publication
    join core.country_weekly_metrics as weekly
      on weekly.run_id = publication.run_id
     and weekly.market_id = publication.market_id
     and weekly.metric_key = publication.metric_key
     and weekly.week_id = publication.week_id
    join core.country_index_runs as run
      on run.run_id = weekly.run_id
     and run.methodology_version = weekly.methodology_version
    join core.country_cohorts as cohort
      on cohort.market_id = weekly.market_id
     and cohort.cohort_version = weekly.cohort_version
    left join lateral (
      select jsonb_agg(jsonb_build_object(
        'warning_code', warning.warning_code,
        'warning_level', warning.warning_level,
        'warning_message', warning.warning_message,
        'affected_market_weight', warning.affected_market_weight::text,
        'interval_width_contribution', warning.interval_width_contribution::text,
        'structured_reason', warning.structured_reason
      ) order by warning.warning_code) as warnings
      from core.country_metric_warnings as warning
      where warning.run_id = weekly.run_id
        and warning.market_id = weekly.market_id
        and warning.metric_key = weekly.metric_key
        and warning.week_id = weekly.week_id
    ) as warning_bundle on true
    where publication.is_current = true
      and run.run_status = 'completed'
      and run.completed_at is not null
  ) as ranked
`;

function toIsoString(value: string | Date): string {
  return value instanceof Date ? value.toISOString() : value;
}

function toDateString(value: string | Date): string {
  return value instanceof Date ? value.toISOString().slice(0, 10) : value;
}

function metadataFor(row: PublishedCountryIndexMetricRow): MarketMetadata {
  const fallback = MARKET_METADATA[row.market_id] ?? { marketName: row.market_id.toUpperCase(), region: "Other" };
  return {
    marketName: row.market_name ?? fallback.marketName,
    region: row.region ?? fallback.region,
  };
}

function objectArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null) : [];
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function addReference(state: MutableReferenceState, reference: EquityMarketValuationReference): string {
  if (!state.seenReferenceIds.has(reference.id)) {
    state.seenReferenceIds.add(reference.id);
    state.references.push(reference);
  }

  return reference.id;
}

function referencesFromCoverage(value: unknown): EquityMarketValuationReference[] {
  if (typeof value !== "object" || value === null) {
    return [];
  }

  const coverage = value as Record<string, unknown>;
  return objectArray(coverage.references).flatMap((reference) => {
    const id = reference.id;
    const label = reference.label;
    const url = reference.url;

    if (typeof id !== "string" || !id || typeof label !== "string" || !label) {
      return [];
    }

    return [{ id, label, url: typeof url === "string" && url ? url : null }];
  });
}

function referenceIdsFor(row: PublishedCountryIndexMetricRow, state: MutableReferenceState): string[] {
  const ids = [
    addReference(state, {
      id: `methodology:${row.methodology_version}`,
      label: `MVD country index methodology ${row.methodology_version}`,
      url: null,
    }),
  ];

  for (const reference of [...referencesFromCoverage(row.run_source_coverage), ...referencesFromCoverage(row.source_coverage)]) {
    ids.push(addReference(state, reference));
  }

  return ids;
}

function sensitivityComponents(value: unknown) {
  return objectArray(value).map((component) => ({
    code: typeof component.code === "string" ? component.code : "unknown",
    intervalWidthContribution:
      typeof component.interval_width_contribution === "string"
        ? component.interval_width_contribution
        : typeof component.intervalWidthContribution === "string"
          ? component.intervalWidthContribution
          : null,
    available: typeof component.available === "boolean" ? component.available : null,
  }));
}

function sensitivityFor(row: PublishedCountryIndexMetricRow) {
  const sourceCoverage = row.source_coverage ?? {};
  const sensitivity =
    typeof sourceCoverage.sensitivity === "object" && sourceCoverage.sensitivity !== null
      ? (sourceCoverage.sensitivity as Record<string, unknown>)
      : {};

  return {
    point: typeof sensitivity.point_estimate === "string" ? sensitivity.point_estimate : row.metric_value,
    lower: row.interval_lower,
    upper: row.interval_upper,
    status: typeof sensitivity.status === "string" ? sensitivity.status : "unavailable",
    model: typeof sensitivity.model === "string" ? sensitivity.model : null,
    draws: typeof sensitivity.draws === "number" ? sensitivity.draws : null,
    components: sensitivityComponents(sensitivity.components),
  };
}

function warningsFor(row: PublishedCountryIndexMetricRow) {
  const emittedCodes = new Set<string>();
  const warnings = objectArray(row.warnings).flatMap((warning) => {
    const code = warning.warning_code;
    if (typeof code !== "string" || !code) {
      return [];
    }

    emittedCodes.add(code);
    return [
      {
        code,
        level: typeof warning.warning_level === "string" ? warning.warning_level : "warning",
        message: typeof warning.warning_message === "string" ? warning.warning_message : code,
        affectedMarketWeight: typeof warning.affected_market_weight === "string" ? warning.affected_market_weight : null,
        intervalWidthContribution:
          typeof warning.interval_width_contribution === "string" ? warning.interval_width_contribution : null,
        reason:
          typeof warning.structured_reason === "object" && warning.structured_reason !== null
            ? (warning.structured_reason as Record<string, unknown>)
            : { code },
      },
    ];
  });

  for (const code of stringArray(row.structured_reasons)) {
    if (!emittedCodes.has(code)) {
      warnings.push({
        code,
        level: "warning",
        message: code,
        affectedMarketWeight: null,
        intervalWidthContribution: null,
        reason: { code },
      });
    }
  }

  return warnings;
}

export function metricFromRow(row: PublishedCountryIndexMetricRow, state: MutableReferenceState): EquityMarketValuationMetric {
  const method = METRIC_METHODS[row.metric_key] ?? {
    method: `aggregate_country_index_${row.metric_key}`,
    formula: `aggregate country index ${row.metric_key}`,
  };

  return {
    metricKey: row.metric_key,
    value: row.metric_value,
    weeklyMin: row.weekly_min_value,
    weeklyMax: row.weekly_max_value,
    status: row.metric_status,
    method: method.method,
    formula: method.formula,
    sensitivity: sensitivityFor(row),
    coverage: {
      wholeCohort: {
        market: row.current_market_coverage,
        reported: row.reported_fact_coverage,
        carriedForward: row.carried_forward_coverage,
        imputed: row.imputed_coverage,
        missingOrInvalid: row.missing_or_invalid_coverage,
      },
      eligibleScope: { market: row.current_market_coverage, eligible: row.metric_eligible_coverage },
      formationMarket: row.formation_market_coverage,
      currentMarket: row.current_market_coverage,
    },
    constituents: {
      actualCount: row.actual_constituent_count,
      targetCount: row.cohort_target_count,
      effectiveCount: row.effective_constituent_count,
      largestWeight: row.largest_constituent_weight,
      topFiveConcentration: row.top_five_concentration,
      topTenConcentration: row.top_ten_concentration,
      membershipOverlap: row.membership_overlap,
    },
    cohort: { version: row.cohort_version, effectiveDate: row.cohort_version },
    valuation: {
      week: toDateString(row.week_id),
      dates: row.valuation_dates.map(toDateString),
      dailyObservationCount: row.daily_observation_count,
    },
    warnings: warningsFor(row),
    methodologyVersion: row.methodology_version,
    referenceIds: referenceIdsFor(row, state),
  };
}

export function emptyReferenceState(): MutableReferenceState {
  return { references: [], seenReferenceIds: new Set<string>() };
}

export async function registerEquityMarketValuationsRoute(app: FastifyInstance) {
  app.get("/equity-markets/valuations", async (): Promise<EquityMarketValuationsResponse> => {
    const result = await getDbPool().query<PublishedCountryIndexMetricRow>(`
      ${PUBLISHED_COUNTRY_INDEX_METRICS_SELECT}
      where ranked.latest_metric_rank = 1
      order by ranked.market_id asc, ranked.metric_key asc
    `);

    if (result.rows.length === 0) {
      return {
        asOf: null,
        regions: [],
        references: [],
      };
    }

    const referenceState = emptyReferenceState();
    const regionMap = new Map<
      string,
      {
        region: string;
        markets: Map<
          string,
          {
            marketId: string;
            marketName: string;
            latestWeek: string;
            publication: { runId: string; publishedAt: string };
            metrics: Record<string, EquityMarketValuationMetric>;
          }
        >;
      }
    >();

    let asOf: string | null = null;

    for (const row of result.rows) {
      const week = toDateString(row.week_id);
      if (asOf === null || week > asOf) {
        asOf = week;
      }
      const metadata = metadataFor(row);
      const region = regionMap.get(metadata.region) ?? { region: metadata.region, markets: new Map() };
      regionMap.set(metadata.region, region);
      const market =
        region.markets.get(row.market_id) ??
        {
          marketId: row.market_id,
          marketName: metadata.marketName,
          latestWeek: week,
          publication: { runId: row.run_id, publishedAt: toIsoString(row.published_at) },
          metrics: {},
        };

      if (week > market.latestWeek) {
        market.latestWeek = week;
        market.publication = { runId: row.run_id, publishedAt: toIsoString(row.published_at) };
      }

      if (!(row.metric_key in market.metrics)) {
        market.metrics[row.metric_key] = metricFromRow(row, referenceState);
      }

      region.markets.set(row.market_id, market);
    }

    return {
      asOf,
      regions: Array.from(regionMap.values()).map((region) => ({
        region: region.region,
        markets: Array.from(region.markets.values()),
      })),
      references: referenceState.references,
    };
  });
}

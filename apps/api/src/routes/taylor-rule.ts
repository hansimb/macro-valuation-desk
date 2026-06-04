import type { FastifyInstance } from "fastify";

import type { TaylorRuleResponse } from "../../../../packages/shared/src/contracts/taylor-rule";
import { getDbPool } from "../lib/db";

const FORMULA = "i = r* + pi + 0.5(pi - pi*) + 0.5(slack)";

function sourceNameFromUrl(url: string | null | undefined) {
  if (!url) {
    return null;
  }

  if (url.includes("data.ecb.europa.eu")) {
    return "ECB";
  }

  if (url.includes("fred.stlouisfed.org")) {
    return "FRED";
  }

  if (url.includes("db.nomics.world") || url.includes("ec.europa.eu")) {
    return "AMECO";
  }

  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

export async function registerTaylorRuleRoute(app: FastifyInstance) {
  app.get("/macro/taylor-rule", async (): Promise<TaylorRuleResponse> => {
    const result = await getDbPool().query(`
      select
        tr.region,
        tr.as_of_date::text,
        tr.policy_rate::text,
        tr.inflation::text,
        tr.inflation_target::text,
        tr.neutral_rate::text,
        tr.slack_proxy::text,
        tr.implied_rate::text,
        tr.policy_gap::text,
        tr.policy_series_key,
        tr.policy_source_url,
        tr.inflation_series_key,
        tr.inflation_source_url,
        tr.slack_source_note,
        mrm.headline_inflation::text,
        mrm.headline_inflation_as_of_date::text,
        mrm.core_inflation::text,
        mrm.core_inflation_as_of_date::text,
        mrm.policy_real_rate::text,
        mrm.policy_real_rate_as_of_date::text,
        mrm.market_real_rate::text,
        mrm.market_real_rate_as_of_date::text,
        mrm.output_gap::text,
        mrm.output_gap_as_of_date::text,
        mrm.gdp_growth_yoy_current::text,
        mrm.gdp_growth_yoy_historical_average::text,
        mrm.gdp_growth_yoy_gap::text,
        mrm.gdp_growth_yoy_as_of_date::text,
        mrm.gdp_growth_yoy_history_window,
        mrm.gdp_growth_qoq_annualized_current::text,
        mrm.gdp_growth_qoq_annualized_historical_average::text,
        mrm.gdp_growth_qoq_annualized_gap::text,
        mrm.gdp_growth_qoq_annualized_as_of_date::text,
        mrm.gdp_growth_qoq_annualized_history_window,
        mrm.headline_series_key,
        mrm.headline_source_url,
        mrm.core_series_key,
        mrm.core_source_url,
        mrm.market_real_rate_series_key,
        mrm.market_real_rate_source_url,
        mrm.output_gap_series_key,
        mrm.output_gap_source_url,
        mrm.gdp_series_key,
        mrm.gdp_source_url,
        mrm.policy_real_rate_note
      from mart.taylor_rule_inputs tr
      left join mart.macro_reference_metrics mrm
        on mrm.region = tr.region
      order by tr.region asc
    `);

    if (result.rows.length === 0) {
      return {
        asOf: null,
        formula: FORMULA,
        assumptions: {
          neutralRate: "1.00",
          inflationTarget: "2.00",
          slackProxy: "0.00",
          inflationWeight: "0.50",
          slackWeight: "0.50"
        },
        regions: [],
        references: []
      };
    }

    const regions = result.rows.map((row) => {
      const referenceMetrics =
        row.headline_inflation === null
          ? undefined
          : {
              headlineInflation: {
                value: row.headline_inflation,
                asOf: row.headline_inflation_as_of_date
              },
              coreInflation: {
                value: row.core_inflation,
                asOf: row.core_inflation_as_of_date
              },
              policyRealRate: {
                value: row.policy_real_rate,
                asOf: row.policy_real_rate_as_of_date,
                note: row.policy_real_rate_note
              },
              marketRealRate: {
                value: row.market_real_rate,
                asOf: row.market_real_rate_as_of_date
              },
              outputGap: {
                value: row.output_gap,
                asOf: row.output_gap_as_of_date
              },
              gdpGrowthYoy: {
                current: row.gdp_growth_yoy_current,
                historicalAverage: row.gdp_growth_yoy_historical_average,
                gap: row.gdp_growth_yoy_gap,
                asOf: row.gdp_growth_yoy_as_of_date,
                historyWindow: row.gdp_growth_yoy_history_window
              },
              gdpGrowthQoqAnnualized: {
                current: row.gdp_growth_qoq_annualized_current,
                historicalAverage: row.gdp_growth_qoq_annualized_historical_average,
                gap: row.gdp_growth_qoq_annualized_gap,
                asOf: row.gdp_growth_qoq_annualized_as_of_date,
                historyWindow: row.gdp_growth_qoq_annualized_history_window
              }
            };

      const sourceNames = [
        row.policy_source_url,
        row.inflation_source_url,
        row.headline_source_url,
        row.core_source_url,
        row.market_real_rate_source_url,
        row.output_gap_source_url,
        row.gdp_source_url
      ]
        .map(sourceNameFromUrl)
        .filter((value, index, array): value is string => value !== null && array.indexOf(value) === index);

      return {
        region: row.region,
        asOf: row.as_of_date,
        policyRate: row.policy_rate,
        inflation: row.inflation,
        target: row.inflation_target,
        neutralRate: row.neutral_rate,
        slackProxy: row.slack_proxy,
        impliedRate: row.implied_rate,
        policyGap: row.policy_gap,
        sourceNames,
        references: {
          policySeriesKey: row.policy_series_key,
          policySourceUrl: row.policy_source_url,
          inflationSeriesKey: row.inflation_series_key,
          inflationSourceUrl: row.inflation_source_url,
          slackSourceNote: row.slack_source_note
        },
        ...(referenceMetrics ? { referenceMetrics } : {})
      };
    });

    const uniqueReferences = [
      ...regions.flatMap((region) => {
        const items = [
          {
            label: `${region.region} policy rate`,
            url: region.references.policySourceUrl
          },
          {
            label: `${region.region} inflation`,
            url: region.references.inflationSourceUrl
          }
        ];

        if (region.referenceMetrics) {
          items.push(
            {
              label: `${region.region} core inflation`,
              url: result.rows.find((row) => row.region === region.region)?.core_source_url
            },
            {
              label: `${region.region} market real rate`,
              url: result.rows.find((row) => row.region === region.region)?.market_real_rate_source_url
            },
            {
              label: `${region.region} output gap`,
              url: result.rows.find((row) => row.region === region.region)?.output_gap_source_url
            },
            {
              label: `${region.region} GDP growth proxy`,
              url: result.rows.find((row) => row.region === region.region)?.gdp_source_url
            }
          );
        }

        return items;
      }),
      {
        label: "Slack proxy",
        note: regions[0]?.references.slackSourceNote ?? "Assumed neutral slack proxy in v1"
      }
    ];

    return {
      asOf: regions[0]?.asOf ?? null,
      formula: FORMULA,
      assumptions: {
        neutralRate: regions[0]?.neutralRate ?? "1.00",
        inflationTarget: regions[0]?.target ?? "2.00",
        slackProxy: regions[0]?.slackProxy ?? "0.00",
        inflationWeight: "0.50",
        slackWeight: "0.50"
      },
      regions,
      references: uniqueReferences
    };
  });
}

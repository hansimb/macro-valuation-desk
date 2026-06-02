import type { FastifyInstance } from "fastify";

import type { TaylorRuleResponse } from "../../../../packages/shared/src/contracts/taylor-rule";
import { getDbPool } from "../lib/db";

const FORMULA = "i = r* + pi + 0.5(pi - pi*) + 0.5(slack)";

export async function registerTaylorRuleRoute(app: FastifyInstance) {
  app.get("/macro/taylor-rule", async (): Promise<TaylorRuleResponse> => {
    const result = await getDbPool().query(`
      select
        region,
        as_of_date::text,
        policy_rate::text,
        inflation::text,
        inflation_target::text,
        neutral_rate::text,
        slack_proxy::text,
        implied_rate::text,
        policy_gap::text,
        policy_series_key,
        policy_source_url,
        inflation_series_key,
        inflation_source_url,
        slack_source_note
      from mart.taylor_rule_inputs
      order by region asc
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

    const regions = result.rows.map((row) => ({
      region: row.region,
      asOf: row.as_of_date,
      policyRate: row.policy_rate,
      inflation: row.inflation,
      target: row.inflation_target,
      neutralRate: row.neutral_rate,
      slackProxy: row.slack_proxy,
      impliedRate: row.implied_rate,
      policyGap: row.policy_gap,
      references: {
        policySeriesKey: row.policy_series_key,
        policySourceUrl: row.policy_source_url,
        inflationSeriesKey: row.inflation_series_key,
        inflationSourceUrl: row.inflation_source_url,
        slackSourceNote: row.slack_source_note
      }
    }));

    const uniqueReferences = [
      ...regions.flatMap((region) => [
        {
          label: `${region.region} policy rate`,
          url: region.references.policySourceUrl
        },
        {
          label: `${region.region} inflation`,
          url: region.references.inflationSourceUrl
        }
      ]),
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

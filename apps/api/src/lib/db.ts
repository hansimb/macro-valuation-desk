import { Pool } from "pg";

let pool: Pool | null = null;

export function getDbPool() {
  if (!pool) {
    pool = new Pool({
      connectionString: process.env.DATABASE_URL ?? "postgresql://mvd:mvd@localhost:5432/mvd"
    });
  }

  return pool;
}

export interface TaylorRuleInputRow {
  region: string;
  as_of_date: string;
  policy_rate: string;
  inflation: string;
  inflation_target: string;
  neutral_rate: string;
  slack_proxy: string;
  implied_rate: string;
  policy_gap: string;
  policy_series_key: string;
  policy_source_url: string;
  inflation_series_key: string;
  inflation_source_url: string;
  slack_source_note: string;
}

export async function queryTaylorRuleInputs() {
  return getDbPool().query<TaylorRuleInputRow>(`
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
}

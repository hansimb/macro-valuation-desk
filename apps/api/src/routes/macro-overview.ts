import type { FastifyInstance } from "fastify";

import type { MacroOverviewResponse } from "../../../packages/shared/src/contracts/macro-overview";
import { getDbPool } from "../lib/db";

export async function registerMacroOverviewRoute(app: FastifyInstance) {
  app.get("/macro/overview", async (): Promise<MacroOverviewResponse> => {
    const pool = getDbPool();

    try {
      const result = await pool.query<{
        series: string;
        value: string;
        as_of: string;
      }>("select series, value::text, as_of::text from raw.macro_series order by as_of desc limit 3");

      if (result.rows.length > 0) {
        return {
          asOf: result.rows[0].as_of,
          metrics: result.rows.map((row) => ({
            label: row.series,
            value: row.value
          }))
        };
      }
    } catch {
      // Fall back to a stable seed response when the database is not ready yet.
    }

    return {
      asOf: new Date("2026-05-01").toISOString(),
      metrics: [
        { label: "cpi_yoy", value: "2.9" },
        { label: "fed_funds_upper", value: "5.50" },
        { label: "valuation_context", value: "watchful" }
      ]
    };
  });
}

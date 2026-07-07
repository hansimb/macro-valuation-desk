import Fastify from "fastify";

import { registerCurrencyAnalysisRoute } from "./routes/currency-analysis";
import { registerEquityMarketValuationsRoute } from "./routes/equity-market-valuations";
import { registerHealthRoute } from "./routes/health";
import { registerMacroOverviewRoute } from "./routes/macro-overview";
import { registerTaylorRuleRoute } from "./routes/taylor-rule";

export function buildServer() {
  const app = Fastify({
    logger: false
  });

  registerHealthRoute(app);
  registerMacroOverviewRoute(app);
  registerTaylorRuleRoute(app);
  registerCurrencyAnalysisRoute(app);
  registerEquityMarketValuationsRoute(app);

  return app;
}

export async function startServer(app = buildServer()) {
  await app.listen({
    host: "0.0.0.0",
    port: Number(process.env.PORT ?? 4000)
  });

  return app;
}

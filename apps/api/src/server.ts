import Fastify from "fastify";

import { registerHealthRoute } from "./routes/health";
import { registerMacroOverviewRoute } from "./routes/macro-overview";

export function buildServer() {
  const app = Fastify({
    logger: false
  });

  registerHealthRoute(app);
  registerMacroOverviewRoute(app);

  return app;
}

async function start() {
  const app = buildServer();

  await app.listen({
    host: "0.0.0.0",
    port: Number(process.env.PORT ?? 4000)
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  start().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}

import type { FastifyInstance } from "fastify";

import type { HighestPsRankingResponse } from "../../../../packages/shared/src/contracts/highest-ps-ranking";
import { mapHighestPsRankingResponse } from "../features/highest-ps-ranking/mapper";
import { readHighestPsRankingRows } from "../features/highest-ps-ranking/queries";

export async function registerHighestPsRankingRoute(app: FastifyInstance) {
  app.get("/equity/highest-ps-ranking", async (): Promise<HighestPsRankingResponse> => {
    const rows = await readHighestPsRankingRows();
    return mapHighestPsRankingResponse(rows.summaries, rows.rankings);
  });
}

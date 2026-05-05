import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { buildServer } from "../src/server";

describe("macro overview route", () => {
  const app = buildServer();

  beforeAll(async () => {
    await app.ready();
  });

  afterAll(async () => {
    await app.close();
  });

  it("returns a stable contract", async () => {
    const response = await app.inject({ method: "GET", url: "/macro/overview" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toHaveProperty("metrics");
  });
});

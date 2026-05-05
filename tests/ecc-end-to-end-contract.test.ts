import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("end-to-end macro slice contract", () => {
  it("connects pipeline, api, and web around macro overview", () => {
    expect(readFileSync("infra/docker/postgres/init/001_schema.sql", "utf8")).toContain("macro_series");
    expect(readFileSync("apps/api/src/routes/macro-overview.ts", "utf8")).toContain("macro_series");
    expect(readFileSync("apps/web/src/app/macro/page.tsx", "utf8")).toContain("/macro/overview");
  });
});

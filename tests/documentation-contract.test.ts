import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("documentation contract", () => {
  it("describes the core stack", () => {
    const readme = readFileSync("README.md", "utf8");

    expect(readme).toContain("Docker Compose");
    expect(readme).toContain("Prefect");
    expect(readme).toContain("Fastify");
    expect(readme).toContain("PostgreSQL");
  });
});

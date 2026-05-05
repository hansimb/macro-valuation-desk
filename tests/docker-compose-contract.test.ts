import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("docker compose contract", () => {
  it("defines the core services", () => {
    const compose = readFileSync("docker-compose.yml", "utf8");

    expect(compose).toContain("web:");
    expect(compose).toContain("api:");
    expect(compose).toContain("pipelines:");
    expect(compose).toContain("postgres:");
  });
});

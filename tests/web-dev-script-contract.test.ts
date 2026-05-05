import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

describe("web dev script contract", () => {
  it("uses turbopack for local web development", () => {
    const packageJson = JSON.parse(readFileSync("apps/web/package.json", "utf8")) as {
      scripts?: Record<string, string>;
    };

    expect(packageJson.scripts?.dev).toContain("--turbopack");
  });
});

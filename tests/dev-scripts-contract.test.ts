import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

describe("development scripts contract", () => {
  it("defines the expected root development scripts", () => {
    const packageJson = JSON.parse(readFileSync("package.json", "utf8")) as {
      scripts?: Record<string, string>;
    };

    expect(packageJson.scripts).toMatchObject({
      dev: expect.any(String),
      "dev:db": expect.any(String),
      "dev:web": expect.any(String),
      "dev:api": expect.any(String),
      "dev:pipeline": expect.any(String),
      "dev:stack": expect.any(String)
    });
  });
});

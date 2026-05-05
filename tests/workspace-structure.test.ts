import { existsSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("workspace structure", () => {
  it("contains the expected service roots", () => {
    expect(existsSync("apps/web/package.json")).toBe(true);
    expect(existsSync("apps/api/package.json")).toBe(true);
    expect(existsSync("packages/shared/package.json")).toBe(true);
  });
});

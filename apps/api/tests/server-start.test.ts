import { afterEach, describe, expect, it, vi } from "vitest";

import { startServer } from "../src/server";

describe("startServer", () => {
  afterEach(() => {
    delete process.env.PORT;
  });

  it("listens on the default host and port", async () => {
    const app = {
      listen: vi.fn().mockResolvedValue(undefined)
    };

    await startServer(app as never);

    expect(app.listen).toHaveBeenCalledWith({
      host: "0.0.0.0",
      port: 4000
    });
  });

  it("uses the configured PORT when provided", async () => {
    process.env.PORT = "4321";
    const app = {
      listen: vi.fn().mockResolvedValue(undefined)
    };

    await startServer(app as never);

    expect(app.listen).toHaveBeenCalledWith({
      host: "0.0.0.0",
      port: 4321
    });
  });
});

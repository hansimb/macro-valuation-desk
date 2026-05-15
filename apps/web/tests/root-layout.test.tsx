import { describe, expect, it } from "vitest";

import RootLayout from "../src/app/layout";

describe("RootLayout", () => {
  it("suppresses hydration warnings at the html boundary for the client theme provider", () => {
    const element = RootLayout({
      children: "content"
    });

    expect(element.props.suppressHydrationWarning).toBe(true);
    expect(element.props.lang).toBe("en");
  });
});

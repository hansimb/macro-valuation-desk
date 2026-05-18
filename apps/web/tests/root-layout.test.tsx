import { describe, expect, it } from "vitest";

import RootLayout from "../src/app/layout";
import { EmotionRegistry } from "../src/features/theme/emotion-registry";
import { ThemeProvider } from "../src/features/theme/provider";

describe("RootLayout", () => {
  it("suppresses hydration warnings at the html boundary for the client theme provider", () => {
    const element = RootLayout({
      children: "content"
    });

    expect(element.props.suppressHydrationWarning).toBe(true);
    expect(element.props.lang).toBe("en");
  });

  it("wraps Chakra in an SSR-safe emotion registry", () => {
    const element = ThemeProvider({
      children: "content"
    });

    expect(element.type).toBe(EmotionRegistry);
  });
});

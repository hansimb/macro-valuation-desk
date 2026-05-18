import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

export const mvdThemeConfig = defineConfig({
  globalCss: {
    html: {
      colorPalette: "accent"
    },
    body: {
      bg: "canvas",
      color: "text",
      margin: "0",
      fontFeatureSettings: '"tnum"',
      letterSpacing: "0"
    },
    "::selection": {
      bg: "accent",
      color: "#050816"
    }
  },
  theme: {
    tokens: {
      colors: {
        accent: { value: "#8adfe5" },
        canvas: { value: "#050816" },
        edge: { value: "#1a2236" },
        muted: { value: "#8b97b3" },
        surface: { value: "#0a1224" },
        surfaceRaised: { value: "#101a31" },
        text: { value: "#eef2ff" }
      },
      fonts: {
        body: { value: "var(--font-sans), sans-serif" },
        heading: { value: "var(--font-serif), serif" }
      },
      radii: {
        panel: { value: "6px" },
        control: { value: "4px" },
        sharp: { value: "0" }
      }
    },
    semanticTokens: {
      colors: {
        "bg.panel": { value: "{colors.surface}" },
        "bg.panel.raised": { value: "{colors.surfaceRaised}" },
        "fg.default": { value: "{colors.text}" },
        "fg.muted": { value: "{colors.muted}" },
        "border.default": { value: "{colors.edge}" }
      }
    }
  }
});

export const mvdSystem = createSystem(defaultConfig, mvdThemeConfig);

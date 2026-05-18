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
    "h1, h2, h3, h4, h5, h6": {
      color: "heading"
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
        canvas: { value: "#040612" },
        edge: { value: "#7e91a8" },
        muted: { value: "#d7c7b8" },
        surface: { value: "#181A1B" },
        surfaceRaised: { value: "#181A1B" },
        text: { value: "#d9e8ff" },
        heading: { value: "#b9d8ff" }
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
    }
  }
});

export const mvdSystem = createSystem(defaultConfig, mvdThemeConfig);

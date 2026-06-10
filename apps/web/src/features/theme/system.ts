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
      fontSize: "var(--chakra-font-sizes-body)",
      fontFeatureSettings: '"tnum"',
      lineHeight: "1.6",
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
      fontSizes: {
        eyebrow: { value: "0.72rem" },
        caption: { value: "0.78rem" },
        body: { value: "0.95rem" },
        subtitle: { value: "1.05rem" },
        subheading: { value: "1.35rem" },
        title: { value: "1.85rem" },
        hero: { value: "3rem" },
        metric: { value: "1.65rem" },
        formula: { value: "1.35rem" }
      },
      radii: {
        panel: { value: "6px" },
        control: { value: "4px" },
        sharp: { value: "0" }
      }
    },
    textStyles: {
      hero: {
        value: {
          fontFamily: "heading",
          fontSize: { base: "2.75rem", md: "3rem" },
          fontWeight: "700",
          letterSpacing: "0",
          lineHeight: "0.98"
        }
      },
      title: {
        value: {
          fontFamily: "heading",
          fontSize: { base: "1.75rem", md: "1.85rem" },
          fontWeight: "700",
          letterSpacing: "0",
          lineHeight: "1.08"
        }
      },
      subheading: {
        value: {
          fontFamily: "heading",
          fontSize: { base: "1.25rem", md: "1.35rem" },
          fontWeight: "700",
          letterSpacing: "0",
          lineHeight: "1.15"
        }
      },
      subtitle: {
        value: {
          fontSize: { base: "1rem", md: "1.05rem" },
          letterSpacing: "0",
          lineHeight: "1.55"
        }
      },
      body: {
        value: {
          fontSize: "0.95rem",
          letterSpacing: "0",
          lineHeight: "1.55"
        }
      },
      eyebrow: {
        value: {
          fontSize: "0.72rem",
          fontWeight: "600",
          letterSpacing: "0.12em",
          lineHeight: "1.25",
          textTransform: "uppercase"
        }
      },
      caption: {
        value: {
          fontSize: "0.78rem",
          letterSpacing: "0",
          lineHeight: "1.4"
        }
      },
      metric: {
        value: {
          fontSize: { base: "1.45rem", md: "1.65rem" },
          fontWeight: "600",
          letterSpacing: "0",
          lineHeight: "1"
        }
      },
      formula: {
        value: {
          fontFamily: "heading",
          fontSize: { base: "1.25rem", md: "1.35rem" },
          letterSpacing: "0",
          lineHeight: "1.4"
        }
      }
    }
  }
});

export const mvdSystem = createSystem(defaultConfig, mvdThemeConfig);

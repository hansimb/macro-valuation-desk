import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

export const mvdThemeConfig = defineConfig({
  globalCss: {
    html: {
      colorPalette: "blue"
    },
    body: {
      bg: "bg.subtle",
      color: "fg",
      margin: "0",
      fontFeatureSettings: '"tnum"'
    }
  },
  theme: {
    tokens: {
      fonts: {
        body: { value: "Georgia, Cambria, 'Times New Roman', serif" },
        heading: { value: "'Avenir Next', 'Segoe UI', sans-serif" }
      },
      radii: {
        panel: { value: "24px" }
      },
      colors: {
        brand: {
          50: { value: "#eff6ff" },
          100: { value: "#dbeafe" },
          500: { value: "#2563eb" },
          700: { value: "#1d4ed8" },
          950: { value: "#172554" }
        }
      }
    }
  }
});

export const mvdSystem = createSystem(defaultConfig, mvdThemeConfig);

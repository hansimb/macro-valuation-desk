import React, { type PropsWithChildren } from "react";
import { Manrope, Newsreader } from "next/font/google";

import { LayoutShell } from "../features/site-shell/layout-shell";
import { ThemeProvider } from "../features/theme/provider";

const sans = Manrope({
  variable: "--font-sans",
  subsets: ["latin"]
});

const serif = Newsreader({
  variable: "--font-serif",
  subsets: ["latin"],
  style: ["normal", "italic"]
});

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html
      lang="en"
      className={`${sans.variable} ${serif.variable}`}
      suppressHydrationWarning
    >
      <body>
        <ThemeProvider>
          <LayoutShell>{children}</LayoutShell>
        </ThemeProvider>
      </body>
    </html>
  );
}

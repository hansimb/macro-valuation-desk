import type { PropsWithChildren } from "react";

import { ThemeProvider } from "../features/theme/provider";

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import MacroPage from "../src/app/macro/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("Macro page", () => {
  it("renders the Taylor Rule analysis entry from the macro registry", async () => {
    const page = await MacroPage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: "Macro" })).toBeInTheDocument();
    expect(screen.getByText("Analysis")).toBeInTheDocument();
    expect(screen.queryByText("No analysis yet")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Taylor Rule/i })).toBeInTheDocument();
    expect(
      screen.getByText("Rule-based policy benchmark with minimal assumption controls and scenario presets.")
    ).toBeInTheDocument();
  });
});

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import MacroPage from "../src/app/macro/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("Macro page", () => {
  it("renders the macro driver workspace structure", async () => {
    const page = await MacroPage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: "Macro" })).toBeInTheDocument();
    expect(screen.getByText("Headline layer")).toBeInTheDocument();
    expect(screen.getByText("Driver analysis")).toBeInTheDocument();
    expect(screen.getByText("Liquidity and Money Impulse")).toBeInTheDocument();
    expect(screen.getByText("Housing and Construction Transmission")).toBeInTheDocument();
    expect(screen.queryByText("Drilldown-oriented layer")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Liquidity and Money Impulse/i })).toBeInTheDocument();
  });
});

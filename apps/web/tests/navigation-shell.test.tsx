import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "../src/app/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("MVD home shell", () => {
  it("renders the primary sections", () => {
    render(
      <ThemeProvider>
        <HomePage />
      </ThemeProvider>
    );

    expect(screen.getByText("Macro")).toBeInTheDocument();
    expect(screen.getByText("Equity Markets")).toBeInTheDocument();
    expect(screen.getByText("Signal density over dashboard sprawl")).toBeInTheDocument();
  });
});

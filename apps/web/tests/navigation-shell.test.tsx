import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "../src/app/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("MVD home shell", () => {
  it("renders featured analysis instead of overview placeholders", () => {
    render(
      <ThemeProvider>
        <HomePage />
      </ThemeProvider>
    );

    expect(screen.getByText("Macro")).toBeInTheDocument();
    expect(screen.getByText("Equity Markets")).toBeInTheDocument();
    expect(screen.getByText("Featured analysis")).toBeInTheDocument();
    expect(screen.getByText("No featured analysis yet.")).toBeInTheDocument();
    expect(screen.getByText("A growing set of reasoning-led macro analyses that update through dedicated data pipelines.")).toBeInTheDocument();
    expect(screen.queryByText("GDP growth")).not.toBeInTheDocument();
  });
});

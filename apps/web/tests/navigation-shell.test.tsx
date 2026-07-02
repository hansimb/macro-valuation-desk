import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import HomePage from "../src/app/page";
import { SiteNavigation } from "../src/features/site-shell/navigation";
import { ThemeProvider } from "../src/features/theme/provider";

vi.mock("next/navigation", async (importOriginal) => {
  const actual = await importOriginal<typeof import("next/navigation")>();

  return {
    ...actual,
    usePathname: () => "/equity-markets",
  };
});

describe("MVD home shell", () => {
  it("renders featured analysis instead of overview placeholders", () => {
    render(
      <ThemeProvider>
        <HomePage />
      </ThemeProvider>
    );

    expect(screen.getByText("Macro")).toBeInTheDocument();
    expect(screen.getByText("Equity Markets")).toBeInTheDocument();
    expect(screen.getAllByText("Featured analysis").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /Featured analysis Stock Return Expectation/i })).toHaveAttribute("href", "/equity-markets/return-expectation");
    expect(screen.queryByText("No featured analysis yet.")).not.toBeInTheDocument();
    expect(screen.getByText("A growing set of reasoning-led macro analyses that update through dedicated data pipelines.")).toBeInTheDocument();
    expect(screen.getAllByText("Analysis archive.").length).toBeGreaterThan(1);
    expect(screen.getByText("Equity analysis tools, calculators, and valuation workups collected in one research archive.")).toBeInTheDocument();
    expect(screen.queryByText("GDP growth")).not.toBeInTheDocument();
  });

  it("renders Equity as the navigation label for the equity route", () => {
    render(
      <ThemeProvider>
        <SiteNavigation />
      </ThemeProvider>
    );

    expect(screen.getByRole("link", { name: "Equity" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Index Valuations" })).not.toBeInTheDocument();
  });
});

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
    expect(screen.getByText("Featured analysis")).toBeInTheDocument();
    expect(screen.getByText("No featured analysis yet.")).toBeInTheDocument();
    expect(screen.getByText("A growing set of reasoning-led macro analyses that update through dedicated data pipelines.")).toBeInTheDocument();
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

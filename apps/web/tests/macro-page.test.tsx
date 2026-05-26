import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import MacroPage from "../src/app/macro/page";
import { ThemeProvider } from "../src/features/theme/provider";

describe("Macro page", () => {
  it("renders an empty-state card when the macro analysis registry is empty", async () => {
    const page = await MacroPage();

    render(<ThemeProvider>{page}</ThemeProvider>);

    expect(screen.getByRole("heading", { name: "Macro" })).toBeInTheDocument();
    expect(screen.getByText("Analysis")).toBeInTheDocument();
    expect(screen.getByText("No analysis yet")).toBeInTheDocument();
    expect(screen.queryByText("Overview")).not.toBeInTheDocument();
    expect(screen.queryByText("Driver analysis")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Taylor Rule/i })).not.toBeInTheDocument();
  });
});

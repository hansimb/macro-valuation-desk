import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";

import EquityMarketsPage from "../src/app/equity-markets/page";
import EquityReturnExpectationPage from "../src/app/equity-markets/return-expectation/page";
import { ThemeProvider } from "../src/features/theme/provider";

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  vi.restoreAllMocks();
});

function renderPage() {
  render(
    <ThemeProvider>
      <EquityReturnExpectationPage />
    </ThemeProvider>,
  );
}

describe("Equity return expectation page", () => {
  it("is discoverable from the equity analysis registry", () => {
    render(
      <ThemeProvider>
        <EquityMarketsPage />
      </ThemeProvider>,
    );

    expect(screen.getByRole("link", { name: /Stock Return Expectation/i })).toBeInTheDocument();
    expect(screen.getByText(/Frontend-only calculator for dividend, earnings-yield, and free-cash-flow return models/i)).toBeInTheDocument();
  });

  it("calculates the earnings yield plus growth model from P/E and direct growth assumptions", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Earnings Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Direct growth estimate" }));
    fireEvent.click(screen.getByRole("button", { name: "P/E input" }));
    fireEvent.change(screen.getByLabelText("P/E ratio"), { target: { value: "20" } });
    fireEvent.change(screen.getByLabelText("Expected annual growth"), { target: { value: "6" } });

    expect(screen.getByText("11.00%")).toBeInTheDocument();
    expect(screen.getByText("5.00%")).toBeInTheDocument();
    expect(screen.getByText("6.00%")).toBeInTheDocument();

    await waitFor(() => {
      expect(window.localStorage.getItem("equity-return-expectation-v1")).toContain("\"peRatio\":\"20\"");
    });
  });

  it("can estimate growth from four or five years of history and reuse it in the FCF model", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Historical growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Revenue growth" }));
    fireEvent.click(screen.getByRole("button", { name: "5 years" }));
    fireEvent.click(screen.getByRole("button", { name: "FCF amount input" }));

    ["100", "110", "121", "133.1", "146.41"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(`Year ${index + 1} value`), { target: { value } });
    });
    fireEvent.change(screen.getByLabelText("Market capitalization"), { target: { value: "1000" } });
    fireEvent.change(screen.getByLabelText("Free cash flow"), { target: { value: "80" } });

    expect(screen.getByText("18.00%")).toBeInTheDocument();
    expect(screen.getByText("8.00%")).toBeInTheDocument();
    expect(screen.getByText("10.00%")).toBeInTheDocument();
    expect(screen.getByText("12.5x")).toBeInTheDocument();
  });

  it("hydrates saved choices from local storage", () => {
    window.localStorage.setItem(
      "equity-return-expectation-v1",
      JSON.stringify({
        model: "gordon",
        growth: {
          basis: "eps",
          mode: "direct",
          directPct: "4",
          years: "4",
          historicalValues: ["", "", "", "", ""],
        },
        gordon: {
          dividendYieldPct: "3",
          dividendGrowthPct: "5",
        },
        earnings: {
          yieldMode: "pe",
          peRatio: "20",
          marketCap: "",
          netIncome: "",
        },
        fcf: {
          yieldMode: "direct",
          directYieldPct: "7",
          marketCap: "",
          freeCashFlow: "",
        },
      }),
    );

    renderPage();

    expect(screen.getByRole("button", { name: "Gordon Growth" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByDisplayValue("3")).toBeInTheDocument();
    expect(screen.getByDisplayValue("5")).toBeInTheDocument();
    expect(screen.getByText("8.00%")).toBeInTheDocument();
  });

  it("can calculate Gordon dividend growth from four or five years of dividend history", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Gordon Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Historical dividend growth" }));
    fireEvent.click(screen.getByRole("button", { name: "5 years" }));
    fireEvent.change(screen.getByLabelText("Dividend yield"), { target: { value: "3" } });

    ["1", "1.10", "1.21", "1.331", "1.4641"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(`Dividend year ${index + 1}`), { target: { value } });
    });

    expect(screen.getByText("13.00%")).toBeInTheDocument();
    expect(screen.getByText("3.00%")).toBeInTheDocument();
    expect(screen.getByText("10.00%")).toBeInTheDocument();
  });

  it("can calculate Gordon dividend yield from dividend amount and share price", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Gordon Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Dividend amount input" }));
    fireEvent.change(screen.getByLabelText("Annual dividend per share"), { target: { value: "1.50" } });
    fireEvent.change(screen.getByLabelText("Share price"), { target: { value: "50" } });
    fireEvent.change(screen.getByLabelText("Dividend growth"), { target: { value: "5" } });

    expect(screen.getByText("8.00%")).toBeInTheDocument();
    expect(screen.getByText("3.00%")).toBeInTheDocument();
    expect(screen.getByText("5.00%")).toBeInTheDocument();
  });
});

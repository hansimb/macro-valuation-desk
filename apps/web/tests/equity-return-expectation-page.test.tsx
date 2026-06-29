import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { hydrateRoot } from "react-dom/client";
import { renderToString } from "react-dom/server";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

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

function expectButtonBefore(leftName: string, rightName: string) {
  const left = screen.getByRole("button", { name: leftName });
  const right = screen.getByRole("button", { name: rightName });

  expect(left.compareDocumentPosition(right) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
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

  it("hydrates saved choices from local storage without a hydration mismatch", async () => {
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

    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const originalWindow = globalThis.window;
    vi.stubGlobal("window", undefined);
    const serverHtml = renderToString(
      <ThemeProvider>
        <EquityReturnExpectationPage />
      </ThemeProvider>,
    );
    vi.stubGlobal("window", originalWindow);
    const container = document.createElement("div");
    container.innerHTML = serverHtml;
    document.body.appendChild(container);

    const root = hydrateRoot(
      container,
      <ThemeProvider>
        <EquityReturnExpectationPage />
      </ThemeProvider>,
    );

    const hydratedPage = within(container);
    await waitFor(() => {
      expect(hydratedPage.getByRole("button", { name: "Gordon Growth" })).toHaveAttribute("aria-pressed", "true");
    });
    const hydrationErrors = consoleError.mock.calls.filter((call) =>
      call.some((part) => String(part).includes("Hydration failed")),
    );
    expect(hydrationErrors).toEqual([]);

    root.unmount();
    container.remove();
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Gordon Growth" })).toHaveAttribute("aria-pressed", "true");
    });
    expect(screen.getByDisplayValue("3")).toBeInTheDocument();
    expect(screen.getByDisplayValue("5")).toBeInTheDocument();
    expect(screen.getByText("8.00%")).toBeInTheDocument();
  });

  it("can calculate Gordon dividend growth from four or five years of dividend history", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Gordon Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Dividend yield input" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Direct dividend growth" }));
    fireEvent.change(screen.getByLabelText("Annual dividend per share"), { target: { value: "1.50" } });
    fireEvent.change(screen.getByLabelText("Share price"), { target: { value: "50" } });
    fireEvent.change(screen.getByLabelText("Dividend growth"), { target: { value: "5" } });

    expect(screen.getByText("8.00%")).toBeInTheDocument();
    expect(screen.getByText("3.00%")).toBeInTheDocument();
    expect(screen.getByText("5.00%")).toBeInTheDocument();
  });

  it("saves named analyses locally and restores them from the saved analyses menu", async () => {
    renderPage();

    expect(screen.getByText(/Saved analyses are stored only on this device/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Analysis name"), { target: { value: "ADOBE" } });
    fireEvent.click(screen.getByRole("button", { name: "Earnings Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Direct growth estimate" }));
    fireEvent.click(screen.getByRole("button", { name: "P/E input" }));
    fireEvent.change(screen.getByLabelText("P/E ratio"), { target: { value: "25" } });
    fireEvent.change(screen.getByLabelText("Expected annual growth"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "Save analysis" }));

    expect(screen.getByRole("option", { name: "ADOBE" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("P/E ratio"), { target: { value: "10" } });
    expect(screen.getByText("17.00%")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Selected analysis"), { target: { value: "ADOBE" } });

    expect(screen.getByLabelText("Analysis name")).toHaveValue("ADOBE");
    expect(screen.getByLabelText("Selected analysis")).toHaveValue("ADOBE");
    expect(screen.getByDisplayValue("25")).toBeInTheDocument();
    expect(screen.getByText("11.00%")).toBeInTheDocument();
    expect(window.localStorage.getItem("equity-return-expectation-analyses-v1")).toContain("ADOBE");
  });

  it("manages selected, modified, deleted, and new saved analyses", async () => {
    renderPage();

    expect(screen.getByText("Unnamed analysis")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Analysis name"), { target: { value: "ADOBE" } });
    fireEvent.click(screen.getByRole("button", { name: "Direct growth estimate" }));
    fireEvent.click(screen.getByRole("button", { name: "P/E input" }));
    fireEvent.change(screen.getByLabelText("P/E ratio"), { target: { value: "25" } });
    fireEvent.change(screen.getByLabelText("Expected annual growth"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "Save analysis" }));

    expect(screen.getByLabelText("Selected analysis")).toHaveValue("ADOBE");
    expect(screen.getByText("Saved analysis: ADOBE")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("P/E ratio"), { target: { value: "20" } });

    expect(screen.getByText("Unsaved changes to ADOBE")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Save analysis" }));

    expect(screen.getByText("Saved analysis: ADOBE")).toBeInTheDocument();
    expect(window.localStorage.getItem("equity-return-expectation-analyses-v1")).toContain("\"peRatio\":\"20\"");

    fireEvent.click(screen.getByRole("button", { name: "New analysis" }));

    expect(screen.getByLabelText("Selected analysis")).toHaveValue("");
    expect(screen.getByLabelText("Analysis name")).toHaveValue("");
    expect(screen.queryByDisplayValue("20")).not.toBeInTheDocument();
    expect(screen.getByRole("option", { name: "ADOBE" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Selected analysis"), { target: { value: "ADOBE" } });
    fireEvent.click(screen.getByRole("button", { name: "Delete analysis" }));

    expect(screen.getByText("Unnamed analysis")).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "ADOBE" })).not.toBeInTheDocument();

    await waitFor(() => {
      expect(window.localStorage.getItem("equity-return-expectation-analyses-v1")).toBe("[]");
    });
  });

  it("keeps separate saved historical growth values for EPS and revenue assumptions", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Earnings Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Historical growth" }));
    fireEvent.click(screen.getByRole("button", { name: "EPS growth" }));

    ["100", "110", "121", "133.1", "146.41"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(`Year ${index + 1} value`), { target: { value } });
    });

    fireEvent.click(screen.getByRole("button", { name: "Revenue growth" }));

    expect(screen.queryByDisplayValue("100")).not.toBeInTheDocument();
    expect(screen.getAllByLabelText(/Year \d value/).map((input) => (input as HTMLInputElement).value)).toEqual(["", "", "", "", ""]);

    ["200", "220", "242", "266.2", "292.82"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(`Year ${index + 1} value`), { target: { value } });
    });

    fireEvent.click(screen.getByRole("button", { name: "EPS growth" }));

    expect(screen.getByDisplayValue("100")).toBeInTheDocument();
    expect(screen.getByDisplayValue("146.41")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("200")).not.toBeInTheDocument();
  });

  it("shows calculated input choices before direct input choices by default", () => {
    renderPage();

    expectButtonBefore("Historical growth", "Direct growth estimate");
    expect(screen.getByRole("button", { name: "Historical growth" })).toHaveAttribute("aria-pressed", "true");
    expectButtonBefore("Market cap input", "P/E input");
    expect(screen.getByRole("button", { name: "Market cap input" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));

    expectButtonBefore("FCF amount input", "FCF yield input");
    expect(screen.getByRole("button", { name: "FCF amount input" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "Gordon Growth" }));

    expectButtonBefore("Dividend amount input", "Dividend yield input");
    expect(screen.getByRole("button", { name: "Dividend amount input" })).toHaveAttribute("aria-pressed", "true");
    expectButtonBefore("Historical dividend growth", "Direct dividend growth");
    expect(screen.getByRole("button", { name: "Historical dividend growth" })).toHaveAttribute("aria-pressed", "true");
  });
});

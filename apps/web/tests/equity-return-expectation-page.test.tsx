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

function expectTextBefore(leftText: string, rightText: string) {
  const left = screen.getAllByText(leftText)[0];
  const right = screen.getAllByText(rightText)[0];

  expect(left.compareDocumentPosition(right) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
}

function expectTextVisible(value: string) {
  expect(screen.getAllByText(value).length).toBeGreaterThan(0);
}

function expectLabelBefore(leftLabel: string, rightLabel: string) {
  const left = screen.getByLabelText(leftLabel);
  const right = screen.getByLabelText(rightLabel);

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

    expect(screen.getAllByText("11.00%").length).toBeGreaterThan(0);
    expectTextVisible("5.00%");
    expectTextVisible("6.00%");

    await waitFor(() => {
      expect(window.localStorage.getItem("equity-return-expectation-v1")).toContain("\"peRatio\":\"20\"");
    });
  });

  it("calculates FCF yield and growth from a locked four-year FCF window", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Calculated 4-year average" }));
    fireEvent.click(screen.getByRole("button", { name: "Historical FCF growth" }));

    fireEvent.change(screen.getByLabelText("Market capitalization"), { target: { value: "1000" } });
    ["180", "160", "140", "120"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(index === 0 ? "Latest operating cash flow" : `Operating cash flow year ${index + 1}`), { target: { value } });
    });
    ["60", "50", "40", "30"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(index === 0 ? "Latest capital expenditures" : `Capital expenditures year ${index + 1}`), { target: { value } });
    });

    expect(screen.queryByRole("button", { name: "Cash flow statement input" })).not.toBeInTheDocument();
    expect(screen.getByText(/Historical FCF growth uses the same 4-year window/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "2 years" })).not.toBeInTheDocument();
    expectTextVisible("20.57%");
    expectTextVisible("10.50%");
    expectTextVisible("10.07%");
    expectTextVisible("9.5x");

    fireEvent.click(screen.getByRole("button", { name: "Calculated latest year" }));
    fireEvent.change(screen.getByLabelText("Latest operating cash flow"), { target: { value: "180" } });
    fireEvent.change(screen.getByLabelText("Latest capital expenditures"), { target: { value: "60" } });
    fireEvent.click(screen.getByRole("button", { name: "Direct FCF growth estimate" }));
    fireEvent.change(screen.getByLabelText("Direct FCF growth estimate"), { target: { value: "5" } });
    expectTextVisible("17.00%");
    expectTextVisible("12.00%");
    expectTextVisible("5.00%");
    expectTextVisible("8.3x");
  });

  it("uses direct FCF growth estimate with direct FCF yield and does not show EPS or revenue growth choices", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Direct FCF yield estimate" }));
    fireEvent.click(screen.getByRole("button", { name: "Direct FCF growth estimate" }));
    fireEvent.change(screen.getByLabelText("FCF yield"), { target: { value: "7" } });
    fireEvent.change(screen.getByLabelText("Direct FCF growth estimate"), { target: { value: "4" } });

    expect(screen.queryByRole("button", { name: "EPS growth" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Revenue growth" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Historical growth" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Direct growth estimate" })).not.toBeInTheDocument();
    expect(screen.getByText("Expected return = free cash flow yield + FCF growth")).toBeInTheDocument();
    expect(screen.getAllByText("11.00%").length).toBeGreaterThan(0);
    expectTextVisible("7.00%");
    expectTextVisible("4.00%");
    expect(screen.queryByText("FCF Yield · latest fiscal year FCF + FCF growth estimate")).not.toBeInTheDocument();
  });

  it("asks only for the latest fiscal year when FCF yield uses the latest year", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));

    expect(screen.getByRole("button", { name: "Calculated latest year" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByRole("button", { name: "Calculated 4-year average" })).toBeInTheDocument();
    expect(screen.getByLabelText("Latest operating cash flow")).toBeInTheDocument();
    expect(screen.getByLabelText("Latest capital expenditures")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Direct FCF growth estimate" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByLabelText("1 year ago operating cash flow")).not.toBeInTheDocument();
  });

  it("orders FCF cash flow statement inputs by fiscal year pairs", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Calculated 4-year average" }));

    expect(screen.getByLabelText("Latest operating cash flow")).toBeInTheDocument();
    expect(screen.getByLabelText("Latest capital expenditures")).toBeInTheDocument();
    expect(screen.getByLabelText("Operating cash flow year 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Capital expenditures year 2")).toBeInTheDocument();
    expect(screen.queryByLabelText("1 year ago operating cash flow")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("1 year ago capital expenditures")).not.toBeInTheDocument();

    expectLabelBefore("Latest operating cash flow", "Latest capital expenditures");
    expectLabelBefore("Latest capital expenditures", "Operating cash flow year 2");
    expectLabelBefore("Operating cash flow year 2", "Capital expenditures year 2");
    expectLabelBefore("Capital expenditures year 2", "Operating cash flow year 3");
    expectLabelBefore("Operating cash flow year 3", "Capital expenditures year 3");
    expectLabelBefore("Capital expenditures year 3", "Operating cash flow year 4");
    expectLabelBefore("Operating cash flow year 4", "Capital expenditures year 4");
  });

  it("shares market capitalization across earnings and FCF models", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Earnings Yield + Growth" }));
    fireEvent.change(screen.getByLabelText("Market capitalization"), { target: { value: "1000" } });
    fireEvent.change(screen.getByLabelText("Net income"), { target: { value: "80" } });

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));

    expect(screen.getByLabelText("Market capitalization")).toHaveValue("1000");
    fireEvent.change(screen.getByLabelText("Latest operating cash flow"), { target: { value: "100" } });
    fireEvent.change(screen.getByLabelText("Latest capital expenditures"), { target: { value: "20" } });

    fireEvent.click(screen.getByRole("button", { name: "Earnings Yield + Growth" }));
    expect(screen.getByLabelText("Market capitalization")).toHaveValue("1000");
  });

  it("calculates shared market capitalization from shares outstanding and share price", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Earnings Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Shares x price" }));
    fireEvent.change(screen.getByLabelText("Shares outstanding"), { target: { value: "100" } });
    fireEvent.change(screen.getByLabelText("Share price for market cap"), { target: { value: "10" } });
    fireEvent.change(screen.getByLabelText("Net income"), { target: { value: "80" } });

    expect(screen.getByText("Earnings yield = net income / market capitalization")).toBeInTheDocument();
    expect(screen.getByText("Calculated Market Capitalization")).toBeInTheDocument();
    expect(screen.getByText("Calculated Earnings Yield")).toBeInTheDocument();
    expect(screen.getByText("Calculated P/E")).toBeInTheDocument();
    expectTextVisible("1000");
    expectTextVisible("8.00%");
    expectTextVisible("12.5x");

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));

    expect(screen.getByRole("button", { name: "Shares x price" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.change(screen.getByLabelText("Latest operating cash flow"), { target: { value: "100" } });
    fireEvent.change(screen.getByLabelText("Latest capital expenditures"), { target: { value: "20" } });

    expectTextVisible("8.00%");
    expectTextVisible("12.5x");
  });

  it("compares valid return expectation methods and prefers historical growth over estimates", () => {
    renderPage();

    expect(screen.queryByText("Return Expectation Methods")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Earnings Yield + Growth" }));
    fireEvent.change(screen.getByLabelText("Market capitalization"), { target: { value: "1000" } });
    fireEvent.change(screen.getByLabelText("Net income"), { target: { value: "80" } });
    ["100", "110", "121", "133.1", "146.41"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(`Year ${index + 1} value`), { target: { value } });
    });

    expect(screen.queryByText("Return Expectation Methods")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Revenue growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Direct growth estimate" }));
    fireEvent.change(screen.getByLabelText("Expected annual growth"), { target: { value: "6" } });

    expect(screen.getByText("Return Expectation Methods")).toBeInTheDocument();
    expect(screen.getByText("Earnings Yield · EPS growth history")).toBeInTheDocument();
    expect(screen.getByText("Earnings Yield · revenue growth estimate")).toBeInTheDocument();
    expect(screen.getByText("Compares completed methods only; no average is calculated across models.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "EPS growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Direct growth estimate" }));
    fireEvent.change(screen.getByLabelText("Expected annual growth"), { target: { value: "4" } });

    expect(screen.getByText("Earnings Yield · EPS growth history")).toBeInTheDocument();
    expect(screen.queryByText("Earnings Yield · EPS growth estimate")).not.toBeInTheDocument();
  });

  it("uses the active FCF yield and growth selections in the comparison summary", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Earnings Yield + Growth" }));
    fireEvent.change(screen.getByLabelText("Market capitalization"), { target: { value: "1000" } });
    fireEvent.change(screen.getByLabelText("Net income"), { target: { value: "80" } });
    ["100", "110", "121", "133.1", "146.41"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(`Year ${index + 1} value`), { target: { value } });
    });

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Direct FCF yield estimate" }));
    fireEvent.change(screen.getByLabelText("FCF yield"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Calculated 4-year average" }));
    fireEvent.click(screen.getByRole("button", { name: "Direct FCF growth estimate" }));
    fireEvent.change(screen.getByLabelText("Market capitalization"), { target: { value: "1000" } });
    ["180", "160", "140", "120"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(index === 0 ? "Latest operating cash flow" : `Operating cash flow year ${index + 1}`), { target: { value } });
    });
    ["60", "50", "40", "30"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(index === 0 ? "Latest capital expenditures" : `Capital expenditures year ${index + 1}`), { target: { value } });
    });
    fireEvent.change(screen.getByLabelText("Direct FCF growth estimate"), { target: { value: "5" } });

    expect(screen.getAllByText("15.50%").length).toBeGreaterThan(1);
    expect(screen.getByText("FCF Yield Â· 4-year average FCF + FCF growth estimate")).toBeInTheDocument();
    expect(screen.queryByText("FCF Yield Â· direct FCF yield + FCF growth estimate")).not.toBeInTheDocument();
  });

  it("shows a metric summary between the active result and return method comparison", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Gordon Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Dividend amount input" }));
    fireEvent.click(screen.getByRole("button", { name: "Historical dividend growth" }));
    fireEvent.change(screen.getByLabelText("Annual dividend per share"), { target: { value: "1.50" } });
    fireEvent.change(screen.getByLabelText("Share price"), { target: { value: "50" } });
    ["1", "1.10", "1.21", "1.331", "1.4641"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(`Dividend year ${index + 1}`), { target: { value } });
    });

    fireEvent.click(screen.getByRole("button", { name: "Earnings Yield + Growth" }));
    fireEvent.change(screen.getByLabelText("Market capitalization"), { target: { value: "1000" } });
    fireEvent.change(screen.getByLabelText("Net income"), { target: { value: "80" } });
    ["100", "110", "121", "133.1", "146.41"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(`Year ${index + 1} value`), { target: { value } });
    });
    fireEvent.click(screen.getByRole("button", { name: "Revenue growth" }));
    ["200", "220", "242", "266.2", "292.82"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(`Year ${index + 1} value`), { target: { value } });
    });

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Calculated 4-year average" }));
    fireEvent.click(screen.getByRole("button", { name: "Historical FCF growth" }));
    ["180", "160", "140", "120"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(index === 0 ? "Latest operating cash flow" : `Operating cash flow year ${index + 1}`), { target: { value } });
    });
    ["60", "50", "40", "30"].forEach((value, index) => {
      fireEvent.change(screen.getByLabelText(index === 0 ? "Latest capital expenditures" : `Capital expenditures year ${index + 1}`), { target: { value } });
    });

    expectTextBefore("Result", "Metric Summary");
    expectTextBefore("Metric Summary", "Return Expectation Methods");
    expect(screen.getByText("Yield Metrics")).toBeInTheDocument();
    expect(screen.getByText("Historical Growth Metrics")).toBeInTheDocument();
    expect(screen.getByText("Dividend Yield")).toBeInTheDocument();
    expect(screen.getByText("Earnings Yield")).toBeInTheDocument();
    expect(screen.getAllByText("FCF Yield").length).toBeGreaterThan(0);
    expect(screen.getByText("EPS Growth History")).toBeInTheDocument();
    expect(screen.getByText("Revenue Growth History")).toBeInTheDocument();
    expect(screen.getByText("Dividend Growth History")).toBeInTheDocument();
    expect(screen.getByText("FCF Growth History")).toBeInTheDocument();
    expect(screen.getAllByText("3.00%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("8.00%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("10.00%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("10.50%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("10.07%").length).toBeGreaterThan(0);
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
    expect(screen.getAllByText("8.00%").length).toBeGreaterThan(0);
  });

  it("normalizes legacy direct growth storage with missing values", async () => {
    window.localStorage.setItem(
      "equity-return-expectation-v1",
      JSON.stringify({
        model: "earnings",
        growth: {
          basis: "eps",
          mode: "direct",
          years: "5",
          historicalValues: ["", "", "", "", ""],
        },
        earnings: {
          yieldMode: "pe",
          peRatio: "20",
        },
      }),
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Direct growth estimate" })).toHaveAttribute("aria-pressed", "true");
    });
    expect(screen.getByLabelText("Expected annual growth")).toHaveValue("");
    expectTextVisible("5.00%");
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

    expectTextVisible("13.00%");
    expectTextVisible("3.00%");
    expectTextVisible("10.00%");
  });

  it("can calculate Gordon dividend yield from dividend amount and share price", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Gordon Growth" }));
    fireEvent.click(screen.getByRole("button", { name: "Dividend amount input" }));
    fireEvent.click(screen.getByRole("button", { name: "Direct dividend growth" }));
    fireEvent.change(screen.getByLabelText("Annual dividend per share"), { target: { value: "1.50" } });
    fireEvent.change(screen.getByLabelText("Share price"), { target: { value: "50" } });
    fireEvent.change(screen.getByLabelText("Dividend growth"), { target: { value: "5" } });

    expectTextVisible("8.00%");
    expectTextVisible("3.00%");
    expectTextVisible("5.00%");
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
    expectTextVisible("17.00%");

    fireEvent.change(screen.getByLabelText("Selected analysis"), { target: { value: "ADOBE" } });

    expect(screen.getByLabelText("Analysis name")).toHaveValue("ADOBE");
    expect(screen.getByLabelText("Selected analysis")).toHaveValue("ADOBE");
    expect(screen.getByDisplayValue("25")).toBeInTheDocument();
    expectTextVisible("11.00%");
    expect(window.localStorage.getItem("equity-return-expectation-analyses-v1")).toContain("ADOBE");
  });

  it("restores the selected saved analysis context when reopening the calculator", async () => {
    renderPage();

    fireEvent.change(screen.getByLabelText("Analysis name"), { target: { value: "ADOBE" } });
    fireEvent.click(screen.getByRole("button", { name: "Direct growth estimate" }));
    fireEvent.click(screen.getByRole("button", { name: "P/E input" }));
    fireEvent.change(screen.getByLabelText("P/E ratio"), { target: { value: "25" } });
    fireEvent.change(screen.getByLabelText("Expected annual growth"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "Save analysis" }));

    cleanup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText("Selected analysis")).toHaveValue("ADOBE");
    });
    expect(screen.getByLabelText("Analysis name")).toHaveValue("ADOBE");
    expect(screen.getByText("Saved analysis: ADOBE")).toBeInTheDocument();
    expect(screen.getByDisplayValue("25")).toBeInTheDocument();
  });

  it("restores unsaved changes to a selected analysis when reopening the calculator", async () => {
    renderPage();

    fireEvent.change(screen.getByLabelText("Analysis name"), { target: { value: "ADOBE" } });
    fireEvent.click(screen.getByRole("button", { name: "Direct growth estimate" }));
    fireEvent.click(screen.getByRole("button", { name: "P/E input" }));
    fireEvent.change(screen.getByLabelText("P/E ratio"), { target: { value: "25" } });
    fireEvent.change(screen.getByLabelText("Expected annual growth"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "Save analysis" }));
    fireEvent.change(screen.getByLabelText("P/E ratio"), { target: { value: "20" } });

    cleanup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText("Selected analysis")).toHaveValue("ADOBE");
    });
    expect(screen.getByLabelText("Analysis name")).toHaveValue("ADOBE");
    expect(screen.getByText("Unsaved changes to ADOBE")).toBeInTheDocument();
    expect(screen.getByDisplayValue("20")).toBeInTheDocument();
  });

  it("labels a restored unnamed draft as unsaved when reopening the calculator", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Direct growth estimate" }));
    fireEvent.click(screen.getByRole("button", { name: "P/E input" }));
    fireEvent.change(screen.getByLabelText("P/E ratio"), { target: { value: "20" } });

    cleanup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByDisplayValue("20")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Selected analysis")).toHaveValue("");
    expect(screen.getByLabelText("Analysis name")).toHaveValue("");
    expect(screen.getByText("Unsaved unnamed analysis")).toBeInTheDocument();
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

    expect(screen.getByText("Unsaved unnamed analysis")).toBeInTheDocument();
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

    expectTextBefore("Earnings Yield", "Growth Assumption");
    expectButtonBefore("Historical growth", "Direct growth estimate");
    expect(screen.getByRole("button", { name: "Historical growth" })).toHaveAttribute("aria-pressed", "true");
    expectButtonBefore("Market cap input", "P/E input");
    expect(screen.getByRole("button", { name: "Market cap input" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "FCF Yield + Growth" }));

    expectTextBefore("FCF Yield", "FCF Growth");
    expectButtonBefore("Calculated latest year", "Direct FCF yield estimate");
    expect(screen.getByRole("button", { name: "Calculated latest year" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "Gordon Growth" }));

    expectTextBefore("Dividend Yield", "Dividend Growth");
    expectButtonBefore("Dividend amount input", "Dividend yield input");
    expect(screen.getByRole("button", { name: "Dividend amount input" })).toHaveAttribute("aria-pressed", "true");
    expectButtonBefore("Historical dividend growth", "Direct dividend growth");
    expect(screen.getByRole("button", { name: "Historical dividend growth" })).toHaveAttribute("aria-pressed", "true");
  });
});

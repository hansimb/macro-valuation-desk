import { describe, expect, it } from "vitest";

import { buildReturnExpectationCsv, datedReturnExpectationExportFilename } from "../src/features/equity/return-expectation-export";

describe("return expectation export", () => {
  it("formats saved analyses as one escaped CSV row per analysis", () => {
    const csv = buildReturnExpectationCsv([
      {
        analysisName: "ACME, Inc.",
        model: "Earnings Yield + Growth",
        expectedReturn: "11.00%",
        primaryComponentLabel: "Earnings Yield",
        primaryComponent: "5.00%",
        growthLabel: "EPS Growth",
        growth: "6.00%",
        impliedMultipleLabel: "Implied P/E",
        impliedMultiple: "20.0x",
        dividendYield: "N/A",
        earningsYield: "5.00%",
        fcfYield: "N/A",
        epsGrowthHistory: "N/A",
        revenueGrowthHistory: "N/A",
        dividendGrowthHistory: "N/A",
        fcfGrowthHistory: "N/A",
      },
      {
        analysisName: "Quote \"Test\"",
        model: "FCF Yield + Growth",
        expectedReturn: "12.00%",
        primaryComponentLabel: "FCF Yield",
        primaryComponent: "7.00%",
        growthLabel: "FCF Growth",
        growth: "5.00%",
        impliedMultipleLabel: "Implied P/FCF",
        impliedMultiple: "14.3x",
        dividendYield: "N/A",
        earningsYield: "N/A",
        fcfYield: "7.00%",
        epsGrowthHistory: "N/A",
        revenueGrowthHistory: "N/A",
        dividendGrowthHistory: "N/A",
        fcfGrowthHistory: "N/A",
      },
    ]);

    expect(csv).toBe([
      "Analysis name,Model,Expected return,Primary component label,Primary component,Growth label,Growth,Implied multiple label,Implied multiple,Dividend yield,Earnings yield,FCF yield,EPS growth history,Revenue growth history,Dividend growth history,FCF growth history",
      "\"ACME, Inc.\",Earnings Yield + Growth,11.00%,Earnings Yield,5.00%,EPS Growth,6.00%,Implied P/E,20.0x,N/A,5.00%,N/A,N/A,N/A,N/A,N/A",
      "\"Quote \"\"Test\"\"\",FCF Yield + Growth,12.00%,FCF Yield,7.00%,FCF Growth,5.00%,Implied P/FCF,14.3x,N/A,N/A,7.00%,N/A,N/A,N/A,N/A",
    ].join("\r\n"));
  });

  it("uses an ISO date in the export filename", () => {
    expect(datedReturnExpectationExportFilename(new Date("2026-07-06T10:30:00.000Z"))).toBe(
      "return-expectation-analyses-2026-07-06.csv",
    );
  });
});

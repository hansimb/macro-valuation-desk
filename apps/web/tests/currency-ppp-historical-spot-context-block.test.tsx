import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ThemeProvider } from "../src/features/theme/provider";
import {
  buildYearTicks,
  CurrencyPppHistoricalSpotContextBlock,
} from "../src/features/macro/components/currency-ppp-historical-spot-context-block";

const yearlyRows = [
  { actualSpot: "1.0500", monthLabel: "2016-01-01", observationMonth: "2016-01-01" },
  { actualSpot: "1.0600", monthLabel: "2017-01-01", observationMonth: "2017-01-01" },
  { actualSpot: "1.0700", monthLabel: "2018-01-01", observationMonth: "2018-01-01" },
  { actualSpot: "1.0800", monthLabel: "2019-01-01", observationMonth: "2019-01-01" },
  { actualSpot: "1.0900", monthLabel: "2020-01-01", observationMonth: "2020-01-01" },
  { actualSpot: "1.1000", monthLabel: "2021-01-01", observationMonth: "2021-01-01" },
  { actualSpot: "1.1100", monthLabel: "2022-01-01", observationMonth: "2022-01-01" },
  { actualSpot: "1.1200", monthLabel: "2023-01-01", observationMonth: "2023-01-01" },
  { actualSpot: "1.1300", monthLabel: "2024-01-01", observationMonth: "2024-01-01" },
  { actualSpot: "1.1400", monthLabel: "2025-01-01", observationMonth: "2025-01-01" },
  { actualSpot: "1.1500", monthLabel: "2026-01-01", observationMonth: "2026-01-01" },
];

describe("CurrencyPppHistoricalSpotContextBlock", () => {
  it("does not add a duplicate final year when the latest observation is a non-january month", () => {
    const ticks = buildYearTicks([
      ...yearlyRows.slice(1),
      {
        actualSpot: "1.1600",
        monthLabel: "2026-02-01",
        observationMonth: "2026-02-01",
      },
    ], 6);

    expect(ticks).toEqual([
      "2017-01-01",
      "2019-01-01",
      "2021-01-01",
      "2023-01-01",
      "2025-01-01",
    ]);
  });

  it("reduces dense year ticks to an even cadence when the range divides cleanly", () => {
    const ticks = buildYearTicks(yearlyRows, 6);

    expect(ticks).toEqual([
      "2016-01-01",
      "2018-01-01",
      "2020-01-01",
      "2022-01-01",
      "2024-01-01",
      "2026-01-01",
    ]);
  });

  it("keeps year tick spacing even instead of ending with a shorter final gap", () => {
    const longRows = Array.from({ length: 19 }, (_, index) => {
      const year = 2008 + index;
      const month = `${year}-01-01`;

      return {
        actualSpot: `1.${index.toString().padStart(4, "0")}`,
        monthLabel: month,
        observationMonth: month,
      };
    });

    const ticks = buildYearTicks(longRows, 5);

    expect(ticks).toEqual([
      "2008-01-01",
      "2013-01-01",
      "2018-01-01",
      "2023-01-01",
    ]);
  });

  it("does not append an off-cadence final year in a 10Y-style window", () => {
    const ticks = buildYearTicks(yearlyRows.slice(1), 6);

    expect(ticks).toEqual([
      "2017-01-01",
      "2019-01-01",
      "2021-01-01",
      "2023-01-01",
      "2025-01-01",
    ]);
  });

  it("does not append an off-cadence final year in wider windows either", () => {
    const rows2007 = Array.from({ length: 20 }, (_, index) => {
      const year = 2007 + index;
      const month = `${year}-01-01`;

      return {
        actualSpot: `1.${index.toString().padStart(4, "0")}`,
        monthLabel: month,
        observationMonth: month,
      };
    });

    expect(buildYearTicks(rows2007, 6)).toEqual([
      "2007-01-01",
      "2011-01-01",
      "2015-01-01",
      "2019-01-01",
      "2023-01-01",
    ]);

    const rows2002 = Array.from({ length: 25 }, (_, index) => {
      const year = 2002 + index;
      const month = `${year}-01-01`;

      return {
        actualSpot: `1.${index.toString().padStart(4, "0")}`,
        monthLabel: month,
        observationMonth: month,
      };
    });

    expect(buildYearTicks(rows2002, 6)).toEqual([
      "2002-01-01",
      "2007-01-01",
      "2012-01-01",
      "2017-01-01",
      "2022-01-01",
    ]);
  });

  it("renders the Recharts-based historical spot chart shell", () => {
    render(
      <ThemeProvider>
        <CurrencyPppHistoricalSpotContextBlock
          anchorLabel="10-year average anchor"
          baseSpot="1.1200"
          currentSpot="1.1750"
          latestMonth="2026-02-01"
          rows={yearlyRows}
        />
      </ThemeProvider>,
    );

    expect(screen.getByText(/Historical Spot Context/i)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Historical EUR\/USD spot context/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "10Y" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "20Y" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "MAX" }).length).toBeGreaterThan(0);
  });
});

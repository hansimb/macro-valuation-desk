export type ReturnExpectationCsvRow = {
  analysisName: string;
  model: string;
  expectedReturn: string;
  primaryComponentLabel: string;
  primaryComponent: string;
  growthLabel: string;
  growth: string;
  impliedMultipleLabel: string;
  impliedMultiple: string;
  dividendYield: string;
  earningsYield: string;
  fcfYield: string;
  epsGrowthHistory: string;
  revenueGrowthHistory: string;
  dividendGrowthHistory: string;
  fcfGrowthHistory: string;
};

const CSV_COLUMNS: Array<{ header: string; key: keyof ReturnExpectationCsvRow }> = [
  { header: "Analysis name", key: "analysisName" },
  { header: "Model", key: "model" },
  { header: "Expected return", key: "expectedReturn" },
  { header: "Primary component label", key: "primaryComponentLabel" },
  { header: "Primary component", key: "primaryComponent" },
  { header: "Growth label", key: "growthLabel" },
  { header: "Growth", key: "growth" },
  { header: "Implied multiple label", key: "impliedMultipleLabel" },
  { header: "Implied multiple", key: "impliedMultiple" },
  { header: "Dividend yield", key: "dividendYield" },
  { header: "Earnings yield", key: "earningsYield" },
  { header: "FCF yield", key: "fcfYield" },
  { header: "EPS growth history", key: "epsGrowthHistory" },
  { header: "Revenue growth history", key: "revenueGrowthHistory" },
  { header: "Dividend growth history", key: "dividendGrowthHistory" },
  { header: "FCF growth history", key: "fcfGrowthHistory" },
];

function escapeCsvCell(value: string) {
  if (/[",\r\n]/.test(value)) {
    return `"${value.replaceAll("\"", "\"\"")}"`;
  }

  return value;
}

export function buildReturnExpectationCsv(rows: ReturnExpectationCsvRow[]) {
  return [
    CSV_COLUMNS.map((column) => escapeCsvCell(column.header)).join(","),
    ...rows.map((row) => CSV_COLUMNS.map((column) => escapeCsvCell(row[column.key])).join(",")),
  ].join("\r\n");
}

export function datedReturnExpectationExportFilename(now = new Date()) {
  const isoDate = now.toISOString().slice(0, 10);
  return `return-expectation-analyses-${isoDate}.csv`;
}

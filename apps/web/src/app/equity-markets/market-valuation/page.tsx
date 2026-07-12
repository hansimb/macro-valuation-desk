import React from "react";
import { Badge, Box, Heading, Link, Stack, Text } from "@chakra-ui/react";

import type {
  EquityMarketValuationMetric,
  EquityMarketValuationRow,
  EquityMarketValuationsResponse,
} from "../../../../../../packages/shared/src/contracts/equity-market-valuation";
import { BackLink } from "../../../features/site-shell/back-link";

const emptyValuations: EquityMarketValuationsResponse = {
  asOf: null,
  markets: [],
  references: [],
};

const metricColumns = [
  { key: "trailingPe", label: "P/E" },
  { key: "priceToBook", label: "P/B" },
  { key: "priceToSales", label: "P/S" },
  { key: "priceToCashFlow", label: "P/CF proxy" },
  { key: "priceToFreeCashFlow", label: "Exact P/FCF" },
  { key: "dividendYieldPct", label: "Dividend yield" },
] as const;

type MetricKey = (typeof metricColumns)[number]["key"];

async function getMarketValuations(): Promise<{
  data: EquityMarketValuationsResponse;
  unavailable: boolean;
}> {
  const apiBaseUrl = process.env.MVD_API_URL ?? process.env.API_BASE_URL ?? "http://127.0.0.1:4000";

  try {
    const response = await fetch(`${apiBaseUrl}/equity-markets/valuations`, { cache: "no-store" });

    if (!response.ok) {
      return { data: emptyValuations, unavailable: true };
    }

    const data = (await response.json()) as EquityMarketValuationsResponse;
    return { data, unavailable: data.markets.length === 0 };
  } catch {
    return { data: emptyValuations, unavailable: true };
  }
}

function formatMetric(metric: EquityMarketValuationMetric, key: MetricKey) {
  if (metric.value === null) {
    return "Unavailable";
  }

  return key === "dividendYieldPct" ? `${metric.value}%` : metric.value;
}

function measuredTypeLabel(row: EquityMarketValuationRow) {
  if (row.measuredType.toLowerCase() === "etf") {
    return "ETF proxy";
  }

  return `${row.measuredType} series`;
}

function MarketValuationTable({ markets }: { markets: EquityMarketValuationRow[] }) {
  return (
    <Box overflowX="auto">
      <Box
        as="table"
        aria-label="Market valuation overview"
        borderCollapse="collapse"
        minW="76rem"
        w="100%"
      >
        <Box as="thead">
          <Box as="tr" borderBottomColor="edge" borderBottomWidth="1px">
            {["Market", "Measured object", ...metricColumns.map((column) => column.label), "Sources"].map(
              (heading) => (
                <Box
                  as="th"
                  color="muted"
                  key={heading}
                  p="3"
                  textAlign={heading === "Market" || heading === "Measured object" || heading === "Sources" ? "left" : "right"}
                  textStyle="eyebrow"
                  verticalAlign="bottom"
                >
                  {heading}
                </Box>
              ),
            )}
          </Box>
        </Box>
        <Box as="tbody">
          {markets.map((row) => (
            <Box as="tr" borderBottomColor="edge" borderBottomWidth="1px" key={row.marketId}>
              <Box as="th" p="3" textAlign="left" verticalAlign="top">
                <Stack gap="1">
                  <Text fontWeight="700" textStyle="body">
                    {row.marketName}
                  </Text>
                  <Text color="muted" textStyle="caption">
                    {row.region}
                  </Text>
                  <Text color="muted" textStyle="caption">
                    Row as of {row.asOf}
                  </Text>
                </Stack>
              </Box>
              <Box as="td" p="3" verticalAlign="top">
                <Stack gap="1">
                  <Text fontWeight="700" textStyle="body">
                    {row.measuredSymbol}
                  </Text>
                  <Text color="muted" textStyle="caption">
                    {row.measuredName}
                  </Text>
                  <Badge alignSelf="flex-start" colorPalette="blue" variant="surface">
                    {measuredTypeLabel(row)}
                  </Badge>
                </Stack>
              </Box>
              {metricColumns.map((column) => (
                <Box as="td" key={column.key} p="3" textAlign="right" textStyle="body" verticalAlign="top">
                  {formatMetric(row.metrics[column.key], column.key)}
                </Box>
              ))}
              <Box as="td" p="3" textAlign="left" verticalAlign="top">
                <Link color="accent" href={row.sourceUrl} textStyle="caption">
                  Row source
                </Link>
              </Box>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
}

export default async function MarketValuationPage() {
  const { data, unavailable } = await getMarketValuations();

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <BackLink href="/equity-markets" label="Back to Equity Markets" />
        <Text color="accent" textStyle="eyebrow">
          Market Valuation
        </Text>
        <Heading as="h1" textStyle="hero">
          Market Valuation Dashboard
        </Heading>
        <Text color="muted" maxW="3xl" textStyle="subtitle">
          API-backed overview for scanning broad equity market valuation snapshots across countries
          and regions.
        </Text>
        <Text color="muted" textStyle="caption">
          Latest valuation date: {data.asOf ?? "latest available update"}
        </Text>
      </Stack>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
        <Stack gap="3">
          <Text color="accent" textStyle="eyebrow">
            Methodology
          </Text>
          <Text color="muted" textStyle="body">
            The measured object is shown for every row so ETF proxies and index-native series stay
            visible. P/CF is labeled as a proxy. Exact P/FCF is shown only when the API provides a
            non-null exact value.
          </Text>
        </Stack>
      </Box>

      {unavailable ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
          <Stack gap="2">
            <Text fontWeight="semibold" textStyle="body">
              Live market valuation data is unavailable right now.
            </Text>
            <Text color="muted" textStyle="body">
              Run the market valuation pipeline to populate ETF and index valuation snapshots.
            </Text>
          </Stack>
        </Box>
      ) : (
        <Box
          as="section"
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          p={{ base: "4", md: "6" }}
          rounded="panel"
        >
          <Stack gap="5">
            <Stack gap="2">
              <Text color="accent" textStyle="eyebrow">
                Valuation Matrix
              </Text>
              <Heading as="h2" textStyle="title">
                Broad market ratios
              </Heading>
              <Text color="muted" maxW="3xl" textStyle="body">
                One row per covered market with provider valuation metrics, measured object
                metadata, per-market dates, and row-level source links.
              </Text>
            </Stack>

            <MarketValuationTable markets={data.markets} />
          </Stack>
        </Box>
      )}

      {data.references.length > 0 ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
          <Stack gap="3">
            <Text color="accent" textStyle="eyebrow">
              References
            </Text>
            {data.references.map((reference) => (
              <Link color="accent" href={reference.url} key={reference.url} textStyle="body">
                {reference.label}
              </Link>
            ))}
          </Stack>
        </Box>
      ) : null}
    </Stack>
  );
}

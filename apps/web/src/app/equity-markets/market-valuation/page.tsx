import React from "react";
import { Badge, Box, Heading, SimpleGrid, Stack, Text } from "@chakra-ui/react";

import {
  PLACEHOLDER_MARKET_VALUATION_DATASET_STATUS,
  marketValuationRows,
} from "../../../features/equity/market-valuation-placeholder-data";
import { BackLink } from "../../../features/site-shell/back-link";

const metricColumns = [
  { key: "pe", label: "P/E" },
  { key: "pb", label: "P/B" },
  { key: "ps", label: "P/S" },
  { key: "pfcf", label: "P/FCF" },
  { key: "dividendYield", label: "Dividend yield" },
] as const;

const implementationSteps = [
  {
    label: "Data source",
    value: "Select primary provider for index/ETF holdings and fundamentals.",
  },
  {
    label: "Weighting",
    value: "Calculate weighted ratios from constituents or ingest provider-weighted ratios.",
  },
  {
    label: "Validation",
    value: "Block release until placeholder rows are replaced by API-backed rows.",
  },
];

export default function MarketValuationPage() {
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
          Placeholder workspace for comparing broad index and ETF valuation ratios across major
          equity markets.
        </Text>
      </Stack>

      <Box
        bg="surface"
        borderColor="accent"
        borderWidth="1px"
        p={{ base: "5", md: "6" }}
        rounded="panel"
      >
        <Stack gap="3">
          <Badge alignSelf="flex-start" colorPalette="yellow" variant="surface">
            Placeholder data only
          </Badge>
          <Heading as="h2" textStyle="subheading">
            Do not use these values for analysis
          </Heading>
          <Text color="muted" textStyle="body">
            Every value on this page is fake seed data for layout work. The placeholder dataset is
            isolated behind <Box as="code">{PLACEHOLDER_MARKET_VALUATION_DATASET_STATUS}</Box> and
            must be replaced with API-backed weighted index or ETF metrics before launch.
          </Text>
        </Stack>
      </Box>

      <SimpleGrid columns={{ base: 1, md: 3 }} gap="4">
        {implementationSteps.map((step) => (
          <Box
            as="section"
            bg="surface"
            borderColor="edge"
            borderWidth="1px"
            key={step.label}
            minH="9rem"
            p="5"
            rounded="panel"
          >
            <Stack gap="3">
              <Text color="accent" textStyle="eyebrow">
                {step.label}
              </Text>
              <Text color="muted" textStyle="body">
                {step.value}
              </Text>
            </Stack>
          </Box>
        ))}
      </SimpleGrid>

      <Box as="section" bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "4", md: "6" }} rounded="panel">
        <Stack gap="5">
          <Stack gap="2">
            <Text color="accent" textStyle="eyebrow">
              Valuation Matrix
            </Text>
            <Heading as="h2" textStyle="title">
              Broad market ratios
            </Heading>
            <Text color="muted" maxW="3xl" textStyle="body">
              Initial country and regional coverage mirrors the planned backend scope: USA, Europe,
              Germany, France, UK, Nordics, China, Japan, South Korea, Taiwan, and other major
              index universes.
            </Text>
          </Stack>

          <Box overflowX="auto">
            <Box
              as="table"
              aria-label="Placeholder market valuation matrix"
              borderCollapse="collapse"
              minW="58rem"
              w="100%"
            >
              <Box as="thead">
                <Box as="tr" borderBottomColor="edge" borderBottomWidth="1px">
                  {["Region", "Market proxy", ...metricColumns.map((column) => column.label), "Status"].map(
                    (heading) => (
                      <Box
                        as="th"
                        color="muted"
                        key={heading}
                        p="3"
                        textAlign={heading === "Region" || heading === "Market proxy" ? "left" : "right"}
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
                {marketValuationRows.map((row) => (
                  <Box as="tr" borderBottomColor="edge" borderBottomWidth="1px" key={row.region}>
                    <Box as="th" p="3" textAlign="left" verticalAlign="top">
                      <Stack gap="1">
                        <Text fontWeight="700" textStyle="body">
                          {row.region}
                        </Text>
                        <Text color="muted" textStyle="caption">
                          {row.market}
                        </Text>
                      </Stack>
                    </Box>
                    <Box as="td" color="muted" p="3" textStyle="caption" verticalAlign="top">
                      {row.proxy}
                    </Box>
                    {metricColumns.map((column) => (
                      <Box as="td" key={column.key} p="3" textAlign="right" textStyle="body" verticalAlign="top">
                        {row[column.key]}
                      </Box>
                    ))}
                    <Box as="td" p="3" textAlign="right" verticalAlign="top">
                      <Badge colorPalette="yellow" variant="surface">
                        Placeholder
                      </Badge>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Box>
          </Box>
        </Stack>
      </Box>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
        <Stack gap="3">
          <Text color="accent" textStyle="eyebrow">
            Backend handoff
          </Text>
          <Heading as="h2" textStyle="subheading">
            Replace this dataset with API-backed weighted index/ETF metrics before launch
          </Heading>
          <Text color="muted" textStyle="body">
            The frontend expects one row per market with P/E, P/B, P/S, P/FCF, dividend yield,
            source status, and a freshness timestamp once the backend contract exists.
          </Text>
        </Stack>
      </Box>
    </Stack>
  );
}

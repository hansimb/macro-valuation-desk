import React from "react";
import { Box, Heading, SimpleGrid, Stack, Table, Text } from "@chakra-ui/react";

import { AnalysisMetricCard } from "../../../features/macro/components/analysis-metric-card";
import { BackLink } from "../../../features/site-shell/back-link";

const placeholderRows = [
  { rank: "1", ticker: "SNOW", company: "Snowflake", country: "US", flag: "🇺🇸", ps: "22.4x", sector: "Software" },
  { rank: "2", ticker: "CRWD", company: "CrowdStrike", country: "US", flag: "🇺🇸", ps: "21.1x", sector: "Software" },
  { rank: "3", ticker: "PLTR", company: "Palantir", country: "US", flag: "🇺🇸", ps: "19.6x", sector: "Software" },
  { rank: "4", ticker: "DDOG", company: "Datadog", country: "US", flag: "🇺🇸", ps: "17.8x", sector: "Software" },
  { rank: "5", ticker: "ZS", company: "Zscaler", country: "US", flag: "🇺🇸", ps: "16.9x", sector: "Software" }
];

const referenceRows = [
  { label: "S&P 500 Average P/S", note: "USA benchmark", value: "3.1x" },
  { label: "STOXX Europe 600 Average P/S", note: "Europe benchmark", value: "1.9x" }
];

export default function HighestPsRankingPage() {
  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <BackLink href="/equity-markets" label="Back to Equity Markets" />
        <Text color="accent" textStyle="eyebrow">
          Equity Valuation
        </Text>
        <Heading as="h1" textStyle="hero">
          Highest P/S Stocks
        </Heading>
        <Text color="muted" maxW="4xl" textStyle="subtitle">
          This demo version previews the analysis shape with placeholder rows only. It exists to lock the product surface before the live ranking flow is built.
        </Text>
      </Stack>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="4">
          <Text color="accent" textStyle="eyebrow">
            Theory
          </Text>
          <Text color="muted" textStyle="body">
            Price-to-sales is useful when the market is paying heavily for expected future growth, especially in businesses where current earnings are still noisy or intentionally suppressed.
          </Text>
        </Stack>
      </Box>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="4">
          <Text color="accent" textStyle="eyebrow">
            Formula
          </Text>
          <Box bg="canvas" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
            <Text textAlign={{ base: "left", md: "center" }} textStyle="formula">
              P/S = market capitalization / revenue
            </Text>
          </Box>
          <Stack borderColor="edge" borderTopWidth="1px" gap="2" pt="4">
            <Text color="accent" textStyle="eyebrow">
              Methodology
            </Text>
            <Text color="muted" textStyle="body">
              1. Start with one stock universe and one comparable sales definition.
            </Text>
            <Text color="muted" textStyle="body">
              2. Compute P/S for each company on the same basis.
            </Text>
            <Text color="muted" textStyle="body">
              3. Rank the universe by price-to-sales and inspect which names sit at the extreme top end.
            </Text>
          </Stack>
        </Stack>
      </Box>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="4">
          <Text color="accent" textStyle="eyebrow">
            Reference Valuation Context
          </Text>
          <Text color="muted" textStyle="body">
            These benchmark values are placeholder reference context only. They help frame how extreme the ranked company multiples look relative to broad USA and Europe index averages.
          </Text>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap="4">
            {referenceRows.map((row) => (
              <AnalysisMetricCard
                key={row.label}
                label={row.label}
                note={row.note}
                value={row.value}
              />
            ))}
          </SimpleGrid>
        </Stack>
      </Box>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="4">
          <Text color="accent" textStyle="eyebrow">
            Placeholder Ranking
          </Text>
          <Text color="muted" textStyle="body">
            Placeholder demo data only. This table will be removed once the live full-stack ranking is ready.
          </Text>
          <Box overflowX="auto">
            <Table.Root minW="44rem" size="sm" variant="outline">
              <Table.Header bg="#a4a4a4">
                <Table.Row>
                  <Table.ColumnHeader>Rank</Table.ColumnHeader>
                  <Table.ColumnHeader>Country</Table.ColumnHeader>
                  <Table.ColumnHeader>Ticker</Table.ColumnHeader>
                  <Table.ColumnHeader>Company</Table.ColumnHeader>
                  <Table.ColumnHeader>Sector</Table.ColumnHeader>
                  <Table.ColumnHeader textAlign="right">P/S</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {placeholderRows.map((row) => (
                  <Table.Row key={row.ticker}>
                    <Table.Cell>{row.rank}</Table.Cell>
                    <Table.Cell>{row.flag} {row.country}</Table.Cell>
                    <Table.Cell>{row.ticker}</Table.Cell>
                    <Table.Cell>{row.company}</Table.Cell>
                    <Table.Cell>{row.sector}</Table.Cell>
                    <Table.Cell textAlign="right">{row.ps}</Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Box>
        </Stack>
      </Box>
    </Stack>
  );
}

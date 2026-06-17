import React from "react";
import { Box, Heading, SimpleGrid, Stack, Table, Text } from "@chakra-ui/react";

import {
  emptyHighestPsRankingPageData,
  type HighestPsRankingPageData,
} from "../../../features/equity/highest-ps-ranking-types";
import { AnalysisMetricCard } from "../../../features/macro/components/analysis-metric-card";
import { BackLink } from "../../../features/site-shell/back-link";

async function getHighestPsRankingPageData(): Promise<{ data: HighestPsRankingPageData; unavailable: boolean }> {
  const apiBaseUrl = process.env.MVD_API_URL ?? process.env.API_BASE_URL ?? "http://127.0.0.1:4000";

  try {
    const response = await fetch(`${apiBaseUrl}/equity/highest-ps-ranking?limit=50`, { cache: "no-store" });

    if (!response.ok) {
      return { data: emptyHighestPsRankingPageData, unavailable: true };
    }

    const data = (await response.json()) as HighestPsRankingPageData;
    const unavailable = data.ranking.length === 0 || data.referenceBenchmarks.length < 2;

    return { data, unavailable };
  } catch {
    return { data: emptyHighestPsRankingPageData, unavailable: true };
  }
}

export default async function HighestPsRankingPage() {
  const { data, unavailable } = await getHighestPsRankingPageData();

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
          Top-50 ranking view for the most sales-expensive stocks in the selected live universe.
        </Text>
        {data.asOf ? (
          <Text color="muted" textStyle="caption">
            As of {data.asOf}
          </Text>
        ) : null}
      </Stack>

      {unavailable ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
          <Stack gap="2">
            <Text fontWeight="semibold" textStyle="body">Live highest P/S ranking data is unavailable right now.</Text>
            <Text color="muted" textStyle="body">
              Start the API and run the equity ranking pipeline to populate current values.
            </Text>
          </Stack>
        </Box>
      ) : null}

      {!unavailable ? (
        <>
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
                <Text color="muted" textStyle="body">
                  4. Compare the top tail against broad-market benchmarks before drawing any valuation conclusion.
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
                These benchmark values frame how extreme the top-ranked company multiples look relative to broad USA and Europe index averages.
              </Text>
              <SimpleGrid columns={{ base: 1, md: 2 }} gap="4">
                {data.referenceBenchmarks.map((row) => (
                  <AnalysisMetricCard
                    key={row.key}
                    label={row.label}
                    note={`${row.regionLabel} benchmark`}
                    value={row.averagePsRatio}
                  />
                ))}
              </SimpleGrid>
            </Stack>
          </Box>

          <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="4">
              <Text color="accent" textStyle="eyebrow">
                Ranking
              </Text>
              <Text color="muted" textStyle="body">
                {data.universeLabel ?? "Selected universe"} sorted by the highest trailing price-to-sales multiple.
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
                    {data.ranking.map((row) => (
                      <Table.Row key={row.ticker}>
                        <Table.Cell>{row.rank}</Table.Cell>
                        <Table.Cell>{row.countryFlag} {row.countryCode}</Table.Cell>
                        <Table.Cell>{row.ticker}</Table.Cell>
                        <Table.Cell>{row.company}</Table.Cell>
                        <Table.Cell>{row.sector}</Table.Cell>
                        <Table.Cell textAlign="right">{row.psRatio}</Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Root>
              </Box>
            </Stack>
          </Box>
        </>
      ) : null}
    </Stack>
  );
}

import React from "react";
import { Box, Heading, SimpleGrid, Stack, Table, Text } from "@chakra-ui/react";

import {
  emptyHighestPsRankingPageData,
  hasRenderableHighestPsSection,
  type HighestPsRankingPageData,
} from "../../../features/equity/highest-ps-ranking-types";
import { AnalysisMetricCard } from "../../../features/macro/components/analysis-metric-card";
import { BackLink } from "../../../features/site-shell/back-link";

const mockHighestPsRankingPageData: HighestPsRankingPageData = {
  asOf: "2026-06-17",
  sections: [
    {
      key: "usa",
      label: "USA High P/S Leaders",
      universeKey: "sp500",
      asOf: "2026-06-17",
      unavailable: false,
      benchmark: {
        key: "sp500",
        label: "S&P 500",
        averagePsRatio: "3.1x",
        topBasketAveragePsRatio: "18.4x",
        topBasketIndexWeightPct: "9.2%",
        eligibleConstituentCount: 468,
      },
      ranking: [
        {
          rank: 1,
          ticker: "SNOW",
          company: "Snowflake",
          countryCode: "US",
          countryName: "United States",
          sector: "Software",
          psRatio: "22.4x",
          sectorAveragePsRatio: "8.1x",
          relativeToSectorMultiple: "2.8x",
          indexWeightPct: "0.22%",
        },
        {
          rank: 2,
          ticker: "CRWD",
          company: "CrowdStrike",
          countryCode: "US",
          countryName: "United States",
          sector: "Software",
          psRatio: "21.1x",
          sectorAveragePsRatio: "8.1x",
          relativeToSectorMultiple: "2.6x",
          indexWeightPct: "0.34%",
        },
        {
          rank: 3,
          ticker: "PLTR",
          company: "Palantir",
          countryCode: "US",
          countryName: "United States",
          sector: "Software",
          psRatio: "19.6x",
          sectorAveragePsRatio: "8.1x",
          relativeToSectorMultiple: "2.4x",
          indexWeightPct: "0.48%",
        },
      ],
    },
    {
      key: "europe",
      label: "Europe High P/S Leaders",
      universeKey: "stoxx600",
      asOf: "2026-06-17",
      unavailable: false,
      benchmark: {
        key: "stoxx600",
        label: "STOXX Europe 600",
        averagePsRatio: "1.9x",
        topBasketAveragePsRatio: "9.7x",
        topBasketIndexWeightPct: "4.6%",
        eligibleConstituentCount: 544,
      },
      ranking: [
        {
          rank: 1,
          ticker: "ASML",
          company: "ASML",
          countryCode: "NL",
          countryName: "Netherlands",
          sector: "Semiconductors",
          psRatio: "13.2x",
          sectorAveragePsRatio: "6.4x",
          relativeToSectorMultiple: "2.1x",
          indexWeightPct: "2.35%",
        },
        {
          rank: 2,
          ticker: "DSV",
          company: "DSV",
          countryCode: "DK",
          countryName: "Denmark",
          sector: "Industrials",
          psRatio: "8.8x",
          sectorAveragePsRatio: "2.3x",
          relativeToSectorMultiple: "3.8x",
          indexWeightPct: "0.41%",
        },
        {
          rank: 3,
          ticker: "SAP",
          company: "SAP",
          countryCode: "DE",
          countryName: "Germany",
          sector: "Software",
          psRatio: "7.9x",
          sectorAveragePsRatio: "4.5x",
          relativeToSectorMultiple: "1.8x",
          indexWeightPct: "1.22%",
        },
      ],
    },
  ],
  references: [],
};

async function getHighestPsRankingPageData(): Promise<HighestPsRankingPageData> {
  const apiBaseUrl = process.env.MVD_API_URL ?? process.env.API_BASE_URL ?? "http://127.0.0.1:4000";

  try {
    const response = await fetch(`${apiBaseUrl}/equity/highest-ps-ranking`, { cache: "no-store" });

    if (!response.ok) {
      return mockHighestPsRankingPageData;
    }

    const data = (await response.json()) as HighestPsRankingPageData;

    if (data.sections.length === 0) {
      return mockHighestPsRankingPageData;
    }

    return data;
  } catch {
    return mockHighestPsRankingPageData;
  }
}

function sectionMethodNote(universeKey: "sp500" | "stoxx600") {
  if (universeKey === "sp500") {
    return "Sector-relative high-P/S names inside the S&P 500 eligible large-cap universe.";
  }

  return "Sector-relative high-P/S names inside the STOXX Europe 600 eligible large-cap universe.";
}

export default async function HighestPsRankingPage() {
  const data = await getHighestPsRankingPageData();
  const hasRenderableSections = data.sections.some(hasRenderableHighestPsSection);

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
          Two-track valuation view for the highest price-to-sales leaders in U.S. and European large-cap indices.
        </Text>
        <Text color="muted" textStyle="caption">
          Temporary mock preview for the two-section design. Live data will replace these rows once the backend feed is ready.
        </Text>
        {data.asOf ? (
          <Text color="muted" textStyle="caption">
            As of {data.asOf}
          </Text>
        ) : null}
      </Stack>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="4">
          <Text color="accent" textStyle="eyebrow">
            Theory
          </Text>
          <Text color="muted" textStyle="body">
            This view is not trying to answer which market is “most expensive” with one blended table. It asks a more useful question: which names are the most sales-expensive inside their own market and sector structure?
          </Text>
          <Text color="muted" textStyle="body">
            That makes the comparison cleaner. U.S. and European indices have different sector mixes, different typical margins, and very different concentrations in software, industrials, and healthcare. A separate leaderboard for each market keeps those structural differences visible.
          </Text>
          <Text color="muted" textStyle="body">
            The extra index-weight lens matters for passive holders. A stock can look optically expensive but still be irrelevant for the benchmark if its weight is tiny. The basket weight shows how much real index exposure sits inside the highest-multiple cohort.
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
              1. Start with one eligible large-cap universe for the U.S. and one for Europe.
            </Text>
            <Text color="muted" textStyle="body">
              2. Filter to liquid, index-eligible constituents before comparing valuation tails.
            </Text>
            <Text color="muted" textStyle="body">
              3. Rank names by high P/S extremity within each market and compare each company against its own sector baseline.
            </Text>
            <Text color="muted" textStyle="body">
              4. Summarize the basket using market average P/S, top-basket average P/S, and combined index weight.
            </Text>
          </Stack>
        </Stack>
      </Box>

      {data.sections.map((section) => {
        const renderable = hasRenderableHighestPsSection(section);

        return (
          <Box key={section.key} bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="5">
              <Stack gap="2">
                <Text color="accent" textStyle="eyebrow">
                  {section.universeKey === "sp500" ? "USA Valuation" : "Europe Valuation"}
                </Text>
                <Heading as="h2" textStyle="title">
                  {section.label}
                </Heading>
                {section.asOf ? (
                  <Text color="muted" textStyle="caption">
                    As of {section.asOf}
                  </Text>
                ) : null}
              </Stack>

              {!renderable ? (
                <Stack gap="2">
                  <Text fontWeight="semibold" textStyle="body">
                    Live section data for {section.label} is unavailable right now.
                  </Text>
                  <Text color="muted" textStyle="body">
                    This analysis block will appear once benchmark and ranking inputs are populated for the selected market.
                  </Text>
                </Stack>
              ) : (
                <>
                  <Text color="muted" textStyle="body">
                    {sectionMethodNote(section.universeKey)}
                  </Text>

                  <SimpleGrid columns={{ base: 1, md: 2, xl: 4 }} gap="4">
                    <AnalysisMetricCard
                      label={`${section.benchmark.label} Average P/S`}
                      note="Broad-market benchmark"
                      value={section.benchmark.averagePsRatio ?? ""}
                    />
                    <AnalysisMetricCard
                      label="Top Basket Average P/S"
                      note="Average multiple inside the ranked leader basket"
                      value={section.benchmark.topBasketAveragePsRatio ?? ""}
                    />
                    <AnalysisMetricCard
                      label="Top Basket Index Weight"
                      note="Combined index weight of the ranked basket"
                      value={section.benchmark.topBasketIndexWeightPct ?? ""}
                    />
                    <AnalysisMetricCard
                      label="Eligible Constituents"
                      note="Names passing the market eligibility gate"
                      value={String(section.benchmark.eligibleConstituentCount)}
                    />
                  </SimpleGrid>

                  <Box overflowX="auto">
                    <Table.Root minW="72rem" size="sm" variant="outline">
                      <Table.Header bg="#a4a4a4">
                        <Table.Row>
                          <Table.ColumnHeader>Rank</Table.ColumnHeader>
                          <Table.ColumnHeader>Ticker</Table.ColumnHeader>
                          <Table.ColumnHeader>Company</Table.ColumnHeader>
                          <Table.ColumnHeader>Country</Table.ColumnHeader>
                          <Table.ColumnHeader>Sector</Table.ColumnHeader>
                          <Table.ColumnHeader textAlign="right">P/S</Table.ColumnHeader>
                          <Table.ColumnHeader textAlign="right">Sector Avg P/S</Table.ColumnHeader>
                          <Table.ColumnHeader textAlign="right">Rel. to Sector</Table.ColumnHeader>
                          <Table.ColumnHeader textAlign="right">Index Weight</Table.ColumnHeader>
                        </Table.Row>
                      </Table.Header>
                      <Table.Body>
                        {section.ranking.map((row) => (
                          <Table.Row key={`${section.key}-${row.ticker}`}>
                            <Table.Cell>{row.rank}</Table.Cell>
                            <Table.Cell>{row.ticker}</Table.Cell>
                            <Table.Cell>{row.company}</Table.Cell>
                            <Table.Cell>{row.countryName}</Table.Cell>
                            <Table.Cell>{row.sector}</Table.Cell>
                            <Table.Cell textAlign="right">{row.psRatio}</Table.Cell>
                            <Table.Cell textAlign="right">{row.sectorAveragePsRatio}</Table.Cell>
                            <Table.Cell textAlign="right">{row.relativeToSectorMultiple}</Table.Cell>
                            <Table.Cell textAlign="right">{row.indexWeightPct}</Table.Cell>
                          </Table.Row>
                        ))}
                      </Table.Body>
                    </Table.Root>
                  </Box>
                </>
              )}
            </Stack>
          </Box>
        );
      })}
    </Stack>
  );
}

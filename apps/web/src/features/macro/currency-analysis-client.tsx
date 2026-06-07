"use client";

import React from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Button,
  Grid,
  Heading,
  Link,
  SimpleGrid,
  Stack,
  Table,
  Text,
  VisuallyHidden,
} from "@chakra-ui/react";

import type { CurrencyAnalysisPageData } from "./currency-analysis-types";

type CurrencyReferenceItem = CurrencyAnalysisPageData["ppp"]["references"][number];
type PppSymbolKey = "PPP_t" | "S_0" | "P_h_t" | "P_h_0" | "P_f_t" | "P_f_0";

const pppSymbolGuide: { symbol: PppSymbolKey; meaning: string }[] = [
  {
    symbol: "S_0",
    meaning: "Base-period spot exchange rate (here: the selected long-run anchor value for EUR/USD under the chosen rule).",
  },
  {
    symbol: "P_h_t",
    meaning: "Home-country price level at time t (here: U.S. CPI index at observation month t).",
  },
  {
    symbol: "P_h_0",
    meaning: "Home-country price level in the base period (here: the selected long-run anchor value for U.S. CPI under the chosen rule).",
  },
  {
    symbol: "P_f_t",
    meaning: "Foreign-country price level at time t (here: euro area CPI index at observation month t).",
  },
  {
    symbol: "P_f_0",
    meaning: "Foreign-country price level in the base period (here: the selected long-run anchor value for euro-area CPI under the chosen rule).",
  },
  {
    symbol: "PPP_t",
    meaning: "PPP-implied exchange rate at time t (here: the model-implied EUR/USD fair-value anchor).",
  },
];

function pppTakeaway(data: CurrencyAnalysisPageData) {
  if (!data.ppp.summary) {
    return null;
  }

  const anchorLabel = data.ppp.summary.anchorLabel;
  const deviation = Number.parseFloat(data.ppp.summary.deviationPct);
  if (Number.isNaN(deviation)) {
    return null;
  }

  if (deviation > 0) {
    return `The latest market spot sits ${data.ppp.summary.deviationPct}% above the PPP-implied fair-value anchor built from the selected ${anchorLabel}, so the euro screens rich against the dollar on this relative-PPP lens.`;
  }

  if (deviation < 0) {
    return `The latest market spot sits ${Math.abs(deviation).toFixed(2)}% below the PPP-implied fair-value anchor built from the selected ${anchorLabel}, so the euro screens cheap against the dollar on this relative-PPP lens.`;
  }

  return `The latest market spot is sitting almost exactly on the PPP-implied fair-value anchor built from the selected ${anchorLabel}.`;
}

function currencyAcademicReferenceText(label: string, url?: string) {
  if (url?.includes("data.ecb.europa.eu")) {
    return `European Central Bank, Data Portal, "${label}"`;
  }

  return `Federal Reserve Bank of St. Louis, FRED, "${label}"`;
}

function currencyIeeeReferenceText(index: number, reference: CurrencyReferenceItem) {
  const sourceText = currencyAcademicReferenceText(reference.label, reference.url);
  return `[${index}] ${sourceText}. [Online]. Available: ${reference.url}.`;
}

function MathToken({ symbol }: { symbol: PppSymbolKey }) {
  if (symbol === "PPP_t") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          PPP
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
          t
        </Box>
      </>
    );
  }

  if (symbol === "S_0") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          S
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
          0
        </Box>
      </>
    );
  }

  if (symbol === "P_h_t") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          P
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
          h,t
        </Box>
      </>
    );
  }

  if (symbol === "P_h_0") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          P
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
          h,0
        </Box>
      </>
    );
  }

  if (symbol === "P_f_t") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          P
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
          f,t
        </Box>
      </>
    );
  }

  return (
    <>
      <Box as="span" fontStyle="italic">
        P
      </Box>
      <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
        f,0
      </Box>
    </>
  );
}

function ValueCard({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <Box bg="canvas" borderColor="edge" borderWidth="1px" p="4" rounded="panel">
      <Stack gap="2">
        <Text color="muted" fontSize="xs" letterSpacing="0.08em" textTransform="uppercase">
          {label}
        </Text>
        <Text fontSize="xl" fontWeight="semibold" lineHeight="1.1">
          {value}
        </Text>
        <Text color="muted" fontSize="sm" lineHeight="1.4">
          {description}
        </Text>
      </Stack>
    </Box>
  );
}

function buildSearch(
  params: Record<string, string | null | undefined>,
) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      search.set(key, value);
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function CurrencyAnalysisClient({ data }: { data: CurrencyAnalysisPageData }) {
  const router = useRouter();
  const pppSummary = data.ppp.summary;
  const pppInterpretation = pppTakeaway(data);
  const selectedAnchorKind = data.ppp.selectedAnchorKind ?? "window";
  const selectedAnchorStatistic = data.ppp.selectedAnchorStatistic;
  const selectedWindowYears = data.ppp.selectedWindowYears;
  const selectedBaseYear = data.ppp.selectedBaseYear ?? "";
  const recentPathRows = data.ppp.path.slice(-12);
  const hasReferences = data.ppp.references.length > 0;
  const referenceNumberByLabel = new Map(data.ppp.references.map((reference, index) => [reference.label, index + 1]));

  if (!pppSummary) {
    return null;
  }

  const pathRowsWithGap = recentPathRows.map((point) => {
    const spot = Number.parseFloat(point.actualSpot);
    const implied = Number.parseFloat(point.impliedPpp);
    const gap = Number.isNaN(spot) || Number.isNaN(implied) || implied === 0 ? null : ((spot / implied) - 1) * 100;

    return {
      ...point,
      gapLabel: gap === null ? "N/A" : `${gap.toFixed(2)}%`,
    };
  });

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Box as="section">
        <Stack gap="5">
          <Stack gap="3" maxW="4xl">
            <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }} lineHeight="1.05">
              1.0 Relative Purchasing Power Parity
            </Heading>
            <Text color="muted">
              Relative PPP treats EUR/USD as a long-run valuation relationship: if U.S. prices and euro-area prices
              move differently over time, the exchange rate should eventually reflect that inflation differential.
            </Text>
          </Stack>

          <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="4">
              <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                Formula
              </Text>
              <Box bg="canvas" borderColor="edge" borderWidth="1px" overflowX="auto" p={{ base: "5", md: "6" }} rounded="panel">
                <VisuallyHidden>PPP_t = S_0 * (P_h_t / P_h_0) / (P_f_t / P_f_0)</VisuallyHidden>
                <Text
                  fontFamily="heading"
                  fontSize={{ base: "xl", md: "2xl" }}
                  lineHeight="1.4"
                  textAlign={{ base: "left", md: "center" }}
                  whiteSpace="nowrap"
                >
                  <MathToken symbol="PPP_t" /> = <MathToken symbol="S_0" /> * (
                  <MathToken symbol="P_h_t" /> / <MathToken symbol="P_h_0" />) / (
                  <MathToken symbol="P_f_t" /> / <MathToken symbol="P_f_0" />)
                </Text>
              </Box>
              <Grid columnGap="4" rowGap="2" templateColumns={{ base: "7.5rem 1fr", md: "10rem 1fr" }}>
                {pppSymbolGuide.map((item) => (
                  <React.Fragment key={item.symbol}>
                    <Text color="text" fontFamily="heading" fontSize="sm">
                      <MathToken symbol={item.symbol} />
                    </Text>
                    <Text color="muted" fontSize="sm">
                      {item.meaning}
                    </Text>
                  </React.Fragment>
                ))}
              </Grid>
              <Text color="muted" fontSize="sm">
                The model starts from the selected anchor rule for spot and CPI levels and then re-scales that anchor
                by the relative change in U.S. and euro-area CPI index levels.
              </Text>
            </Stack>
          </Box>

          <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="4">
              <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                Data Inputs
              </Text>
              <Stack gap="5">
                <Stack gap="2">
                  <Text color="muted" fontSize="sm">
                    Anchor statistic
                  </Text>
                  <Grid gap="2" templateColumns={{ base: "repeat(2, minmax(0, 1fr))", md: "repeat(2, minmax(0, 12rem))" }}>
                    {(["average", "median"] as const).map((statistic) => {
                      const isActive = selectedAnchorStatistic === statistic;

                      return (
                        <Button
                          aria-pressed={isActive}
                          bg={isActive ? "accent" : "canvas"}
                          borderColor="edge"
                          borderWidth="1px"
                          color={isActive ? "canvas" : "text"}
                          key={statistic}
                          onClick={() => {
                            router.push(
                              `/macro/currency-analysis${buildSearch({
                                anchorKind: selectedAnchorKind,
                                anchorStatistic: statistic,
                                windowYears: selectedWindowYears ? String(selectedWindowYears) : null,
                                baseYear: selectedBaseYear || null,
                              })}`,
                              { scroll: false },
                            );
                          }}
                          size="sm"
                          variant="outline"
                        >
                          {statistic === "average" ? "Average" : "Median"}
                        </Button>
                      );
                    })}
                  </Grid>
                  <Text color="muted" fontSize="xs">
                    This setting controls whether the long-run anchor uses the arithmetic average or the median of the selected anchor sample.
                  </Text>
                </Stack>

                <Stack gap="2">
                  <Text color="muted" fontSize="sm">
                    Long-term anchor window
                  </Text>
                  <Grid gap="2" templateColumns={{ base: "repeat(2, minmax(0, 1fr))", md: "repeat(5, minmax(0, 1fr))" }}>
                    {[3, 5, 10, 20, 30].map((years) => {
                      const isAvailable = data.ppp.availableWindowYears.includes(years);
                      const isActive = selectedAnchorKind === "window" && selectedWindowYears === years;

                      return (
                        <Button
                          aria-pressed={isActive}
                          bg={isActive ? "accent" : "canvas"}
                          borderColor="edge"
                          borderWidth="1px"
                          color={isActive ? "canvas" : "text"}
                          disabled={!isAvailable}
                          key={years}
                          onClick={() => {
                            if (!isAvailable) {
                              return;
                            }

                            router.push(
                              `/macro/currency-analysis${buildSearch({
                                anchorKind: "window",
                                anchorStatistic: selectedAnchorStatistic,
                                windowYears: String(years),
                                baseYear: selectedBaseYear || null,
                              })}`,
                              { scroll: false },
                            );
                          }}
                          size="sm"
                          variant="outline"
                        >
                          {years}Y
                        </Button>
                      );
                    })}
                  </Grid>
                  <Text color="muted" fontSize="xs">
                    Each button builds a new PPP base anchor from the latest {`3, 5, 10, 20, or 30`} years of monthly data under the selected average or median rule.
                  </Text>
                </Stack>

                <SimpleGrid columns={{ base: 1, md: 2 }} gap="5">
                  <Stack gap="2">
                    <Text color="muted" fontSize="sm">
                      Single-year anchor
                    </Text>
                    <Box position="relative">
                      <select
                        aria-label="Single-year anchor"
                        onChange={(event: React.ChangeEvent<HTMLSelectElement>) => {
                          const nextYear = event.currentTarget.value;
                          if (!nextYear) {
                            return;
                          }

                          router.push(
                            `/macro/currency-analysis${buildSearch({
                              anchorKind: "year",
                              anchorStatistic: selectedAnchorStatistic,
                              windowYears: selectedWindowYears ? String(selectedWindowYears) : null,
                              baseYear: nextYear,
                            })}`,
                            { scroll: false },
                          );
                        }}
                        style={{
                          appearance: "none",
                          background: "#181A1B",
                          border: "1px solid #7e91a8",
                          borderRadius: "0.875rem",
                          color: "#d9e8ff",
                          fontSize: "1rem",
                          lineHeight: "1.2",
                          minHeight: "3rem",
                          paddingInlineEnd: "3rem",
                          paddingInlineStart: "0.875rem",
                          width: "100%",
                        }}
                        value={selectedBaseYear}
                      >
                        {data.ppp.availableBaseYears.map((year) => (
                          <option key={year} style={{ background: "#181A1B", color: "#d9e8ff" }} value={year}>
                            {year}
                          </option>
                        ))}
                      </select>
                      <Box
                        aria-hidden="true"
                        color="text"
                        pointerEvents="none"
                        position="absolute"
                        right="0.875rem"
                        top="50%"
                        transform="translateY(-50%)"
                      >
                        v
                      </Box>
                    </Box>
                    <Text color="muted" fontSize="xs">
                      This is the alternative one-year anchor mode. It uses the selected year's own monthly sample under the same average or median rule.
                    </Text>
                  </Stack>

                  <Stack gap="2">
                    <Text color="muted" fontSize="sm">
                      Selection logic
                    </Text>
                    <Text>
                      The active PPP baseline is now the selected {pppSummary.anchorLabel}. That anchor supplies the base spot value and the base CPI values used in the relative-PPP formula.
                    </Text>
                    <Text color="muted" fontSize="sm">
                      {data.ppp.availableBaseYears.length} available single-year anchors and {data.ppp.availableWindowYears.length} available long-run windows in the dataset.
                    </Text>
                  </Stack>
                </SimpleGrid>
              </Stack>
            </Stack>
          </Box>

          <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="4">
              <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                Current PPP Valuation Readout
              </Text>
              <Text color="muted" fontSize="sm">
                These values are computed from the selected long-run anchor and the latest month where spot and both CPI
                series overlap.
              </Text>
              <Grid gap="4" templateColumns={{ base: "1fr", md: "repeat(2, minmax(0, 1fr))", xl: "repeat(5, minmax(0, 1fr))" }}>
                <ValueCard
                  description={`Base spot anchor implied by the selected ${pppSummary.anchorLabel}.`}
                  label="Selected anchor spot"
                  value={pppSummary.baseSpot}
                />
                <ValueCard
                  description={`Observed EUR/USD spot in the latest overlapping month (${pppSummary.asOf}).`}
                  label="Latest observed spot"
                  value={pppSummary.currentSpot}
                />
                <ValueCard
                  description="PPP-implied EUR/USD fair-value anchor for the latest overlapping month."
                  label="Latest PPP-implied fair value"
                  value={pppSummary.impliedPpp}
                />
                <ValueCard
                  description="Percent gap between the latest market spot and the PPP-implied fair value."
                  label="Current valuation gap"
                  value={`${pppSummary.deviationPct}%`}
                />
                <ValueCard
                  description="Average valuation gap across the latest 12 monthly observations in the selected path."
                  label="Trailing 12M average gap"
                  value={`${pppSummary.trailing12mAverageGapPct}%`}
                />
              </Grid>
              {pppInterpretation ? (
                <Stack borderTopWidth="1px" borderColor="edge" gap="2" pt="4">
                  <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                    Analysis Takeaway
                  </Text>
                  <Text color="muted">{pppInterpretation}</Text>
                </Stack>
              ) : null}
            </Stack>
          </Box>

          <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="4">
              <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                Selected Base-Year Path
              </Text>
              <Text color="muted" fontSize="sm">
                Each row compares the observed EUR/USD spot with the PPP-implied level generated from the selected anchor rule.
              </Text>
              <Table.Root size="sm" variant="outline">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>Month</Table.ColumnHeader>
                    <Table.ColumnHeader>Observed spot</Table.ColumnHeader>
                    <Table.ColumnHeader>PPP-implied level</Table.ColumnHeader>
                    <Table.ColumnHeader>Valuation gap %</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {pathRowsWithGap.map((point) => (
                    <Table.Row key={`${point.observationMonth}-${point.impliedPpp}`}>
                      <Table.Cell>{point.observationMonth}</Table.Cell>
                      <Table.Cell>{point.actualSpot}</Table.Cell>
                      <Table.Cell>{point.impliedPpp}</Table.Cell>
                      <Table.Cell>{point.gapLabel}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Stack>
          </Box>

          {hasReferences ? (
            <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
              <Stack gap="4">
                <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                  References
                </Text>
                {data.ppp.references.map((reference) => {
                  const index = referenceNumberByLabel.get(reference.label) ?? 0;
                  const referenceText = currencyIeeeReferenceText(index, reference);

                  return (
                    <Box key={`${reference.label}-${reference.url}`}>
                      <Link color="text" href={reference.url} target="_blank">
                        {referenceText}
                      </Link>
                    </Box>
                  );
                })}
              </Stack>
            </Box>
          ) : null}
        </Stack>
      </Box>
    </Stack>
  );
}

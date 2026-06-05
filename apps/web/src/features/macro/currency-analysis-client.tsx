"use client";

import React from "react";
import NextLink from "next/link";
import { Box, Grid, Heading, Link, Stack, Table, Text } from "@chakra-ui/react";

import type { CurrencyAnalysisPageData } from "./currency-analysis-types";

function pppTakeaway(data: CurrencyAnalysisPageData) {
  if (!data.ppp.summary) {
    return null;
  }

  const deviation = Number.parseFloat(data.ppp.summary.deviationPct);
  if (Number.isNaN(deviation)) {
    return null;
  }

  if (deviation > 0) {
    return `Relative PPP suggests EUR/USD is trading ${data.ppp.summary.deviationPct}% above its inflation-adjusted fair-value anchor for the selected base month.`;
  }

  if (deviation < 0) {
    return `Relative PPP suggests EUR/USD is trading ${Math.abs(deviation).toFixed(2)}% below its inflation-adjusted fair-value anchor for the selected base month.`;
  }

  return "Relative PPP suggests EUR/USD is sitting almost exactly on its inflation-adjusted fair-value anchor for the selected base month.";
}

function irpTakeaway(data: CurrencyAnalysisPageData) {
  if (data.irp.cipRows.length === 0) {
    return null;
  }

  const negativeSpreadCount = data.irp.cipRows.filter((row) => Number.parseFloat(row.rateSpread) < 0).length;
  if (negativeSpreadCount === data.irp.cipRows.length) {
    return "Across the visible tenors, EUR rates sit below USD rates, so the CIP-implied forwards price a weaker euro path than spot.";
  }

  if (negativeSpreadCount === 0) {
    return "Across the visible tenors, EUR rates sit above USD rates, so the CIP-implied forwards price a stronger euro path than spot.";
  }

  return "The tenor structure is mixed, so IRP is not sending one clean message across the curve.";
}

export function CurrencyAnalysisClient({ data }: { data: CurrencyAnalysisPageData }) {
  const pppSectionVisible = data.ppp.summary !== null;
  const irpSectionVisible = data.irp.cipRows.length > 0;
  const pppSummary = data.ppp.summary;
  const pppInterpretation = pppTakeaway(data);
  const irpInterpretation = irpTakeaway(data);

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      {pppSectionVisible ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
          <Stack gap="5">
            <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
              1.0 Relative Purchasing Power Parity
            </Text>
            <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }}>
              Relative Purchasing Power Parity
            </Heading>
            <Text color="muted">
              Relative PPP treats EUR/USD as a long-run valuation relationship: if U.S. prices and euro-area prices move differently over time, the exchange rate should eventually reflect that inflation differential.
            </Text>
            <Box bg="canvas" borderColor="edge" borderWidth="1px" p="5" rounded="panel">
              <Text fontFamily="heading" fontSize={{ base: "lg", md: "xl" }}>
                PPP_t = S_base * (CPI_US_t / CPI_US_base) / (CPI_EA_t / CPI_EA_base)
              </Text>
            </Box>
            <Stack gap="2">
              <Text color="muted" fontSize="sm">
                Base month
              </Text>
              <Box bg="canvas" borderColor="edge" borderWidth="1px" p="3" rounded="panel">
                <Text fontWeight="medium">{data.ppp.selectedBaseMonth ?? "No base month"}</Text>
              </Box>
              <Stack gap="2">
                {data.ppp.availableBaseMonths.map((baseMonth) => (
                  <Link asChild color={baseMonth === data.ppp.selectedBaseMonth ? "accent" : "muted"} key={baseMonth}>
                    <NextLink href={`/macro/currency-analysis?baseMonth=${encodeURIComponent(baseMonth)}`}>
                      {baseMonth}
                    </NextLink>
                  </Link>
                ))}
              </Stack>
            </Stack>
            {pppSummary ? (
              <Grid gap="4" templateColumns={{ base: "1fr", md: "repeat(4, minmax(0, 1fr))" }}>
                <Box bg="canvas" borderColor="edge" borderWidth="1px" p="4" rounded="panel">
                  <Text color="muted" fontSize="xs" textTransform="uppercase">
                    Base Spot
                  </Text>
                  <Text fontSize="xl" fontWeight="semibold">
                    {pppSummary.baseSpot}
                  </Text>
                </Box>
                <Box bg="canvas" borderColor="edge" borderWidth="1px" p="4" rounded="panel">
                  <Text color="muted" fontSize="xs" textTransform="uppercase">
                    Current Spot
                  </Text>
                  <Text fontSize="xl" fontWeight="semibold">
                    {pppSummary.currentSpot}
                  </Text>
                </Box>
                <Box bg="canvas" borderColor="edge" borderWidth="1px" p="4" rounded="panel">
                  <Text color="muted" fontSize="xs" textTransform="uppercase">
                    Implied PPP
                  </Text>
                  <Text fontSize="xl" fontWeight="semibold">
                    {pppSummary.impliedPpp}
                  </Text>
                </Box>
                <Box bg="canvas" borderColor="edge" borderWidth="1px" p="4" rounded="panel">
                  <Text color="muted" fontSize="xs" textTransform="uppercase">
                    Mispricing
                  </Text>
                  <Text fontSize="xl" fontWeight="semibold">
                    {pppSummary.deviationPct}%
                  </Text>
                </Box>
              </Grid>
            ) : null}
            <Box bg="canvas" borderColor="edge" borderWidth="1px" p="5" rounded="panel">
              <Stack gap="3">
                <Text color="muted" fontSize="sm">
                  Spot vs PPP path
                </Text>
                <Table.Root size="sm" variant="outline">
                  <Table.Header>
                    <Table.Row>
                      <Table.ColumnHeader>Month</Table.ColumnHeader>
                      <Table.ColumnHeader>Spot</Table.ColumnHeader>
                      <Table.ColumnHeader>PPP</Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {data.ppp.path.map((point) => (
                      <Table.Row key={`${point.observationMonth}-${point.impliedPpp}`}>
                        <Table.Cell>{point.observationMonth}</Table.Cell>
                        <Table.Cell>{point.actualSpot}</Table.Cell>
                        <Table.Cell>{point.impliedPpp}</Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Root>
              </Stack>
            </Box>
            {pppInterpretation ? (
              <Box bg="canvas" borderColor="edge" borderWidth="1px" p="5" rounded="panel">
                <Stack gap="2">
                  <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                    Analysis Takeaway
                  </Text>
                  <Text color="muted">{pppInterpretation}</Text>
                </Stack>
              </Box>
            ) : null}
            <Stack gap="2">
              <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                References
              </Text>
              {data.ppp.references.map((reference) => (
                <Link href={reference.url} key={`${reference.label}-${reference.url}`} target="_blank">
                  {reference.label}
                </Link>
              ))}
            </Stack>
          </Stack>
        </Box>
      ) : null}

      {irpSectionVisible ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
          <Stack gap="5">
            <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
              2.0 Interest Rate Parity
            </Text>
            <Heading as="h2" fontSize={{ base: "2xl", md: "3xl" }}>
              Interest Rate Parity
            </Heading>
            <Text color="muted">
              Interest rate parity links spot, tenor-specific rates, and forwards. In this view, covered interest parity is the main market anchor, while uncovered interest parity stays a lighter expectation framework underneath it.
            </Text>
            <Box bg="canvas" borderColor="edge" borderWidth="1px" p="5" rounded="panel">
              <Stack gap="2">
                <Text fontFamily="heading" fontSize={{ base: "lg", md: "xl" }}>
                  F = S * ((1 + r_EUR) / (1 + r_USD))
                </Text>
                <Text color="muted" fontSize="sm">
                  UIP approximation: (F - S) / S ~= r_EUR - r_USD
                </Text>
              </Stack>
            </Box>
            <Table.Root size="sm" variant="outline">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>Tenor</Table.ColumnHeader>
                  <Table.ColumnHeader>EUR Rate</Table.ColumnHeader>
                  <Table.ColumnHeader>USD Rate</Table.ColumnHeader>
                  <Table.ColumnHeader>Spread</Table.ColumnHeader>
                  <Table.ColumnHeader>Spot</Table.ColumnHeader>
                  <Table.ColumnHeader>CIP Implied Forward</Table.ColumnHeader>
                  <Table.ColumnHeader>Observed Forward</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {data.irp.cipRows.map((row) => (
                  <Table.Row key={row.tenor}>
                    <Table.Cell>{row.tenor}</Table.Cell>
                    <Table.Cell>{row.eurRate}%</Table.Cell>
                    <Table.Cell>{row.usdRate}%</Table.Cell>
                    <Table.Cell>{row.rateSpread}%</Table.Cell>
                    <Table.Cell>{row.spot}</Table.Cell>
                    <Table.Cell>{row.cipImpliedForward}</Table.Cell>
                    <Table.Cell>{row.observedForward ?? "Not available"}</Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
            <Box bg="canvas" borderColor="edge" borderWidth="1px" p="5" rounded="panel">
              <Stack gap="3">
                <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                  UIP Subsection
                </Text>
                <Text color="muted">
                  UIP is shown as a theoretical expectation lens rather than a hard market-pricing anchor.
                </Text>
                <Table.Root size="sm" variant="outline">
                  <Table.Header>
                    <Table.Row>
                      <Table.ColumnHeader>Tenor</Table.ColumnHeader>
                      <Table.ColumnHeader>Implied Move</Table.ColumnHeader>
                      <Table.ColumnHeader>Implied Spot</Table.ColumnHeader>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {data.irp.uip.rows.map((row) => (
                      <Table.Row key={`uip-${row.tenor}`}>
                        <Table.Cell>{row.tenor}</Table.Cell>
                        <Table.Cell>{row.impliedMovePct}%</Table.Cell>
                        <Table.Cell>{row.impliedSpot}</Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Root>
              </Stack>
            </Box>
            {irpInterpretation ? (
              <Box bg="canvas" borderColor="edge" borderWidth="1px" p="5" rounded="panel">
                <Stack gap="2">
                  <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                    Analysis Takeaway
                  </Text>
                  <Text color="muted">{irpInterpretation}</Text>
                </Stack>
              </Box>
            ) : null}
            <Stack gap="2">
              <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                References
              </Text>
              {data.irp.references.map((reference) => (
                <Link href={reference.url} key={`${reference.label}-${reference.url}`} target="_blank">
                  {reference.label}
                </Link>
              ))}
            </Stack>
          </Stack>
        </Box>
      ) : null}
    </Stack>
  );
}

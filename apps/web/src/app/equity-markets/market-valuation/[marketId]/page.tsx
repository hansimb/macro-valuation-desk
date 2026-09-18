import React from "react";
import NextLink from "next/link";
import { Box, Heading, Link, Stack, Text } from "@chakra-ui/react";

import type { EquityMarketValuationHistoryResponse } from "../../../../../../../packages/shared/src/contracts/equity-market-valuation";
import { MarketValuationMethodology } from "../../../../features/equity/market-valuation-methodology";
import { BackLink } from "../../../../features/site-shell/back-link";

async function getHistory(marketId: string): Promise<EquityMarketValuationHistoryResponse | null> {
  const apiBaseUrl = process.env.MVD_API_URL ?? process.env.API_BASE_URL ?? "http://127.0.0.1:4000";
  try {
    const response = await fetch(`${apiBaseUrl}/equity-markets/valuations/${encodeURIComponent(marketId)}`, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as EquityMarketValuationHistoryResponse;
  } catch {
    return null;
  }
}

export default async function MarketValuationHistoryPage({ params }: { params: Promise<{ marketId: string }> }) {
  const { marketId } = await params;
  const data = await getHistory(marketId);
  const marketName = data?.marketName ?? marketId.toUpperCase();
  return <Stack gap={{ base: "8", md: "10" }}>
    <Stack gap="4" maxW="4xl">
      <BackLink href="/equity-markets/market-valuation" label="Back to Market Valuation Dashboard" />
      <Text color="accent" textStyle="eyebrow">{data?.region ?? "Country valuation"}</Text>
      <Link asChild color="text" textDecoration="none" _hover={{ textDecoration: "none" }}><NextLink href={`/equity-markets/market-valuation/${marketId}`}><Heading as="h1" textStyle="hero">{marketName} valuation history</Heading></NextLink></Link>
      <Text color="muted" maxW="3xl" textStyle="subtitle">Weekly MVD country valuation ratios with their observed daily ranges, model sensitivity, cohort diagnostics, and source lineage.</Text>
    </Stack>
    {!data || data.observations.length === 0 ? <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel"><Text fontWeight="semibold">Valuation history is unavailable for this market.</Text><Text color="muted">No published weekly observations were returned for the requested country.</Text></Box> : <MarketValuationMethodology data={data} />}
  </Stack>;
}

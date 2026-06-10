import { notFound } from "next/navigation";
import { Box, Heading, Stack, Text } from "@chakra-ui/react";

import { BackLink } from "../../../features/site-shell/back-link";
import { equityMarketAnalyses } from "../../../features/site-shell/mvd-data";

export function generateStaticParams() {
  return equityMarketAnalyses.map((market) => ({ market: market.slug }));
}

export default async function EquityMarketDetailPage({
  params
}: {
  params: Promise<{ market: string }>;
}) {
  const { market } = await params;
  const current = equityMarketAnalyses.find((item) => item.slug === market);

  if (!current) {
    notFound();
  }

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <BackLink href="/equity-markets" label="Back to Equity Markets" />
        <Text color="accent" textStyle="eyebrow">
          {current.eyebrow}
        </Text>
        <Heading as="h1" textStyle="hero">
          {current.market}
        </Heading>
        <Text color="muted" maxW="4xl" textStyle="subtitle">
          {current.summary}
        </Text>
      </Stack>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="3">
          <Text color="accent" textStyle="eyebrow">
            Analysis
          </Text>
          <Text color="muted" textStyle="body">
            {current.flagEmoji} {current.region} | {current.ticker}
          </Text>
          <Text color="muted" textStyle="body">{current.methodologyNote}</Text>
        </Stack>
      </Box>
    </Stack>
  );
}

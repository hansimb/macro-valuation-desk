import { notFound } from "next/navigation";
import {
  Box,
  Heading,
  Stack,
  Text
} from "@chakra-ui/react";

import { equityCoverage } from "../../../features/site-shell/mvd-data";

export function generateStaticParams() {
  return equityCoverage.map((market) => ({ market: market.slug }));
}

export default async function EquityMarketDetailPage({
  params
}: {
  params: Promise<{ market: string }>;
}) {
  const { market } = await params;
  const current = equityCoverage.find((item) => item.slug === market);

  if (!current) {
    notFound();
  }

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Equity Market
        </Text>
        <Heading as="h1" fontSize={{ base: "4xl", md: "5xl" }} lineHeight="0.98">
          {current.market}
        </Heading>
        <Text color="muted" fontSize={{ base: "lg", md: "xl" }} maxW="4xl">
          Detailed market page placeholder for valuation history, methodology, and interpretation.
        </Text>
      </Stack>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="3">
          <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
            Analysis
          </Text>
          <Text color="muted">{current.region} · {current.ticker}</Text>
          <Text color="muted">Current posture: {current.posture}</Text>
        </Stack>
      </Box>
    </Stack>
  );
}

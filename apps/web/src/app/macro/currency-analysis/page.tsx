import React from "react";
import { Box, Heading, Stack, Text } from "@chakra-ui/react";

import { BackLink } from "../../../features/site-shell/back-link";
import { CurrencyAnalysisClient } from "../../../features/macro/currency-analysis-client";
import {
  emptyCurrencyAnalysisPageData,
  type CurrencyAnalysisPageData,
} from "../../../features/macro/currency-analysis-types";

async function getCurrencyAnalysisPageData(
  baseYear?: string,
): Promise<{ data: CurrencyAnalysisPageData; unavailable: boolean }> {
  const apiBaseUrl = process.env.MVD_API_URL ?? process.env.API_BASE_URL ?? "http://127.0.0.1:4000";
  const search = baseYear ? `?baseYear=${encodeURIComponent(baseYear)}` : "";

  try {
    const response = await fetch(`${apiBaseUrl}/macro/currency-analysis${search}`, { cache: "no-store" });

    if (!response.ok) {
      return { data: emptyCurrencyAnalysisPageData, unavailable: true };
    }

    const data = (await response.json()) as CurrencyAnalysisPageData;
    return {
      data,
      unavailable: data.ppp.summary === null,
    };
  } catch {
    return { data: emptyCurrencyAnalysisPageData, unavailable: true };
  }
}

export default async function CurrencyAnalysisPage({
  searchParams,
}: {
  searchParams?: Promise<{ baseYear?: string }>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const { data, unavailable } = await getCurrencyAnalysisPageData(resolvedSearchParams?.baseYear);

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <BackLink href="/macro" label="Back to Macro" />
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Macro FX
        </Text>
        <Heading as="h1" fontSize={{ base: "4xl", md: "5xl" }} lineHeight="0.98">
          Currency Analysis
        </Heading>
        <Text color="muted" fontSize={{ base: "lg", md: "xl" }} maxW="3xl">
          Open-methodology EUR/USD analysis through relative purchasing power parity.
        </Text>
        <Text color="muted" fontSize="sm">
          As of {data.asOf ?? "latest available update"}
        </Text>
      </Stack>

      {unavailable ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
          <Stack gap="2">
            <Text fontWeight="semibold">Live currency analysis data is unavailable right now.</Text>
            <Text color="muted">
              Start the API and run the currency analysis pipeline to populate current values.
            </Text>
          </Stack>
        </Box>
      ) : null}

      <CurrencyAnalysisClient data={data} />
    </Stack>
  );
}

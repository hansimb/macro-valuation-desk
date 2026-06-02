import React from "react";
import { Box, Heading, Stack, Text } from "@chakra-ui/react";

import { TaylorRuleClient } from "../../../features/macro/taylor-rule-client";
import { emptyTaylorRulePageData, type TaylorRulePageData } from "../../../features/macro/taylor-rule-types";
import { BackLink } from "../../../features/site-shell/back-link";

async function getTaylorRulePageData(): Promise<{ data: TaylorRulePageData; unavailable: boolean }> {
  const apiBaseUrl = process.env.MVD_API_URL ?? process.env.API_BASE_URL ?? "http://127.0.0.1:4000";

  try {
    const response = await fetch(`${apiBaseUrl}/macro/taylor-rule`, { cache: "no-store" });

    if (!response.ok) {
      return { data: emptyTaylorRulePageData, unavailable: true };
    }

    const data = (await response.json()) as TaylorRulePageData;
    return { data, unavailable: data.regions.length === 0 };
  } catch {
    return { data: emptyTaylorRulePageData, unavailable: true };
  }
}

export default async function TaylorRulePage() {
  const { data, unavailable } = await getTaylorRulePageData();

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <BackLink href="/macro" label="Back to Macro" />
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Macro policy
        </Text>
        <Heading as="h1" fontSize={{ base: "4xl", md: "5xl" }} lineHeight="0.98">
          Taylor Rule
        </Heading>
        <Text color="muted" fontSize={{ base: "lg", md: "xl" }} maxW="3xl">
          A compact policy benchmark comparing current rates against a simple Taylor-style rule for the U.S. and euro area.
        </Text>
        <Text color="muted" fontSize="sm">
          As of {data.asOf ?? "latest available update"}
        </Text>
      </Stack>

      {unavailable ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
          <Stack gap="2">
            <Text fontWeight="semibold">Live Taylor Rule data is unavailable right now.</Text>
            <Text color="muted">
              Start the API and run the Taylor Rule pipeline to populate current values.
            </Text>
          </Stack>
        </Box>
      ) : null}

      <TaylorRuleClient data={data} />
    </Stack>
  );
}

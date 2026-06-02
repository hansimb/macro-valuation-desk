import React from "react";
import { Heading, Stack, Text } from "@chakra-ui/react";

import { TaylorRuleClient } from "../../../features/macro/taylor-rule-client";
import { fallbackTaylorRulePageData, type TaylorRulePageData } from "../../../features/macro/taylor-rule-types";
import { BackLink } from "../../../features/site-shell/back-link";

async function getTaylorRulePageData(): Promise<TaylorRulePageData> {
  const apiBaseUrl = process.env.MVD_API_URL ?? "http://127.0.0.1:4000";

  try {
    const response = await fetch(`${apiBaseUrl}/macro/taylor-rule`, { cache: "no-store" });

    if (!response.ok) {
      return fallbackTaylorRulePageData;
    }

    return (await response.json()) as TaylorRulePageData;
  } catch {
    return fallbackTaylorRulePageData;
  }
}

export default async function TaylorRulePage() {
  const data = await getTaylorRulePageData();

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

      <TaylorRuleClient data={data} />
    </Stack>
  );
}

import React from "react";
import { Heading, Stack, Text } from "@chakra-ui/react";

import { EquityReturnExpectationClient } from "../../../features/equity/return-expectation-client";
import { BackLink } from "../../../features/site-shell/back-link";

export default function EquityReturnExpectationPage() {
  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <BackLink href="/equity-markets" label="Back to Equity Markets" />
        <Text color="accent" textStyle="eyebrow">
          Equity Valuation
        </Text>
        <Heading as="h1" textStyle="hero">
          Stock Return Expectation
        </Heading>
        <Text color="muted" maxW="3xl" textStyle="subtitle">
          Frontend-only calculator for dividend, earnings-yield, and free-cash-flow return models.
        </Text>
        <Text color="muted" textStyle="caption">
          Inputs are saved automatically in this browser.
        </Text>
      </Stack>

      <EquityReturnExpectationClient />
    </Stack>
  );
}

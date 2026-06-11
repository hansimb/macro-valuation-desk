"use client";

import React from "react";
import { Box, Stack, Text } from "@chakra-ui/react";

import { AnalysisFormulaTerms } from "./analysis-formula-terms";

const irpSymbolGuide = [
  {
    symbol: "F",
    meaning: "Forward exchange rate implied by covered interest parity for the selected tenor.",
  },
  {
    symbol: "S",
    meaning: "Current EUR/USD spot exchange rate.",
  },
  {
    symbol: "r_EUR",
    meaning: "EUR tenor-matched money-market or government-bill proxy rate.",
  },
  {
    symbol: "r_USD",
    meaning: "USD tenor-matched money-market or government-bill proxy rate.",
  },
  {
    symbol: "T",
    meaning: "Tenor expressed as a year fraction, such as 0.25 for 3M.",
  },
  {
    symbol: "E[S_T]",
    meaning: "UIP theoretical expected future spot level for the selected tenor.",
  },
];

export function CurrencyIrpFormulaBlock() {
  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" textStyle="eyebrow">
          Formula
        </Text>
        <Box bg="canvas" borderColor="edge" borderWidth="1px" overflowX="auto" p={{ base: "5", md: "6" }} rounded="panel">
          <Stack gap="3">
            <Text textAlign={{ base: "left", md: "center" }} textStyle="formula" whiteSpace="nowrap">
              F = S x ((1 + r_EUR x T) / (1 + r_USD x T))
            </Text>
            <Text color="muted" textAlign={{ base: "left", md: "center" }} textStyle="body" whiteSpace="nowrap">
              (F - S) / S ~= r_EUR - r_USD
            </Text>
            <Text color="muted" textAlign={{ base: "left", md: "center" }} textStyle="body" whiteSpace="nowrap">
              UIP framing: E[S_T] = S x (1 + (r_EUR - r_USD) x T)
            </Text>
          </Stack>
        </Box>
        <AnalysisFormulaTerms items={irpSymbolGuide} symbolColumnWidth={{ base: "4.25rem", md: "5rem" }} />
        <Text color="muted" textStyle="body">
          CIP translates spot and tenor-matched rate proxies into an implied forward. UIP uses the same rate spread as a theoretical expected-spot framing, not as a mechanical forecast.
        </Text>
      </Stack>
    </Box>
  );
}

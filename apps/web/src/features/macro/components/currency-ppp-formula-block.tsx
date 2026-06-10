"use client";

import React from "react";
import { Box, Stack, Text, VisuallyHidden } from "@chakra-ui/react";

import { AnalysisFormulaTerms } from "./analysis-formula-terms";

type PppSymbolKey = "PPP_t" | "S_0" | "P_h_t" | "P_h_0" | "P_f_t" | "P_f_0";

const pppSymbolGuide: { symbol: PppSymbolKey; meaning: string }[] = [
  {
    symbol: "S_0",
    meaning:
      "Base-period spot exchange rate (here: the selected long-run anchor value for EUR/USD under the chosen rule).",
  },
  {
    symbol: "P_h_t",
    meaning:
      "Home-country price level at time t (here: U.S. CPI index at observation month t).",
  },
  {
    symbol: "P_h_0",
    meaning:
      "Home-country price level in the base period (here: the selected long-run anchor value for U.S. CPI under the chosen rule).",
  },
  {
    symbol: "P_f_t",
    meaning:
      "Foreign-country price level at time t (here: euro area CPI index at observation month t).",
  },
  {
    symbol: "P_f_0",
    meaning:
      "Foreign-country price level in the base period (here: the selected long-run anchor value for euro-area CPI under the chosen rule).",
  },
  {
    symbol: "PPP_t",
    meaning:
      "PPP-implied exchange rate at time t (here: the model-implied EUR/USD fair-value anchor).",
  },
];

function MathToken({ symbol }: { symbol: PppSymbolKey }) {
  if (symbol === "PPP_t") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          PPP
        </Box>
        <Box
          as="sub"
          display="inline-block"
          fontSize="0.7em"
          transform="translateY(0.22em)"
        >
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
        <Box
          as="sub"
          display="inline-block"
          fontSize="0.7em"
          transform="translateY(0.22em)"
        >
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
        <Box
          as="sub"
          display="inline-block"
          fontSize="0.7em"
          transform="translateY(0.22em)"
        >
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
        <Box
          as="sub"
          display="inline-block"
          fontSize="0.7em"
          transform="translateY(0.22em)"
        >
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
        <Box
          as="sub"
          display="inline-block"
          fontSize="0.7em"
          transform="translateY(0.22em)"
        >
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
      <Box
        as="sub"
        display="inline-block"
        fontSize="0.7em"
        transform="translateY(0.22em)"
      >
        f,0
      </Box>
    </>
  );
}

export function CurrencyPppFormulaBlock() {
  return (
    <Box
      bg="surface"
      borderColor="edge"
      borderWidth="1px"
      p={{ base: "6", md: "7" }}
      rounded="panel"
    >
      <Stack gap="4">
        <Text
          color="accent"
          textStyle="eyebrow"
        >
          Formula
        </Text>
        <Box
          bg="canvas"
          borderColor="edge"
          borderWidth="1px"
          overflowX="auto"
          p={{ base: "5", md: "6" }}
          rounded="panel"
        >
          <VisuallyHidden>
            PPP_t = S_0 * (P_h_t / P_h_0) / (P_f_t / P_f_0)
          </VisuallyHidden>
          <Text
            textAlign={{ base: "left", md: "center" }}
            textStyle="formula"
            whiteSpace="nowrap"
          >
            <MathToken symbol="PPP_t" /> = <MathToken symbol="S_0" /> * (
            <MathToken symbol="P_h_t" /> / <MathToken symbol="P_h_0" />) / (
            <MathToken symbol="P_f_t" /> / <MathToken symbol="P_f_0" />)
          </Text>
        </Box>
        <AnalysisFormulaTerms
          items={pppSymbolGuide.map((item) => ({
            symbol: <MathToken symbol={item.symbol} />,
            meaning: item.meaning,
          }))}
        />
        <Stack borderColor="edge" borderTopWidth="1px" gap="2" pt="4">
          <Text
            color="accent"
            textStyle="eyebrow"
          >
            Methodology
          </Text>
          <Text color="muted" textStyle="body">
            1. For each eligible base month in the selected anchor sample, the
            model uses that month&apos;s own observed spot and CPI base values.
          </Text>
          <Text color="muted" textStyle="body">
            2. It calculates one current PPP-implied fair value from each of
            those base months using the relative-PPP formula above.
          </Text>
          <Text color="muted" textStyle="body">
            3. It aggregates those completed current fair values with the
            selected `average` or `median` rule, and then compares the latest
            observed spot with that aggregated fair value.
          </Text>
        </Stack>
      </Stack>
    </Box>
  );
}

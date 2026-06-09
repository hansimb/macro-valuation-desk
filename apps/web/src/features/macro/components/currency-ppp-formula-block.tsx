"use client";

import React from "react";
import { Box, Stack, Text, VisuallyHidden } from "@chakra-ui/react";

import { AnalysisFormulaTerms } from "./analysis-formula-terms";

type PppSymbolKey = "PPP_t" | "S_0" | "P_h_t" | "P_h_0" | "P_f_t" | "P_f_0";

const pppSymbolGuide: { symbol: PppSymbolKey; meaning: string }[] = [
  {
    symbol: "S_0",
    meaning: "Base-period spot exchange rate (here: the selected long-run anchor value for EUR/USD under the chosen rule).",
  },
  {
    symbol: "P_h_t",
    meaning: "Home-country price level at time t (here: U.S. CPI index at observation month t).",
  },
  {
    symbol: "P_h_0",
    meaning: "Home-country price level in the base period (here: the selected long-run anchor value for U.S. CPI under the chosen rule).",
  },
  {
    symbol: "P_f_t",
    meaning: "Foreign-country price level at time t (here: euro area CPI index at observation month t).",
  },
  {
    symbol: "P_f_0",
    meaning: "Foreign-country price level in the base period (here: the selected long-run anchor value for euro-area CPI under the chosen rule).",
  },
  {
    symbol: "PPP_t",
    meaning: "PPP-implied exchange rate at time t (here: the model-implied EUR/USD fair-value anchor).",
  },
];

function MathToken({ symbol }: { symbol: PppSymbolKey }) {
  if (symbol === "PPP_t") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          PPP
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
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
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
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
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
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
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
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
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
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
      <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
        f,0
      </Box>
    </>
  );
}

export function CurrencyPppFormulaBlock() {
  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Formula
        </Text>
        <Box bg="canvas" borderColor="edge" borderWidth="1px" overflowX="auto" p={{ base: "5", md: "6" }} rounded="panel">
          <VisuallyHidden>PPP_t = S_0 * (P_h_t / P_h_0) / (P_f_t / P_f_0)</VisuallyHidden>
          <Text
            fontFamily="heading"
            fontSize={{ base: "xl", md: "2xl" }}
            lineHeight="1.4"
            textAlign={{ base: "left", md: "center" }}
            whiteSpace="nowrap"
          >
            <MathToken symbol="PPP_t" /> = <MathToken symbol="S_0" /> * (<MathToken symbol="P_h_t" /> /{" "}
            <MathToken symbol="P_h_0" />) / (<MathToken symbol="P_f_t" /> / <MathToken symbol="P_f_0" />)
          </Text>
        </Box>
        <AnalysisFormulaTerms
          items={pppSymbolGuide.map((item) => ({
            symbol: <MathToken symbol={item.symbol} />,
            meaning: item.meaning,
          }))}
        />
        <Text color="muted" fontSize="sm">
          The model starts from the selected anchor rule for spot and CPI levels and then re-scales that anchor by the
          relative change in U.S. and euro-area CPI index levels.
        </Text>
      </Stack>
    </Box>
  );
}

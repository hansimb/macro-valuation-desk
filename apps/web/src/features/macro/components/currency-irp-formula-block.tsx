"use client";

import React from "react";
import { Box, Stack, Text, VisuallyHidden } from "@chakra-ui/react";

import { AnalysisFormulaTerms } from "./analysis-formula-terms";

type IrpSymbolKey = "F" | "S" | "r_EUR" | "r_USD" | "T" | "E_S_T";

const irpSymbolGuide: { symbol: IrpSymbolKey; meaning: string }[] = [
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
    symbol: "E_S_T",
    meaning: "UIP theoretical expected future spot level for the selected tenor.",
  },
];

function MathToken({ symbol }: { symbol: IrpSymbolKey }) {
  if (symbol === "r_EUR" || symbol === "r_USD") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          r
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
          {symbol === "r_EUR" ? "EUR" : "USD"}
        </Box>
      </>
    );
  }

  if (symbol === "E_S_T") {
    return (
      <>
        E[
        <Box as="span" fontStyle="italic">
          S
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
          T
        </Box>
        ]
      </>
    );
  }

  return (
    <Box as="span" fontStyle="italic">
      {symbol}
    </Box>
  );
}

export function CurrencyIrpFormulaBlock() {
  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" textStyle="eyebrow">
          Formula
        </Text>
        <Box bg="canvas" borderColor="edge" borderWidth="1px" overflowX="auto" p={{ base: "5", md: "6" }} rounded="panel">
          <VisuallyHidden>
            F = S x ((1 + r_EUR x T) / (1 + r_USD x T))
          </VisuallyHidden>
          <Stack gap="3">
            <Text textAlign={{ base: "left", md: "center" }} textStyle="formula" whiteSpace="nowrap">
              <MathToken symbol="F" /> = <MathToken symbol="S" /> x ((1 + <MathToken symbol="r_EUR" /> x{" "}
              <MathToken symbol="T" />) / (1 + <MathToken symbol="r_USD" /> x <MathToken symbol="T" />))
            </Text>
            <Text color="muted" textAlign={{ base: "left", md: "center" }} textStyle="body" whiteSpace="nowrap">
              (<MathToken symbol="F" /> - <MathToken symbol="S" />) / <MathToken symbol="S" /> ~={" "}
              <MathToken symbol="r_EUR" /> - <MathToken symbol="r_USD" />
            </Text>
            <Text color="muted" textAlign={{ base: "left", md: "center" }} textStyle="body" whiteSpace="nowrap">
              UIP framing:{" "}
              <MathToken symbol="E_S_T" /> = <MathToken symbol="S" /> x (1 + (<MathToken symbol="r_EUR" /> -{" "}
              <MathToken symbol="r_USD" />) x <MathToken symbol="T" />)
            </Text>
          </Stack>
        </Box>
        <AnalysisFormulaTerms
          items={irpSymbolGuide.map((item) => ({
            symbol: <MathToken symbol={item.symbol} />,
            meaning: item.meaning,
          }))}
          symbolColumnWidth={{ base: "4.25rem", md: "5rem" }}
        />
        <Text color="muted" textStyle="body">
          CIP translates spot and tenor-matched rate proxies into an implied forward. UIP uses the same rate spread as a theoretical expected-spot framing, not as a mechanical forecast.
        </Text>
      </Stack>
    </Box>
  );
}

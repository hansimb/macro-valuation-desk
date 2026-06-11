"use client";

import React from "react";
import { Box, SimpleGrid, Stack, Text, VisuallyHidden } from "@chakra-ui/react";

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

function FormulaLine({
  children,
  label,
}: {
  children: React.ReactNode;
  label: string;
}) {
  return (
    <Box bg="canvas" borderColor="edge" borderWidth="1px" p={{ base: "4", md: "5" }} rounded="panel">
      <Stack gap="2">
        <Text color="accent" textStyle="eyebrow">
          {label}
        </Text>
        <Text textStyle="formula" whiteSpace="nowrap">
          {children}
        </Text>
      </Stack>
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
          <Stack gap="3" minW="42rem">
            <FormulaLine label="CIP exact">
              <MathToken symbol="F" /> = <MathToken symbol="S" /> x ((1 + <MathToken symbol="r_EUR" /> x{" "}
              <MathToken symbol="T" />) / (1 + <MathToken symbol="r_USD" /> x <MathToken symbol="T" />))
            </FormulaLine>
            <FormulaLine label="Carry approximation">
              (<MathToken symbol="F" /> - <MathToken symbol="S" />) / <MathToken symbol="S" /> ~={" "}
              <MathToken symbol="r_EUR" /> - <MathToken symbol="r_USD" />
            </FormulaLine>
            <FormulaLine label="UIP framing">
              <MathToken symbol="E_S_T" /> = <MathToken symbol="S" /> x (1 + (<MathToken symbol="r_EUR" /> -{" "}
              <MathToken symbol="r_USD" />) x <MathToken symbol="T" />)
            </FormulaLine>
          </Stack>
        </Box>
        <SimpleGrid columns={{ base: 1, md: 2 }} gap="3">
          {irpSymbolGuide.map((item) => (
            <Box bg="canvas" borderColor="edge" borderWidth="1px" key={item.symbol} p="4" rounded="panel">
              <Stack gap="1.5">
                <Text color="text" fontFamily="heading" textStyle="body">
                  <MathToken symbol={item.symbol} />
                </Text>
                <Text color="muted" textStyle="body">
                  {item.meaning}
                </Text>
              </Stack>
            </Box>
          ))}
        </SimpleGrid>
        <Text color="muted" textStyle="body">
          CIP translates spot and tenor-matched rate proxies into an implied forward. UIP uses the same rate spread as a theoretical expected-spot framing, not as a mechanical forecast.
        </Text>
      </Stack>
    </Box>
  );
}

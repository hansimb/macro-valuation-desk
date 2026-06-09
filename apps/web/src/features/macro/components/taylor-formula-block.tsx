"use client";

import React from "react";
import { Box, Stack, Text } from "@chakra-ui/react";

import { AnalysisFormulaTerms } from "./analysis-formula-terms";

type SymbolKey = "i_t" | "r_t_star" | "pi_t" | "pi_t_star" | "y_t";

const symbolGuide: { symbol: SymbolKey; meaning: string }[] = [
  { symbol: "i_t", meaning: "Implied nominal policy rate from the rule." },
  { symbol: "r_t_star", meaning: "Neutral real rate assumption." },
  { symbol: "pi_t", meaning: "Current inflation rate." },
  { symbol: "pi_t_star", meaning: "Inflation target." },
  { symbol: "y_t", meaning: "Slack or output-gap proxy." },
];

function MathSymbol({ symbol }: { symbol: SymbolKey }) {
  if (symbol === "i_t") {
    return (
      <>
        <Box as="span" fontStyle="italic">i</Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">t</Box>
      </>
    );
  }

  if (symbol === "r_t_star") {
    return (
      <>
        <Box as="span" fontStyle="italic">r</Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">t</Box>
        <Box as="sup" display="inline-block" fontSize="0.7em" transform="translateY(-0.15em)">*</Box>
      </>
    );
  }

  if (symbol === "pi_t") {
    return (
      <>
        <Box as="span" fontStyle="italic">pi</Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">t</Box>
      </>
    );
  }

  if (symbol === "pi_t_star") {
    return (
      <>
        <Box as="span" fontStyle="italic">pi</Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">t</Box>
        <Box as="sup" display="inline-block" fontSize="0.7em" transform="translateY(-0.15em)">*</Box>
      </>
    );
  }

  return (
    <>
      <Box as="span" fontStyle="italic">y</Box>
      <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">t</Box>
    </>
  );
}

export function TaylorFormulaBlock() {
  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Formula
        </Text>
        <Box bg="canvas" borderColor="edge" borderWidth="1px" overflowX="auto" p={{ base: "5", md: "6" }} rounded="panel">
          <Text
            fontFamily="heading"
            fontSize={{ base: "2xl", md: "3xl" }}
            lineHeight="1.3"
            textAlign={{ base: "left", md: "center" }}
            whiteSpace="nowrap"
          >
            <MathSymbol symbol="i_t" /> = <MathSymbol symbol="pi_t" /> + <MathSymbol symbol="r_t_star" /> + 0.5(
            <MathSymbol symbol="pi_t" /> - <MathSymbol symbol="pi_t_star" />) + 0.5<MathSymbol symbol="y_t" />
          </Text>
        </Box>
        <AnalysisFormulaTerms
          items={symbolGuide.map((item) => ({
            symbol: <MathSymbol symbol={item.symbol} />,
            meaning: item.meaning,
          }))}
        />
        <Text color="muted">
          Policy rate and inflation come from source data. In this view, the assumptions are adjusted separately for the euro area and the United States.
        </Text>
      </Stack>
    </Box>
  );
}

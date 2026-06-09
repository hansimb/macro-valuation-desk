"use client";

import React from "react";
import { Grid, Text } from "@chakra-ui/react";

type FormulaTermItem = {
  symbol: React.ReactNode;
  meaning: string;
};

export function AnalysisFormulaTerms({
  items,
  symbolColumnWidth = { base: "2.25rem", md: "2.75rem" },
}: {
  items: FormulaTermItem[];
  symbolColumnWidth?: { base: string; md: string };
}) {
  return (
    <Grid
      alignItems="start"
      columnGap={{ base: "1", md: "1.5" }}
      rowGap="2"
      templateColumns={{ base: `${symbolColumnWidth.base} minmax(0, 1fr)`, md: `${symbolColumnWidth.md} minmax(0, 1fr)` }}
    >
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <Text color="text" fontFamily="heading" fontSize="sm" whiteSpace="nowrap">
            {item.symbol}
          </Text>
          <Text color="muted" fontSize="sm">
            {item.meaning}
          </Text>
        </React.Fragment>
      ))}
    </Grid>
  );
}

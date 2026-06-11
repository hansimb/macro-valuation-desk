"use client";

import React from "react";
import { Box, SimpleGrid, Stack, Text } from "@chakra-ui/react";

import { AnalysisCitationLinks, type AnalysisCitationRef } from "./analysis-citation-links";

type IrpInputRef = {
  label: string;
  ref?: AnalysisCitationRef;
};

export function CurrencyIrpDataInputsBlock({
  asOf,
  inputs,
}: {
  asOf: string | null;
  inputs: IrpInputRef[];
}) {
  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" textStyle="eyebrow">
          Data Inputs And Proxy Notes
        </Text>
        <Text color="muted" textStyle="body">
          EUR/USD spot is the latest available daily reference rate. EUR rates use compounded euro short-term average rate tenor proxies. USD rates use Treasury bill secondary market rate proxies. Observed forwards are shown only when a reliable forward series is present.
        </Text>
        <SimpleGrid columns={{ base: 1, md: 2 }} gap="3">
          {inputs.map((input) => (
            <Box bg="canvas" borderColor="edge" borderWidth="1px" key={input.label} p="4" rounded="panel">
              <Text color="text" fontWeight="semibold" textStyle="body">
                {input.label}
                {input.ref ? <AnalysisCitationLinks refs={[input.ref]} /> : null}
              </Text>
            </Box>
          ))}
        </SimpleGrid>
        <Text color="muted" textStyle="caption">
          Latest IRP observation date: {asOf ?? "not available"}.
        </Text>
      </Stack>
    </Box>
  );
}

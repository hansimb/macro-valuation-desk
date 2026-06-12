"use client";

import React from "react";
import { Box, SimpleGrid, Stack, Text } from "@chakra-ui/react";

import { AnalysisCitationLinks, type AnalysisCitationRef } from "./analysis-citation-links";

type IrpInputRef = {
  label: string;
  ref?: AnalysisCitationRef;
};

type IrpInputRow = {
  tenor: string;
  asOf: string;
  spot: string;
  eurRate: string;
  usdRate: string;
};

function referenceForLabel(inputs: IrpInputRef[], label: string) {
  return inputs.find((input) => input.label === label)?.ref;
}

function RateInputCard({
  label,
  value,
  note,
  ref,
}: {
  label: string;
  value: string;
  note: string;
  ref?: AnalysisCitationRef;
}) {
  return (
    <Box bg="canvas" borderColor="edge" borderWidth="1px" p="4" rounded="panel">
      <Stack gap="2">
        <Text color="muted" textStyle="eyebrow">
          {label}
          {ref ? <AnalysisCitationLinks refs={[ref]} /> : null}
        </Text>
        <Text color="text" fontWeight="semibold" textStyle="metric">
          {value}
        </Text>
        <Text color="muted" textStyle="caption">
          {note}
        </Text>
      </Stack>
    </Box>
  );
}

export function CurrencyIrpDataInputsBlock({
  asOf,
  inputs,
  rows,
}: {
  asOf: string | null;
  inputs: IrpInputRef[];
  rows: IrpInputRow[];
}) {
  if (rows.length === 0) {
    return null;
  }

  const spotRef = referenceForLabel(inputs, "EUR/USD spot");
  const cards = [
    {
      label: "EUR/USD spot",
      value: rows[0].spot,
      note: `Spot input used for the ${rows[0].tenor} CIP calculation.`,
      ref: spotRef,
    },
    ...rows.flatMap((row) => [
      {
        label: `EUR ${row.tenor} rate`,
        value: `${row.eurRate}%`,
        note: `EUR tenor-matched rate proxy as of ${row.asOf}.`,
        ref: referenceForLabel(inputs, `EUR ${row.tenor} rate`),
      },
      {
        label: `USD ${row.tenor} rate`,
        value: `${row.usdRate}%`,
        note: `USD tenor-matched rate proxy as of ${row.asOf}.`,
        ref: referenceForLabel(inputs, `USD ${row.tenor} rate`),
      },
    ]),
  ];

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
          {cards.map((card) => (
            <RateInputCard
              key={card.label}
              label={card.label}
              note={card.note}
              ref={card.ref}
              value={card.value}
            />
          ))}
        </SimpleGrid>
        <Text color="muted" textStyle="caption">
          Latest IRP observation date: {asOf ?? "not available"}.
        </Text>
      </Stack>
    </Box>
  );
}

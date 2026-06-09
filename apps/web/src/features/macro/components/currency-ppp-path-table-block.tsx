"use client";

import React from "react";
import { Box, Stack, Table, Text } from "@chakra-ui/react";

import { AnalysisCitationLinks, type AnalysisCitationRef } from "./analysis-citation-links";

type PathRow = {
  actualSpotLabel: string;
  gapDisplayLabel: string;
  impliedPppLabel: string;
  monthLabel: string;
  observationMonth: string;
};

export function CurrencyPppPathTableBlock({
  pppInputRefs,
  rows,
  spotRef,
}: {
  pppInputRefs?: AnalysisCitationRef[];
  rows: PathRow[];
  spotRef?: AnalysisCitationRef;
}) {
  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          Selected PPP Path
        </Text>
        <Text color="muted" fontSize="sm">
          Each row compares the observed EUR/USD spot with the PPP-implied level generated from the selected anchor rule.
        </Text>
        <Table.Root size="sm" variant="outline">
          <Table.Header bg="#a4a4a4">
            <Table.Row>
              <Table.ColumnHeader>Month</Table.ColumnHeader>
              <Table.ColumnHeader>
                Observed spot
                {spotRef ? <AnalysisCitationLinks refs={[spotRef]} /> : null}
              </Table.ColumnHeader>
              <Table.ColumnHeader>
                PPP-implied level (calculated)
                {pppInputRefs?.length ? <AnalysisCitationLinks refs={pppInputRefs} /> : null}
              </Table.ColumnHeader>
              <Table.ColumnHeader>Valuation gap %</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {rows.map((point) => (
              <Table.Row key={`${point.observationMonth}-${point.impliedPppLabel}`}>
                <Table.Cell>{point.monthLabel}</Table.Cell>
                <Table.Cell>{point.actualSpotLabel}</Table.Cell>
                <Table.Cell>{point.impliedPppLabel}</Table.Cell>
                <Table.Cell>{point.gapDisplayLabel}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
        <Text color="muted" fontSize="xs">
          Rows marked with * use at least one filled observation based on a +/- 6 month median assumption.
        </Text>
      </Stack>
    </Box>
  );
}

"use client";

import React from "react";
import { Box, Stack, Table, Text } from "@chakra-ui/react";

type CurrencyIrpTenorRow = {
  tenor: string;
  asOf: string;
  spot: string;
  eurRate: string;
  usdRate: string;
  rateSpread: string;
  cipImpliedForward: string;
  observedForward?: string;
  cipBasisBps?: string;
  hasObservedForward: boolean;
};

export function CurrencyIrpTenorTableBlock({
  rows,
}: {
  rows: CurrencyIrpTenorRow[];
}) {
  const primaryRow = rows[0];
  const hasObservedForwardColumn = rows.some((row) => row.hasObservedForward && Boolean(row.observedForward));
  const hasCipGapColumn = rows.some((row) => row.hasObservedForward && Boolean(row.cipBasisBps));
  const takeaway =
    primaryRow && Number.parseFloat(primaryRow.rateSpread) < 0
      ? "EUR rates sit below USD rates across the shown tenor set, so CIP implies forward EUR/USD levels below spot. This is a forward-pricing relationship, not a standalone spot forecast."
      : "The tenor-rate spread determines whether CIP-implied forwards sit above or below spot. This is a forward-pricing relationship, not a standalone spot forecast.";

  if (rows.length === 0) {
    return null;
  }

  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" textStyle="eyebrow">
          CIP Tenor Comparison
        </Text>
        <Text color="muted" textStyle="body">
          The table compares tenor-matched rate differentials with the forward level implied by covered interest parity. Observed-forward columns appear only when validated forward-market observations are available.
        </Text>
        <Box overflowX="auto">
          <Table.Root minW="56rem" size="sm" variant="outline">
            <Table.Header bg="#a4a4a4">
              <Table.Row>
                <Table.ColumnHeader>Tenor</Table.ColumnHeader>
                <Table.ColumnHeader>EUR/USD spot</Table.ColumnHeader>
                <Table.ColumnHeader>EUR rate</Table.ColumnHeader>
                <Table.ColumnHeader>USD rate</Table.ColumnHeader>
                <Table.ColumnHeader>Spread</Table.ColumnHeader>
                <Table.ColumnHeader>CIP-implied forward</Table.ColumnHeader>
                {hasObservedForwardColumn ? <Table.ColumnHeader>Observed forward</Table.ColumnHeader> : null}
                {hasCipGapColumn ? <Table.ColumnHeader>CIP gap</Table.ColumnHeader> : null}
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {rows.map((row) => (
                <Table.Row key={row.tenor}>
                  <Table.Cell>{row.tenor}</Table.Cell>
                  <Table.Cell>{row.spot}</Table.Cell>
                  <Table.Cell>{row.eurRate}%</Table.Cell>
                  <Table.Cell>{row.usdRate}%</Table.Cell>
                  <Table.Cell>{row.rateSpread}%</Table.Cell>
                  <Table.Cell>{row.cipImpliedForward}</Table.Cell>
                  {hasObservedForwardColumn ? <Table.Cell>{row.hasObservedForward ? row.observedForward : ""}</Table.Cell> : null}
                  {hasCipGapColumn ? <Table.Cell>{row.hasObservedForward && row.cipBasisBps ? `${row.cipBasisBps} bps` : ""}</Table.Cell> : null}
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
        </Box>
        <Stack borderColor="edge" borderTopWidth="1px" gap="2" pt="4">
          <Text color="accent" textStyle="eyebrow">
            Analysis Takeaway
          </Text>
          <Text color="muted" textStyle="body">
            {takeaway}
          </Text>
        </Stack>
      </Stack>
    </Box>
  );
}

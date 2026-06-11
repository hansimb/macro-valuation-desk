"use client";

import React from "react";
import { Box, Stack, Table, Text } from "@chakra-ui/react";

type CurrencyIrpUipRow = {
  tenor: string;
  impliedMovePct: string;
  impliedSpot: string;
};

export function CurrencyIrpUipBlock({
  rows,
}: {
  rows: CurrencyIrpUipRow[];
}) {
  if (rows.length === 0) {
    return null;
  }

  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" textStyle="eyebrow">
          UIP Theoretical Framing
        </Text>
        <Text color="muted" textStyle="body">
          UIP is shown as a theoretical expected-spot framing, not as a mechanical forecast. It asks what spot move would offset the interest-rate differential if investors were comparing uncovered returns.
        </Text>
        <Table.Root size="sm" variant="outline">
          <Table.Header bg="#a4a4a4">
            <Table.Row>
              <Table.ColumnHeader>Tenor</Table.ColumnHeader>
              <Table.ColumnHeader>Theoretical move</Table.ColumnHeader>
              <Table.ColumnHeader>UIP-implied spot</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {rows.map((row) => (
              <Table.Row key={row.tenor}>
                <Table.Cell>{row.tenor}</Table.Cell>
                <Table.Cell>{row.impliedMovePct}%</Table.Cell>
                <Table.Cell>{row.impliedSpot}</Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Stack>
    </Box>
  );
}

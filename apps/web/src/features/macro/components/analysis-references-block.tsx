"use client";

import React from "react";
import { Box, Link, Stack, Text } from "@chakra-ui/react";

export type AnalysisReferenceLine = {
  href?: string;
  key: string;
  note?: string;
  text: string;
};

export function AnalysisReferencesBlock({
  items,
}: {
  items: AnalysisReferenceLine[];
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
          References
        </Text>
        {items.map((item) => (
          <Box key={item.key}>
            {item.href ? (
              <Link color="text" href={item.href} target="_blank">
                {item.text}
              </Link>
            ) : (
              <Text>{item.text}</Text>
            )}
            {item.note ? (
              <Text color="muted" fontSize="sm">
                {item.note}
              </Text>
            ) : null}
          </Box>
        ))}
      </Stack>
    </Box>
  );
}

"use client";

import React from "react";
import { Box, Stack, Text } from "@chakra-ui/react";

export function AnalysisMetricCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: React.ReactNode;
}) {
  return (
    <Box bg="canvas" borderColor="edge" borderWidth="1px" minH="11.5rem" p="4" rounded="panel">
      <Stack align="stretch" gap="3" h="100%">
        <Text
          color="muted"
          fontSize="xs"
          letterSpacing="0.08em"
          h="2.5rem"
          textTransform="uppercase"
        >
          {label}
        </Text>
        <Text
          alignSelf="center"
          flex="1"
          display="flex"
          alignItems="center"
          justifyContent="center"
          fontSize={{ base: "xl", md: "1.75rem" }}
          fontWeight="semibold"
          lineHeight="1"
          textAlign="center"
        >
          {value}
        </Text>
        <Box
          h={{ base: "3.8rem", md: "3.2rem" }}
          display="flex"
          alignItems="flex-start"
          justifyContent="center"
        >
          <Text color="muted" fontSize="xs" lineHeight="1.35" textAlign="center">
            {note ?? ""}
          </Text>
        </Box>
      </Stack>
    </Box>
  );
}

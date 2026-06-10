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
          letterSpacing="0.08em"
          h="2.5rem"
          textStyle="eyebrow"
        >
          {label}
        </Text>
        <Text
          alignSelf="center"
          flex="1"
          display="flex"
          alignItems="center"
          justifyContent="center"
          fontWeight="semibold"
          textAlign="center"
          textStyle="metric"
        >
          {value}
        </Text>
        <Box
          h={{ base: "3.8rem", md: "3.2rem" }}
          display="flex"
          alignItems="flex-start"
          justifyContent="center"
        >
          <Text color="muted" textAlign="center" textStyle="caption">
            {note ?? ""}
          </Text>
        </Box>
      </Stack>
    </Box>
  );
}

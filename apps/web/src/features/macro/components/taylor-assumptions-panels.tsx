"use client";

import React from "react";
import { Box, Button, Heading, HStack, SimpleGrid, Stack, Text } from "@chakra-ui/react";

import type { TaylorRuleRegionComparison } from "../taylor-rule-types";

type RegionAssumptions = {
  inflationMeasure: "headline" | "core";
  neutralRate: string;
  slackProxy: string;
};

function regionReferenceHeading(region: string) {
  return region === "US" ? "USA" : region;
}

function InflationMeasureSwitch({
  regionLabel,
  value,
  onChange,
}: {
  regionLabel: string;
  value: "headline" | "core";
  onChange: (nextValue: "headline" | "core") => void;
}) {
  const isCore = value === "core";

  return (
    <Button
      aria-checked={isCore}
      aria-label={`${regionLabel} inflation input`}
      bg="canvas"
      borderColor="edge"
      borderRadius="full"
      borderWidth="1px"
      h="3rem"
      onClick={() => onChange(isCore ? "headline" : "core")}
      p="1"
      position="relative"
      role="switch"
      w="100%"
    >
      <Box
        bg="surfaceElevated"
        borderRadius="full"
        bottom="1"
        boxShadow="sm"
        left={isCore ? "calc(50% + 0.125rem)" : "0.25rem"}
        position="absolute"
        top="1"
        transition="left 0.18s ease"
        width="calc(50% - 0.25rem)"
      />
      <HStack justify="space-between" position="relative" px="2" w="100%">
        <Text color={isCore ? "muted" : "text"} flex="1" fontSize="sm" fontWeight={isCore ? "medium" : "semibold"} textAlign="center">
          Headline CPI
        </Text>
        <Text color={isCore ? "text" : "muted"} flex="1" fontSize="sm" fontWeight={isCore ? "semibold" : "medium"} textAlign="center">
          Core CPI
        </Text>
      </HStack>
    </Button>
  );
}

export function TaylorAssumptionsPanels({
  assumptionsByRegion,
  onAdjust,
  onSetInflationMeasure,
  regions,
}: {
  assumptionsByRegion: Record<string, RegionAssumptions>;
  onAdjust: (region: string, field: "neutralRate" | "slackProxy", delta: number) => void;
  onSetInflationMeasure: (region: string, inflationMeasure: "headline" | "core") => void;
  regions: TaylorRuleRegionComparison[];
}) {
  return (
    <SimpleGrid columns={{ base: 1, md: 2 }} gap="6">
      {regions.map((region) => {
        const assumptions = assumptionsByRegion[region.region];

        return (
          <Box key={`${region.region}-assumptions`} bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="4">
              <Heading as="h3" fontSize={{ base: "xl", md: "2xl" }}>
                {regionReferenceHeading(region.region)} assumptions
              </Heading>
              <Stack gap="4">
                <Stack gap="2">
                  <Text color="muted" fontSize="sm">
                    Inflation input
                  </Text>
                  <InflationMeasureSwitch
                    onChange={(inflationMeasure) => onSetInflationMeasure(region.region, inflationMeasure)}
                    regionLabel={regionReferenceHeading(region.region)}
                    value={assumptions.inflationMeasure}
                  />
                </Stack>
                <Stack gap="2">
                  <Text color="muted" fontSize="sm">
                    Neutral rate
                  </Text>
                  <HStack justify="space-between">
                    <Button aria-label={`Decrease ${regionReferenceHeading(region.region)} neutral rate`} bg="transparent" borderColor="edge" borderWidth="1px" onClick={() => onAdjust(region.region, "neutralRate", -0.25)}>
                      Decrease
                    </Button>
                    <Text fontSize="lg" fontWeight="semibold" minW="4.5rem" textAlign="center">
                      {assumptions.neutralRate}
                    </Text>
                    <Button aria-label={`Increase ${regionReferenceHeading(region.region)} neutral rate`} bg="transparent" borderColor="edge" borderWidth="1px" onClick={() => onAdjust(region.region, "neutralRate", 0.25)}>
                      Increase
                    </Button>
                  </HStack>
                </Stack>
                <Stack gap="2">
                  <Text color="muted" fontSize="sm">
                    Slack proxy
                  </Text>
                  <HStack justify="space-between">
                    <Button aria-label={`Decrease ${regionReferenceHeading(region.region)} slack proxy`} bg="transparent" borderColor="edge" borderWidth="1px" onClick={() => onAdjust(region.region, "slackProxy", -0.25)}>
                      Decrease
                    </Button>
                    <Text fontSize="lg" fontWeight="semibold" minW="4.5rem" textAlign="center">
                      {assumptions.slackProxy}
                    </Text>
                    <Button aria-label={`Increase ${regionReferenceHeading(region.region)} slack proxy`} bg="transparent" borderColor="edge" borderWidth="1px" onClick={() => onAdjust(region.region, "slackProxy", 0.25)}>
                      Increase
                    </Button>
                  </HStack>
                </Stack>
              </Stack>
            </Stack>
          </Box>
        );
      })}
    </SimpleGrid>
  );
}

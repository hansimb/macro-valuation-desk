"use client";

import React from "react";
import { Box, Heading, SimpleGrid, Stack, Text } from "@chakra-ui/react";

import type { TaylorRuleRegionComparison } from "../taylor-rule-types";
import { AnalysisCitationLinks, type AnalysisCitationRef } from "./analysis-citation-links";

type RegionAssumptions = {
  inflationMeasure: "headline" | "core";
  neutralRate: string;
  slackProxy: string;
};

function regionReferenceHeading(region: string) {
  return region === "US" ? "United States" : "Euro Area";
}

export function TaylorScenarioPanels({
  assumptionsByRegion,
  getInterpretation,
  getReferenceLookup,
  getScenario,
  getSelectedInflationValue,
  regions,
}: {
  assumptionsByRegion: Record<string, RegionAssumptions>;
  getInterpretation: (region: TaylorRuleRegionComparison, assumptions: RegionAssumptions) => string;
  getReferenceLookup: (region: TaylorRuleRegionComparison) => {
    core?: AnalysisCitationRef;
    headline?: AnalysisCitationRef;
    policy?: AnalysisCitationRef;
  };
  getScenario: (region: TaylorRuleRegionComparison, assumptions: RegionAssumptions) => { impliedRate: string; policyGap: string };
  getSelectedInflationValue: (region: TaylorRuleRegionComparison, inflationMeasure: "headline" | "core") => string;
  regions: TaylorRuleRegionComparison[];
}) {
  return (
    <SimpleGrid columns={{ base: 1, md: 2 }} gap="6">
      {regions.map((region) => {
        const assumptions = assumptionsByRegion[region.region];
        const refs = getReferenceLookup(region);
        const scenario = getScenario(region, assumptions);
        const interpretation = getInterpretation(region, assumptions);

        return (
          <Box key={region.region} bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="4">
              <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                {region.region}
              </Text>
              <Heading as="h3" fontSize={{ base: "2xl", md: "3xl" }}>
                {regionReferenceHeading(region.region)}
              </Heading>
              <SimpleGrid columns={2} gap="3">
                <Text color="muted">
                  Policy rate
                  {refs.policy ? <AnalysisCitationLinks refs={[refs.policy]} /> : null}
                </Text>
                <Text>{region.policyRate}%</Text>
                <Text color="muted">
                  {assumptions.inflationMeasure === "core" ? "Core CPI" : "Headline CPI"}
                  {assumptions.inflationMeasure === "core" && refs.core ? <AnalysisCitationLinks refs={[refs.core]} /> : null}
                  {assumptions.inflationMeasure === "headline" && refs.headline ? <AnalysisCitationLinks refs={[refs.headline]} /> : null}
                </Text>
                <Text>{getSelectedInflationValue(region, assumptions.inflationMeasure)}%</Text>
                <Text color="muted">Target</Text>
                <Text>{region.target}%</Text>
                <Text color="muted">Scenario implied</Text>
                <Text>{scenario.impliedRate}%</Text>
                <Text color="muted">Scenario gap</Text>
                <Text>{scenario.policyGap}%</Text>
              </SimpleGrid>
              <Text color="muted" fontSize="sm">
                Interpretation: {interpretation}
              </Text>
            </Stack>
          </Box>
        );
      })}
    </SimpleGrid>
  );
}

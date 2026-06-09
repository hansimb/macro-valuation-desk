"use client";

import React from "react";
import { Box, Heading, SimpleGrid, Stack, Text } from "@chakra-ui/react";

import type {
  TaylorRuleGrowthMetric,
  TaylorRuleMetricPoint,
  TaylorRulePageData,
  TaylorRuleRegionComparison,
} from "../taylor-rule-types";
import { AnalysisCitationLinks, type AnalysisCitationRef } from "./analysis-citation-links";

function ReferenceMetric({
  label,
  value,
  meta,
}: {
  label: React.ReactNode;
  value: string;
  meta: string;
}) {
  return (
    <Stack gap="1">
      <Text color="muted" fontSize="xs" letterSpacing="0.08em" textTransform="uppercase">
        {label}
      </Text>
      <Text fontSize="lg" fontWeight="semibold" lineHeight="1.1">
        {value}
      </Text>
      <Text color="muted" fontSize="xs" lineHeight="1.3">
        {meta}
      </Text>
    </Stack>
  );
}

function formatPointValue(metric: TaylorRuleMetricPoint) {
  return `${metric.value}%`;
}

function formatGrowthValue(metric: TaylorRuleGrowthMetric, key: "current" | "historicalAverage" | "gap") {
  return `${metric[key]}%`;
}

function regionReferenceHeading(region: string) {
  return region === "US" ? "USA" : region;
}

function outputGapIsForecast(referenceUrl: string | undefined) {
  return referenceUrl?.includes("db.nomics.world") ?? false;
}

type ReferenceLookup = {
  core?: { href?: string; number: number };
  gdp?: { href?: string; number: number };
  headline?: { href?: string; number: number };
  market?: { href?: string; number: number };
  output?: { href?: string; number: number };
  policy?: { href?: string; number: number };
};

export function TaylorReferencePanels({
  getReferenceLookup,
  regions,
}: {
  getReferenceLookup: (region: TaylorRuleRegionComparison) => ReferenceLookup;
  regions: TaylorRuleRegionComparison[];
}) {
  const referenceRegions = regions.filter((region) => region.referenceMetrics);
  if (referenceRegions.length === 0) {
    return null;
  }

  return (
    <SimpleGrid columns={{ base: 1, md: 2 }} gap="6">
      {referenceRegions.map((region) => {
        const metrics = region.referenceMetrics;
        const refs = getReferenceLookup(region);

        if (!metrics) {
          return null;
        }

        return (
          <Box
            key={`${region.region}-reference-metrics`}
            bg="surface"
            borderColor="edge"
            borderWidth="1px"
            p={{ base: "6", md: "7" }}
            rounded="panel"
          >
            <Stack gap="4">
              <Heading as="h3" fontSize={{ base: "xl", md: "2xl" }}>
                {regionReferenceHeading(region.region)}
              </Heading>
              <SimpleGrid columns={2} gap={{ base: "4", md: "5" }}>
                <ReferenceMetric
                  label={
                    <>
                      CPI
                      {refs.headline ? <AnalysisCitationLinks refs={[refs.headline]} /> : null}
                    </>
                  }
                  meta={metrics.headlineInflation.asOf}
                  value={formatPointValue(metrics.headlineInflation)}
                />
                <ReferenceMetric
                  label={
                    <>
                      Core CPI
                      {refs.core ? <AnalysisCitationLinks refs={[refs.core]} /> : null}
                    </>
                  }
                  meta={metrics.coreInflation.asOf}
                  value={formatPointValue(metrics.coreInflation)}
                />
                <ReferenceMetric
                  label={
                    <>
                      Policy real rate
                      {refs.policy && refs.headline ? <AnalysisCitationLinks refs={[refs.policy, refs.headline]} /> : null}
                    </>
                  }
                  meta={metrics.policyRealRate.asOf}
                  value={formatPointValue(metrics.policyRealRate)}
                />
                <ReferenceMetric
                  label={
                    <>
                      Market real rate
                      {refs.market ? <AnalysisCitationLinks refs={[refs.market]} /> : null}
                    </>
                  }
                  meta={metrics.marketRealRate.asOf}
                  value={formatPointValue(metrics.marketRealRate)}
                />
                <ReferenceMetric
                  label={
                    <>
                      GDP YoY growth
                      {refs.gdp ? <AnalysisCitationLinks refs={[refs.gdp]} /> : null}
                    </>
                  }
                  meta={metrics.gdpGrowthYoy.asOf}
                  value={formatGrowthValue(metrics.gdpGrowthYoy, "current")}
                />
                <ReferenceMetric
                  label={
                    <>
                      GDP YoY Avg
                      {refs.gdp ? <AnalysisCitationLinks refs={[refs.gdp]} /> : null}
                    </>
                  }
                  meta={metrics.gdpGrowthYoy.historyWindow}
                  value={formatGrowthValue(metrics.gdpGrowthYoy, "historicalAverage")}
                />
                <ReferenceMetric
                  label={
                    <>
                      GDP YoY growth gap
                      {refs.gdp ? <AnalysisCitationLinks refs={[refs.gdp]} /> : null}
                    </>
                  }
                  meta={`${metrics.gdpGrowthYoy.asOf} vs avg`}
                  value={formatGrowthValue(metrics.gdpGrowthYoy, "gap")}
                />
                <ReferenceMetric
                  label={
                    <>
                      Output gap
                      {refs.output ? <AnalysisCitationLinks refs={[refs.output]} /> : null}
                    </>
                  }
                  meta={outputGapIsForecast(refs.output?.href) ? `${metrics.outputGap.asOf} forecast` : metrics.outputGap.asOf}
                  value={formatPointValue(metrics.outputGap)}
                />
              </SimpleGrid>
            </Stack>
          </Box>
        );
      })}
    </SimpleGrid>
  );
}

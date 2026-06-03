"use client";

import React, { useState } from "react";
import {
  Box,
  Button,
  Heading,
  HStack,
  Input,
  Link,
  SimpleGrid,
  Stack,
  Text
} from "@chakra-ui/react";

import type {
  TaylorRuleGrowthMetric,
  TaylorRuleMetricPoint,
  TaylorRulePageData,
  TaylorRuleRegionComparison
} from "./taylor-rule-types";

type ScenarioKey = "base" | "dovish" | "hawkish";
type SymbolKey = "i_t" | "r_t_star" | "pi_t" | "pi_t_star" | "y_t";

const scenarioPresets: Record<ScenarioKey, { neutralRate: string; slackProxy: string }> = {
  base: { neutralRate: "1.00", slackProxy: "0.00" },
  dovish: { neutralRate: "0.50", slackProxy: "-0.50" },
  hawkish: { neutralRate: "1.50", slackProxy: "0.50" }
};

const symbolGuide: { symbol: SymbolKey; meaning: string }[] = [
  { symbol: "i_t", meaning: "Implied nominal policy rate from the rule." },
  { symbol: "r_t_star", meaning: "Neutral real rate assumption." },
  { symbol: "pi_t", meaning: "Current inflation rate." },
  { symbol: "pi_t_star", meaning: "Inflation target." },
  { symbol: "y_t", meaning: "Slack or output-gap proxy." }
];

function toNumber(value: string) {
  return Number.parseFloat(value);
}

function calculateScenario(region: TaylorRuleRegionComparison, neutralRate: string, slackProxy: string) {
  const inflation = toNumber(region.inflation);
  const target = toNumber(region.target);
  const actualPolicyRate = toNumber(region.policyRate);
  const parsedNeutralRate = toNumber(neutralRate);
  const parsedSlackProxy = toNumber(slackProxy);
  const impliedRate = parsedNeutralRate + inflation + 0.5 * (inflation - target) + 0.5 * parsedSlackProxy;
  const policyGap = actualPolicyRate - impliedRate;

  return {
    impliedRate: impliedRate.toFixed(2),
    policyGap: policyGap.toFixed(2)
  };
}

function buildInterpretation(regions: TaylorRuleRegionComparison[], neutralRate: string, slackProxy: string) {
  const lines = regions.map((region) => {
    const scenario = calculateScenario(region, neutralRate, slackProxy);
    const gap = toNumber(scenario.policyGap);

    if (gap >= 0) {
      return `${region.region} screens tighter than the rule benchmark by ${scenario.policyGap} percentage points.`;
    }

    return `${region.region} screens easier than the rule benchmark by ${Math.abs(gap).toFixed(2)} percentage points.`;
  });

  return lines.join(" ");
}

function MathSymbol({ symbol }: { symbol: SymbolKey }) {
  if (symbol === "i_t") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          i
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">
          t
        </Box>
      </>
    );
  }

  if (symbol === "r_t_star") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          r
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">
          t
        </Box>
        <Box as="sup" display="inline-block" fontSize="0.7em" transform="translateY(-0.15em)">
          *
        </Box>
      </>
    );
  }

  if (symbol === "pi_t") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          π
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">
          t
        </Box>
      </>
    );
  }

  if (symbol === "pi_t_star") {
    return (
      <>
        <Box as="span" fontStyle="italic">
          π
        </Box>
        <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">
          t
        </Box>
        <Box as="sup" display="inline-block" fontSize="0.7em" transform="translateY(-0.15em)">
          *
        </Box>
      </>
    );
  }

  return (
    <>
      <Box as="span" fontStyle="italic">
        y
      </Box>
      <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.2em)">
        t
      </Box>
    </>
  );
}

function ReferenceMetric({
  label,
  value,
  meta
}: {
  label: string;
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

function regionSourceSummary(region: TaylorRuleRegionComparison) {
  return region.sourceNames.join(", ");
}

export function TaylorRuleClient({ data }: { data: TaylorRulePageData }) {
  const [neutralRate, setNeutralRate] = useState(data.assumptions.neutralRate);
  const [slackProxy, setSlackProxy] = useState(data.assumptions.slackProxy);
  const interpretation = buildInterpretation(data.regions, neutralRate, slackProxy);
  const referenceRegions = data.regions.filter((region) => region.referenceMetrics);
  const hasRegionData = data.regions.length > 0;
  const hasReferences = data.references.length > 0;

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="4">
          <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
            Formula
          </Text>
          <Box
            bg="canvas"
            borderColor="edge"
            borderWidth="1px"
            overflowX="auto"
            p={{ base: "5", md: "6" }}
            rounded="panel"
          >
            <Text
              fontFamily="heading"
              fontSize={{ base: "2xl", md: "3xl" }}
              lineHeight="1.3"
              textAlign={{ base: "left", md: "center" }}
              whiteSpace="nowrap"
            >
              <MathSymbol symbol="i_t" /> = <MathSymbol symbol="pi_t" /> + <MathSymbol symbol="r_t_star" /> + 0.5(
              <MathSymbol symbol="pi_t" /> - <MathSymbol symbol="pi_t_star" />) + 0.5
              <MathSymbol symbol="y_t" />
            </Text>
          </Box>
          <Stack gap="2">
            {symbolGuide.map((item) => (
              <Text key={item.symbol} color="muted" fontSize="sm">
                <Box as="span" color="text" fontFamily="heading" mr="2">
                  <MathSymbol symbol={item.symbol} />
                </Box>
                {item.meaning}
              </Text>
            ))}
          </Stack>
          <Text color="muted">
            Policy rate and inflation come from source data. In this view, the scenario controls only move the neutral
            rate and slack proxy assumptions.
          </Text>
        </Stack>
      </Box>

      {referenceRegions.length > 0 ? (
        <SimpleGrid columns={{ base: 1, md: 2 }} gap="6">
          {referenceRegions.map((region) => {
            const metrics = region.referenceMetrics;

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
                      label="CPI"
                      meta={metrics.headlineInflation.asOf}
                      value={formatPointValue(metrics.headlineInflation)}
                    />
                    <ReferenceMetric
                      label="Core"
                      meta={metrics.coreInflation.asOf}
                      value={formatPointValue(metrics.coreInflation)}
                    />
                    <ReferenceMetric
                      label="Policy real rate"
                      meta={metrics.policyRealRate.asOf}
                      value={formatPointValue(metrics.policyRealRate)}
                    />
                    <ReferenceMetric
                      label="Market real rate"
                      meta={metrics.marketRealRate.asOf}
                      value={formatPointValue(metrics.marketRealRate)}
                    />
                    <ReferenceMetric
                      label="GDP YoY"
                      meta={metrics.gdpGrowthYoy.asOf}
                      value={formatGrowthValue(metrics.gdpGrowthYoy, "current")}
                    />
                    <ReferenceMetric
                      label="YoY Avg"
                      meta={metrics.gdpGrowthYoy.historyWindow}
                      value={formatGrowthValue(metrics.gdpGrowthYoy, "historicalAverage")}
                    />
                    <ReferenceMetric
                      label="YoY Gap"
                      meta={`${metrics.gdpGrowthYoy.asOf} vs avg`}
                      value={formatGrowthValue(metrics.gdpGrowthYoy, "gap")}
                    />
                    <ReferenceMetric
                      label="GDP q/q ann."
                      meta={metrics.gdpGrowthQoqAnnualized.asOf}
                      value={formatGrowthValue(metrics.gdpGrowthQoqAnnualized, "current")}
                    />
                    <ReferenceMetric
                      label="q/q Avg"
                      meta={metrics.gdpGrowthQoqAnnualized.historyWindow}
                      value={formatGrowthValue(metrics.gdpGrowthQoqAnnualized, "historicalAverage")}
                    />
                    <ReferenceMetric
                      label="q/q Gap"
                      meta={`${metrics.gdpGrowthQoqAnnualized.asOf} vs avg`}
                      value={formatGrowthValue(metrics.gdpGrowthQoqAnnualized, "gap")}
                    />
                  </SimpleGrid>
                  <Text color="muted" fontSize="xs">
                    Source: {regionSourceSummary(region)}
                  </Text>
                </Stack>
              </Box>
            );
          })}
        </SimpleGrid>
      ) : null}

      {hasRegionData ? (
        <>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap="6">
            <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
              <Stack gap="4">
                <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                  Assumptions
                </Text>
                <HStack align="end" gap="4">
                  <Stack flex="1" gap="2">
                    <Text color="muted" fontSize="sm">
                      Neutral rate r*
                    </Text>
                    <Input value={neutralRate} onChange={(event) => setNeutralRate(event.target.value)} type="number" />
                  </Stack>
                  <Stack flex="1" gap="2">
                    <Text color="muted" fontSize="sm">
                      Slack proxy
                    </Text>
                    <Input value={slackProxy} onChange={(event) => setSlackProxy(event.target.value)} type="number" />
                  </Stack>
                </HStack>
                <HStack gap="3" wrap="wrap">
                  {(["base", "dovish", "hawkish"] as ScenarioKey[]).map((scenarioKey) => (
                    <Button
                      key={scenarioKey}
                      bg="transparent"
                      borderColor="edge"
                      borderWidth="1px"
                      onClick={() => {
                        setNeutralRate(scenarioPresets[scenarioKey].neutralRate);
                        setSlackProxy(scenarioPresets[scenarioKey].slackProxy);
                      }}
                    >
                      {scenarioKey.charAt(0).toUpperCase() + scenarioKey.slice(1)}
                    </Button>
                  ))}
                </HStack>
              </Stack>
            </Box>

            <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
              <Stack gap="4">
                <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                  Interpretation
                </Text>
                <Text color="muted">{interpretation}</Text>
              </Stack>
            </Box>
          </SimpleGrid>

          <SimpleGrid columns={{ base: 1, md: 2 }} gap="6">
            {data.regions.map((region) => {
              const scenario = calculateScenario(region, neutralRate, slackProxy);

              return (
                <Box
                  key={region.region}
                  bg="surface"
                  borderColor="edge"
                  borderWidth="1px"
                  p={{ base: "6", md: "7" }}
                  rounded="panel"
                >
                  <Stack gap="4">
                    <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
                      {region.region}
                    </Text>
                    <Heading as="h3" fontSize={{ base: "2xl", md: "3xl" }}>
                      {region.region === "US" ? "United States" : "Euro Area"}
                    </Heading>
                    <SimpleGrid columns={2} gap="3">
                      <Text color="muted">Policy rate</Text>
                      <Text>{region.policyRate}%</Text>
                      <Text color="muted">Inflation</Text>
                      <Text>{region.inflation}%</Text>
                      <Text color="muted">Target</Text>
                      <Text>{region.target}%</Text>
                      <Text color="muted">Scenario implied</Text>
                      <Text>{scenario.impliedRate}%</Text>
                      <Text color="muted">Scenario gap</Text>
                      <Text>{scenario.policyGap}%</Text>
                    </SimpleGrid>
                  </Stack>
                </Box>
              );
            })}
          </SimpleGrid>
        </>
      ) : null}

      {hasReferences ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
          <Stack gap="4">
            <Text color="accent" fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">
              References
            </Text>
            {data.references.map((reference) => (
              <Box key={reference.label}>
                {reference.url ? (
                  <Link color="text" href={reference.url} target="_blank">
                    {reference.label}
                  </Link>
                ) : (
                  <Text>{reference.label}</Text>
                )}
                {reference.note ? (
                  <Text color="muted" fontSize="sm">
                    {reference.note}
                  </Text>
                ) : null}
              </Box>
            ))}
          </Stack>
        </Box>
      ) : null}
    </Stack>
  );
}

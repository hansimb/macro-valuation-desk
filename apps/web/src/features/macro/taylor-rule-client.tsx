"use client";

import React, { useEffect, useState } from "react";
import { Box, Button, Heading, HStack, Link, SimpleGrid, Stack, Text } from "@chakra-ui/react";

import type {
  TaylorRuleGrowthMetric,
  TaylorRuleMetricPoint,
  TaylorRuleReferenceItem,
  TaylorRulePageData,
  TaylorRuleRegionComparison
} from "./taylor-rule-types";

type SymbolKey = "i_t" | "r_t_star" | "pi_t" | "pi_t_star" | "y_t";
type RegionAssumptions = {
  neutralRate: string;
  slackProxy: string;
  inflationMeasure: "headline" | "core";
};

const ADJUSTMENT_STEP = 0.25;
const ASSUMPTIONS_STORAGE_KEY = "taylor-rule-assumptions-v1";

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

function formatAdjustmentValue(value: number) {
  return value.toFixed(2);
}

function selectedInflationValue(region: TaylorRuleRegionComparison, inflationMeasure: "headline" | "core") {
  if (inflationMeasure === "core" && region.referenceMetrics) {
    return region.referenceMetrics.coreInflation.value;
  }

  if (inflationMeasure === "headline" && region.referenceMetrics) {
    return region.referenceMetrics.headlineInflation.value;
  }

  return region.inflation;
}

function calculateScenario(
  region: TaylorRuleRegionComparison,
  neutralRate: string,
  slackProxy: string,
  inflationMeasure: "headline" | "core"
) {
  const inflation = toNumber(selectedInflationValue(region, inflationMeasure));
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

function buildInterpretation(
  region: TaylorRuleRegionComparison,
  neutralRate: string,
  slackProxy: string,
  inflationMeasure: "headline" | "core"
) {
  const scenario = calculateScenario(region, neutralRate, slackProxy, inflationMeasure);
  const gap = toNumber(scenario.policyGap);

  if (gap >= 0) {
    return `${region.region} screens tighter than the rule benchmark by ${scenario.policyGap} percentage points.`;
  }

  return `${region.region} screens easier than the rule benchmark by ${Math.abs(gap).toFixed(2)} percentage points.`;
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

function buildInitialAssumptions(regions: TaylorRuleRegionComparison[]) {
  return regions.reduce<Record<string, RegionAssumptions>>((accumulator, region) => {
    accumulator[region.region] = {
      neutralRate: "0.00",
      slackProxy: "0.00",
      inflationMeasure: "headline"
    };
    return accumulator;
  }, {});
}

function adjustValue(currentValue: string, delta: number) {
  return formatAdjustmentValue(toNumber(currentValue) + delta);
}

function isRegionAssumptions(value: unknown): value is RegionAssumptions {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<RegionAssumptions>;
  return (
    typeof candidate.neutralRate === "string" &&
    typeof candidate.slackProxy === "string" &&
    (candidate.inflationMeasure === "headline" || candidate.inflationMeasure === "core")
  );
}

function mergePersistedAssumptions(
  regions: TaylorRuleRegionComparison[],
  persisted: unknown
): Record<string, RegionAssumptions> {
  const defaults = buildInitialAssumptions(regions);

  if (!persisted || typeof persisted !== "object") {
    return defaults;
  }

  const persistedRecord = persisted as Record<string, unknown>;

  return Object.keys(defaults).reduce<Record<string, RegionAssumptions>>((accumulator, regionKey) => {
    accumulator[regionKey] = isRegionAssumptions(persistedRecord[regionKey])
      ? persistedRecord[regionKey]
      : defaults[regionKey];
    return accumulator;
  }, {});
}

function academicReferenceText(label: string, url?: string) {
  if (url?.includes("data.ecb.europa.eu")) {
    return `European Central Bank, Data Portal, "${label}"`;
  }

  if (url?.includes("db.nomics.world")) {
    return `European Commission, AMECO (via DBnomics), "${label}"`;
  }

  return `Federal Reserve Bank of St. Louis, FRED, "${label}"`;
}

function ieeeReferenceText(index: number, reference: TaylorRuleReferenceItem) {
  const sourceText = academicReferenceText(reference.label, reference.url);

  if (!reference.url) {
    return `[${index}] ${sourceText}.`;
  }

  return `[${index}] ${sourceText}. [Online]. Available: ${reference.url}.`;
}

function labelReference(
  region: TaylorRuleRegionComparison,
  kind: "policy" | "inflation" | "core" | "market" | "output" | "gdp"
) {
  if (kind === "policy") {
    return `${region.region} policy rate`;
  }

  if (kind === "inflation") {
    return `${region.region} inflation`;
  }

  if (kind === "core") {
    return `${region.region} core inflation`;
  }

  if (kind === "market") {
    return `${region.region} market real rate`;
  }

  if (kind === "output") {
    return `${region.region} output gap`;
  }

  return `${region.region} GDP growth proxy`;
}

function outputGapIsForecast(referenceUrl: string | undefined) {
  return referenceUrl?.includes("db.nomics.world") ?? false;
}

function Citation({
  numbers,
  href,
}: {
  numbers: number[];
  href?: string;
}) {
  const content = numbers.map((number) => `[${number}]`).join("");

  if (href) {
    return (
      <Link color="accent" display="inline" fontSize="0.8em" href={href} ml="1" target="_blank">
        {content}
      </Link>
    );
  }

  return (
    <Box as="span" color="accent" fontSize="0.8em" ml="1">
      {content}
    </Box>
  );
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
        <Text
          color={isCore ? "muted" : "text"}
          flex="1"
          fontSize="sm"
          fontWeight={isCore ? "medium" : "semibold"}
          textAlign="center"
        >
          Headline CPI
        </Text>
        <Text
          color={isCore ? "text" : "muted"}
          flex="1"
          fontSize="sm"
          fontWeight={isCore ? "semibold" : "medium"}
          textAlign="center"
        >
          Core CPI
        </Text>
      </HStack>
    </Button>
  );
}

export function TaylorRuleClient({ data }: { data: TaylorRulePageData }) {
  const [assumptionsByRegion, setAssumptionsByRegion] = useState<Record<string, RegionAssumptions>>(
    buildInitialAssumptions(data.regions)
  );
  const referenceRegions = data.regions.filter((region) => region.referenceMetrics);
  const hasRegionData = data.regions.length > 0;
  const hasReferences = data.references.length > 0;
  const referenceNumberByLabel = new Map(data.references.map((reference, index) => [reference.label, index + 1]));

  function updateRegionAssumption(regionKey: string, field: keyof RegionAssumptions, delta: number) {
    setAssumptionsByRegion((current) => ({
      ...current,
      [regionKey]: {
        ...current[regionKey],
        [field]: adjustValue(current[regionKey][field], delta)
      }
    }));
  }

  useEffect(() => {
    try {
      const persisted = window.localStorage.getItem(ASSUMPTIONS_STORAGE_KEY);
      if (!persisted) {
        return;
      }

      setAssumptionsByRegion(mergePersistedAssumptions(data.regions, JSON.parse(persisted)));
    } catch {
      setAssumptionsByRegion(buildInitialAssumptions(data.regions));
    }
  }, [data.regions]);

  useEffect(() => {
    window.localStorage.setItem(ASSUMPTIONS_STORAGE_KEY, JSON.stringify(assumptionsByRegion));
  }, [assumptionsByRegion]);

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
            Policy rate and inflation come from source data. In this view, the assumptions are adjusted separately for
            the euro area and the United States.
          </Text>
        </Stack>
      </Box>

      {referenceRegions.length > 0 ? (
        <SimpleGrid columns={{ base: 1, md: 2 }} gap="6">
          {referenceRegions.map((region) => {
            const metrics = region.referenceMetrics;
            const headlineReference = referenceNumberByLabel.get(labelReference(region, "inflation"));
            const coreReference = referenceNumberByLabel.get(labelReference(region, "core"));
            const policyReference = referenceNumberByLabel.get(labelReference(region, "policy"));
            const marketReference = referenceNumberByLabel.get(labelReference(region, "market"));
            const outputReference = referenceNumberByLabel.get(labelReference(region, "output"));
            const gdpReference = referenceNumberByLabel.get(labelReference(region, "gdp"));
            const headlineReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "inflation"));
            const coreReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "core"));
            const policyReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "policy"));
            const marketReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "market"));
            const outputReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "output"));
            const gdpReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "gdp"));

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
                          {headlineReference ? (
                            <Citation href={headlineReferenceItem?.url} numbers={[headlineReference]} />
                          ) : null}
                        </>
                      }
                      meta={metrics.headlineInflation.asOf}
                      value={formatPointValue(metrics.headlineInflation)}
                    />
                    <ReferenceMetric
                      label={
                        <>
                          Core CPI
                          {coreReference ? <Citation href={coreReferenceItem?.url} numbers={[coreReference]} /> : null}
                        </>
                      }
                      meta={metrics.coreInflation.asOf}
                      value={formatPointValue(metrics.coreInflation)}
                    />
                    <ReferenceMetric
                      label={
                        <>
                          Policy real rate
                          {policyReference && headlineReference ? (
                            <Citation href={policyReferenceItem?.url} numbers={[policyReference, headlineReference]} />
                          ) : null}
                        </>
                      }
                      meta={metrics.policyRealRate.asOf}
                      value={formatPointValue(metrics.policyRealRate)}
                    />
                    <ReferenceMetric
                      label={
                        <>
                          Market real rate
                          {marketReference ? (
                            <Citation href={marketReferenceItem?.url} numbers={[marketReference]} />
                          ) : null}
                        </>
                      }
                      meta={metrics.marketRealRate.asOf}
                      value={formatPointValue(metrics.marketRealRate)}
                    />
                    <ReferenceMetric
                      label={
                        <>
                          GDP YoY growth
                          {gdpReference ? <Citation href={gdpReferenceItem?.url} numbers={[gdpReference]} /> : null}
                        </>
                      }
                      meta={metrics.gdpGrowthYoy.asOf}
                      value={formatGrowthValue(metrics.gdpGrowthYoy, "current")}
                    />
                    <ReferenceMetric
                      label={
                        <>
                          GDP YoY Avg
                          {gdpReference ? <Citation href={gdpReferenceItem?.url} numbers={[gdpReference]} /> : null}
                        </>
                      }
                      meta={metrics.gdpGrowthYoy.historyWindow}
                      value={formatGrowthValue(metrics.gdpGrowthYoy, "historicalAverage")}
                    />
                    <ReferenceMetric
                      label={
                        <>
                          GDP YoY growth gap
                          {gdpReference ? <Citation href={gdpReferenceItem?.url} numbers={[gdpReference]} /> : null}
                        </>
                      }
                      meta={`${metrics.gdpGrowthYoy.asOf} vs avg`}
                      value={formatGrowthValue(metrics.gdpGrowthYoy, "gap")}
                    />
                    <ReferenceMetric
                      label={
                        <>
                          Output gap
                          {outputReference ? (
                            <Citation href={outputReferenceItem?.url} numbers={[outputReference]} />
                          ) : null}
                        </>
                      }
                      meta={
                        outputGapIsForecast(outputReferenceItem?.url)
                          ? `${metrics.outputGap.asOf} forecast`
                          : metrics.outputGap.asOf
                      }
                      value={formatPointValue(metrics.outputGap)}
                    />
                  </SimpleGrid>
                </Stack>
              </Box>
            );
          })}
        </SimpleGrid>
      ) : null}

      {hasRegionData ? (
        <>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap="6">
            {data.regions.map((region) => {
              const assumptions = assumptionsByRegion[region.region];

              return (
                <Box
                  key={`${region.region}-assumptions`}
                  bg="surface"
                  borderColor="edge"
                  borderWidth="1px"
                  p={{ base: "6", md: "7" }}
                  rounded="panel"
                >
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
                          onChange={(inflationMeasure) =>
                            setAssumptionsByRegion((current) => ({
                              ...current,
                              [region.region]: {
                                ...current[region.region],
                                inflationMeasure
                              }
                            }))
                          }
                          regionLabel={regionReferenceHeading(region.region)}
                          value={assumptions.inflationMeasure}
                        />
                      </Stack>
                      <Stack gap="2">
                        <Text color="muted" fontSize="sm">
                          Neutral rate
                        </Text>
                        <HStack justify="space-between">
                          <Button
                            aria-label={`Decrease ${regionReferenceHeading(region.region)} neutral rate`}
                            bg="transparent"
                            borderColor="edge"
                            borderWidth="1px"
                            onClick={() => updateRegionAssumption(region.region, "neutralRate", -ADJUSTMENT_STEP)}
                          >
                            Decrease
                          </Button>
                          <Text fontSize="lg" fontWeight="semibold" minW="4.5rem" textAlign="center">
                            {assumptions.neutralRate}
                          </Text>
                          <Button
                            aria-label={`Increase ${regionReferenceHeading(region.region)} neutral rate`}
                            bg="transparent"
                            borderColor="edge"
                            borderWidth="1px"
                            onClick={() => updateRegionAssumption(region.region, "neutralRate", ADJUSTMENT_STEP)}
                          >
                            Increase
                          </Button>
                        </HStack>
                      </Stack>
                      <Stack gap="2">
                        <Text color="muted" fontSize="sm">
                          Slack proxy
                        </Text>
                        <HStack justify="space-between">
                          <Button
                            aria-label={`Decrease ${regionReferenceHeading(region.region)} slack proxy`}
                            bg="transparent"
                            borderColor="edge"
                            borderWidth="1px"
                            onClick={() => updateRegionAssumption(region.region, "slackProxy", -ADJUSTMENT_STEP)}
                          >
                            Decrease
                          </Button>
                          <Text fontSize="lg" fontWeight="semibold" minW="4.5rem" textAlign="center">
                            {assumptions.slackProxy}
                          </Text>
                          <Button
                            aria-label={`Increase ${regionReferenceHeading(region.region)} slack proxy`}
                            bg="transparent"
                            borderColor="edge"
                            borderWidth="1px"
                            onClick={() => updateRegionAssumption(region.region, "slackProxy", ADJUSTMENT_STEP)}
                          >
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

          <SimpleGrid columns={{ base: 1, md: 2 }} gap="6">
            {data.regions.map((region) => {
              const assumptions = assumptionsByRegion[region.region];
              const policyReference = referenceNumberByLabel.get(labelReference(region, "policy"));
              const headlineReference = referenceNumberByLabel.get(labelReference(region, "inflation"));
              const coreReference = referenceNumberByLabel.get(labelReference(region, "core"));
              const policyReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "policy"));
              const headlineReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "inflation"));
              const coreReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "core"));
              const scenario = calculateScenario(
                region,
                assumptions.neutralRate,
                assumptions.slackProxy,
                assumptions.inflationMeasure
              );
              const interpretation = buildInterpretation(
                region,
                assumptions.neutralRate,
                assumptions.slackProxy,
                assumptions.inflationMeasure
              );

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
                      <Text color="muted">
                        Policy rate
                        {policyReference ? <Citation href={policyReferenceItem?.url} numbers={[policyReference]} /> : null}
                      </Text>
                      <Text>{region.policyRate}%</Text>
                      <Text color="muted">
                        {assumptions.inflationMeasure === "core" ? "Core CPI" : "Headline CPI"}
                        {assumptions.inflationMeasure === "core" && coreReference ? (
                          <Citation href={coreReferenceItem?.url} numbers={[coreReference]} />
                        ) : null}
                        {assumptions.inflationMeasure === "headline" && headlineReference ? (
                          <Citation href={headlineReferenceItem?.url} numbers={[headlineReference]} />
                        ) : null}
                      </Text>
                      <Text>{selectedInflationValue(region, assumptions.inflationMeasure)}%</Text>
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
                    {ieeeReferenceText(referenceNumberByLabel.get(reference.label) ?? 0, reference)}
                  </Link>
                ) : (
                  <Text>{ieeeReferenceText(referenceNumberByLabel.get(reference.label) ?? 0, reference)}</Text>
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

"use client";

import React from "react";
import { Box, Flex, Heading, SimpleGrid, Stack, Text } from "@chakra-ui/react";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { EquityMarketValuationHistoryResponse, MvdCountryValuationMetric } from "../../../../../packages/shared/src/contracts/equity-market-valuation";
import { AnalysisCitationLinks, type AnalysisCitationRef } from "../macro/components/analysis-citation-links";
import { AnalysisReferencesBlock, type AnalysisReferenceLine } from "../macro/components/analysis-references-block";

const metricLabels: Record<string, string> = { pe: "P/E", pb: "P/B", ps: "P/S", pcf: "P/CF", pfcf: "Exact P/FCF", dividend_yield: "Dividend yield" };

function formatValue(value: string | null, key: string) {
  if (value === null) return "Unavailable";
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return "Unavailable";
  return key === "dividend_yield" ? `${(parsed * 100).toFixed(2)}%` : parsed.toFixed(2);
}

function range(lower: string | null, upper: string | null, key: string) {
  return lower !== null && upper !== null ? `${formatValue(lower, key)}–${formatValue(upper, key)}` : "Unavailable";
}

function buildReferences(data: EquityMarketValuationHistoryResponse) {
  const lines: AnalysisReferenceLine[] = [];
  const citations = new Map<string, AnalysisCitationRef>();
  data.references.forEach((reference, index) => {
    const number = index + 1;
    if (reference.id) citations.set(reference.id, { number, href: reference.url ?? undefined });
    lines.push({
      key: reference.id ?? `${reference.label}-${number}`,
      href: reference.url ?? undefined,
      text: reference.url ? `[${number}] ${reference.label}. [Online]. Available: ${reference.url}.` : `[${number}] ${reference.label}.`,
      note: reference.url ? undefined : "Methodology reference supplied by the MVD publication metadata; no external URL was provided.",
    });
  });
  return { lines, citations };
}

function refsFor(metric: MvdCountryValuationMetric, citations: Map<string, AnalysisCitationRef>) {
  return metric.referenceIds.flatMap((id) => citations.has(id) ? [citations.get(id)!] : []);
}

type HistoryChartDatum = {
  week: string;
  value: number | null;
  weeklyMin: number | null;
  weeklyMax: number | null;
  sensitivityRange: [number, number] | null;
};

function HistoryChart({ data, label, marketName, metricKey }: { data: HistoryChartDatum[]; label: string; marketName: string; metricKey: string }) {
  return <Box bg="canvas" borderColor="edge" borderWidth="1px" p={{ base: "3", md: "5" }} rounded="panel">
    <Box aria-label={`${marketName} ${label} weekly valuation history`} h={{ base: "260px", md: "340px" }} role="img" w="100%">
      <ResponsiveContainer height="100%" minHeight={260} minWidth={280} width="100%">
        <ComposedChart data={data} margin={{ top: 12, right: 12, bottom: 8, left: 4 }}>
          <CartesianGrid horizontal stroke="rgba(126,145,168,0.16)" strokeDasharray="4 8" vertical={false} />
          <XAxis dataKey="week" stroke="#aeb7c5" tick={{ fill: "#aeb7c5", fontSize: 12 }} tickMargin={10} />
          <YAxis stroke="#aeb7c5" tick={{ fill: "#aeb7c5", fontSize: 12 }} tickFormatter={(value: number) => metricKey === "dividend_yield" ? `${(value * 100).toFixed(1)}%` : value.toFixed(1)} width={58} />
          <Tooltip formatter={(value) => formatValue(String(value), metricKey)} />
          <Area dataKey="sensitivityRange" fill="#7fb0ff" fillOpacity={0.16} stroke="#7fb0ff" strokeOpacity={0.35} type="monotone" />
          <Line dataKey="weeklyMax" dot={false} isAnimationActive={false} stroke="#e6b566" strokeDasharray="5 5" strokeWidth={1.5} type="monotone" />
          <Line dataKey="weeklyMin" dot={false} isAnimationActive={false} stroke="#e6b566" strokeDasharray="5 5" strokeWidth={1.5} type="monotone" />
          <Line dataKey="value" dot={{ fill: "#f5f7fb", r: 3 }} isAnimationActive={false} stroke="#7fb0ff" strokeWidth={3} type="monotone" />
        </ComposedChart>
      </ResponsiveContainer>
    </Box>
    <Flex color="muted" gap="5" mt="3" textStyle="caption" wrap="wrap"><Text>Blue: weekly median</Text><Text>Dashed: daily weekly range</Text><Text>Shaded: sensitivity interval</Text></Flex>
  </Box>;
}

function MetricHistory({ data, metricKey, citations }: { data: EquityMarketValuationHistoryResponse; metricKey: string; citations: Map<string, AnalysisCitationRef> }) {
  const points = data.observations.flatMap((observation) => {
    const metric = observation.metrics[metricKey];
    if (!metric) return [];
    return [{ observation, metric, week: observation.valuation.week, value: metric.value === null ? null : Number(metric.value), weeklyMin: metric.weeklyMin === null ? null : Number(metric.weeklyMin), weeklyMax: metric.weeklyMax === null ? null : Number(metric.weeklyMax), sensitivityLower: metric.sensitivity.lower === null ? null : Number(metric.sensitivity.lower), sensitivityUpper: metric.sensitivity.upper === null ? null : Number(metric.sensitivity.upper) }];
  });
  const latest = points.at(-1);
  if (!latest) return null;
  const label = metricLabels[metricKey] ?? metricKey.toUpperCase();
  const metricRefs = refsFor(latest.metric, citations);

  return <Stack as="section" gap="5">
    <Stack gap="2"><Heading as="h2" textStyle="title">{label} weekly history</Heading><Text color="muted">The headline is the median of the daily aggregate country values for the valuation week. The chart preserves the observed daily range and the model sensitivity interval.<AnalysisCitationLinks refs={metricRefs} /></Text></Stack>
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel"><Stack gap="4"><Text color="accent" textStyle="eyebrow">Formula</Text><Text fontFamily="mono" fontWeight="700">{latest.metric.formula}</Text><SimpleGrid columns={{ base: 1, md: 2 }} gap="3"><Text fontFamily="mono">Numerator</Text><Text color="muted">Aggregate market value for eligible companies.</Text><Text fontFamily="mono">Denominator</Text><Text color="muted">Aggregate eligible trailing fundamental named by the formula.</Text></SimpleGrid><Text color="muted">The ratio is calculated from aggregate values before the weekly median is taken.</Text></Stack></Box>
    <SimpleGrid columns={{ base: 1, md: 3 }} gap="4">
      <Box bg="surface" borderColor="edge" borderWidth="1px" p="5" rounded="panel"><Text color="muted" textStyle="caption">Latest weekly median</Text><Text fontSize="2xl" fontWeight="700">{formatValue(latest.metric.value, metricKey)}</Text></Box>
      <Box bg="surface" borderColor="edge" borderWidth="1px" p="5" rounded="panel"><Text color="muted" textStyle="caption">Daily weekly range</Text><Text fontSize="2xl" fontWeight="700">{range(latest.metric.weeklyMin, latest.metric.weeklyMax, metricKey)}</Text></Box>
      <Box bg="surface" borderColor="edge" borderWidth="1px" p="5" rounded="panel"><Text color="muted" textStyle="caption">{latest.metric.sensitivity.intervalLabel ?? "Sensitivity interval"}</Text><Text fontSize="2xl" fontWeight="700">{range(latest.metric.sensitivity.lower, latest.metric.sensitivity.upper, metricKey)}</Text></Box>
    </SimpleGrid>
    <HistoryChart data={points.map(({ week, value, weeklyMin, weeklyMax, sensitivityLower, sensitivityUpper }) => ({ week, value, weeklyMin, weeklyMax, sensitivityRange: sensitivityLower === null || sensitivityUpper === null ? null : [sensitivityLower, sensitivityUpper] }))} label={label} marketName={data.marketName} metricKey={metricKey} />
    <Box as="table" aria-label={`${data.marketName} ${label} history data`} borderCollapse="collapse" display={{ base: "block", md: "table" }} tableLayout="fixed" w="100%">
      <Box as="thead" display={{ base: "none", md: "table-header-group" }}>
        <Box as="tr"><Box as="th" p="3" textAlign="left">Week</Box><Box as="th" p="3" textAlign="right">Median</Box><Box as="th" p="3" textAlign="right">Daily range</Box><Box as="th" p="3" textAlign="right">Sensitivity</Box><Box as="th" p="3" textAlign="right">Cohort</Box><Box as="th" p="3" textAlign="right">Published</Box></Box>
      </Box>
      <Box as="tbody" display={{ base: "block", md: "table-row-group" }}>
        {points.map(({ observation, metric, week }) => (
          <Box as="tr" borderTopColor="edge" borderTopWidth="1px" display={{ base: "grid", md: "table-row" }} gap="3" gridTemplateColumns="repeat(2, minmax(0, 1fr))" key={`${week}-${observation.publication.runId}`} py={{ base: "4", md: "0" }}>
            {[
              ["Week", week],
              ["Median", formatValue(metric.value, metricKey)],
              ["Daily range", range(metric.weeklyMin, metric.weeklyMax, metricKey)],
              ["Sensitivity", range(metric.sensitivity.lower, metric.sensitivity.upper, metricKey)],
              ["Cohort", metric.cohort.version],
              ["Published", observation.publication.publishedAt.slice(0, 10)],
            ].map(([cellLabel, cellValue], index) => (
              <Box as="td" key={cellLabel} minW="0" p={{ base: "0", md: "3" }} textAlign={{ base: "left", md: index === 0 ? "left" : "right" }}>
                <Text display={{ base: "block", md: "none" }} color="muted" textStyle="caption">{cellLabel}</Text>
                <Text overflowWrap="anywhere">{cellValue}</Text>
              </Box>
            ))}
          </Box>
        ))}
      </Box>
    </Box>
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel"><Stack gap="2"><Text color="accent" textStyle="eyebrow">Coverage and freshness</Text><Text>Cohort boundary: {latest.metric.cohort.version} effective {latest.metric.cohort.effectiveDate}.</Text><Text>Published {latest.observation.publication.publishedAt.slice(0, 10)} from {latest.observation.valuation.dailyObservationCount} daily observations ({latest.observation.valuation.dates[0]} to {latest.observation.valuation.dates.at(-1)}).</Text><Text color="muted">Companies: {latest.metric.constituents.actualCount} actual / {latest.metric.constituents.targetCount} target; effective count {latest.metric.constituents.effectiveCount ?? "unavailable"}. Current market coverage {range(latest.metric.coverage.currentMarket, latest.metric.coverage.currentMarket, "dividend_yield").split("–")[0]}; reported facts {formatValue(latest.metric.coverage.wholeCohort.reported, "dividend_yield")}, carried forward {formatValue(latest.metric.coverage.wholeCohort.carriedForward, "dividend_yield")}, imputed {formatValue(latest.metric.coverage.wholeCohort.imputed, "dividend_yield")}.</Text></Stack></Box>
  </Stack>;
}

export function MarketValuationMethodology({ data }: { data: EquityMarketValuationHistoryResponse }) {
  const { lines, citations } = buildReferences(data);
  const keys = Array.from(new Set(data.observations.flatMap((observation) => Object.keys(observation.metrics)))).filter((key) => data.observations.some((observation) => observation.metrics[key]?.value !== null));
  const usesDevelopmentPrices = data.references.some((reference) => reference.label.toLowerCase().includes("development price"));
  return <Stack gap={{ base: "10", md: "12" }}>
    <Stack gap="4"><Heading as="h2" textStyle="title">1.0 MVD weekly country valuation methodology</Heading><Text color="muted">MVD calculates each daily country value from aggregate company market capitalization and aggregate eligible fundamentals, then publishes the weekly median of the daily aggregate country values. It does not average company multiples.</Text>{usesDevelopmentPrices ? <Text color="accent">Development-price methodology is active. Prices come from the development price adapter and the result is not a production price publication.</Text> : null}</Stack>
    {keys.map((key) => <MetricHistory citations={citations} data={data} key={key} metricKey={key} />)}
    <AnalysisReferencesBlock items={lines} />
  </Stack>;
}

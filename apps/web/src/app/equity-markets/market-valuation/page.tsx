import React from "react";
import NextLink from "next/link";
import { Box, Flex, Heading, Link, Stack, Text } from "@chakra-ui/react";

import type {
  EquityMarketValuationMarketOverview,
  EquityMarketValuationMetric,
  EquityMarketValuationRow,
  EquityMarketValuationsResponse,
  MvdCountryValuationMetric,
} from "../../../../../../packages/shared/src/contracts/equity-market-valuation";
import { AnalysisCitationLinks, type AnalysisCitationRef } from "../../../features/macro/components/analysis-citation-links";
import { AnalysisReferencesBlock } from "../../../features/macro/components/analysis-references-block";
import { BackLink } from "../../../features/site-shell/back-link";

const emptyValuations: EquityMarketValuationsResponse = { asOf: null, regions: [], markets: [], references: [] };

const mvdMetricColumns = [
  { key: "pe", label: "P/E", percent: false },
  { key: "pb", label: "P/B", percent: false },
  { key: "ps", label: "P/S", percent: false },
  { key: "pcf", label: "P/CF", percent: false },
  { key: "pfcf", label: "Exact P/FCF", percent: false },
  { key: "dividend_yield", label: "Dividend yield", percent: true },
] as const;

const legacyMetricColumns = [
  { key: "trailingPe", label: "P/E" }, { key: "priceToBook", label: "P/B" },
  { key: "priceToSales", label: "P/S" }, { key: "priceToCashFlow", label: "P/CF proxy" },
  { key: "dividendYieldPct", label: "Dividend yield" },
] as const;
type LegacyMetricKey = (typeof legacyMetricColumns)[number]["key"];

async function getMarketValuations() {
  const apiBaseUrl = process.env.MVD_API_URL ?? process.env.API_BASE_URL ?? "http://127.0.0.1:4000";
  try {
    const response = await fetch(`${apiBaseUrl}/equity-markets/valuations`, { cache: "no-store" });
    if (!response.ok) return { data: emptyValuations, unavailable: true };
    const data = (await response.json()) as EquityMarketValuationsResponse;
    const hasMarkets = (data.regions?.some((region) => region.markets.length > 0) ?? false) || data.markets.length > 0;
    return { data, unavailable: !hasMarkets };
  } catch {
    return { data: emptyValuations, unavailable: true };
  }
}

function decimalPercent(value: string | null) {
  if (value === null) return "Unavailable";
  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${(parsed * 100).toFixed(1)}%` : "Unavailable";
}

function metricValue(metric: MvdCountryValuationMetric | undefined, percent = false) {
  if (!metric?.value) return "Unavailable";
  return percent ? decimalPercent(metric.value) : metric.value;
}

function primaryMetric(market: EquityMarketValuationMarketOverview) {
  return market.metrics.pe ?? Object.values(market.metrics)[0];
}

function CountryOverview({ data }: { data: EquityMarketValuationsResponse }) {
  const markets = data.regions?.flatMap((region) => region.markets) ?? [];
  const visibleMetrics = mvdMetricColumns.filter((column) => markets.some((market) => market.metrics[column.key]?.value !== null && market.metrics[column.key] !== undefined));
  const metricGridColumns = visibleMetrics.length > 0 ? ` repeat(${visibleMetrics.length}, minmax(0, .65fr))` : "";
  const gridColumns = `minmax(10rem, 1.7fr)${metricGridColumns} repeat(4, minmax(0, .8fr))`;

  return (
    <Stack gap="8">
      {data.regions?.map((region) => (
        <Stack gap="3" key={region.region}>
          <Heading as="h3" textStyle="subtitle">{region.region}</Heading>
          <Box>
              <Box aria-hidden="true" display={{ base: "none", lg: "grid" }} gridTemplateColumns={gridColumns} gap="3" px="4" py="3">
                <Text textStyle="eyebrow">Market</Text>
                {visibleMetrics.map((column) => <Text key={column.key} textAlign="right" textStyle="eyebrow">{column.label}</Text>)}
                <Text textAlign="right" textStyle="eyebrow">Companies</Text>
                <Text textAlign="right" textStyle="eyebrow">Effective count</Text>
                <Text textAlign="right" textStyle="eyebrow">Market coverage</Text>
                <Text textAlign="right" textStyle="eyebrow">Fundamental coverage</Text>
              </Box>
              <Box role="table" aria-label={`${region.region} country valuation overview`}>
                <Box role="row" position="absolute" w="1px" h="1px" overflow="hidden">
                  <Box role="columnheader">Market</Box>
                  {visibleMetrics.map((column) => <Box role="columnheader" key={column.key}>{column.label}</Box>)}
                  <Box role="columnheader">Companies</Box><Box role="columnheader">Effective count</Box>
                  <Box role="columnheader">Market coverage</Box><Box role="columnheader">Fundamental coverage</Box>
                </Box>
                {region.markets.map((market) => {
                  const diagnostic = primaryMetric(market);
                  const warnings = diagnostic?.warnings ?? [];
                  return (
                    <Link asChild key={market.marketId} display="block" color="inherit" textDecoration="none" _hover={{ textDecoration: "none" }}>
                      <NextLink aria-label={`${market.marketName} valuation history`} href={`/equity-markets/market-valuation/${market.marketId}`}>
                        <Box role="row" display="grid" gridTemplateColumns={{ base: "repeat(2, minmax(0, 1fr))", lg: gridColumns }} gap="3" alignItems="center" borderColor="edge" borderTopWidth="1px" px="4" py="4" transition="background 0.2s ease, border-color 0.2s ease" _hover={{ bg: "canvas", borderColor: "accent" }}>
                          <Stack role="cell" gap="1" gridColumn={{ base: "1 / -1", lg: "auto" }}>
                            <Flex align="center" gap="2"><Text fontWeight="700">{market.marketName}</Text>{warnings.length ? <Text as="span" aria-label={`Warning: ${warnings.map((warning) => warning.message).join(" ")}`} color="accent" title={warnings.map((warning) => warning.message).join(" ")}>⚠</Text> : null}</Flex>
                            <Text color="muted" textStyle="caption">Week {market.latestWeek}</Text>
                            {warnings.map((warning) => <Text color="muted" key={warning.code} textStyle="caption">{warning.message}</Text>)}
                          </Stack>
                          {visibleMetrics.map((column) => <Stack role="cell" key={column.key} gap="0" textAlign={{ base: "left", lg: "right" }}><Text display={{ base: "block", lg: "none" }} color="muted" textStyle="caption">{column.label}</Text><Text>{metricValue(market.metrics[column.key], column.percent)}</Text></Stack>)}
                          <Stack role="cell" gap="0" textAlign={{ base: "left", lg: "right" }}><Text display={{ base: "block", lg: "none" }} color="muted" textStyle="caption">Companies</Text><Text>{diagnostic ? `${diagnostic.constituents.actualCount} / ${diagnostic.constituents.targetCount}` : "Unavailable"}</Text></Stack>
                          <Stack role="cell" gap="0" textAlign={{ base: "left", lg: "right" }}><Text display={{ base: "block", lg: "none" }} color="muted" textStyle="caption">Effective count</Text><Text>{diagnostic?.constituents.effectiveCount ?? "Unavailable"}</Text></Stack>
                          <Stack role="cell" gap="0" textAlign={{ base: "left", lg: "right" }}><Text display={{ base: "block", lg: "none" }} color="muted" textStyle="caption">Market coverage</Text><Text>{decimalPercent(diagnostic?.coverage.currentMarket ?? null)}</Text></Stack>
                          <Stack role="cell" gap="0" textAlign={{ base: "left", lg: "right" }}><Text display={{ base: "block", lg: "none" }} color="muted" textStyle="caption">Fundamental coverage</Text><Text>{decimalPercent(diagnostic?.coverage.wholeCohort.reported ?? null)}</Text></Stack>
                        </Box>
                      </NextLink>
                    </Link>
                  );
                })}
              </Box>
          </Box>
        </Stack>
      ))}
    </Stack>
  );
}

function legacyFormat(metric: EquityMarketValuationMetric, key: LegacyMetricKey) {
  if (metric.value === null) return "Unavailable";
  return key === "dividendYieldPct" ? `${metric.value}%` : metric.value;
}

function LegacyOverview({ markets, citations }: { markets: EquityMarketValuationRow[]; citations: Map<string, AnalysisCitationRef> }) {
  const columns = legacyMetricColumns.filter((column) => markets.filter((row) => row.metrics[column.key].value !== null).length * 2 >= markets.length);
  return <Box as="table" role="table" aria-label="Market valuation overview" borderCollapse="collapse" w="100%">
    <Box as="thead" role="rowgroup"><Box as="tr" role="row"><Box as="th" role="columnheader" p="3" textAlign="left">Market / measured object</Box>{columns.map((column) => <Box as="th" role="columnheader" key={column.key} p="3" textAlign="right">{column.label}</Box>)}</Box></Box>
    <Box as="tbody" role="rowgroup">{markets.map((row) => <Box as="tr" role="row" key={row.marketId} borderTopColor="edge" borderTopWidth="1px"><Box as="th" role="rowheader" p="3" textAlign="left"><Text fontWeight="700">{row.marketName}</Text><Stack color="muted" gap="1" textStyle="caption"><Text>{row.region}</Text><Text>{row.measuredSymbol}</Text><Text>{row.measuredType.toLowerCase() === "etf" ? "ETF proxy" : `${row.measuredType} series`}</Text><Text>{row.measuredName}{citations.has(row.sourceUrl) ? <AnalysisCitationLinks refs={[citations.get(row.sourceUrl)!]} /> : null}</Text></Stack><Text color="muted" textStyle="caption">Valuation as of {row.asOf}</Text></Box>{columns.map((column) => <Box as="td" role="cell" key={column.key} p="3" textAlign="right">{legacyFormat(row.metrics[column.key], column.key)}</Box>)}</Box>)}</Box>
  </Box>;
}

function buildLegacyReferences(data: EquityMarketValuationsResponse) {
  const sources = new Map<string, string>();
  data.references.forEach((reference) => { if (reference.url) sources.set(reference.url, reference.label); });
  data.markets.forEach((row) => { if (row.sourceUrl && !sources.has(row.sourceUrl)) sources.set(row.sourceUrl, row.measuredName); });
  return Array.from(sources, ([href, label], index) => ({ number: index + 1, href, key: href, text: `[${index + 1}] ${label}. [Online]. Available: ${href}.` }));
}

export default async function MarketValuationPage() {
  const { data, unavailable } = await getMarketValuations();
  const legacyReferences = buildLegacyReferences(data);
  const legacyCitations = new Map(legacyReferences.map((reference) => [reference.href, { number: reference.number, href: reference.href }]));
  const hasCountryIndices = data.regions?.some((region) => region.markets.length > 0) ?? false;

  return <Stack gap={{ base: "8", md: "10" }}>
    <Stack gap="4" maxW="4xl"><BackLink href="/equity-markets" label="Back to Equity Markets" /><Text color="accent" textStyle="eyebrow">Market Valuation</Text><Heading as="h1" textStyle="hero">Market Valuation Dashboard</Heading><Text color="muted" maxW="3xl" textStyle="subtitle">MVD-owned weekly country valuation indices with coverage, concentration, freshness, and uncertainty diagnostics.</Text><Text color="muted" textStyle="caption">Latest valuation {hasCountryIndices ? "week" : "date"}: {data.asOf ?? "latest available update"}</Text></Stack>
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel"><Stack gap="3"><Text color="accent" textStyle="eyebrow">Methodology</Text><Text color="muted">Each headline is the median of daily aggregate country values. Company multiples are never averaged. Open a country row for weekly ranges, sensitivity intervals, cohort boundaries, formulas, freshness, and source lineage.</Text></Stack></Box>
    {unavailable ? <Box bg="surface" borderColor="edge" borderWidth="1px" p="6" rounded="panel"><Text fontWeight="semibold">Live market valuation data is unavailable right now.</Text><Text color="muted">Run the MVD country valuation pipeline to publish weekly observations.</Text></Box> : <Box as="section" bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "4", md: "6" }} rounded="panel"><Stack gap="5"><Stack gap="2"><Text color="accent" textStyle="eyebrow">Valuation Matrix</Text><Heading as="h2" textStyle="title">Country valuation indices</Heading></Stack>{hasCountryIndices ? <CountryOverview data={data} /> : <LegacyOverview markets={data.markets} citations={legacyCitations} />}</Stack></Box>}
    {!hasCountryIndices ? <AnalysisReferencesBlock items={legacyReferences} /> : null}
  </Stack>;
}

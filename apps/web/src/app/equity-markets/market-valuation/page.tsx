import React from "react";
import { Box, Flex, Heading, Stack, Text } from "@chakra-ui/react";

import type {
  EquityMarketValuationMetric,
  EquityMarketValuationRow,
  EquityMarketValuationsResponse,
} from "../../../../../../packages/shared/src/contracts/equity-market-valuation";
import { AnalysisCitationLinks, type AnalysisCitationRef } from "../../../features/macro/components/analysis-citation-links";
import { AnalysisReferencesBlock } from "../../../features/macro/components/analysis-references-block";
import { BackLink } from "../../../features/site-shell/back-link";

const emptyValuations: EquityMarketValuationsResponse = {
  asOf: null,
  markets: [],
  references: [],
};

const metricColumns = [
  { key: "trailingPe", label: "P/E" },
  { key: "priceToBook", label: "P/B" },
  { key: "priceToSales", label: "P/S" },
  { key: "priceToCashFlow", label: "P/CF proxy" },
  { key: "dividendYieldPct", label: "Dividend yield" },
] as const;

type MetricKey = (typeof metricColumns)[number]["key"];

async function getMarketValuations(): Promise<{
  data: EquityMarketValuationsResponse;
  unavailable: boolean;
}> {
  const apiBaseUrl = process.env.MVD_API_URL ?? process.env.API_BASE_URL ?? "http://127.0.0.1:4000";

  try {
    const response = await fetch(`${apiBaseUrl}/equity-markets/valuations`, { cache: "no-store" });

    if (!response.ok) {
      return { data: emptyValuations, unavailable: true };
    }

    const data = (await response.json()) as EquityMarketValuationsResponse;
    return { data, unavailable: data.markets.length === 0 };
  } catch {
    return { data: emptyValuations, unavailable: true };
  }
}

function formatMetric(metric: EquityMarketValuationMetric, key: MetricKey) {
  if (metric.value === null) {
    return "Unavailable";
  }

  return key === "dividendYieldPct" ? `${metric.value}%` : metric.value;
}

function measuredTypeLabel(row: EquityMarketValuationRow) {
  if (row.measuredType.toLowerCase() === "etf") {
    return "ETF proxy";
  }

  return `${row.measuredType} series`;
}

const marketFlags: Record<string, { emoji: string; label: string }> = {
  china: { emoji: "🇨🇳", label: "China" },
  denmark: { emoji: "🇩🇰", label: "Denmark" },
  europe: { emoji: "🇪🇺", label: "Europe" },
  fi: { emoji: "🇫🇮", label: "Finland" },
  finland: { emoji: "🇫🇮", label: "Finland" },
  france: { emoji: "🇫🇷", label: "France" },
  germany: { emoji: "🇩🇪", label: "Germany" },
  japan: { emoji: "🇯🇵", label: "Japan" },
  norway: { emoji: "🇳🇴", label: "Norway" },
  "south korea": { emoji: "🇰🇷", label: "South Korea" },
  sweden: { emoji: "🇸🇪", label: "Sweden" },
  taiwan: { emoji: "🇹🇼", label: "Taiwan" },
  uk: { emoji: "🇬🇧", label: "United Kingdom" },
  "united kingdom": { emoji: "🇬🇧", label: "United Kingdom" },
  us: { emoji: "🇺🇸", label: "United States" },
};

function marketFlag(region: string) {
  return marketFlags[region.trim().toLowerCase()] ?? { emoji: "🌐", label: region };
}

function buildReferences(data: EquityMarketValuationsResponse) {
  const sources = new Map<string, string>();
  for (const reference of data.references) {
    if (reference.url && !sources.has(reference.url)) sources.set(reference.url, reference.label);
  }
  for (const row of data.markets) {
    if (row.sourceUrl && !sources.has(row.sourceUrl)) sources.set(row.sourceUrl, row.measuredName);
  }
  const knownProviders: Record<string, string> = {
    eodhd: "EODHD", ishares: "BlackRock iShares", spdr: "State Street SPDR",
    "ishares.com": "BlackRock iShares", "ssga.com": "State Street SPDR", "eodhd.com": "EODHD",
  };
  return Array.from(sources, ([href, label], index) => {
    const rows = data.markets.filter((row) => row.sourceUrl === href);
    let hostname = "Source provider";
    try { hostname = new URL(href).hostname.replace(/^www\./, ""); } catch { /* Keep supplied URL without inventing metadata. */ }
    const provider = rows.find((row) => row.provider.trim())?.provider;
    const institution = (provider && knownProviders[provider.toLowerCase()]) || knownProviders[hostname] || provider || hostname;
    const titles = Array.from(new Set(rows.map((row) =>
      row.measuredName ? `${row.measuredName}${row.measuredSymbol ? ` (${row.measuredSymbol})` : ""}` : row.measuredSymbol,
    ).filter(Boolean)));
    const title = titles.length ? titles.join("; ") : label || "Source document";
    return { number: index + 1, href, key: href, text: `[${index + 1}] ${institution}, "${title}." [Online]. Available: ${href}.` };
  });
}

function MarketValuationTable({ markets, citations }: { markets: EquityMarketValuationRow[]; citations: Map<string, AnalysisCitationRef> }) {
  const visibleColumns = metricColumns.filter((column) => {
    const availableCount = markets.filter((row) => row.metrics[column.key].value !== null).length;
    return availableCount * 2 >= markets.length;
  });

  return (
    <Box
      as="table"
      role="table"
      aria-label="Market valuation overview"
      borderCollapse="collapse"
      tableLayout="fixed"
      display={{ base: "block", lg: "table" }}
      w="100%"
      css={{ overflowWrap: "anywhere" }}
    >
      <Box as="thead" role="rowgroup" display={{ base: "none", lg: "table-header-group" }}>
        <Box as="tr" role="row" borderBottomColor="edge" borderBottomWidth="1px">
          <Box as="th" role="columnheader" scope="col" w={visibleColumns.length ? "34%" : "100%"} p="3" textAlign="left" color="muted" textStyle="eyebrow">
            Market / measured object
          </Box>
          {visibleColumns.map((column) => (
            <Box as="th" role="columnheader" scope="col" key={column.key} p="3" textAlign="right" color="muted" textStyle="eyebrow" verticalAlign="bottom">
              {column.label}
            </Box>
          ))}
        </Box>
      </Box>
      <Box as="tbody" role="rowgroup" display={{ base: "block", lg: "table-row-group" }}>
        {markets.map((row) => {
          const flag = marketFlag(row.region);
          return (
          <Box as="tr" role="row" display={{ base: "grid", lg: "table-row" }} gridTemplateColumns="repeat(2, minmax(0, 1fr))" borderBottomColor="edge" borderBottomWidth="1px" py={{ base: "4", lg: "0" }} key={row.marketId}>
            <Box as="th" role="rowheader" scope="row" gridColumn="1 / -1" minW="0" p="3" textAlign="left" verticalAlign="top">
              <Flex align="flex-start" gap="3">
                <Box as="span" aria-label={`${flag.label} flag`} flexShrink="0" fontSize="xl" lineHeight="1" role="img">
                  {flag.emoji}
                </Box>
                <Stack gap="1" minW="0">
                <Text fontWeight="700" textStyle="body">
                  {row.marketName}
                </Text>
                <Text color="muted" textStyle="caption">
                  <Text as="span" color="text" fontWeight="700" title={row.measuredName}>{row.measuredSymbol}</Text>
                  {" | "}<Text as="span">{measuredTypeLabel(row)}</Text>
                  {citations.has(row.sourceUrl) ? <AnalysisCitationLinks refs={[citations.get(row.sourceUrl)!]} /> : null}
                  <Text as="span" display="block">{row.measuredName}</Text>
                </Text>
                <Text color="muted" textStyle="caption">Valuation as of {row.asOf}</Text>
                </Stack>
              </Flex>
            </Box>
            {visibleColumns.map((column) => (
              <Box as="td" role="cell" key={column.key} minW="0" p="3" textAlign={{ base: "left", lg: "right" }} textStyle="body" verticalAlign="top">
                <Text as="span" display={{ base: "block", lg: "none" }} color="muted" textStyle="caption" mb="1">
                  {column.label}
                </Text>
                {formatMetric(row.metrics[column.key], column.key)}
                {column.key === "trailingPe" && row.metrics[column.key].value !== null && row.metrics[column.key].method.includes("prospective") ? (
                  <Text color="muted" textStyle="caption">Prospective earnings</Text>
                ) : null}
              </Box>
            ))}
          </Box>
          );
        })}
      </Box>
    </Box>
  );
}

export default async function MarketValuationPage() {
  const { data, unavailable } = await getMarketValuations();
  const references = buildReferences(data);
  const citations = new Map(references.map((reference) => [reference.href, { number: reference.number, href: reference.href }]));

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Stack gap="4" maxW="4xl">
        <BackLink href="/equity-markets" label="Back to Equity Markets" />
        <Text color="accent" textStyle="eyebrow">
          Market Valuation
        </Text>
        <Heading as="h1" textStyle="hero">
          Market Valuation Dashboard
        </Heading>
        <Text color="muted" maxW="3xl" textStyle="subtitle">
          API-backed overview for scanning broad equity market valuation snapshots across countries
          and regions.
        </Text>
        <Text color="muted" textStyle="caption">
          Latest valuation date: {data.asOf ?? "latest available update"}
        </Text>
      </Stack>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
        <Stack gap="3">
          <Text color="accent" textStyle="eyebrow">
            Methodology
          </Text>
          <Text color="muted" textStyle="body">
            The measured object is shown for every row so ETF proxies and index-native series stay
            visible. P/CF is a cash-flow proxy, not exact P/FCF. Metrics unavailable for a majority
            of the returned markets are omitted; occasional missing values stay explicit.
          </Text>
          <Text color="muted" textStyle="body">
            Dividend yield follows each provider's definition: iShares reports 12-month fund
            distribution yield; SPDR reports indicated index dividend yield. The iShares yield
            may predate the valuation ratios; see the linked source for its reporting date.
            P/E values based on prospective earnings are identified alongside the ratio.
          </Text>
        </Stack>
      </Box>

      {unavailable ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
          <Stack gap="2">
            <Text fontWeight="semibold" textStyle="body">
              Live market valuation data is unavailable right now.
            </Text>
            <Text color="muted" textStyle="body">
              Run the market valuation pipeline to populate ETF and index valuation snapshots.
            </Text>
          </Stack>
        </Box>
      ) : (
        <Box
          as="section"
          bg="surface"
          borderColor="edge"
          borderWidth="1px"
          p={{ base: "4", md: "6" }}
          rounded="panel"
        >
          <Stack gap="5">
            <Stack gap="2">
              <Text color="accent" textStyle="eyebrow">
                Valuation Matrix
              </Text>
              <Heading as="h2" textStyle="title">
                Broad market ratios
              </Heading>
              <Text color="muted" maxW="3xl" textStyle="body">
                One row per covered market with provider valuation metrics, measured object
                metadata, per-market dates, and numbered source citations.
              </Text>
            </Stack>

            <MarketValuationTable markets={data.markets} citations={citations} />
          </Stack>
        </Box>
      )}

      <AnalysisReferencesBlock items={references} />
    </Stack>
  );
}

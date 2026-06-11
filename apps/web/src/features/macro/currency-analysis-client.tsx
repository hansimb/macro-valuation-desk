"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Box, Heading, Stack, Text } from "@chakra-ui/react";

import { AnalysisReferencesBlock } from "./components/analysis-references-block";
import { CurrencyIrpDataInputsBlock } from "./components/currency-irp-data-inputs-block";
import { CurrencyIrpFormulaBlock } from "./components/currency-irp-formula-block";
import { CurrencyIrpTenorTableBlock } from "./components/currency-irp-tenor-table-block";
import { CurrencyIrpUipBlock } from "./components/currency-irp-uip-block";
import { CurrencyPppDataInputsBlock } from "./components/currency-ppp-data-inputs-block";
import { CurrencyPppFormulaBlock } from "./components/currency-ppp-formula-block";
import { CurrencyPppHistoricalSpotContextBlock } from "./components/currency-ppp-historical-spot-context-block";
import { CurrencyPppPathTableBlock } from "./components/currency-ppp-path-table-block";
import { CurrencyPppReadoutBlock } from "./components/currency-ppp-readout-block";
import type { CurrencyAnalysisPageData } from "./currency-analysis-types";

type CurrencyReferenceItem = CurrencyAnalysisPageData["ppp"]["references"][number];

function pppTakeaway(data: CurrencyAnalysisPageData) {
  if (!data.ppp.summary) {
    return null;
  }

  const deviation = Number.parseFloat(data.ppp.summary.deviationPct);
  const trailingAverageGap = data.ppp.summary.trailing12mAverageGapPct
    ? Number.parseFloat(data.ppp.summary.trailing12mAverageGapPct)
    : Number.NaN;
  if (Number.isNaN(deviation)) {
    return null;
  }

  if (deviation > 0) {
    return `The latest market spot sits ${data.ppp.summary.deviationPct}% above the PPP-implied fair-value anchor, so the euro screens rich against the dollar on this relative-PPP lens. This means that EUR/USD is currently above its PPP fair value, so on this measure the euro looks somewhat overvalued against the dollar. The current gap is ${!Number.isNaN(trailingAverageGap) && deviation > trailingAverageGap ? "larger" : "close to"} than the average gap over the past 12 months, which means the current overvaluation looks ${!Number.isNaN(trailingAverageGap) && deviation > trailingAverageGap ? "more stretched than" : "broadly similar to"} the recent 12-month average.`;
  }

  if (deviation < 0) {
    return `The latest market spot sits ${Math.abs(deviation).toFixed(2)}% below the PPP-implied fair-value anchor, so the euro screens cheap against the dollar on this relative-PPP lens. This means that EUR/USD is currently below its PPP fair value, so on this measure the euro looks somewhat undervalued against the dollar. The current gap is ${!Number.isNaN(trailingAverageGap) && Math.abs(deviation) > Math.abs(trailingAverageGap) ? "larger" : "close to"} than the average gap over the past 12 months, which means the current undervaluation looks ${!Number.isNaN(trailingAverageGap) && Math.abs(deviation) > Math.abs(trailingAverageGap) ? "more stretched than" : "broadly similar to"} the recent 12-month average.`;
  }

  return "The latest market spot is sitting almost exactly on the PPP-implied fair-value anchor. This means that, on this relative-PPP lens, EUR/USD is trading close to its PPP fair value.";
}

function currencyAcademicReferenceText(label: string, url?: string) {
  if (url?.includes("data.ecb.europa.eu")) {
    return `European Central Bank, Data Portal, "${label}"`;
  }

  return `Federal Reserve Bank of St. Louis, FRED, "${label}"`;
}

function currencyIeeeReferenceText(index: number, reference: CurrencyReferenceItem) {
  const sourceText = currencyAcademicReferenceText(reference.label, reference.url);
  return `[${index}] ${sourceText}. [Online]. Available: ${reference.url}.`;
}

function buildSearch(params: Record<string, string | null | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      search.set(key, value);
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function CurrencyAnalysisClient({ data }: { data: CurrencyAnalysisPageData }) {
  const router = useRouter();
  const pppSummary = data.ppp.summary;
  const pppInterpretation = pppTakeaway(data);
  const selectedAnchorKind = data.ppp.selectedAnchorKind ?? "window";
  const selectedAnchorStatistic = data.ppp.selectedAnchorStatistic;
  const selectedWindowCode = data.ppp.selectedWindowCode;
  const selectedBaseYear = data.ppp.selectedBaseYear ?? "";
  const recentPathRows = data.ppp.path.slice(-12);
  const fullPathRows = data.ppp.path;
  const referenceNumberByLabel = new Map(data.ppp.references.map((reference, index) => [reference.label, index + 1]));
  const spotReference = data.ppp.references.find((reference) => reference.label === "EUR/USD spot");
  const usCpiReference = data.ppp.references.find((reference) => reference.label === "US CPI index");
  const euroAreaCpiReference = data.ppp.references.find((reference) => reference.label === "Euro Area CPI index");
  const spotReferenceNumber = referenceNumberByLabel.get("EUR/USD spot");
  const usCpiReferenceNumber = referenceNumberByLabel.get("US CPI index");
  const euroAreaCpiReferenceNumber = referenceNumberByLabel.get("Euro Area CPI index");
  const spotRef = spotReferenceNumber ? { number: spotReferenceNumber, href: spotReference?.url } : undefined;
  const usCpiRef = usCpiReferenceNumber ? { number: usCpiReferenceNumber, href: usCpiReference?.url } : undefined;
  const euroAreaCpiRef = euroAreaCpiReferenceNumber ? { number: euroAreaCpiReferenceNumber, href: euroAreaCpiReference?.url } : undefined;
  const irpReferenceNumberByLabel = new Map(data.irp.references.map((reference, index) => [reference.label, index + 1]));
  const irpRefs = data.irp.references.map((reference) => ({
    label: reference.label,
    ref: {
      number: irpReferenceNumberByLabel.get(reference.label) ?? 0,
      href: reference.url,
    },
  }));
  const hasPpp = Boolean(pppSummary);
  const hasIrp = data.irp.cipRows.length > 0 || data.irp.uip.rows.length > 0;

  if (!hasPpp && !hasIrp) {
    return null;
  }

  const pathRowsWithGap = recentPathRows.map((point) => {
    const spot = Number.parseFloat(point.actualSpot);
    const implied = Number.parseFloat(point.impliedPpp);
    const gap = Number.isNaN(spot) || Number.isNaN(implied) || implied === 0 ? null : ((spot / implied) - 1) * 100;

    return {
      actualSpotLabel: point.hasImputedInputs ? `${point.actualSpot}*` : point.actualSpot,
      gapDisplayLabel: point.hasImputedInputs && gap !== null ? `${gap.toFixed(2)}%*` : gap === null ? "N/A" : `${gap.toFixed(2)}%`,
      impliedPppLabel: point.hasImputedInputs ? `${point.impliedPpp}*` : point.impliedPpp,
      monthLabel: point.hasImputedInputs ? `${point.observationMonth}*` : point.observationMonth,
      observationMonth: point.observationMonth,
    };
  });

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      {pppSummary ? (
      <Box as="section">
        <Stack gap="5">
          <Stack gap="3" maxW="4xl">
            <Heading as="h2" textStyle="title">
              1.0 Relative Purchasing Power Parity
            </Heading>
            <Text color="muted" textStyle="body">
              Relative PPP treats EUR/USD as a long-run valuation relationship: if U.S. prices and euro-area prices move differently over time, the exchange rate should eventually reflect that inflation differential.
            </Text>
          </Stack>

          <CurrencyPppFormulaBlock />

          <CurrencyPppHistoricalSpotContextBlock
            anchorLabel={pppSummary.anchorLabel}
            baseSpot={pppSummary.baseSpot}
            currentSpot={pppSummary.currentSpot}
            latestMonth={pppSummary.asOf}
            rows={data.ppp.spotHistory.map((point) => ({
              actualSpot: point.actualSpot,
              monthLabel: point.observationMonth,
              observationMonth: point.observationMonth,
            }))}
            spotRef={spotRef}
          />

          <CurrencyPppDataInputsBlock
            anchorSource={spotRef ? { label: "EUR/USD spot", ref: spotRef } : undefined}
            availableBaseYears={data.ppp.availableBaseYears}
            availableWindowOptions={data.ppp.availableWindowOptions}
            onSelectBaseYear={(nextYear) => {
              router.push(
                `/macro/currency-analysis${buildSearch({
                  anchorKind: "year",
                  anchorStatistic: selectedAnchorStatistic,
                  windowCode: selectedWindowCode,
                  baseYear: nextYear,
                })}`,
                { scroll: false },
              );
            }}
            onSelectStatistic={(statistic) => {
              router.push(
                `/macro/currency-analysis${buildSearch({
                  anchorKind: selectedAnchorKind,
                  anchorStatistic: statistic,
                  windowCode: selectedWindowCode,
                  baseYear: selectedBaseYear || null,
                })}`,
                { scroll: false },
              );
            }}
            onSelectWindowCode={(windowCode) => {
              router.push(
                `/macro/currency-analysis${buildSearch({
                  anchorKind: "window",
                  anchorStatistic: selectedAnchorStatistic,
                  windowCode,
                  baseYear: selectedBaseYear || null,
                })}`,
                { scroll: false },
              );
            }}
            selectedAnchorKind={selectedAnchorKind}
            selectedAnchorStatistic={selectedAnchorStatistic}
            selectedBaseYear={selectedBaseYear}
            selectedWindowCode={selectedWindowCode}
            selectionLogicLabel={`The active PPP baseline is now the selected ${pppSummary.anchorLabel}. For window anchors, the model evaluates the relative-PPP formula across all eligible base months in that sample and aggregates the resulting current fair values.`}
            pppInflationSources={[
              ...(usCpiRef ? [{ label: "U.S. CPI index", ref: usCpiRef }] : []),
              ...(euroAreaCpiRef ? [{ label: "Euro area CPI index", ref: euroAreaCpiRef }] : []),
            ]}
          />

          <CurrencyPppReadoutBlock
            anchorEndMonth={pppSummary.anchorEndMonth}
            anchorStartMonth={pppSummary.anchorStartMonth}
            anchorYearsCovered={pppSummary.anchorYearsCovered}
            asOf={pppSummary.asOf}
            baseSpot={pppSummary.baseSpot}
            currentSpot={pppSummary.currentSpot}
            deviationPct={pppSummary.deviationPct}
            impliedPpp={pppSummary.impliedPpp}
            interpretation={pppInterpretation}
            euroAreaCpiRef={euroAreaCpiRef}
            selectedAnchorLabel={pppSummary.anchorLabel}
            spotRef={spotRef}
            trailing12mAverageGapPct={pppSummary.trailing12mAverageGapPct}
            usCpiRef={usCpiRef}
          />

          <CurrencyPppPathTableBlock
            pppInputRefs={[spotRef, usCpiRef, euroAreaCpiRef].filter(
              (ref): ref is NonNullable<typeof ref> => Boolean(ref),
            )}
            rows={pathRowsWithGap}
            spotRef={spotRef}
          />

          <AnalysisReferencesBlock
            items={data.ppp.references.map((reference) => {
              const index = referenceNumberByLabel.get(reference.label) ?? 0;
              return {
                href: reference.url,
                key: `${reference.label}-${reference.url}`,
                text: currencyIeeeReferenceText(index, reference),
              };
            })}
          />
        </Stack>
      </Box>
      ) : null}

      {hasIrp ? (
        <Box as="section">
          <Stack gap="5">
            <Stack gap="3" maxW="4xl">
              <Heading as="h2" textStyle="title">
                2.0 Interest Rate Parity
              </Heading>
              <Text color="muted" textStyle="body">
                Covered interest parity links spot, tenor-matched interest rates, and forwards. Here it is used as the main market-pricing anchor, while UIP is shown separately as a theoretical expected-spot framing.
              </Text>
            </Stack>

            <CurrencyIrpFormulaBlock />
            <CurrencyIrpDataInputsBlock asOf={data.asOf} inputs={irpRefs} />
            <CurrencyIrpTenorTableBlock rows={data.irp.cipRows} />
            <CurrencyIrpUipBlock rows={data.irp.uip.rows} />

            {data.irp.references.length > 0 ? (
              <AnalysisReferencesBlock
                items={data.irp.references.map((reference) => {
                  const index = irpReferenceNumberByLabel.get(reference.label) ?? 0;
                  return {
                    href: reference.url,
                    key: `irp-${reference.label}-${reference.url}`,
                    text: currencyIeeeReferenceText(index, reference),
                  };
                })}
              />
            ) : null}
          </Stack>
        </Box>
      ) : null}
    </Stack>
  );
}

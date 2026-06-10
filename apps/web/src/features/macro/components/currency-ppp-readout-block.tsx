"use client";

import React from "react";
import { Box, Grid, Stack, Text } from "@chakra-ui/react";

import { AnalysisCitationLinks, type AnalysisCitationRef } from "./analysis-citation-links";
import { AnalysisMetricCard } from "./analysis-metric-card";

export function CurrencyPppReadoutBlock({
  anchorEndMonth,
  anchorStartMonth,
  anchorYearsCovered,
  asOf,
  baseSpot,
  currentSpot,
  deviationPct,
  impliedPpp,
  interpretation,
  spotRef,
  usCpiRef,
  euroAreaCpiRef,
  selectedAnchorLabel,
  trailing12mAverageGapPct,
}: {
  anchorEndMonth: string;
  anchorStartMonth: string;
  anchorYearsCovered: number | null;
  asOf: string;
  baseSpot: string;
  currentSpot: string;
  deviationPct: string;
  impliedPpp: string;
  interpretation: string | null;
  spotRef?: AnalysisCitationRef;
  usCpiRef?: AnalysisCitationRef;
  euroAreaCpiRef?: AnalysisCitationRef;
  selectedAnchorLabel: string;
  trailing12mAverageGapPct: string | null;
}) {
  const pppInputRefs = [spotRef, usCpiRef, euroAreaCpiRef].filter((ref): ref is AnalysisCitationRef => Boolean(ref));

  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" textStyle="eyebrow">
          Current PPP Valuation Readout
        </Text>
        <Text color="muted" textStyle="body">
          These values are computed from the selected long-run anchor and the latest month where spot and both CPI series overlap.
        </Text>
        <Grid gap="4" templateColumns={{ base: "1fr", md: "repeat(2, minmax(0, 1fr))", xl: "repeat(5, minmax(0, 1fr))" }}>
          <AnalysisMetricCard
            label="Selected anchor spot"
            note={
              <>
                Calculated {selectedAnchorLabel} spot summary (
                <Box as="span" fontStyle="italic">
                  S
                </Box>
                <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                  0
                </Box>
                ).
                {spotRef ? <AnalysisCitationLinks refs={[spotRef]} /> : null}
              </>
            }
            value={baseSpot}
          />
          <AnalysisMetricCard
            label="Latest observed spot"
            note={
              <>
                Observed at {asOf}.
                {spotRef ? <AnalysisCitationLinks refs={[spotRef]} /> : null}
              </>
            }
            value={currentSpot}
          />
          <AnalysisMetricCard
            label="Latest PPP-implied fair value"
            note={
              <>
                Calculated aggregated fair value (
                <Box as="span" fontStyle="italic">
                  PPP
                </Box>
                <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                  t
                </Box>
                ).
                {pppInputRefs.length ? <AnalysisCitationLinks refs={pppInputRefs} /> : null}
              </>
            }
            value={impliedPpp}
          />
          <AnalysisMetricCard
            label="Current valuation gap"
            note={
              <>
                Calculated spot-versus-fair-value gap (
                <Box as="span" fontStyle="italic">
                  PPP
                </Box>
                <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                  t
                </Box>
                ).
                {spotRef ? <AnalysisCitationLinks refs={[spotRef]} /> : null}
              </>
            }
            value={`${deviationPct}%`}
          />
          <AnalysisMetricCard
            label="Trailing 12M average gap"
            note={
              trailing12mAverageGapPct ? (
                <>
                  Calculated 12M average gap versus (
                  <Box as="span" fontStyle="italic">
                    PPP
                  </Box>
                  <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                    t
                  </Box>
                  ) gaps.
                  {spotRef ? <AnalysisCitationLinks refs={[spotRef]} /> : null}
                </>
              ) : (
                "Calculated series unavailable for 12 consecutive months."
              )
            }
            value={trailing12mAverageGapPct ? `${trailing12mAverageGapPct}%` : "N/A"}
          />
        </Grid>
        <Text color="muted" textStyle="body">
          Active anchor sample: {anchorStartMonth} to {anchorEndMonth}
          {anchorYearsCovered ? ` (${anchorYearsCovered} years covered)` : ""}.
        </Text>
        {interpretation ? (
          <Stack borderColor="edge" borderTopWidth="1px" gap="2" pt="4">
            <Text color="accent" textStyle="eyebrow">
              Analysis Takeaway
            </Text>
            <Text color="muted" textStyle="body">{interpretation}</Text>
          </Stack>
        ) : null}
      </Stack>
    </Box>
  );
}

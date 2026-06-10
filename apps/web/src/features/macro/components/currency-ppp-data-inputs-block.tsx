"use client";

import React from "react";
import { Box, Button, Grid, SimpleGrid, Stack, Text } from "@chakra-ui/react";

import { AnalysisCitationLinks, type AnalysisCitationRef } from "./analysis-citation-links";

type WindowOption = {
  code: "3Y" | "5Y" | "10Y" | "20Y" | "MAX";
  label: string;
  yearsCovered: number;
};

export function CurrencyPppDataInputsBlock({
  anchorSource,
  availableBaseYears,
  availableWindowOptions,
  pppInflationSources,
  selectedAnchorKind,
  selectedAnchorStatistic,
  selectedBaseYear,
  selectedWindowCode,
  onSelectBaseYear,
  onSelectStatistic,
  onSelectWindowCode,
  selectionLogicLabel,
}: {
  anchorSource?: { label: string; ref: AnalysisCitationRef };
  availableBaseYears: string[];
  availableWindowOptions: WindowOption[];
  pppInflationSources: Array<{ label: string; ref: AnalysisCitationRef }>;
  selectedAnchorKind: "window" | "year";
  selectedAnchorStatistic: "average" | "median";
  selectedBaseYear: string;
  selectedWindowCode: "3Y" | "5Y" | "10Y" | "20Y" | "MAX" | null;
  onSelectBaseYear: (baseYear: string) => void;
  onSelectStatistic: (statistic: "average" | "median") => void;
  onSelectWindowCode: (windowCode: "3Y" | "5Y" | "10Y" | "20Y" | "MAX") => void;
  selectionLogicLabel: string;
}) {
  const orderedWindowOptions = ["3Y", "5Y", "10Y", "20Y", "MAX"]
    .map((code) => availableWindowOptions.find((option) => option.code === code))
    .filter((option): option is WindowOption => option !== undefined);

  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" textStyle="eyebrow">
          Model Inputs And Anchor Method
        </Text>
        <Stack gap="5">
          <Stack gap="2">
            <Text color="muted" textStyle="body">
              Anchor statistic
            </Text>
            <Grid gap="2" templateColumns={{ base: "repeat(2, minmax(0, 1fr))", md: "repeat(2, minmax(0, 12rem))" }}>
              {(["average", "median"] as const).map((statistic) => {
                const isActive = selectedAnchorStatistic === statistic;
                return (
                  <Button
                    aria-pressed={isActive}
                    bg={isActive ? "accent" : "canvas"}
                    borderColor="edge"
                    borderWidth="1px"
                    color={isActive ? "canvas" : "text"}
                    key={statistic}
                    onClick={() => onSelectStatistic(statistic)}
                    size="sm"
                    variant="outline"
                  >
                    {statistic === "average" ? "Average" : "Median"}
                  </Button>
                );
              })}
            </Grid>
            <Text color="muted" textStyle="caption">
              This setting controls whether the long-run anchor uses the arithmetic average or the median of the selected anchor sample.
            </Text>
          </Stack>

          <Stack gap="2">
            <Text color="muted" textStyle="body">
              Long-term anchor window
            </Text>
            <Grid gap="2" templateColumns={{ base: "repeat(2, minmax(0, 1fr))", md: "repeat(5, minmax(0, 1fr))" }}>
              {["3Y", "5Y", "10Y", "20Y", "MAX"].map((code) => {
                const option = availableWindowOptions.find((candidate) => candidate.code === code);
                const isAvailable = Boolean(option);
                const isActive = selectedAnchorKind === "window" && selectedWindowCode === code;

                return (
                  <Button
                    aria-pressed={isActive}
                    bg={isActive ? "accent" : "canvas"}
                    borderColor="edge"
                    borderWidth="1px"
                    color={isActive ? "canvas" : "text"}
                    disabled={!isAvailable}
                    key={code}
                    onClick={() => {
                      if (option) {
                        onSelectWindowCode(option.code);
                      }
                    }}
                    size="sm"
                    variant="outline"
                  >
                    {code}
                  </Button>
                );
              })}
            </Grid>
            <Text color="muted" textStyle="caption">
              Each button builds a new PPP long-run anchor from the latest 3, 5, 10, or 20 years of monthly data, or the full maximum overlapping history, under the selected average or median rule.
            </Text>
            <Text color="muted" textStyle="caption">
              Available windows:{" "}
              {orderedWindowOptions.map((option) =>
                option.code === "MAX" ? `MAX (${option.yearsCovered}Y covered)` : `${option.code} (${option.yearsCovered}Y covered)`,
              ).join(", ")}
            </Text>
          </Stack>

          <SimpleGrid columns={{ base: 1, md: 2 }} gap="5">
            <Stack gap="2">
              <Text color="muted" textStyle="body">
                Single-year anchor
              </Text>
              <Box position="relative">
                <select
                  aria-label="Single-year anchor"
                  onChange={(event: React.ChangeEvent<HTMLSelectElement>) => {
                    const nextYear = event.currentTarget.value;
                    if (nextYear) {
                      onSelectBaseYear(nextYear);
                    }
                  }}
                  style={{
                    appearance: "none",
                    background: "#181A1B",
                    border: "1px solid #7e91a8",
                    borderRadius: "0.875rem",
                    color: "#d9e8ff",
                    fontSize: "var(--chakra-font-sizes-body)",
                    lineHeight: "1.2",
                    minHeight: "3rem",
                    paddingInlineEnd: "3rem",
                    paddingInlineStart: "0.875rem",
                    width: "100%",
                  }}
                  value={selectedBaseYear}
                >
                  {availableBaseYears.map((year) => (
                    <option key={year} style={{ background: "#181A1B", color: "#d9e8ff" }} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
                <Box aria-hidden="true" color="text" pointerEvents="none" position="absolute" right="0.875rem" top="50%" transform="translateY(-50%)">
                  v
                </Box>
              </Box>
            <Text color="muted" textStyle="caption">
              This is the alternative one-year anchor mode. It uses the selected year&apos;s own monthly sample under the same average or median rule.
            </Text>
            </Stack>

            <Stack gap="2">
              <Text color="muted" textStyle="body">
                Selection logic
              </Text>
              <Text textStyle="body">{selectionLogicLabel}</Text>
              <Text color="muted" textStyle="body">
                {availableBaseYears.length} available single-year anchors and {availableWindowOptions.length} available long-run windows in the dataset.
              </Text>
            </Stack>
          </SimpleGrid>

          <Stack borderColor="edge" borderTopWidth="1px" gap="2" pt="4">
            <Text color="muted" textStyle="eyebrow">
              Source And Calculation Chain
            </Text>
            <Text color="muted" textStyle="caption">
              Anchor spot source:
              {anchorSource ? (
                <>
                  {" "}
                  {anchorSource.label}
                  <AnalysisCitationLinks refs={[anchorSource.ref]} />.
                </>
              ) : (
                " EUR/USD spot source unavailable."
              )}
              {" "}Observed base-month spot inputs (
              <Box as="span" fontStyle="italic">
                S
              </Box>
              <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                0
              </Box>
              )
            </Text>
            <Text color="muted" textStyle="caption">
              PPP inflation inputs:
              {pppInflationSources[0] ? (
                <>
                  {" "}
                  {pppInflationSources[0].label}
                  <AnalysisCitationLinks refs={[pppInflationSources[0].ref]} />{" "}
                  observed base and latest U.S. CPI terms (
                  <Box as="span" fontStyle="italic">
                    P
                  </Box>
                  <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                    h,t
                  </Box>
                  ,{" "}
                  <Box as="span" fontStyle="italic">
                    P
                  </Box>
                  <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                    h,0
                  </Box>
                  )
                </>
              ) : null}
              {pppInflationSources[1] ? (
                <>
                  {pppInflationSources[0] ? ", " : " "}
                  {pppInflationSources[1].label}
                  <AnalysisCitationLinks refs={[pppInflationSources[1].ref]} />{" "}
                  observed base and latest euro-area CPI terms (
                  <Box as="span" fontStyle="italic">
                    P
                  </Box>
                  <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                    f,t
                  </Box>
                  ,{" "}
                  <Box as="span" fontStyle="italic">
                    P
                  </Box>
                  <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                    f,0
                  </Box>
                  )
                </>
              ) : null}
            </Text>
            <Text color="muted" textStyle="caption">
              Window anchors calculate one current fair value per eligible base month and then aggregate those completed outputs into the active result (
              <Box as="span" fontStyle="italic">
                PPP
              </Box>
              <Box as="sub" display="inline-block" fontSize="0.7em" transform="translateY(0.22em)">
                t
              </Box>
              )
            </Text>
          </Stack>
        </Stack>
      </Stack>
    </Box>
  );
}

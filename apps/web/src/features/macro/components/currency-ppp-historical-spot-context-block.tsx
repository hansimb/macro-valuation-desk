"use client";

import React from "react";
import {
  Box,
  Button,
  ButtonGroup,
  HStack,
  Stack,
  Text,
} from "@chakra-ui/react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";

import {
  AnalysisCitationLinks,
  type AnalysisCitationRef,
} from "./analysis-citation-links";

type SpotHistoryPoint = {
  actualSpot: string;
  monthLabel: string;
  observationMonth: string;
};

type ParsedSpotHistoryPoint = SpotHistoryPoint & {
  parsedMonth: Date;
  parsedMonthValue: number;
  spotValue: number;
};

type ChartRange = "10Y" | "20Y" | "MAX";

type ChartRow = ParsedSpotHistoryPoint & {
  yearLabel: string;
};

function parseMonthStamp(value: string) {
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function subtractYears(date: Date, years: number) {
  const next = new Date(date);
  next.setUTCFullYear(next.getUTCFullYear() - years);
  return next;
}

function formatSpotValue(value: number) {
  return value.toFixed(4);
}

function formatAxisSpotValue(value: number) {
  return value.toFixed(3);
}

export function buildYearTicks(
  rows: Array<{ observationMonth: string }>,
  maxLabels = 6,
) {
  const ticks = rows
    .filter((row) => row.observationMonth.slice(5, 7) === "01")
    .map((row) => row.observationMonth);

  if (ticks.length <= maxLabels) {
    return ticks;
  }

  const step = Math.ceil((ticks.length - 1) / (maxLabels - 1));
  return ticks.filter((_, index) => index % step === 0);
}

function HistoricalSpotTooltip({
  active,
  payload,
}: TooltipContentProps) {
  if (!active || !payload?.length) {
    return null;
  }

  const point = payload[0]?.payload as ChartRow | undefined;
  if (!point) {
    return null;
  }

  return (
    <Box
      bg="rgba(10,14,28,0.96)"
      borderColor="rgba(126,145,168,0.28)"
      borderRadius="12px"
      borderWidth="1px"
      boxShadow="0 12px 28px rgba(0,0,0,0.28)"
      px="3"
      py="2.5"
    >
      <Text color="white" fontSize="xs" fontWeight="semibold">
        {point.observationMonth}
      </Text>
      <Text color="gray.300" fontSize="xs" mt="1">
        Spot {formatSpotValue(point.spotValue)}
      </Text>
    </Box>
  );
}

export function CurrencyPppHistoricalSpotContextBlock({
  anchorLabel,
  baseSpot,
  currentSpot,
  latestMonth,
  rows,
  spotRef,
}: {
  anchorLabel: string;
  baseSpot: string;
  currentSpot: string;
  latestMonth: string;
  rows: SpotHistoryPoint[];
  spotRef?: AnalysisCitationRef;
}) {
  const parsedRows = rows
    .map((row) => ({
      ...row,
      parsedMonth: parseMonthStamp(row.observationMonth),
      parsedMonthValue: parseMonthStamp(row.observationMonth)?.getTime() ?? Number.NaN,
      spotValue: Number.parseFloat(row.actualSpot),
      yearLabel: row.observationMonth.slice(0, 4),
    }))
    .filter(
      (row): row is ChartRow =>
        row.parsedMonth !== null && !Number.isNaN(row.spotValue),
    );

  const [selectedRange, setSelectedRange] = React.useState<ChartRange>("10Y");

  if (parsedRows.length < 2) {
    return null;
  }

  const latestRow = parsedRows[parsedRows.length - 1];
  const cutoffByRange: Record<Exclude<ChartRange, "MAX">, Date> = {
    "10Y": subtractYears(latestRow.parsedMonth, 10),
    "20Y": subtractYears(latestRow.parsedMonth, 20),
  };

  const chartRows =
    selectedRange === "MAX"
      ? parsedRows
      : parsedRows.filter(
          (row) => row.parsedMonth >= cutoffByRange[selectedRange],
        );

  const safeRows = chartRows.length >= 2 ? chartRows : parsedRows;
  const yearTicks = buildYearTicks(
    safeRows,
    selectedRange === "10Y" ? 6 : 7,
  );
  const xAxisTicks = yearTicks
    .map((value) => parseMonthStamp(value)?.getTime() ?? Number.NaN)
    .filter((value) => Number.isFinite(value));
  const baseSpotValue = Number.parseFloat(baseSpot);
  const currentSpotValue = Number.parseFloat(currentSpot);
  const latestObservationMonth = safeRows[safeRows.length - 1]?.parsedMonthValue;

  return (
    <Box
      bg="surface"
      borderColor="edge"
      borderWidth="1px"
      p={{ base: "6", md: "7" }}
      rounded="panel"
    >
      <Stack gap="4">
        <HStack align="start" gap="4" justify="space-between" wrap="wrap">
          <Stack gap="2">
            <Text
              color="accent"
              fontSize="xs"
              letterSpacing="0.16em"
              textTransform="uppercase"
            >
              Historical Spot Context
            </Text>
            <Text color="muted" fontSize="sm">
              Observed EUR/USD spot history with the selected long-run anchor
              spot shown as a reference line.
              {spotRef ? <AnalysisCitationLinks refs={[spotRef]} /> : null}
            </Text>
          </Stack>

          <ButtonGroup gap="2" size="2xs" variant="outline">
            {(["10Y", "20Y", "MAX"] as const).map((range) => (
              <Button
                colorPalette={selectedRange === range ? "blue" : undefined}
                key={range}
                onClick={() => setSelectedRange(range)}
                px="2.5"
                variant={selectedRange === range ? "solid" : "subtle"}
              >
                {range}
              </Button>
            ))}
          </ButtonGroup>
        </HStack>

        <HStack align="start" justify="space-between" gap="4" wrap="wrap">
          <Text color="muted" fontSize="xs">
            X-axis: yearly marks. Y-axis: observed EUR/USD spot.
          </Text>
          <Text color="muted" fontSize="xs">
            Hover the line to inspect month and spot.
          </Text>
        </HStack>

        <Box
          bg="canvas"
          borderColor="edge"
          borderWidth="1px"
          p={{ base: "4", md: "5" }}
          rounded="panel"
        >
          <Box
            aria-label="Historical EUR/USD spot context"
            h={{ base: "260px", md: "320px" }}
            role="img"
            w="100%"
          >
            <ResponsiveContainer
              height="100%"
              minHeight={260}
              minWidth={280}
              width="100%"
            >
              <LineChart
                data={safeRows}
                margin={{ top: 12, right: 12, bottom: 8, left: 4 }}
              >
                <CartesianGrid
                  horizontal
                  stroke="rgba(126,145,168,0.16)"
                  strokeDasharray="4 8"
                  vertical={false}
                />
                <XAxis
                  axisLine={{ stroke: "rgba(126,145,168,0.28)" }}
                  dataKey="parsedMonthValue"
                  domain={[
                    safeRows[0]?.parsedMonthValue ?? "dataMin",
                    safeRows[safeRows.length - 1]?.parsedMonthValue ?? "dataMax",
                  ]}
                  interval={0}
                  minTickGap={36}
                  padding={{ left: 16, right: 16 }}
                  scale="time"
                  stroke="#aeb7c5"
                  tick={{ fill: "#aeb7c5", fontSize: 12 }}
                  tickMargin={10}
                  tickLine={{ stroke: "rgba(126,145,168,0.24)" }}
                  ticks={xAxisTicks}
                  tickFormatter={(value: number) =>
                    new Date(value).getUTCFullYear().toString()
                  }
                  type="number"
                />
                <YAxis
                  axisLine={{ stroke: "rgba(126,145,168,0.28)" }}
                  domain={["auto", "auto"]}
                  stroke="#aeb7c5"
                  tick={{ fill: "#aeb7c5", fontSize: 12 }}
                  tickCount={5}
                  tickFormatter={formatAxisSpotValue}
                  tickLine={{ stroke: "rgba(126,145,168,0.24)" }}
                  width={54}
                />
                <Tooltip
                  content={(props) => <HistoricalSpotTooltip {...props} />}
                  cursor={{ stroke: "rgba(245,247,251,0.22)", strokeDasharray: "4 6" }}
                />
                {!Number.isNaN(baseSpotValue) ? (
                  <ReferenceLine
                    ifOverflow="extendDomain"
                    stroke="#e6b566"
                    strokeDasharray="6 6"
                    strokeWidth={2}
                    y={baseSpotValue}
                  />
                ) : null}
                <Line
                  activeDot={{ fill: "#f5f7fb", r: 5, stroke: "#7fb0ff", strokeWidth: 2 }}
                  dataKey="spotValue"
                  dot={false}
                  isAnimationActive={false}
                  stroke="#7fb0ff"
                  strokeWidth={3}
                  type="monotone"
                />
                {!Number.isNaN(currentSpotValue) && latestObservationMonth ? (
                  <ReferenceDot
                    fill="#f5f7fb"
                    ifOverflow="extendDomain"
                    r={5}
                    stroke="#7fb0ff"
                    strokeWidth={2}
                    x={latestObservationMonth}
                    y={currentSpotValue}
                    zIndex={700}
                  />
                ) : null}
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </Box>

        <HStack
          align="start"
          color="muted"
          flexWrap="wrap"
          fontSize="xs"
          gap="5"
        >
          <Text>Observed line: selected spot history.</Text>
          <Text>Dashed line: selected {anchorLabel} spot reference.</Text>
          <Text>Latest point: {latestMonth}.</Text>
        </HStack>
      </Stack>
    </Box>
  );
}

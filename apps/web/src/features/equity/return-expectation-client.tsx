"use client";

import React, { useState } from "react";
import { Box, Button, Grid, Heading, Input, SimpleGrid, Stack, Text } from "@chakra-ui/react";

import { AnalysisMetricCard } from "../macro/components/analysis-metric-card";

type ReturnModel = "gordon" | "earnings" | "fcf";
type GrowthBasis = "eps" | "revenue";
type GrowthMode = "direct" | "historical";
type DividendYieldMode = "direct" | "amounts";
type DividendGrowthMode = "direct" | "historical";
type YearCount = "4" | "5";
type EarningsYieldMode = "pe" | "amounts";
type FcfYieldMode = "direct" | "amounts";

type GrowthInputsState = {
  mode: GrowthMode;
  directPct: string;
  years: YearCount;
  historicalValues: string[];
};

type CalculatorState = {
  model: ReturnModel;
  growth: {
    basis: GrowthBasis;
    byBasis: Record<GrowthBasis, GrowthInputsState>;
  };
  gordon: {
    dividendYieldMode: DividendYieldMode;
    dividendYieldPct: string;
    annualDividendPerShare: string;
    sharePrice: string;
    dividendGrowthMode: DividendGrowthMode;
    dividendGrowthPct: string;
    dividendYears: YearCount;
    dividendHistory: string[];
  };
  earnings: {
    yieldMode: EarningsYieldMode;
    peRatio: string;
    marketCap: string;
    netIncome: string;
  };
  fcf: {
    yieldMode: FcfYieldMode;
    directYieldPct: string;
    marketCap: string;
    freeCashFlow: string;
  };
};

type SavedAnalysis = {
  name: string;
  state: CalculatorState;
};

const STORAGE_KEY = "equity-return-expectation-v1";
const SAVED_ANALYSES_STORAGE_KEY = "equity-return-expectation-analyses-v1";

const DEFAULT_STATE: CalculatorState = {
  model: "earnings",
  growth: {
    basis: "eps",
    byBasis: {
      eps: {
        mode: "historical",
        directPct: "",
        years: "5",
        historicalValues: ["", "", "", "", ""],
      },
      revenue: {
        mode: "historical",
        directPct: "",
        years: "5",
        historicalValues: ["", "", "", "", ""],
      },
    },
  },
  gordon: {
    dividendYieldMode: "amounts",
    dividendYieldPct: "",
    annualDividendPerShare: "",
    sharePrice: "",
    dividendGrowthMode: "historical",
    dividendGrowthPct: "",
    dividendYears: "5",
    dividendHistory: ["", "", "", "", ""],
  },
  earnings: {
    yieldMode: "amounts",
    peRatio: "",
    marketCap: "",
    netIncome: "",
  },
  fcf: {
    yieldMode: "amounts",
    directYieldPct: "",
    marketCap: "",
    freeCashFlow: "",
  },
};

function readPersistedState(): CalculatorState {
  if (typeof window === "undefined") {
    return DEFAULT_STATE;
  }

  try {
    const persisted = window.localStorage.getItem(STORAGE_KEY);
    if (!persisted) {
      return DEFAULT_STATE;
    }

    const parsed = JSON.parse(persisted) as Partial<CalculatorState>;
    return normalizeCalculatorState(parsed);
  } catch {
    return DEFAULT_STATE;
  }
}

function normalizeGrowthInputs(value?: Partial<GrowthInputsState>): GrowthInputsState {
  return {
    ...DEFAULT_STATE.growth.byBasis.eps,
    ...value,
    historicalValues: [
      ...(value?.historicalValues ?? DEFAULT_STATE.growth.byBasis.eps.historicalValues),
      "",
      "",
      "",
      "",
      "",
    ].slice(0, 5),
  };
}

function normalizeCalculatorState(value: Partial<CalculatorState>): CalculatorState {
  const legacyGrowth = value.growth as Partial<CalculatorState["growth"] & GrowthInputsState> | undefined;
  const epsGrowth = legacyGrowth?.byBasis?.eps ?? {
    mode: legacyGrowth?.mode,
    directPct: legacyGrowth?.directPct,
    years: legacyGrowth?.years,
    historicalValues: legacyGrowth?.historicalValues,
  };
  const revenueGrowth = legacyGrowth?.byBasis?.revenue;
  const gordon = {
    ...DEFAULT_STATE.gordon,
    ...value.gordon,
    dividendYieldMode: value.gordon?.dividendYieldMode ??
      (value.gordon?.dividendYieldPct ? "direct" : DEFAULT_STATE.gordon.dividendYieldMode),
    dividendGrowthMode: value.gordon?.dividendGrowthMode ??
      (value.gordon?.dividendGrowthPct ? "direct" : DEFAULT_STATE.gordon.dividendGrowthMode),
    dividendHistory: [
      ...(value.gordon?.dividendHistory ?? DEFAULT_STATE.gordon.dividendHistory),
      "",
      "",
      "",
      "",
      "",
    ].slice(0, 5),
  };
  const earnings = {
    ...DEFAULT_STATE.earnings,
    ...value.earnings,
    yieldMode: value.earnings?.yieldMode ?? (value.earnings?.peRatio ? "pe" : DEFAULT_STATE.earnings.yieldMode),
  };
  const fcf = {
    ...DEFAULT_STATE.fcf,
    ...value.fcf,
    yieldMode: value.fcf?.yieldMode ?? (value.fcf?.directYieldPct ? "direct" : DEFAULT_STATE.fcf.yieldMode),
  };

  return {
    ...DEFAULT_STATE,
    ...value,
    growth: {
      ...DEFAULT_STATE.growth,
      basis: value.growth?.basis ?? DEFAULT_STATE.growth.basis,
      byBasis: {
        eps: normalizeGrowthInputs(epsGrowth),
        revenue: normalizeGrowthInputs(revenueGrowth),
      },
    },
    gordon,
    earnings,
    fcf,
  };
}

function readPersistedAnalyses(): SavedAnalysis[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const persisted = window.localStorage.getItem(SAVED_ANALYSES_STORAGE_KEY);
    if (!persisted) {
      return [];
    }

    const parsed = JSON.parse(persisted) as Array<Partial<SavedAnalysis>>;
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .filter((analysis): analysis is SavedAnalysis => Boolean(analysis.name && analysis.state))
      .map((analysis) => ({
        name: analysis.name,
        state: normalizeCalculatorState(analysis.state),
      }));
  } catch {
    return [];
  }
}

function persistCurrentState(nextState: CalculatorState) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
  } catch {
    // Storage is convenience only; keep the calculator usable if persistence fails.
  }
}

function persistSavedAnalyses(nextAnalyses: SavedAnalysis[]) {
  try {
    window.localStorage.setItem(SAVED_ANALYSES_STORAGE_KEY, JSON.stringify(nextAnalyses));
  } catch {
    // Saved analyses are local convenience state only.
  }
}

function statesEqual(left: CalculatorState, right: CalculatorState) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function toNumber(value: string) {
  const parsed = Number.parseFloat(value.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : null;
}

function positiveNumber(value: string) {
  const parsed = toNumber(value);
  return parsed !== null && parsed > 0 ? parsed : null;
}

function formatPct(value: number | null) {
  return value === null || !Number.isFinite(value) ? "N/A" : `${value.toFixed(2)}%`;
}

function formatMultiple(value: number | null) {
  return value === null || !Number.isFinite(value) ? "N/A" : `${value.toFixed(1)}x`;
}

function averageHistoricalGrowth(values: string[], years: YearCount) {
  const selectedValues = values.slice(0, Number.parseInt(years, 10)).map(positiveNumber);
  if (selectedValues.some((value) => value === null)) {
    return null;
  }

  const numericValues = selectedValues as number[];
  const yearOverYearRates = numericValues.slice(1).map((value, index) => ((value / numericValues[index]) - 1) * 100);
  if (yearOverYearRates.length === 0) {
    return null;
  }

  return yearOverYearRates.reduce((sum, value) => sum + value, 0) / yearOverYearRates.length;
}

function selectedGrowthPct(state: CalculatorState) {
  const activeGrowth = state.growth.byBasis[state.growth.basis];
  if (activeGrowth.mode === "direct") {
    return toNumber(activeGrowth.directPct);
  }

  return averageHistoricalGrowth(activeGrowth.historicalValues, activeGrowth.years);
}

function earningsYieldPct(state: CalculatorState) {
  if (state.earnings.yieldMode === "pe") {
    const pe = positiveNumber(state.earnings.peRatio);
    return pe === null ? null : 100 / pe;
  }

  const marketCap = positiveNumber(state.earnings.marketCap);
  const netIncome = toNumber(state.earnings.netIncome);
  return marketCap === null || netIncome === null ? null : (netIncome / marketCap) * 100;
}

function impliedEarningsPe(state: CalculatorState) {
  if (state.earnings.yieldMode === "pe") {
    return positiveNumber(state.earnings.peRatio);
  }

  const marketCap = positiveNumber(state.earnings.marketCap);
  const netIncome = positiveNumber(state.earnings.netIncome);
  return marketCap === null || netIncome === null ? null : marketCap / netIncome;
}

function fcfYieldPct(state: CalculatorState) {
  if (state.fcf.yieldMode === "direct") {
    return toNumber(state.fcf.directYieldPct);
  }

  const marketCap = positiveNumber(state.fcf.marketCap);
  const freeCashFlow = toNumber(state.fcf.freeCashFlow);
  return marketCap === null || freeCashFlow === null ? null : (freeCashFlow / marketCap) * 100;
}

function dividendYieldPct(state: CalculatorState) {
  if (state.gordon.dividendYieldMode === "direct") {
    return toNumber(state.gordon.dividendYieldPct);
  }

  const annualDividendPerShare = toNumber(state.gordon.annualDividendPerShare);
  const sharePrice = positiveNumber(state.gordon.sharePrice);
  return annualDividendPerShare === null || sharePrice === null ? null : (annualDividendPerShare / sharePrice) * 100;
}

function impliedPriceToFcf(state: CalculatorState) {
  if (state.fcf.yieldMode === "direct") {
    const directYield = positiveNumber(state.fcf.directYieldPct);
    return directYield === null ? null : 100 / directYield;
  }

  const marketCap = positiveNumber(state.fcf.marketCap);
  const freeCashFlow = positiveNumber(state.fcf.freeCashFlow);
  return marketCap === null || freeCashFlow === null ? null : marketCap / freeCashFlow;
}

function sumNullable(left: number | null, right: number | null) {
  return left === null || right === null ? null : left + right;
}

function calculatorResults(state: CalculatorState) {
  const growthPct = selectedGrowthPct(state);
  const dividendYield = dividendYieldPct(state);
  const dividendGrowth = state.gordon.dividendGrowthMode === "direct"
    ? toNumber(state.gordon.dividendGrowthPct)
    : averageHistoricalGrowth(state.gordon.dividendHistory, state.gordon.dividendYears);
  const earningsYield = earningsYieldPct(state);
  const fcfYield = fcfYieldPct(state);

  if (state.model === "gordon") {
    return {
      primaryComponentLabel: "Dividend Yield",
      primaryComponent: dividendYield,
      growthLabel: "Dividend Growth",
      growthPct: dividendGrowth,
      impliedMultipleLabel: "Model Form",
      impliedMultiple: "Yield + growth",
      expectedReturn: sumNullable(dividendYield, dividendGrowth),
    };
  }

  if (state.model === "earnings") {
    return {
      primaryComponentLabel: "Earnings Yield",
      primaryComponent: earningsYield,
      growthLabel: state.growth.basis === "eps" ? "EPS Growth" : "Revenue Growth",
      growthPct,
      impliedMultipleLabel: "Implied P/E",
      impliedMultiple: formatMultiple(impliedEarningsPe(state)),
      expectedReturn: sumNullable(earningsYield, growthPct),
    };
  }

  return {
    primaryComponentLabel: "FCF Yield",
    primaryComponent: fcfYield,
    growthLabel: state.growth.basis === "eps" ? "EPS Growth" : "Revenue Growth",
    growthPct,
    impliedMultipleLabel: "Implied P/FCF",
    impliedMultiple: formatMultiple(impliedPriceToFcf(state)),
    expectedReturn: sumNullable(fcfYield, growthPct),
  };
}

function SegmentedButton<T extends string>({
  activeValue,
  children,
  onSelect,
  value,
}: {
  activeValue: T;
  children: React.ReactNode;
  onSelect: (value: T) => void;
  value: T;
}) {
  const active = activeValue === value;

  return (
    <Button
      aria-pressed={active}
      bg={active ? "accent" : "canvas"}
      borderColor="edge"
      borderWidth="1px"
      color={active ? "canvas" : "text"}
      minH="2.75rem"
      onClick={() => onSelect(value)}
      size="sm"
      variant="outline"
      whiteSpace="normal"
    >
      {children}
    </Button>
  );
}

function NumberField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  const id = label.toLowerCase().replace(/[^a-z0-9]+/g, "-");

  return (
    <Stack gap="2">
      <label htmlFor={id}>
        <Text as="span" color="muted" textStyle="body">
          {label}
        </Text>
      </label>
      <Input
        bg="canvas"
        borderColor="edge"
        color="text"
        id={id}
        inputMode="decimal"
        onChange={(event) => onChange(event.currentTarget.value)}
        rounded="control"
        value={value}
      />
    </Stack>
  );
}

function TextField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  const id = label.toLowerCase().replace(/[^a-z0-9]+/g, "-");

  return (
    <Stack gap="2">
      <label htmlFor={id}>
        <Text as="span" color="muted" textStyle="body">
          {label}
        </Text>
      </label>
      <Input
        bg="canvas"
        borderColor="edge"
        color="text"
        id={id}
        onChange={(event) => onChange(event.currentTarget.value)}
        rounded="control"
        value={value}
      />
    </Stack>
  );
}

function FormulaBlock({ model }: { model: ReturnModel }) {
  const formula = model === "gordon"
    ? "Expected return = dividend yield + expected dividend growth"
    : model === "earnings"
      ? "Expected return = earnings yield + expected growth"
      : "Expected return = free cash flow yield + expected growth";

  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="4">
        <Text color="accent" textStyle="eyebrow">
          Formula
        </Text>
        <Box bg="canvas" borderColor="edge" borderWidth="1px" p={{ base: "5", md: "6" }} rounded="panel">
          <Text textAlign={{ base: "left", md: "center" }} textStyle="formula">
            {formula}
          </Text>
        </Box>
        <Text color="muted" textStyle="body">
          This is a valuation calculator, not a live data feed. Enter the company values yourself; the selected model only combines the
          inputs into an expected annual return estimate.
        </Text>
      </Stack>
    </Box>
  );
}

function GrowthInputs({
  state,
  updateState,
}: {
  state: CalculatorState;
  updateState: (updater: (state: CalculatorState) => CalculatorState) => void;
}) {
  const activeGrowth = state.growth.byBasis[state.growth.basis];
  const selectedYears = Number.parseInt(activeGrowth.years, 10);

  function updateActiveGrowth(updater: (growth: GrowthInputsState) => GrowthInputsState) {
    updateState((current) => {
      const currentActiveGrowth = current.growth.byBasis[current.growth.basis];
      return {
        ...current,
        growth: {
          ...current.growth,
          byBasis: {
            ...current.growth.byBasis,
            [current.growth.basis]: updater(currentActiveGrowth),
          },
        },
      };
    });
  }

  return (
    <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
      <Stack gap="5">
        <Stack gap="2">
          <Text color="accent" textStyle="eyebrow">
            Growth Assumption
          </Text>
          <Text color="muted" textStyle="body">
            Use either a direct annual estimate or calculate the average realized annual growth from four or five yearly observations.
          </Text>
        </Stack>

        <Grid gap="2" templateColumns={{ base: "1fr", md: "repeat(2, minmax(0, 14rem))" }}>
          <SegmentedButton
            activeValue={state.growth.basis}
            onSelect={(basis) => updateState((current) => ({ ...current, growth: { ...current.growth, basis } }))}
            value="eps"
          >
            EPS growth
          </SegmentedButton>
          <SegmentedButton
            activeValue={state.growth.basis}
            onSelect={(basis) => updateState((current) => ({ ...current, growth: { ...current.growth, basis } }))}
            value="revenue"
          >
            Revenue growth
          </SegmentedButton>
        </Grid>

        <Grid gap="2" templateColumns={{ base: "1fr", md: "repeat(2, minmax(0, 14rem))" }}>
          <SegmentedButton
            activeValue={activeGrowth.mode}
            onSelect={(mode) => updateActiveGrowth((growth) => ({ ...growth, mode }))}
            value="historical"
          >
            Historical growth
          </SegmentedButton>
          <SegmentedButton
            activeValue={activeGrowth.mode}
            onSelect={(mode) => updateActiveGrowth((growth) => ({ ...growth, mode }))}
            value="direct"
          >
            Direct growth estimate
          </SegmentedButton>
        </Grid>

        {activeGrowth.mode === "direct" ? (
          <NumberField
            label="Expected annual growth"
            onChange={(directPct) => updateActiveGrowth((growth) => ({ ...growth, directPct }))}
            value={activeGrowth.directPct}
          />
        ) : (
          <Stack gap="4">
            <Grid gap="2" templateColumns={{ base: "repeat(2, minmax(0, 1fr))", md: "repeat(2, minmax(0, 8rem))" }}>
              <SegmentedButton
                activeValue={activeGrowth.years}
                onSelect={(years) => updateActiveGrowth((growth) => ({ ...growth, years }))}
                value="4"
              >
                4 years
              </SegmentedButton>
              <SegmentedButton
                activeValue={activeGrowth.years}
                onSelect={(years) => updateActiveGrowth((growth) => ({ ...growth, years }))}
                value="5"
              >
                5 years
              </SegmentedButton>
            </Grid>
            <SimpleGrid columns={{ base: 1, md: selectedYears === 5 ? 5 : 4 }} gap="3">
              {activeGrowth.historicalValues.slice(0, selectedYears).map((value, index) => (
                <NumberField
                  key={index}
                  label={`Year ${index + 1} value`}
                  onChange={(nextValue) => updateActiveGrowth((growth) => {
                    const historicalValues = [...growth.historicalValues];
                    historicalValues[index] = nextValue;
                    return { ...growth, historicalValues };
                  })}
                  value={value}
                />
              ))}
            </SimpleGrid>
          </Stack>
        )}
      </Stack>
    </Box>
  );
}

export function EquityReturnExpectationClient() {
  const [state, setState] = useState<CalculatorState>(() => readPersistedState());
  const [analysisName, setAnalysisName] = useState("");
  const [selectedAnalysisName, setSelectedAnalysisName] = useState("");
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>(() => readPersistedAnalyses());
  const results = calculatorResults(state);
  const selectedSavedAnalysis = savedAnalyses.find((analysis) => analysis.name === selectedAnalysisName);
  const trimmedAnalysisName = analysisName.trim();
  const analysisStatus = selectedSavedAnalysis
    ? statesEqual(state, selectedSavedAnalysis.state) && trimmedAnalysisName === selectedSavedAnalysis.name
      ? `Saved analysis: ${selectedSavedAnalysis.name}`
      : `Unsaved changes to ${selectedSavedAnalysis.name}`
    : trimmedAnalysisName
      ? `Unsaved analysis: ${trimmedAnalysisName}`
      : "Unnamed analysis";

  function updateState(updater: (state: CalculatorState) => CalculatorState) {
    setState((current) => {
      const next = updater(current);
      persistCurrentState(next);
      return next;
    });
  }

  function updateAnalysisName(nextName: string) {
    setAnalysisName(nextName);
    if (selectedAnalysisName && nextName.trim() !== selectedAnalysisName) {
      setSelectedAnalysisName("");
    }
  }

  function saveNamedAnalysis() {
    if (!trimmedAnalysisName) {
      return;
    }

    const nextAnalysis = { name: trimmedAnalysisName, state };
    const nextAnalyses = [
      ...savedAnalyses.filter((analysis) => analysis.name.toLowerCase() !== trimmedAnalysisName.toLowerCase()),
      nextAnalysis,
    ].sort((left, right) => left.name.localeCompare(right.name));
    setSavedAnalyses(nextAnalyses);
    setAnalysisName(trimmedAnalysisName);
    setSelectedAnalysisName(trimmedAnalysisName);
    persistSavedAnalyses(nextAnalyses);
  }

  function loadNamedAnalysis(name: string) {
    const savedAnalysis = savedAnalyses.find((analysis) => analysis.name === name);
    if (!savedAnalysis) {
      setSelectedAnalysisName("");
      return;
    }

    setAnalysisName(savedAnalysis.name);
    setSelectedAnalysisName(savedAnalysis.name);
    setState(savedAnalysis.state);
    persistCurrentState(savedAnalysis.state);
  }

  function deleteSelectedAnalysis() {
    if (!selectedAnalysisName) {
      return;
    }

    const nextAnalyses = savedAnalyses.filter((analysis) => analysis.name !== selectedAnalysisName);
    setSavedAnalyses(nextAnalyses);
    setAnalysisName("");
    setSelectedAnalysisName("");
    persistSavedAnalyses(nextAnalyses);
  }

  function startNewAnalysis() {
    const nextState = normalizeCalculatorState({});
    setState(nextState);
    setAnalysisName("");
    setSelectedAnalysisName("");
    persistCurrentState(nextState);
  }

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="5">
          <Stack align={{ base: "stretch", md: "start" }} direction={{ base: "column", md: "row" }} gap="4" justify="space-between">
            <Stack gap="2">
              <Text color="accent" textStyle="eyebrow">
                Saved Analyses
              </Text>
              <Text color="muted" textStyle="body">
                Saved analyses are stored only on this device.
              </Text>
              <Text color={selectedSavedAnalysis && !analysisStatus.startsWith("Saved") ? "accent" : "muted"} textStyle="body">
                {analysisStatus}
              </Text>
            </Stack>
            <Button
              bg="canvas"
              borderColor="edge"
              borderWidth="1px"
              color="text"
              minH="2.5rem"
              onClick={startNewAnalysis}
              rounded="control"
              size="sm"
              variant="outline"
            >
              New analysis
            </Button>
          </Stack>
          <SimpleGrid columns={{ base: 1, md: 4 }} gap="4">
            <TextField label="Analysis name" onChange={updateAnalysisName} value={analysisName} />
            <Stack gap="2">
              <label htmlFor="saved-analyses">
                <Text as="span" color="muted" textStyle="body">
                  Selected analysis
                </Text>
              </label>
              <Box position="relative">
                <select
                  aria-label="Selected analysis"
                  id="saved-analyses"
                  onChange={(event) => loadNamedAnalysis(event.currentTarget.value)}
                  style={{
                    appearance: "none",
                    background: "#040612",
                    border: "1px solid #7e91a8",
                    borderRadius: "4px",
                    color: "#d9e8ff",
                    fontSize: "var(--chakra-font-sizes-body)",
                    minHeight: "2.5rem",
                    paddingInlineEnd: "2.25rem",
                    paddingInlineStart: "0.75rem",
                    width: "100%",
                  }}
                  value={selectedAnalysisName}
                >
                  <option style={{ background: "#181A1B", color: "#d9e8ff" }} value="">
                    Select saved analysis
                  </option>
                  {savedAnalyses.map((analysis) => (
                    <option key={analysis.name} style={{ background: "#181A1B", color: "#d9e8ff" }} value={analysis.name}>
                      {analysis.name}
                    </option>
                  ))}
                </select>
                <Box aria-hidden="true" color="text" pointerEvents="none" position="absolute" right="0.75rem" top="50%" transform="translateY(-50%)">
                  v
                </Box>
              </Box>
            </Stack>
            <Stack gap="2" justify="end">
              <Text aria-hidden="true" color="muted" textStyle="body">
                &nbsp;
              </Text>
              <Button
                bg="accent"
                color="canvas"
                disabled={!analysisName.trim()}
                minH="2.5rem"
                onClick={saveNamedAnalysis}
                rounded="control"
                size="sm"
              >
                Save analysis
              </Button>
            </Stack>
            <Stack gap="2" justify="end">
              <Text aria-hidden="true" color="muted" textStyle="body">
                &nbsp;
              </Text>
              <Button
                bg="canvas"
                borderColor="edge"
                borderWidth="1px"
                color="text"
                disabled={!selectedAnalysisName}
                minH="2.5rem"
                onClick={deleteSelectedAnalysis}
                rounded="control"
                size="sm"
                variant="outline"
              >
                Delete analysis
              </Button>
            </Stack>
          </SimpleGrid>
        </Stack>
      </Box>

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="4">
          <Text color="accent" textStyle="eyebrow">
            Model
          </Text>
          <Grid gap="2" templateColumns={{ base: "1fr", md: "repeat(3, minmax(0, 1fr))" }}>
            <SegmentedButton
              activeValue={state.model}
              onSelect={(model) => updateState((current) => ({ ...current, model }))}
              value="gordon"
            >
              Gordon Growth
            </SegmentedButton>
            <SegmentedButton
              activeValue={state.model}
              onSelect={(model) => updateState((current) => ({ ...current, model }))}
              value="earnings"
            >
              Earnings Yield + Growth
            </SegmentedButton>
            <SegmentedButton
              activeValue={state.model}
              onSelect={(model) => updateState((current) => ({ ...current, model }))}
              value="fcf"
            >
              FCF Yield + Growth
            </SegmentedButton>
          </Grid>
        </Stack>
      </Box>

      <FormulaBlock model={state.model} />

      {state.model === "gordon" ? (
        <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
          <Stack gap="5">
            <Stack gap="2">
              <Text color="accent" textStyle="eyebrow">
                Gordon Growth Inputs
              </Text>
              <Text color="muted" textStyle="body">
                Gordon-style expected return uses the current dividend yield plus expected long-run dividend growth.
              </Text>
            </Stack>
            <Stack gap="4">
              <Grid gap="2" templateColumns={{ base: "1fr", md: "repeat(2, minmax(0, 14rem))" }}>
                <SegmentedButton
                  activeValue={state.gordon.dividendYieldMode}
                  onSelect={(dividendYieldMode) =>
                    updateState((current) => ({ ...current, gordon: { ...current.gordon, dividendYieldMode } }))
                  }
                  value="amounts"
                >
                  Dividend amount input
                </SegmentedButton>
                <SegmentedButton
                  activeValue={state.gordon.dividendYieldMode}
                  onSelect={(dividendYieldMode) =>
                    updateState((current) => ({ ...current, gordon: { ...current.gordon, dividendYieldMode } }))
                  }
                  value="direct"
                >
                  Dividend yield input
                </SegmentedButton>
              </Grid>
              {state.gordon.dividendYieldMode === "direct" ? (
                <NumberField
                  label="Dividend yield"
                  onChange={(dividendYieldPct) => updateState((current) => ({ ...current, gordon: { ...current.gordon, dividendYieldPct } }))}
                  value={state.gordon.dividendYieldPct}
                />
              ) : (
                <SimpleGrid columns={{ base: 1, md: 2 }} gap="4">
                  <NumberField
                    label="Annual dividend per share"
                    onChange={(annualDividendPerShare) =>
                      updateState((current) => ({ ...current, gordon: { ...current.gordon, annualDividendPerShare } }))
                    }
                    value={state.gordon.annualDividendPerShare}
                  />
                  <NumberField
                    label="Share price"
                    onChange={(sharePrice) => updateState((current) => ({ ...current, gordon: { ...current.gordon, sharePrice } }))}
                    value={state.gordon.sharePrice}
                  />
                </SimpleGrid>
              )}
            </Stack>
            <Grid gap="2" templateColumns={{ base: "1fr", md: "repeat(2, minmax(0, 14rem))" }}>
              <SegmentedButton
                activeValue={state.gordon.dividendGrowthMode}
                onSelect={(dividendGrowthMode) =>
                  updateState((current) => ({ ...current, gordon: { ...current.gordon, dividendGrowthMode } }))
                }
                value="historical"
              >
                Historical dividend growth
              </SegmentedButton>
              <SegmentedButton
                activeValue={state.gordon.dividendGrowthMode}
                onSelect={(dividendGrowthMode) =>
                  updateState((current) => ({ ...current, gordon: { ...current.gordon, dividendGrowthMode } }))
                }
                value="direct"
              >
                Direct dividend growth
              </SegmentedButton>
            </Grid>
            {state.gordon.dividendGrowthMode === "direct" ? (
              <NumberField
                label="Dividend growth"
                onChange={(dividendGrowthPct) => updateState((current) => ({ ...current, gordon: { ...current.gordon, dividendGrowthPct } }))}
                value={state.gordon.dividendGrowthPct}
              />
            ) : (
              <Stack gap="4">
                <Grid gap="2" templateColumns={{ base: "repeat(2, minmax(0, 1fr))", md: "repeat(2, minmax(0, 8rem))" }}>
                  <SegmentedButton
                    activeValue={state.gordon.dividendYears}
                    onSelect={(dividendYears) =>
                      updateState((current) => ({ ...current, gordon: { ...current.gordon, dividendYears } }))
                    }
                    value="4"
                  >
                    4 years
                  </SegmentedButton>
                  <SegmentedButton
                    activeValue={state.gordon.dividendYears}
                    onSelect={(dividendYears) =>
                      updateState((current) => ({ ...current, gordon: { ...current.gordon, dividendYears } }))
                    }
                    value="5"
                  >
                    5 years
                  </SegmentedButton>
                </Grid>
                <SimpleGrid columns={{ base: 1, md: state.gordon.dividendYears === "5" ? 5 : 4 }} gap="3">
                  {state.gordon.dividendHistory.slice(0, Number.parseInt(state.gordon.dividendYears, 10)).map((value, index) => (
                    <NumberField
                      key={index}
                      label={`Dividend year ${index + 1}`}
                      onChange={(nextValue) =>
                        updateState((current) => {
                          const dividendHistory = [...current.gordon.dividendHistory];
                          dividendHistory[index] = nextValue;
                          return { ...current, gordon: { ...current.gordon, dividendHistory } };
                        })
                      }
                      value={value}
                    />
                  ))}
                </SimpleGrid>
              </Stack>
            )}
          </Stack>
        </Box>
      ) : null}

      {state.model === "earnings" ? (
        <>
          <GrowthInputs state={state} updateState={updateState} />
          <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="5">
              <Stack gap="2">
                <Text color="accent" textStyle="eyebrow">
                  Earnings Yield
                </Text>
                <Text color="muted" textStyle="body">
                  Enter P/E directly, or calculate earnings yield and P/E from market capitalization and net income.
                </Text>
              </Stack>
              <Grid gap="2" templateColumns={{ base: "1fr", md: "repeat(2, minmax(0, 14rem))" }}>
                <SegmentedButton
                  activeValue={state.earnings.yieldMode}
                  onSelect={(yieldMode) => updateState((current) => ({ ...current, earnings: { ...current.earnings, yieldMode } }))}
                  value="amounts"
                >
                  Market cap input
                </SegmentedButton>
                <SegmentedButton
                  activeValue={state.earnings.yieldMode}
                  onSelect={(yieldMode) => updateState((current) => ({ ...current, earnings: { ...current.earnings, yieldMode } }))}
                  value="pe"
                >
                  P/E input
                </SegmentedButton>
              </Grid>
              {state.earnings.yieldMode === "pe" ? (
                <NumberField
                  label="P/E ratio"
                  onChange={(peRatio) => updateState((current) => ({ ...current, earnings: { ...current.earnings, peRatio } }))}
                  value={state.earnings.peRatio}
                />
              ) : (
                <SimpleGrid columns={{ base: 1, md: 2 }} gap="4">
                  <NumberField
                    label="Market capitalization"
                    onChange={(marketCap) => updateState((current) => ({ ...current, earnings: { ...current.earnings, marketCap } }))}
                    value={state.earnings.marketCap}
                  />
                  <NumberField
                    label="Net income"
                    onChange={(netIncome) => updateState((current) => ({ ...current, earnings: { ...current.earnings, netIncome } }))}
                    value={state.earnings.netIncome}
                  />
                </SimpleGrid>
              )}
            </Stack>
          </Box>
        </>
      ) : null}

      {state.model === "fcf" ? (
        <>
          <GrowthInputs state={state} updateState={updateState} />
          <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
            <Stack gap="5">
              <Stack gap="2">
                <Text color="accent" textStyle="eyebrow">
                  Free Cash Flow Yield
                </Text>
                <Text color="muted" textStyle="body">
                  Enter FCF yield directly, or calculate it from market capitalization and free cash flow.
                </Text>
              </Stack>
              <Grid gap="2" templateColumns={{ base: "1fr", md: "repeat(2, minmax(0, 14rem))" }}>
                <SegmentedButton
                  activeValue={state.fcf.yieldMode}
                  onSelect={(yieldMode) => updateState((current) => ({ ...current, fcf: { ...current.fcf, yieldMode } }))}
                  value="amounts"
                >
                  FCF amount input
                </SegmentedButton>
                <SegmentedButton
                  activeValue={state.fcf.yieldMode}
                  onSelect={(yieldMode) => updateState((current) => ({ ...current, fcf: { ...current.fcf, yieldMode } }))}
                  value="direct"
                >
                  FCF yield input
                </SegmentedButton>
              </Grid>
              {state.fcf.yieldMode === "direct" ? (
                <NumberField
                  label="FCF yield"
                  onChange={(directYieldPct) => updateState((current) => ({ ...current, fcf: { ...current.fcf, directYieldPct } }))}
                  value={state.fcf.directYieldPct}
                />
              ) : (
                <SimpleGrid columns={{ base: 1, md: 2 }} gap="4">
                  <NumberField
                    label="Market capitalization"
                    onChange={(marketCap) => updateState((current) => ({ ...current, fcf: { ...current.fcf, marketCap } }))}
                    value={state.fcf.marketCap}
                  />
                  <NumberField
                    label="Free cash flow"
                    onChange={(freeCashFlow) => updateState((current) => ({ ...current, fcf: { ...current.fcf, freeCashFlow } }))}
                    value={state.fcf.freeCashFlow}
                  />
                </SimpleGrid>
              )}
            </Stack>
          </Box>
        </>
      ) : null}

      <Box bg="surface" borderColor="edge" borderWidth="1px" p={{ base: "6", md: "7" }} rounded="panel">
        <Stack gap="5">
          <Stack gap="2">
            <Text color="accent" textStyle="eyebrow">
              Result
            </Text>
            <Heading as="h2" textStyle="title">
              Expected Return Estimate
            </Heading>
          </Stack>
          <SimpleGrid columns={{ base: 1, md: 2, xl: 4 }} gap="4">
            <AnalysisMetricCard
              label="Expected Return"
              note="Primary model output"
              value={formatPct(results.expectedReturn)}
            />
            <AnalysisMetricCard
              label={results.primaryComponentLabel}
              note="Yield component"
              value={formatPct(results.primaryComponent)}
            />
            <AnalysisMetricCard
              label={results.growthLabel}
              note="Growth component"
              value={formatPct(results.growthPct)}
            />
            <AnalysisMetricCard
              label={results.impliedMultipleLabel}
              note="Diagnostic valuation multiple"
              value={results.impliedMultiple}
            />
          </SimpleGrid>
        </Stack>
      </Box>
    </Stack>
  );
}

"use client";

import React from "react";
import { useEffect, useState } from "react";
import { Stack } from "@chakra-ui/react";

import type { TaylorRulePageData, TaylorRuleReferenceItem, TaylorRuleRegionComparison } from "./taylor-rule-types";
import { AnalysisReferencesBlock } from "./components/analysis-references-block";
import { TaylorAssumptionsPanels } from "./components/taylor-assumptions-panels";
import { TaylorFormulaBlock } from "./components/taylor-formula-block";
import { TaylorReferencePanels } from "./components/taylor-reference-panels";
import { TaylorScenarioPanels } from "./components/taylor-scenario-panels";

type RegionAssumptions = {
  inflationMeasure: "headline" | "core";
  neutralRate: string;
  slackProxy: string;
};

const ADJUSTMENT_STEP = 0.25;
const ASSUMPTIONS_STORAGE_KEY = "taylor-rule-assumptions-v1";

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
  inflationMeasure: "headline" | "core",
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
    policyGap: policyGap.toFixed(2),
  };
}

function buildInterpretation(
  region: TaylorRuleRegionComparison,
  neutralRate: string,
  slackProxy: string,
  inflationMeasure: "headline" | "core",
) {
  const scenario = calculateScenario(region, neutralRate, slackProxy, inflationMeasure);
  const gap = toNumber(scenario.policyGap);

  if (gap >= 0) {
    return `${region.region} screens tighter than the rule benchmark by ${scenario.policyGap} percentage points.`;
  }

  return `${region.region} screens easier than the rule benchmark by ${Math.abs(gap).toFixed(2)} percentage points.`;
}

function buildInitialAssumptions(regions: TaylorRuleRegionComparison[]) {
  return regions.reduce<Record<string, RegionAssumptions>>((accumulator, region) => {
    accumulator[region.region] = {
      neutralRate: "0.00",
      slackProxy: "0.00",
      inflationMeasure: "headline",
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
  persisted: unknown,
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

function readPersistedAssumptions() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const persisted = window.localStorage.getItem(ASSUMPTIONS_STORAGE_KEY);
    return persisted ? JSON.parse(persisted) : null;
  } catch {
    return null;
  }
}

function buildClientInitialAssumptions(regions: TaylorRuleRegionComparison[]) {
  return mergePersistedAssumptions(regions, readPersistedAssumptions());
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
  kind: "policy" | "inflation" | "core" | "market" | "output" | "gdp",
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

export function TaylorRuleClient({ data }: { data: TaylorRulePageData }) {
  const [assumptionsByRegion, setAssumptionsByRegion] = useState<Record<string, RegionAssumptions>>(
    () => buildClientInitialAssumptions(data.regions),
  );
  const hasRegionData = data.regions.length > 0;
  const referenceNumberByLabel = new Map(data.references.map((reference, index) => [reference.label, index + 1]));

  function persistAssumptions(nextAssumptions: Record<string, RegionAssumptions>) {
    try {
      window.localStorage.setItem(ASSUMPTIONS_STORAGE_KEY, JSON.stringify(nextAssumptions));
    } catch {
      // Ignore storage failures and keep the UI state usable.
    }
  }

  function setRegionAssumptionsAndPersist(
    updater: (current: Record<string, RegionAssumptions>) => Record<string, RegionAssumptions>,
  ) {
    setAssumptionsByRegion((current) => {
      const next = updater(current);
      persistAssumptions(next);
      return next;
    });
  }

  function updateRegionAssumption(regionKey: string, field: "neutralRate" | "slackProxy", delta: number) {
    setRegionAssumptionsAndPersist((current) => ({
      ...current,
      [regionKey]: {
        ...current[regionKey],
        [field]: adjustValue(current[regionKey][field], delta),
      },
    }));
  }

  function getReferenceLookup(region: TaylorRuleRegionComparison) {
    const headlineReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "inflation"));
    const coreReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "core"));
    const policyReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "policy"));
    const marketReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "market"));
    const outputReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "output"));
    const gdpReferenceItem = data.references.find((reference) => reference.label === labelReference(region, "gdp"));

    const headlineReference = referenceNumberByLabel.get(labelReference(region, "inflation"));
    const coreReference = referenceNumberByLabel.get(labelReference(region, "core"));
    const policyReference = referenceNumberByLabel.get(labelReference(region, "policy"));
    const marketReference = referenceNumberByLabel.get(labelReference(region, "market"));
    const outputReference = referenceNumberByLabel.get(labelReference(region, "output"));
    const gdpReference = referenceNumberByLabel.get(labelReference(region, "gdp"));

    return {
      ...(headlineReference ? { headline: { href: headlineReferenceItem?.url, number: headlineReference } } : {}),
      ...(coreReference ? { core: { href: coreReferenceItem?.url, number: coreReference } } : {}),
      ...(policyReference ? { policy: { href: policyReferenceItem?.url, number: policyReference } } : {}),
      ...(marketReference ? { market: { href: marketReferenceItem?.url, number: marketReference } } : {}),
      ...(outputReference ? { output: { href: outputReferenceItem?.url, number: outputReference } } : {}),
      ...(gdpReference ? { gdp: { href: gdpReferenceItem?.url, number: gdpReference } } : {}),
    };
  }

  useEffect(() => {
    setAssumptionsByRegion(mergePersistedAssumptions(data.regions, readPersistedAssumptions()));
  }, [data.regions]);

  return (
    <Stack gap={{ base: "8", md: "10" }}>
      <TaylorFormulaBlock />

      <TaylorReferencePanels getReferenceLookup={getReferenceLookup} regions={data.regions} />

      {hasRegionData ? (
        <>
          <TaylorAssumptionsPanels
            assumptionsByRegion={assumptionsByRegion}
            onAdjust={updateRegionAssumption}
            onSetInflationMeasure={(region, inflationMeasure) =>
              setRegionAssumptionsAndPersist((current) => ({
                ...current,
                [region]: {
                  ...current[region],
                  inflationMeasure,
                },
              }))
            }
            regions={data.regions}
          />

          <TaylorScenarioPanels
            assumptionsByRegion={assumptionsByRegion}
            getInterpretation={(region, assumptions) =>
              buildInterpretation(region, assumptions.neutralRate, assumptions.slackProxy, assumptions.inflationMeasure)
            }
            getReferenceLookup={getReferenceLookup}
            getScenario={(region, assumptions) =>
              calculateScenario(region, assumptions.neutralRate, assumptions.slackProxy, assumptions.inflationMeasure)
            }
            getSelectedInflationValue={selectedInflationValue}
            regions={data.regions}
          />
        </>
      ) : null}

      <AnalysisReferencesBlock
        items={data.references.map((reference) => ({
          href: reference.url,
          key: reference.label,
          note: reference.note,
          text: ieeeReferenceText(referenceNumberByLabel.get(reference.label) ?? 0, reference),
        }))}
      />
    </Stack>
  );
}

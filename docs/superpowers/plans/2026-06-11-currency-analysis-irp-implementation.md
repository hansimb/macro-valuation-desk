# Currency Analysis IRP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete `2.0 Interest Rate Parity` for the existing `Currency Analysis` page by making the IRP pipeline support optional observed forwards, serving a stable `CIP`/`UIP` contract, and rendering a theory-first IRP section in the current UI style.

**Architecture:** Keep the existing `source -> pipeline -> postgres -> api -> web` boundary. The pipeline owns parity calculations, Postgres stores mart-ready IRP rows, the API only shapes mart data, and the web layer renders formulas, inputs, outputs, takeaways, and references without provider-specific logic.

**Tech Stack:** Python, Prefect, PostgreSQL, Fastify, Next.js, TypeScript, Chakra UI, pytest, Vitest

---

## Scope Boundary

This plan covers only `2.0 Interest Rate Parity`.

Do not change the PPP methodology except where `currency-analysis-client.tsx` must stop hiding IRP when PPP is unavailable.

Do not register fake `EUR/USD` forward series. `apps/pipelines/tests/test_source_registry.py` already asserts that `eurusd_forward_3m`, `eurusd_forward_6m`, and `eurusd_forward_12m` are not registered without a real source path. Keep that rule.

Observed-forward support should be implemented as optional transform/API/UI capability so the system is ready when a reliable source exists. In current v1 data, the UI should honestly show `CIP` rows without observed-forward basis values.

## Current State Summary

- `apps/pipelines/src/lib/pipeline/transforms/currency_irp.py` already builds `3M`, `6M`, and `12M` `CIP`/`UIP` rows from `eurusd_spot_daily`, `eur_*_rate`, and `usd_*_rate`.
- `apps/pipelines/src/sql/pipeline_schema.sql` already has `mart.currency_irp_snapshots` with optional `observed_forward`, `cip_basis_bps`, `forward_series_key`, `forward_source_url`, and `has_observed_forward`.
- `packages/shared/src/contracts/currency-analysis.ts` already exposes `irp.cipRows` and `irp.uip.rows`.
- `apps/api/src/routes/currency-analysis.ts` already reads `mart.currency_irp_snapshots`, but `UIP` row shaping currently depends on array index alignment after sorting and should be made tenor-keyed.
- `apps/web/src/features/macro/currency-analysis-client.tsx` renders only PPP. It returns `null` when PPP summary is missing, so IRP cannot render independently yet.
- Reusable UI pieces already exist under `apps/web/src/features/macro/components/`: `AnalysisFormulaTerms`, `AnalysisCitationLinks`, `AnalysisReferencesBlock`, and `AnalysisMetricCard`.

## File Map

### Modify

- `apps/pipelines/src/lib/pipeline/transforms/currency_irp.py`
- `apps/pipelines/tests/test_currency_irp_transform.py`
- `apps/api/src/routes/currency-analysis.ts`
- `apps/api/tests/currency-analysis-route.test.ts`
- `apps/web/src/features/macro/currency-analysis-client.tsx`
- `apps/web/tests/currency-analysis-page.test.tsx`

### Create

- `apps/web/src/features/macro/components/currency-irp-formula-block.tsx`
- `apps/web/src/features/macro/components/currency-irp-data-inputs-block.tsx`
- `apps/web/src/features/macro/components/currency-irp-tenor-table-block.tsx`
- `apps/web/src/features/macro/components/currency-irp-uip-block.tsx`

### Explicitly Do Not Modify Unless A Real Forward Source Is Confirmed

- `apps/pipelines/src/lib/source/registry.py`
- `apps/pipelines/src/tasks/run_currency_market_etl.py`

---

### Task 1: Make IRP Transform Forward-Aware Without Requiring Forward Data

**Files:**
- Modify: `apps/pipelines/src/lib/pipeline/transforms/currency_irp.py`
- Modify: `apps/pipelines/tests/test_currency_irp_transform.py`

- [ ] **Step 1: Add a failing transform test for optional observed forwards**

Append this test to `apps/pipelines/tests/test_currency_irp_transform.py`. It uses a synthetic staged forward row to verify transform behavior only; it does not imply the source registry has a real forward provider.

```python
def test_build_currency_irp_outputs_includes_observed_forward_when_staged_forward_exists():
    staging_rows = [
        {
            "series_id": "eurusd_spot_daily",
            "observation_date": "2026-05-30",
            "numeric_value": 1.14,
            "category": "fx_spot",
            "region": "FX",
            "frequency": "daily",
            "unit": "usd_per_eur",
            "provider": "ecb",
            "source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
            "is_valid": True,
        },
        {
            "series_id": "eur_3m_rate",
            "observation_date": "2026-05-30",
            "numeric_value": 2.0,
            "category": "market_rate",
            "region": "EU",
            "frequency": "daily",
            "unit": "percent",
            "provider": "ecb",
            "source_url": "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR",
            "is_valid": True,
        },
        {
            "series_id": "usd_3m_rate",
            "observation_date": "2026-05-30",
            "numeric_value": 4.0,
            "category": "market_rate",
            "region": "US",
            "frequency": "daily",
            "unit": "percent",
            "provider": "fred",
            "source_url": "https://fred.stlouisfed.org/series/DTB3",
            "is_valid": True,
        },
        {
            "series_id": "eurusd_forward_3m",
            "observation_date": "2026-05-30",
            "numeric_value": 1.1330,
            "category": "fx_forward",
            "region": "FX",
            "frequency": "daily",
            "unit": "usd_per_eur",
            "provider": "verified-provider",
            "source_url": "https://example.com/verified-forward-source",
            "is_valid": True,
        },
    ]

    outputs = build_currency_irp_outputs(staging_rows)

    assert outputs["snapshot_rows"] == [
        {
            "pair_key": "eurusd",
            "as_of_date": "2026-05-30",
            "tenor": "3M",
            "spot": 1.14,
            "eur_rate": 2.0,
            "usd_rate": 4.0,
            "rate_spread": -2.0,
            "cip_implied_forward": 1.1344,
            "observed_forward": 1.133,
            "cip_basis_bps": -11.9,
            "uip_implied_move_pct": -0.5,
            "uip_implied_spot": 1.1343,
            "spot_series_key": "eurusd_spot_daily",
            "spot_source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A",
            "eur_rate_series_key": "eur_3m_rate",
            "eur_rate_source_url": "https://data.ecb.europa.eu/data/datasets/EST/EST.B.EU000A2QQF32.CR",
            "usd_rate_series_key": "usd_3m_rate",
            "usd_rate_source_url": "https://fred.stlouisfed.org/series/DTB3",
            "forward_series_key": "eurusd_forward_3m",
            "forward_source_url": "https://example.com/verified-forward-source",
            "has_observed_forward": True,
        }
    ]
    assert outputs["availability_rows"][0]["status"] == "available"
    assert outputs["availability_rows"][0]["detail"] == "Observed forward comparison available."
```

- [ ] **Step 2: Run the failing transform test**

Run:

```bash
pytest apps/pipelines/tests/test_currency_irp_transform.py::test_build_currency_irp_outputs_includes_observed_forward_when_staged_forward_exists -v
```

Expected: FAIL because `currency_irp.py` currently always sets `observed_forward`, `cip_basis_bps`, `forward_series_key`, and `forward_source_url` to `None`.

- [ ] **Step 3: Implement optional forward support in the transform**

Update `apps/pipelines/src/lib/pipeline/transforms/currency_irp.py` with these exact structural changes:

```python
FORWARD_SERIES_BY_TENOR = {
    "3M": "eurusd_forward_3m",
    "6M": "eurusd_forward_6m",
    "12M": "eurusd_forward_12m",
}


def _round_basis_points(value: float) -> float:
    return round(value, 1)
```

Inside the tenor loop, after `cip_implied_forward` is calculated:

```python
        forward_series_key = FORWARD_SERIES_BY_TENOR[tenor]
        forward_row = _latest_row(staging_rows, forward_series_key)
        observed_forward = float(forward_row["numeric_value"]) if forward_row is not None else None
        cip_basis_bps = (
            ((observed_forward - cip_implied_forward) / spot) * 10000
            if observed_forward is not None
            else None
        )
```

Replace the existing hardcoded forward fields in `snapshot_rows.append(...)` with:

```python
                "observed_forward": _round_price(observed_forward) if observed_forward is not None else None,
                "cip_basis_bps": _round_basis_points(cip_basis_bps) if cip_basis_bps is not None else None,
                "forward_series_key": forward_series_key if forward_row is not None else None,
                "forward_source_url": str(forward_row["source_url"]) if forward_row is not None else None,
                "has_observed_forward": forward_row is not None,
```

Replace the existing `partial` availability append with:

```python
        availability_rows.append(
            {
                "pair_key": PAIR_KEY,
                "section_key": IRP_SECTION_KEY,
                "item_key": tenor,
                "status": "available" if forward_row is not None else "partial",
                "detail": (
                    "Observed forward comparison available."
                    if forward_row is not None
                    else "Observed forward unavailable; CIP-only comparison returned."
                ),
                "as_of_date": spot_observation_date,
            }
        )
```

- [ ] **Step 4: Run focused transform tests**

Run:

```bash
pytest apps/pipelines/tests/test_currency_irp_transform.py -v
```

Expected: PASS. Existing no-forward tests should keep returning `partial` availability and `has_observed_forward: False`.

- [ ] **Step 5: Commit**

```bash
git add apps/pipelines/src/lib/pipeline/transforms/currency_irp.py apps/pipelines/tests/test_currency_irp_transform.py
git commit -m "feat: support optional observed forwards in irp transform"
```

---

### Task 2: Tighten IRP API Contract Shaping

**Files:**
- Modify: `apps/api/src/routes/currency-analysis.ts`
- Modify: `apps/api/tests/currency-analysis-route.test.ts`

- [ ] **Step 1: Add an API test for three tenor rows and observed-forward passthrough**

In `apps/api/tests/currency-analysis-route.test.ts`, add a new test case that returns DB rows out of tenor order. The assertion should prove that `cipRows` and `uip.rows` are both ordered `3M`, `6M`, `12M` and matched by tenor, not by array index.

Use this core assertion shape:

```ts
expect(response.json().irp.cipRows).toEqual([
  {
    tenor: "3M",
    asOf: "2026-05-30",
    spot: "1.1400",
    eurRate: "2.00",
    usdRate: "4.00",
    rateSpread: "-2.00",
    cipImpliedForward: "1.1344",
    observedForward: "1.1330",
    cipBasisBps: "-11.90",
    hasObservedForward: true,
  },
  {
    tenor: "6M",
    asOf: "2026-05-30",
    spot: "1.1400",
    eurRate: "2.10",
    usdRate: "4.10",
    rateSpread: "-2.00",
    cipImpliedForward: "1.1288",
    hasObservedForward: false,
  },
  {
    tenor: "12M",
    asOf: "2026-05-30",
    spot: "1.1400",
    eurRate: "2.20",
    usdRate: "4.20",
    rateSpread: "-2.00",
    cipImpliedForward: "1.1181",
    hasObservedForward: false,
  },
]);
expect(response.json().irp.uip.rows).toEqual([
  { tenor: "3M", impliedMovePct: "-0.50", impliedSpot: "1.1343" },
  { tenor: "6M", impliedMovePct: "-1.00", impliedSpot: "1.1286" },
  { tenor: "12M", impliedMovePct: "-2.00", impliedSpot: "1.1172" },
]);
```

- [ ] **Step 2: Run the API test to expose the index-alignment risk**

Run:

```bash
npm --prefix apps/api test -- currency-analysis-route.test.ts
```

Expected: FAIL until `uip.rows` is keyed from the same sorted IRP row collection as `cipRows`.

- [ ] **Step 3: Refactor route shaping to sort once and map from sorted rows**

In `apps/api/src/routes/currency-analysis.ts`, replace separate `cipRows` sorting and index-based `uip` mapping with this pattern:

```ts
    const sortedIrpRows = [...irpSnapshotsResult.rows].sort((left, right) => tenorRank(left.tenor) - tenorRank(right.tenor));

    const cipRows: CurrencyAnalysisIrpCipRow[] = sortedIrpRows.map((row) => ({
      tenor: row.tenor,
      asOf: row.as_of_date,
      spot: row.spot,
      eurRate: row.eur_rate,
      usdRate: row.usd_rate,
      rateSpread: row.rate_spread,
      cipImpliedForward: row.cip_implied_forward,
      ...(row.observed_forward ? { observedForward: row.observed_forward } : {}),
      ...(row.cip_basis_bps ? { cipBasisBps: row.cip_basis_bps } : {}),
      hasObservedForward: row.has_observed_forward,
    }));
```

Then return `uip.rows` from `sortedIrpRows`:

```ts
        uip: {
          rows: sortedIrpRows.map((row) => ({
            tenor: row.tenor,
            impliedMovePct: row.uip_implied_move_pct,
            impliedSpot: row.uip_implied_spot,
          })),
        },
```

- [ ] **Step 4: Run focused API tests**

Run:

```bash
npm --prefix apps/api test -- currency-analysis-route.test.ts
```

Expected: PASS with sorted tenor rows, correct optional observed-forward fields, and stable empty-contract behavior.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/routes/currency-analysis.ts apps/api/tests/currency-analysis-route.test.ts
git commit -m "fix: align irp api rows by tenor"
```

---

### Task 3: Add IRP UI Building Blocks

**Files:**
- Create: `apps/web/src/features/macro/components/currency-irp-formula-block.tsx`
- Create: `apps/web/src/features/macro/components/currency-irp-data-inputs-block.tsx`
- Create: `apps/web/src/features/macro/components/currency-irp-tenor-table-block.tsx`
- Create: `apps/web/src/features/macro/components/currency-irp-uip-block.tsx`

- [ ] **Step 1: Create the IRP formula block**

Create `apps/web/src/features/macro/components/currency-irp-formula-block.tsx` using `AnalysisFormulaTerms`.

Required rendered text:

```tsx
"F = S x ((1 + r_EUR x T) / (1 + r_USD x T))"
"(F - S) / S ~= r_EUR - r_USD"
"UIP framing: E[S_T] = S x (1 + (r_EUR - r_USD) x T)"
```

The term list must include `F`, `S`, `r_EUR`, `r_USD`, `T`, and `E[S_T]`.

- [ ] **Step 2: Create the IRP data inputs block**

Create `apps/web/src/features/macro/components/currency-irp-data-inputs-block.tsx`.

Props:

```ts
type IrpInputRef = {
  label: string;
  ref?: {
    number: number;
    href?: string;
  };
};

export function CurrencyIrpDataInputsBlock({
  asOf,
  inputs,
}: {
  asOf: string | null;
  inputs: IrpInputRef[];
}) {
  // render implementation
}
```

Render a `Data Inputs And Proxy Notes` block that states:

```tsx
"EUR/USD spot is the latest available daily reference rate. EUR rates use compounded euro short-term average rate tenor proxies. USD rates use Treasury bill secondary market rate proxies. Observed forwards are shown only when a reliable forward series is present."
```

Use `AnalysisCitationLinks` beside each input label when a reference number exists.

- [ ] **Step 3: Create the CIP tenor table block**

Create `apps/web/src/features/macro/components/currency-irp-tenor-table-block.tsx`.

Props:

```ts
type CurrencyIrpTenorRow = {
  tenor: string;
  asOf: string;
  spot: string;
  eurRate: string;
  usdRate: string;
  rateSpread: string;
  cipImpliedForward: string;
  observedForward?: string;
  cipBasisBps?: string;
  hasObservedForward: boolean;
};

export function CurrencyIrpTenorTableBlock({
  rows,
}: {
  rows: CurrencyIrpTenorRow[];
}) {
  // render implementation
}
```

The table columns must be:

```tsx
"Tenor"
"EUR/USD spot"
"EUR rate"
"USD rate"
"Spread"
"CIP-implied forward"
"Observed forward"
"CIP gap"
```

For missing observed forwards, render:

```tsx
"Not available"
```

For missing `cipBasisBps`, render:

```tsx
"Not shown"
```

The explanatory copy must include:

```tsx
"The table compares tenor-matched rate differentials with the forward level implied by covered interest parity. Missing observed forwards are left blank analytically rather than filled with substitute values."
```

- [ ] **Step 4: Create the UIP block**

Create `apps/web/src/features/macro/components/currency-irp-uip-block.tsx`.

Props:

```ts
type CurrencyIrpUipRow = {
  tenor: string;
  impliedMovePct: string;
  impliedSpot: string;
};

export function CurrencyIrpUipBlock({
  rows,
}: {
  rows: CurrencyIrpUipRow[];
}) {
  // render implementation
}
```

Required copy:

```tsx
"UIP is shown as a theoretical expected-spot framing, not as a mechanical forecast. It asks what spot move would offset the interest-rate differential if investors were comparing uncovered returns."
```

Table columns:

```tsx
"Tenor"
"Theoretical move"
"UIP-implied spot"
```

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/features/macro/components/currency-irp-formula-block.tsx apps/web/src/features/macro/components/currency-irp-data-inputs-block.tsx apps/web/src/features/macro/components/currency-irp-tenor-table-block.tsx apps/web/src/features/macro/components/currency-irp-uip-block.tsx
git commit -m "feat: add irp ui blocks"
```

---

### Task 4: Render `2.0 Interest Rate Parity` On The Currency Analysis Page

**Files:**
- Modify: `apps/web/src/features/macro/currency-analysis-client.tsx`
- Modify: `apps/web/tests/currency-analysis-page.test.tsx`

- [ ] **Step 1: Add failing web assertions for IRP**

In `apps/web/tests/currency-analysis-page.test.tsx`, update the first page test to expect IRP instead of asserting that it is absent.

Replace:

```ts
expect(screen.queryByRole("heading", { name: /Interest Rate Parity/i })).not.toBeInTheDocument();
expect(screen.queryByText("UIP Subsection")).not.toBeInTheDocument();
```

With:

```ts
expect(screen.getByRole("heading", { name: /2.0 Interest Rate Parity/i })).toBeInTheDocument();
expect(screen.getByText(/Covered interest parity links spot, tenor-matched interest rates, and forwards/i)).toBeInTheDocument();
expect(screen.getByText(/F = S x \(\(1 \+ r_EUR x T\) \/ \(1 \+ r_USD x T\)\)/i)).toBeInTheDocument();
expect(screen.getByText(/CIP-implied forward/i)).toBeInTheDocument();
expect(screen.getByText("3M")).toBeInTheDocument();
expect(screen.getByText("6M")).toBeInTheDocument();
expect(screen.getAllByText("Not available").length).toBeGreaterThan(0);
expect(screen.getByText(/UIP is shown as a theoretical expected-spot framing/i)).toBeInTheDocument();
expect(screen.getByText(/Observed forwards are shown only when a reliable forward series is present/i)).toBeInTheDocument();
```

Add a separate test where `payload.ppp.summary` is `null` but `payload.irp.cipRows` has rows. It should assert that `2.0 Interest Rate Parity` still renders.

- [ ] **Step 2: Run the failing web test**

Run:

```bash
npm --prefix apps/web test -- currency-analysis-page.test.tsx
```

Expected: FAIL because the client does not render IRP and returns `null` when PPP summary is missing.

- [ ] **Step 3: Import the new IRP components**

In `apps/web/src/features/macro/currency-analysis-client.tsx`, add:

```tsx
import { CurrencyIrpDataInputsBlock } from "./components/currency-irp-data-inputs-block";
import { CurrencyIrpFormulaBlock } from "./components/currency-irp-formula-block";
import { CurrencyIrpTenorTableBlock } from "./components/currency-irp-tenor-table-block";
import { CurrencyIrpUipBlock } from "./components/currency-irp-uip-block";
```

- [ ] **Step 4: Build IRP reference helpers in the client**

Use the same academic reference style as PPP. Build a separate IRP reference number map:

```tsx
  const irpReferenceNumberByLabel = new Map(data.irp.references.map((reference, index) => [reference.label, index + 1]));
  const irpRefs = data.irp.references.map((reference) => ({
    label: reference.label,
    ref: {
      number: irpReferenceNumberByLabel.get(reference.label) ?? 0,
      href: reference.url,
    },
  }));
```

- [ ] **Step 5: Let PPP and IRP render independently**

Replace:

```tsx
  if (!pppSummary) {
    return null;
  }
```

With:

```tsx
  const hasPpp = Boolean(pppSummary);
  const hasIrp = data.irp.cipRows.length > 0 || data.irp.uip.rows.length > 0;

  if (!hasPpp && !hasIrp) {
    return null;
  }
```

Wrap the existing PPP section in `{pppSummary ? (...) : null}` so its existing variables are only used when present.

- [ ] **Step 6: Add the IRP section after PPP**

Append this section inside the root stack:

```tsx
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
          </Stack>
        </Box>
      ) : null}
```

- [ ] **Step 7: Add a concise IRP takeaway in the tenor table block**

At the bottom of `CurrencyIrpTenorTableBlock`, derive this text from the first available row:

```tsx
const primaryRow = rows[0];
const takeaway =
  primaryRow && Number.parseFloat(primaryRow.rateSpread) < 0
    ? "EUR rates sit below USD rates across the shown tenor set, so CIP implies forward EUR/USD levels below spot. This is a forward-pricing relationship, not a standalone spot forecast."
    : "The tenor-rate spread determines whether CIP-implied forwards sit above or below spot. This is a forward-pricing relationship, not a standalone spot forecast.";
```

Render it under a label:

```tsx
"Analysis Takeaway"
```

- [ ] **Step 8: Run focused web tests**

Run:

```bash
npm --prefix apps/web test -- currency-analysis-page.test.tsx
```

Expected: PASS with PPP and IRP both rendering, and IRP rendering even when PPP summary is unavailable.

- [ ] **Step 9: Commit**

```bash
git add apps/web/src/features/macro/currency-analysis-client.tsx apps/web/tests/currency-analysis-page.test.tsx
git commit -m "feat: render irp section on currency analysis page"
```

---

### Task 5: Final Verification

**Files:**
- Verify only; no planned edits.

- [ ] **Step 1: Run pipeline IRP tests**

Run:

```bash
pytest apps/pipelines/tests/test_currency_irp_transform.py apps/pipelines/tests/test_currency_analysis_flow.py -v
```

Expected: PASS. Flow tests should still tolerate optional IRP fetch failures and write honest availability rows.

- [ ] **Step 2: Run API tests**

Run:

```bash
npm --prefix apps/api test -- currency-analysis-route.test.ts
```

Expected: PASS.

- [ ] **Step 3: Run web tests**

Run:

```bash
npm --prefix apps/web test -- currency-analysis-page.test.tsx
```

Expected: PASS.

- [ ] **Step 4: Run TypeScript checks**

Run:

```bash
npx.cmd tsc -p apps/api/tsconfig.json --noEmit
npx.cmd tsc -p apps/web/tsconfig.json --noEmit
```

Expected: PASS.

- [ ] **Step 5: Run source-registry guard test**

Run:

```bash
pytest apps/pipelines/tests/test_source_registry.py::test_currency_analysis_forward_series_are_not_registered_without_a_real_source_path -v
```

Expected: PASS. This confirms the implementation did not add fake observed-forward sources.

---

## Self-Review Notes

- Spec coverage: Covers current `EUR/USD` spot, `3M`/`6M`/`12M` tenor set, EUR and USD tenor proxy rates, spreads, CIP-implied forwards, optional observed forwards, optional CIP basis, and UIP theoretical framing.
- Architecture coverage: Pipeline computes, mart stores, API serves, web presents. No provider fetches move into API or UI.
- No-fake-data coverage: Forward series remain unregistered unless a real source path is confirmed; missing observed forwards render as unavailable rather than being fabricated.
- UI coverage: IRP follows theory, formula, terms, inputs/proxies, output table, UIP sub-section, takeaway, references.
- DRY/modularity coverage: New UI blocks reuse shared analysis components and keep `currency-analysis-client.tsx` as composition rather than one giant IRP component.

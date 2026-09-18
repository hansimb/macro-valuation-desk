# MVD US country-index feasibility gate

**Gate date:** 2026-09-18

**Methodology:** `us-country-index-v1`
**Decision:** **Not ready for additional jurisdictions.** The deterministic acceptance gate passes, but no live development sample can be measured because this checkout has no configured US provider factory.

## What was verified

The bounded backfill driver accepts only complete Monday-Friday windows and only `--market us`. Both `--from` and `--to` are mandatory. Each week receives a deterministic methodology-versioned run ID and checkpoint namespace. `--resume` reuses the Task 10 checkpoint path; a non-resume run refuses an existing weekly checkpoint. Development prices are rejected when the requested environment is production.

Command:

```powershell
cd apps/pipelines
python -m pytest tests/test_us_country_index_backfill.py -q --basetemp=.tmp/pytest-task13
```

Measured fixture result on 2026-09-18:

| Measure | Result |
|---|---:|
| Tests | 5 passed |
| Runtime | 4.35 s |
| Complete fixture weeks | 3 |
| Weekly methodology-versioned rows per three-week backfill | 18 |
| Metrics per week | 6 |
| Repeated full runs compared | 2 |
| Repeated weekly-row differences | 0 |
| Failed/partial fixture weeks | 0 |

The acceptance fixture runs the real Task 10 calculation and persistence path with deterministic filing, price, cohort-state, share-reconciliation, and database adapters. It explicitly crosses:

- an original filing followed by an amendment becoming visible;
- a 2-for-1 split and a post-split week;
- one missing price day;
- a transition from cohort v1 to cohort v2;
- a four-trading-day holiday week.

The persisted point-in-time rows prove that the amended earnings fact becomes visible only at its publication cutoff. Persisted raw price rows retain the split metadata and omit the intended missing day. Persisted cohort membership changes from `A/B/C` to `A/B/D`, the holiday week has four daily observations, and all 18 weekly rows retain `us-country-index-v1`. A receipt-backed resumed rerun returns identical rows without trying to republish superseded Task 10 runs. Receipt identity binds the environment, development-price mode, methodology, market/week, provider-factory provenance, and the validated Task 10 checkpoint fingerprint. A development receipt therefore cannot satisfy a production resume or bypass its price-license guard.

The test also verifies refusal of an unbounded range, reversed dates, partial-week bounds, a non-US market, and production publication with development prices. A failed weekly runner stops the bounded job and reports the exact failed week.

## Live development sample

A live recent-week and historical-quarter sample was **not run**. The required `MVD_US_COUNTRY_INDEX_PROVIDER_FACTORY` setting is absent from both the process environment and the repository `.env` file. The Task 10 flow requires that factory to provide:

- a US primary-listing universe provider;
- a SEC filing/XBRL provider;
- a price provider and its license declaration;
- audited share reconciliation;
- persistent cohort state;
- FX and sensitivity inputs where applicable.

Running without these inputs would only produce the known configuration failure and would not measure feasibility. Network availability alone cannot supply the missing provider wiring or share/cohort state.

Consequently, these live measures are **not available** and are not estimated:

- eligible-universe count;
- price coverage;
- XBRL concept-mapping coverage;
- achieved market coverage;
- per-metric coverage;
- warning distribution;
- unresolved issuer/listing identifiers;
- unresolved corporate actions;
- one-week and one-quarter runtimes.

This is an exact blocker, not evidence of zero coverage.

## Reconciliation assessment

Fixture acceptance proves the backfill boundary and repeatability contract. It does not establish live source completeness, production price licensing, identifier reconciliation, corporate-action coverage, or commercial readiness. The price adapter remains explicitly development-only.

The architecture should not be promoted to another jurisdiction until a configured live run records at least:

1. one recent complete week;
2. one historical quarter;
3. the requested coverage and warning measures;
4. unresolved identifier and corporate-action cases;
5. identical published rows after a resumed rerun.

## Reproduction

Fixture gate:

```powershell
cd apps/pipelines
python -m pytest tests/test_us_country_index_backfill.py -q --basetemp=.tmp/pytest-task13
```

Configured development sample, after installing a real provider factory:

```powershell
$env:MVD_US_COUNTRY_INDEX_PROVIDER_FACTORY = "your.package:factory"
python -m src.flows.us_country_index_backfill --from YYYY-MM-DD --to YYYY-MM-DD --market us --resume --development-prices
```

Bounds must start on Monday and end on Friday. Use a recent complete Friday for the week sample and quarter-aligned complete-week bounds for the historical sample.

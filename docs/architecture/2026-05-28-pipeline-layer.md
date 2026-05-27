# MVD Pipeline Layer Architecture

## Purpose

Describe the reusable pipeline layer architecture for `Macro Valuation Desk`.

This document focuses on what happens after the source layer and before detailed database/load design.

## Role In The System

The pipeline layer sits between:

- the reusable source layer
- the database/load layer

In the high-level system flow:

`source -> pipeline -> postgres -> api -> web`

In ETL terms, this layer mainly owns:

- `T` = transform

and coordinates the move toward:

- `L` = load

## Main Responsibility

The pipeline layer takes externally fetched data and turns it into reliable, reusable, write-ready data for downstream database layers.

In practice, it is responsible for:

- ingesting source-layer outputs
- validating data
- standardizing data
- preparing derived analytical datasets
- handing write-ready outputs to the load layer

## What The Pipeline Layer Does Not Own

The pipeline layer does not own:

- provider-specific fetch logic
- API response shaping
- UI logic
- final presentation logic
- detailed database physical design

## Internal Structure

The pipeline layer is divided into three parts:

1. `ingestion`
2. `staging transform`
3. `analytical transform`

## 1. Ingestion

Ingestion is responsible for bringing data in from the source layer in a controlled way.

Its responsibilities are:

- select target series from the registry
- call source-layer adapters
- pass fetch options
- receive `result object` responses
- record success and failure states
- decide retry / fail / skip behavior at run level
- pass successful results onward

Ingestion should stay relatively thin.

It is not the place for major business logic or analytical calculations.

## Incremental Processing Responsibilities

The pipeline layer is also responsible for avoiding unnecessary repeated work.

This is primarily a pipeline concern, not a source-layer concern.

The main mechanisms are:

1. `incremental fetch`
2. `high-water mark / checkpoint`
3. `reprocessing window`
4. `change detection`

### 1. Incremental Fetch

The pipeline should avoid re-fetching full long histories by default.

Instead, ingestion should usually request only:

- new observations after the latest known point
- or a bounded recent window when revision risk exists

The source layer may support this with fetch options, but the pipeline owns the decision logic.

### 2. High-Water Mark / Checkpoint

The pipeline should maintain a notion of how far a given series or domain run has already progressed.

This checkpoint state supports:

- incremental fetching
- resumability
- controlled reruns

The database stores the checkpoint state, but the pipeline owns how it is used.

### 3. Reprocessing Window

Some providers revise recent history.

Because of that, the pipeline should be able to re-fetch a recent rolling window instead of only fetching strictly unseen dates.

Examples:

- last `30` days
- last `3` months

This is a pipeline policy decision.

### 4. Change Detection

Even when data is fetched again, the pipeline should be able to determine whether anything materially changed.

This helps avoid unnecessary downstream processing and rewrites.

Typical change detection may compare:

- observation values
- row-level hashes
- relevant metadata used in transforms

## Ownership Of Incremental Logic

The responsibility split is:

- `pipeline` decides what to fetch and what to reprocess
- `database/load` persists checkpoint and layer data
- `source layer` executes constrained fetches when supported

This keeps the core orchestration intelligence in the pipeline layer.

## 2. Staging Transform

Staging transform is responsible for technical cleanup and standardization.

Its responsibilities are:

- schema validation
- date normalization
- type conversion
- unit checks
- missing-value handling rules
- technical cleanup of provider-fed series

Staging transform should make data technically consistent and trustworthy.

It should not yet introduce analysis-specific business meaning.

## 3. Analytical Transform

Analytical transform is responsible for turning technically clean data into analysis-ready datasets.

Its responsibilities are:

- combine multiple series when needed
- compute derived metrics
- prepare reusable analytical inputs
- create comparison-ready structures for macro and equity use cases

Examples:

- Taylor Rule inputs
- valuation-history inputs
- region comparison datasets
- precomputed analysis-ready domain outputs

## Standard Pipeline Flow

The recommended v1 flow is:

1. ingest
2. write raw
3. staging transform
4. write staging
5. analytical transform
6. write mart

This means one ETL run may update multiple data layers in sequence.

## One Run Vs Separate Jobs

The recommended v1 model is:

- one ETL run can update `raw`, `staging`, and `mart`

This keeps orchestration simple in the early system.

However, even when one run updates multiple layers, the layer responsibilities must remain clearly separated.

The pipeline should not collapse into one large undifferentiated job.

## Pipeline Run Unit

The recommended run unit is:

- `domain / series group`

Examples:

- `run_us_macro_core_etl`
- `run_eu_macro_core_etl`
- `run_global_equity_base_etl`

This is preferred over:

- one job per series
- one job per analysis

## Why Domain-First Is Preferred

`Domain-first` ETL design supports reuse better than `analysis-first` design.

This means:

- one analysis may depend on multiple ETL-domain outputs
- one ETL-domain output may serve multiple analyses

This avoids duplicated ingestion and repeated transformation work.

## Relationship To Analyses

Analyses are consumers of pipeline outputs.

They should not normally own the ETL design.

Default rule:

- pipelines are designed around reusable data domains

Exception:

- an analysis-specific ETL path is acceptable only when a truly specialized dataset or derived methodology cannot be cleanly generalized

## Pipeline Outputs

The pipeline layer produces write-ready outputs for downstream database layers.

Conceptually these are:

- `raw-ready`
- `staging-ready`
- `mart-ready`

These are not API responses and not UI-facing contracts.

They are internal prepared outputs for the database/load layer.

## Enterprise Style Fit

This design is intentionally close to a standard analytical data-platform pattern:

- thin ingestion
- separated transforms
- reusable domains
- staged data layers
- analysis consumption on top of shared prepared data

## Pipeline Layer Summary

The reusable pipeline design is:

- split into `ingestion`, `staging transform`, and `analytical transform`
- domain-first rather than analysis-first
- able to update multiple warehouse layers in one ETL run
- responsible for incremental processing strategy
- focused on preparing reusable data rather than presentation-ready data

## Next Planning Steps

The next architecture planning step after this document is:

1. database/load layer
2. API serving layer

## Short Implementation Steps

The pipeline layer can later be implemented in small steps:

1. define pipeline run units by domain
2. define ingestion job inputs and result handling
3. implement staging transform contracts
4. implement analytical transform contracts
5. define raw-ready, staging-ready, and mart-ready outputs
6. wire one domain ETL path end to end

# MVD High-Level Architecture

## Purpose

Describe the current intended top-level architecture for `Macro Valuation Desk`.

This document stays intentionally high level.

## Core Flow

The main system flow is:

`source -> pipeline -> postgres -> api -> web`

This can also be understood as:

`ETL + SP`
(extract, transform, load + service, present)

Where:

- `E` = source layer / extract
- `T` = pipeline transform logic
- `L` = database load
- `S` = API serving layer
- `P` = web presentation layer

This is a useful mental model for MVD because it separates core data-platform work from the later application-facing layers.

## Layer Responsibilities

### 1. Source Layer

The source layer connects to external data providers.

Its responsibility is to:

- know provider-specific access details
- fetch external series
- return them in a standardized internal format

It should be reusable across analyses.

### 2. Pipeline Layer

The pipeline layer is the main consumer of the source layer.

Its responsibility is to:

- ingest source data
- validate it
- normalize it
- prepare reusable downstream datasets
- load data into PostgreSQL

In ETL terms, this layer mainly owns the `T` part and coordinates the move toward `L`.

### 3. PostgreSQL

PostgreSQL is the durable store and central system memory.

Its responsibility is to:

- store ingested and prepared data
- support reusable analysis inputs
- serve as the main backend data source for the API

In ETL terms, this is the main destination of `L`.

### 4. API Layer

The API is the serving layer.

Its responsibility is to:

- expose stable routes
- read prepared data from PostgreSQL
- return data in application-facing shapes

It should not normally fetch live provider data directly.

The API is not the `L` layer itself.

It comes after ETL and should be understood as part of the serving side of the architecture.

### 5. Web Layer

The web layer is the presentation layer.

Its responsibility is to:

- render analysis pages
- present formulas, tables, references, and outputs
- consume stable API responses

It should not contain provider-specific logic.

This is the final presentation layer after the data has already moved through extraction, transformation, loading, and serving.

## Reuse Principle

The key architectural rule is:

- provider logic is implemented once
- standardized data contracts are reused everywhere else

This is what allows:

- multiple analyses
- multiple regions
- multiple providers
- future data expansion

without rebuilding the stack for each new page.

## Planning Order

The recommended planning order is:

1. source layer
2. pipeline layer
3. database/load layer
4. API serving layer
5. implementation bottom-up

The recommended implementation order is bottom-up only after the planning for those layers is clear enough.

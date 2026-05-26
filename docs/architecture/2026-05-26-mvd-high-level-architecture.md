# MVD High-Level Architecture

## Purpose

Describe the current intended top-level architecture for `Macro Valuation Desk`.

This document stays intentionally high level.

## Core Flow

The main system flow is:

`source -> pipeline -> postgres -> api -> web`

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

### 3. PostgreSQL

PostgreSQL is the durable store and central system memory.

Its responsibility is to:

- store ingested and prepared data
- support reusable analysis inputs
- serve as the main backend data source for the API

### 4. API Layer

The API is the serving layer.

Its responsibility is to:

- expose stable routes
- read prepared data from PostgreSQL
- return data in application-facing shapes

It should not normally fetch live provider data directly.

### 5. Web Layer

The web layer is the presentation layer.

Its responsibility is to:

- render analysis pages
- present formulas, tables, references, and outputs
- consume stable API responses

It should not contain provider-specific logic.

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

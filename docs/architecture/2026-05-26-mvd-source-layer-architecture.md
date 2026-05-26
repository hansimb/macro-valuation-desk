# MVD Source Layer Architecture

## Purpose

Describe the reusable source layer architecture for `Macro Valuation Desk`.

This layer is responsible for external data access only.

It is not responsible for:

- analysis calculations
- database loading
- API response shaping
- UI behavior

## Role In The System

The source layer sits at the start of the main system flow:

`source -> pipeline -> postgres -> api -> web`

Its main consumer is the pipeline layer.

## Core Principle

The source layer must be reusable.

That means:

- provider logic is implemented once
- the rest of the system uses internal stable contracts
- analyses do not talk directly to providers

## Main Decisions

### 1. Internal Key System

Series are identified inside MVD with stable internal keys.

Example:

- `us_cpi_headline`
- `eu_policy_rate`

The system should not use provider-native ids as its main internal identifiers.

## 2. Central Series Registry

Series definitions live in one central registry in v1.

This is the simplest starting point and is easiest to understand and maintain while the number of tracked series is still small.

## 3. Registry Entry Model

Each series definition should contain at least:

- `key`
- `category`
- `provider`
- `external_series_id`
- `label`
- `region`
- `frequency`
- `unit`
- `source_url`

Example:

```ts
{
  key: "us_cpi_headline",
  category: "inflation",
  provider: "fred",
  external_series_id: "CPIAUCSL",
  label: "US CPI All Urban Consumers",
  region: "US",
  frequency: "monthly",
  unit: "index",
  source_url: "https://fred.stlouisfed.org/series/CPIAUCSL"
}
```

## 4. Registry Purpose

The registry describes what series MVD knows about.

It does not describe how much data should be fetched for a specific request.

That means request-specific fetch settings must stay outside the registry.

## 5. Fetch Options Stay Separate

These belong to the fetch call, not to the registry entry:

- `start_date`
- `end_date`
- `limit`

This keeps the registry reusable and prevents request-specific settings from polluting stable series definitions.

## 6. One Adapter Per Provider

Each provider should have its own adapter.

Examples:

- `FredAdapter`
- `EcbAdapter`
- `EurostatAdapter`

The adapter is the provider-specific integration layer.

It knows:

- endpoints
- parameters
- response shape
- parsing rules
- provider quirks

## 7. Shared Adapter Interface

All adapters should expose the same conceptual interface:

`fetchSeries(seriesDefinition, fetchOptions) -> result`

This lets the rest of the system work with providers through one stable pattern.

## 8. OpenBB Position

OpenBB may be used inside an adapter as an implementation helper.

It must not become an architectural dependency for the rest of the system.

That means:

- the registry does not depend on OpenBB
- the pipeline does not depend on OpenBB contracts
- the standardized MVD source contract remains primary

## 9. Standardized Series Output

Adapters should return a standardized series shape.

The output should include:

- `key`
- `category`
- `provider`
- `series_id`
- `label`
- `region`
- `frequency`
- `unit`
- `source_url`
- `observations`

Each observation should contain:

- `date`
- `value`

This gives upper layers both:

- internal MVD identifiers
- provider/source metadata
- actual time series values

## 10. Scope Of The Source Layer

The source layer should focus on raw or base series.

Examples:

- CPI
- policy rate
- index level
- earnings series

Derived metrics should generally be handled later in the pipeline layer when needed.

Example:

- direct provider P/E series can come from the source layer
- calculated P/E from `index level / earnings` belongs more naturally in pipeline preparation

## 11. Error Handling Model

The source layer should not use silent fallbacks.

It should not hide failures behind:

- empty arrays
- `null`
- partially broken payloads

Instead, it should return a structured result object.

## 12. Result Object

The adapter should return either:

- success with standardized series data
- failure with a structured error

The recommended v1 structure is conceptually:

- `ok`
- `series` on success
- `error` on failure

The error should contain at least:

- `provider`
- `key`
- `external_series_id`
- `error_type`
- `message`

This allows the pipeline to make explicit decisions about retrying, skipping, failing, or logging.

## 13. Missing Data vs Fetch Failure

These must be treated as different things.

- missing observation = possible valid data condition
- fetch failure = technical or provider failure

The source layer must preserve that distinction clearly.

## Source Layer Summary

The reusable source layer design is:

- internal key based
- backed by one central registry in v1
- powered by one adapter per provider
- standardized on a shared series output model
- explicit about fetch options
- explicit about failures
- reusable across macro and equity use cases

## Next Planning Steps

The next architecture planning steps after this document are:

1. reusable pipeline model
2. reusable database / warehouse model
3. reusable API serving model

These should be handled one layer at a time in that order.

## Short Implementation Steps

The source layer implementation can later be built in small steps:

1. define the shared registry entry type
2. define the standardized series output type
3. define the result/error object type
4. create the first central series registry
5. create the first provider adapter interface
6. implement one real provider adapter
7. test one successful fetch path
8. test one failure path

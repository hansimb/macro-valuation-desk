# Taylor Rule Design

## Goal

Build the first macro analysis page around the Taylor Rule.

The page should compare `USA` and `EU` side by side, show the formula clearly, pull the most important inputs from real data, and allow the user to test only the smallest necessary set of assumption-driven parameters.

## Why This Analysis Matters

Taylor Rule logic is a strong first analysis for MVD because it fits the project direction well:

- it is clearly macro, not single-asset research
- it combines theory, real-world data, and interpretation
- it benefits from both static analysis and interactive scenarios
- it can be extended later through better data pipelines and proxy improvements

It is also a good first page because it forces the system to show its methodology openly instead of hiding assumptions inside a black box.

## Core Design Decision

The page should be both:

- a compact data-driven analysis
- a controlled scenario calculator

But it should not become a free-form macro sandbox.

The user should only be able to adjust parameters that are truly assumption-driven.

## Page Structure

### 1. Header

- page title
- one short explanation of what the Taylor Rule is estimating

### 2. Formula Block

Show the Taylor Rule formula clearly on the page.

The page should also explain each term briefly and state which values come from real data versus assumptions.

### 3. Live Snapshot

For both `USA` and `EU`, show:

- current policy rate
- inflation input
- activity / slack input
- assumed `r*`
- Taylor-implied rate
- gap between actual and implied rate

This should be table-first.

### 4. Scenario Controls

The page should expose only 1-2 assumption-based controls.

Preferred structure:

- preset selector: `dovish`, `base`, `hawkish`
- adjustable `r*`
- optional second control only if needed later

All other inputs should stay locked to real data.

### 5. Output Summary

For both regions, output a very short interpretation:

- policy looks tighter than rule-implied
- policy looks looser than rule-implied
- policy looks close to rule-implied

Text should stay brief.

### 6. References

The page must end with methodology and data references.

## Formula

The intended baseline is the standard Taylor Rule family:

`i = r* + pi + a(pi - pi*) + b(output gap)`

Where:

- `i` = policy rate implied by the rule
- `r*` = neutral real rate
- `pi` = inflation
- `pi*` = inflation target
- `a` = inflation response coefficient
- `b` = output gap response coefficient

The exact displayed variant can be finalized during implementation, but the page must show the chosen form explicitly.

## Inputs From Real Data

The page should try to lock these to real data:

- current policy rate
- inflation series
- inflation target where applicable
- activity/slack metric if a defensible direct series exists

If a true output gap series is not practical for v1, use a clearly labeled proxy.

## Inputs From Assumptions

These are the intended assumption-driven variables:

- `r*`
- possibly one optional coefficient or slack override if truly necessary

The default should be to keep coefficient choices stable and expose only `r*` unless implementation shows a strong reason for a second control.

## `r*` Design

`r*` should not behave like a random free slider.

The interface should guide the user toward plausible values.

V1 design:

- expose `r*` as adjustable
- give it a default economically defensible value
- present a recommendation range or note based on the selected methodological frame
- explain that `r*` is assumption-sensitive and should be interpreted with caution

The purpose is not just to let the user change the number, but to help the user reason about what a plausible number is.

## Scenario Design

Scenarios should be preset and compact:

- `dovish`
- `base`
- `hawkish`

These presets should mainly shift assumption-sensitive inputs, not real data inputs.

The page should always load in `base`.

## USA And EU Scope

The first version should support:

- `USA`
- `EU`

These should be shown side by side using the same framework so the comparison is clean.

## Interpretation Rules

Interpretation should stay restrained.

The page should not claim that Taylor Rule output is “the truth.”

Instead, it should frame the result as:

- a rule-based benchmark
- sensitive to assumptions
- useful for comparing stance, not replacing full policy analysis

## References Plan

The final page should include:

- Taylor Rule methodology source(s)
- source for policy rate data
- source for inflation data
- source for activity/slack data or proxy
- source used for any `r*` framing if one is cited

## Implementation Notes

The current app skeleton is already suitable for this analysis.

The likely implementation path is:

1. add one first-class macro analysis entry
2. build its dedicated route
3. render formula + snapshot + scenario panel + short interpretation
4. keep the first version mostly deterministic and readable
5. improve data pipelines after the UI and logic shape are proven

## Scope Guard

This page should not expand in v1 into:

- a general macro dashboard
- a giant parameter lab
- a full central-bank simulator

The first version wins if it clearly answers one question:

`What policy rate does a Taylor Rule style framework imply for USA and EU under a small number of disciplined assumptions?`

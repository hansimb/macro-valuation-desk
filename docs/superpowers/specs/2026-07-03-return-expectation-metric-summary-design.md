# Return Expectation Metric Summary Design

## Goal

Add a metric summary section to the stock return expectation calculator so each analysis shows the relevant yield and historical growth metrics already derivable from the current inputs.

## Placement

Render the new section after the current `Result` box and before `Return Expectation Methods`. This keeps the flow as active model result, cross-model input metric summary, then completed-method comparison.

## Content

Use a single surface card with two internal groups:

- `Yields`: dividend yield, earnings yield, FCF yield, implied P/E, and implied P/FCF when each can be calculated from current inputs.
- `Historical Growth`: EPS growth history, revenue growth history, dividend growth history, and FCF growth history when each can be calculated from current historical inputs.

Do not introduce new valuation formulas or change existing expected-return outputs. The summary should reuse the existing calculation helpers and show `N/A` for unavailable values.

## UI

Follow the existing Chakra UI patterns in `return-expectation-client.tsx`: `Box` surface, `Stack` spacing, `SimpleGrid` metric cards, and `AnalysisMetricCard` for the metric tiles. Keep the two groups visually distinct inside the same section.

## Testing

Add tests to `apps/web/tests/equity-return-expectation-page.test.tsx` that verify:

- The metric summary appears after `Result` and before `Return Expectation Methods`.
- Yield metrics and historical growth metrics are labeled as separate groups.
- The section shows relevant yield and historical growth values calculated from Gordon, earnings, and FCF inputs.

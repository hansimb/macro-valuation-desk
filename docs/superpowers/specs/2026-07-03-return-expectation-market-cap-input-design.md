# Return Expectation Market Cap Input Design

## Goal

Improve the stock return expectation calculator by allowing market capitalization to be calculated from shares outstanding and share price, and make the earnings-yield calculation path more explicit.

## Scope

This change applies to the frontend-only return expectation calculator in `apps/web/src/features/equity/return-expectation-client.tsx`.

## Market Capitalization Input

Add a shared market-cap input mode:

- `Market cap input`: user enters market capitalization directly.
- `Shares x price`: user enters shares outstanding and share price; the calculator derives market capitalization as `shares outstanding * share price`.

The selected market capitalization value remains shared by the earnings and FCF models. Legacy saved analyses with only `common.marketCap` or `earnings.marketCap` continue to load as direct market cap input.

## Earnings Yield Diagnostics

When the earnings model uses market-cap based inputs, show a clear calculation readout in the Earnings Yield section:

- `Earnings yield = net income / market capitalization`
- calculated earnings yield
- calculated implied P/E

The existing result cards and metric summary continue to show the same outputs; the new readout makes the calculation path visible next to the inputs.

## FCF Growth Logic

Keep the FCF model focused on `Expected return = free cash flow yield + FCF growth`. The FCF view should not show EPS or revenue growth controls. Add test coverage so this stays explicit.

## Testing

Update `apps/web/tests/equity-return-expectation-page.test.tsx` to verify:

- Market capitalization can be calculated from shares outstanding and share price.
- The calculated market capitalization drives earnings yield, implied P/E, and FCF yield.
- The earnings market-cap input path shows the formula and diagnostics.
- The FCF model formula and controls remain FCF-yield plus FCF-growth only.

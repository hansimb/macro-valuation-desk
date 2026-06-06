# Analysis UI Build Instructions For Agents

This document is the explicit UI-construction rulebook for analysis pages in MVD.

Use it together with:

- `docs/analysis/README.md`
- `docs/analysis/FOR-AGENTS.md`

This file exists because analysis UI work has repeatedly failed when agents improvised layout, controls, section hierarchy, formula presentation, and references.

Do not improvise those things.

Follow this document literally unless the user or developer explicitly tells you to do otherwise.

## 1. Core Rule

An analysis page is not a generic dashboard.

It is not a random stack of cards.

It is not a giant single box with everything dumped inside.

It is a structured research-style page with a strict information order:

1. theory
2. formula
3. formula term explanations
4. data inputs and assumptions
5. analysis output
6. references

If there are multiple methodologies on one page, each methodology block must follow that order internally.

## 2. Copy The Taylor Rule Page Structure

When building a new analysis UI, use the Taylor Rule page as the structural reference.

That means:

- clean section hierarchy
- one real methodology block at a time
- theory before numbers
- formula in its own visible block
- references in academic-style format
- no noisy gimmick UI

Do not invent a different presentation style unless the user explicitly asks for one.

## 3. Section Hierarchy Is Mandatory

Each methodology section must have a real numbered section heading such as:

- `1.0 Relative Purchasing Power Parity`
- `2.0 Interest Rate Parity`

Rules:

- the numbered heading must be the actual visible section heading
- do not render the same heading twice
- do not render a tiny label plus a second duplicate heading
- do not bury the section heading inside a card if it is supposed to introduce the whole block

Bad:

- tiny `1.0` eyebrow plus another repeated title below it
- section title duplicated in two places
- heading rendered so small that it does not function as a heading

## 4. Do Not Put Everything In One Giant Box

A methodology section must be split into clearly separated surfaces.

Typical structure:

1. section heading and theory text
2. formula block
3. data inputs block
4. analysis output block
5. supporting table or chart block
6. references block

Rules:

- each block must have one clear purpose
- do not merge unrelated content into one huge card
- do not create a long monolithic surface containing theory, formula, controls, table, takeaway, and references all together

## 5. Formula Block Rules

If a formula is shown, it must be presented in a dedicated formula block.

That formula block must contain:

1. the formula itself
2. the formula term explanations directly underneath in the same block
3. one short plain-language sentence explaining what the formula does

Do not separate:

- `Formula`
- `Formula Terms`

into different cards if they belong to the same method step.

They belong together unless the user explicitly says otherwise.

## 6. Always Open Formula Terms Explicitly

Never show compact notation without opening the symbols.

If the page shows:

`PPP_t = S_base * (CPI_US_t / CPI_US_base) / (CPI_EA_t / CPI_EA_base)`

then the page must explicitly explain each important term in plain language.

The displayed formula should prefer the general mathematical form first.

Applied or dataset-specific interpretation should come second in parentheses.

Example:

- general form: `S_0`, `P_h,t`, `P_h,0`, `P_f,t`, `P_f,0`
- applied clarification: `(here: annual-average EUR/USD in the selected base year)`

Rules:

- do not assume the user understands notation
- do not assume the formula explanation can be inferred from labels elsewhere
- do not hide symbol explanations in tooltips or collapsibles by default
- do not make the formula itself overly application-specific if a general mathematical form exists

Each term explanation should read like:

- `S_0 = base-period spot exchange rate (here: annual-average EUR/USD in the selected base year).`
- `P_h,t = home-country price level at time t (here: U.S. CPI index at observation month t).`

### 6.1 Formula-Term Alignment Is Mandatory

Formula term explanations must be visually aligned.

The symbol column should start at one fixed position and the explanation column should start at one fixed position.

Use a two-column layout such as:

- left column: symbol
- right column: explanation

Do not render formula explanations as a loose stack of lines where the explanation text begins at a different horizontal position on each row.

That looks messy and low quality.

## 7. Controls Must Feel Intentional

If the analysis needs a user control, it must look deliberate and productized.

Do not dump raw links or unstructured lists into the page.

### 7.1 Base-Month Selection

If the user must select a base month:

- use a dropdown or another clearly bounded picker control
- do not render the full month history as an unstructured link list
- do not use only `previous` / `next` links as the primary control
- do not use a control with broken contrast

The control must have:

- explicit label
- readable text
- readable background
- readable border
- obvious affordance that it is selectable

### 7.2 Navigation Behavior

Changing a selection should not create an annoying page jump unless the user explicitly wants full navigation behavior.

If using route updates:

- preserve scroll position when reasonable
- avoid yanking the user to the top of the page for a small local control change

## 8. No Browser-Default Ugly Controls

Do not rely blindly on browser default control styling if it clashes with the site theme.

If a native control is used, verify:

- background color
- text color
- border color
- indicator visibility
- option-row readability

If a themed abstraction does not style correctly, do not keep fighting a broken control blindly.

Use the simplest control that actually renders correctly in the product theme.

But:

- do not replace one bad control with an even uglier improvised one
- align the control visually with the rest of the page

## 9. Output Blocks Must Be Self-Explanatory

Never use vague headings such as:

- `Snapshot`
- `Summary`
- `Current State`

unless the meaning is obvious from the surrounding context.

Prefer explicit names such as:

- `Current PPP Valuation Readout`
- `Selected Base-Month Path`

Every output block must explain:

- what the numbers represent
- what period they refer to
- how they were derived

The user should not have to guess what a number means.

## 10. Analysis Takeaway Placement

`Analysis Takeaway` is not a floating decorative card.

Place it where it belongs logically.

Default rule:

- if the takeaway is interpreting one main output block, put it inside that same output block at the bottom
- do not create a separate standalone takeaway box unless there is a strong structural reason

The takeaway text must be:

- short
- plain-language
- economically clear

Avoid vague wording such as:

- “screens rich” without context
- “suggests a move” without saying relative to what

## 11. Tables Must Earn Their Place

Never include a table just because data exists.

A table must answer a concrete analytical need.

Before rendering a table, ask:

- what question does this table help answer?
- what comparison becomes easier because of this table?
- what is the user supposed to notice in it?

If the answer is unclear, the table is not ready.

### 11.1 Supporting Tables Must Include The Key Analytical Column

If the table compares observed values to model-implied values, it usually also needs the difference or gap column.

Example:

- observed spot
- PPP-implied level
- valuation gap %

Without the gap column, the table often becomes much less useful.

## 12. References Must Match The Taylor Style

References are not raw link dumps.

They must be rendered in the same academic/IEEE-style pattern used on the Taylor Rule page.

Rules:

- numbered references
- source institution named
- series label named
- URL included as online availability

Bad:

- plain naked link list
- provider URLs without source description
- inconsistent format per analysis

## 13. Typography And Labeling Rules

Use labels deliberately.

Rules:

- major headings must be visually major
- labels such as `Formula`, `Data Inputs`, `References` can be small uppercase section labels
- values must be visually stronger than their helper text
- helper text must explain, not decorate

Do not create:

- duplicate labels
- meaningless sublabels
- tiny fake headings

## 14. Visual QA Checklist Before Claiming UI Is Done

Before saying the UI is fixed or complete, check all of these:

1. Is the section heading clear and not duplicated?
2. Is the theory shown before the formula?
3. Are formula terms explained directly and explicitly?
4. Is the formula block visually coherent?
5. Are controls readable in the actual theme?
6. Does the control interaction avoid annoying page jumps when possible?
7. Are output block headings specific and meaningful?
8. Does each table have a clear analytical purpose?
9. Are references in Taylor-style academic format?
10. Is the layout split into logical blocks rather than one giant surface?

If any answer is no, the UI is not done.

## 15. Anti-Patterns That Must Not Reappear

Do not do these again:

- rendering all selectable months as a huge unstructured list
- using `previous` / `next` links as the main picker for month selection
- splitting formula and formula-term explanations into different unrelated cards
- using vague headings like `Snapshot`
- rendering meaningless supporting tables without the key gap/difference column
- dumping references as plain links
- duplicating numbered section titles
- stuffing the full methodology into one giant box
- shipping controls with unreadable contrast

## 16. When In Doubt

If you are unsure how to present an analysis block:

1. look at the Taylor Rule page
2. follow the section order in this document
3. choose the simpler, clearer, more explicit option

Do not improvise a new visual language unless the user explicitly requests one.

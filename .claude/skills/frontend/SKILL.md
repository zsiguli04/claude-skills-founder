---
name: frontend
description: Build UI for financial data, including formatting money, percentages, and dates by locale, number input, tables, charts, and accessible disclosures. Use when writing or reviewing frontend components that show or accept financial values.
---

# Frontend

## Numbers

- Format with `Intl.NumberFormat` (or the framework's locale formatter) using the user's locale and the amount's currency. Never concatenate a symbol.
- Do arithmetic on the server or with a decimal library. Never with JS `Number` for money. Pass amounts as strings or integer minor units over the API.
- Show the precision the context needs: whole units for net worth, cents for transactions, basis points for rates when relevant.
- Negative amounts: pick one style (minus sign or parentheses) and use it everywhere. Never rely on color alone.
- Percentages: say what they're a percentage of. "+4.2% vs. last month".

## Inputs

- Accept locale decimal separators. Parse to a decimal string, not a float.
- Validate range and scale on the client for feedback and on the server for truth.
- Confirm before any action that moves money or files something, showing the exact amount and destination.

## Tables and charts

- Right-align numbers, tabular figures (`font-variant-numeric: tabular-nums`).
- Every chart states its units, period, and whether values are nominal or real.
- Projections look different from history (dashed line, shaded band) and say they are projections.

## Trust and disclosure

- Show the as-of date of every balance and price.
- Estimates and projections carry their disclaimer near the number, not only in a footer.

## Accessibility

- WCAG 2.2 AA. Charts have a text or table alternative. Gains and losses use text or icons, not only red and green.

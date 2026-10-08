---
name: financial-modeling
description: Build, extend, or review driver-based financial models (income statement, balance sheet, cash flow), scenarios, and forecasts. Use when the task involves projections, revenue builds, cost models, or checking that a model's statements tie out.
---

# Financial modeling

## Structure

Every model has four layers, kept apart:

1. **Inputs:** assumptions only. Each one has a name, unit, value, source, and the date it was set.
2. **Drivers:** revenue and cost logic computed from inputs (units x price, headcount x loaded cost, churn x base).
3. **Statements:** income statement, balance sheet, cash flow, all computed from drivers.
4. **Outputs:** KPIs, charts, and summaries computed from statements.

No layer reads from a layer below it. No hardcoded number appears outside the inputs layer.

## Arithmetic

- Use `Decimal` (Python), `BigDecimal` (Java/Kotlin), `decimal.js` or integer minor units (TypeScript). Never `float` for money.
- Round only at presentation or where a rule requires it (a tax return line, an invoice total). State the rounding mode: `ROUND_HALF_EVEN` unless a rule says otherwise.
- Store periods as explicit dates (`2026-01-01` to `2026-01-31`), not column indexes.
- Annual to monthly conversions: say whether you divide by 12 or compound (`(1 + r) ** (1/12) - 1`). They differ.

## Integrity checks

Run these after every change. A model that fails one is broken, not "close".

| Check | Rule |
|:------|:-----|
| Balance | Assets = liabilities + equity, every period, to the cent |
| Cash tie | Ending cash on the cash flow = cash on the balance sheet |
| Retained earnings | Opening RE + net income - dividends = closing RE |
| Signs | Revenue positive, expenses negative (or the reverse), consistently |
| Circularity | Interest on average debt is circular. Resolve with iteration and a convergence tolerance, or use opening balances and say so |

## Scenarios

- Base, upside, downside at minimum. Each scenario is a named set of input overrides, not a copy of the model.
- Show which inputs differ between scenarios in one table.
- Sensitivity: vary the 3 to 5 inputs that move the output most, one at a time, and show the output range.

## Review checklist

- [ ] All inputs sourced and dated
- [ ] No hardcodes in drivers or statements
- [ ] All integrity checks pass every period
- [ ] Units labeled on every row (USD, USD thousands, %, count)
- [ ] Assumptions listed at the top of any output a person reads

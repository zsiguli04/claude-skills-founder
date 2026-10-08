---
name: testing
description: Test financial calculation code with worked examples, golden files, property-based tests, reconciliation checks, and exact decimal assertions. Use when writing tests for models, valuation, tax, wealth projections, ledgers, or data pipelines.
---

# Testing

## Test types

| Type | What it catches | Example |
|:-----|:----------------|:--------|
| Worked example | Wrong formula | A tax authority's published example, a textbook DCF |
| Golden file | Unintended changes | Full model output for a fixed input set, diffed on every run |
| Property-based | Edge cases | Ledger entries always sum to zero; balance sheet always balances; tax is non-decreasing in income |
| Reconciliation | Data drift | Pipeline totals match source totals |
| Boundary | Off-by-one at thresholds | Income exactly at a bracket edge, leap years, period ends |
| Regression | Fixed bugs coming back | One test per bug, named after it |

## Assertions

- Compare `Decimal` to `Decimal` exactly. When a tolerance is right (iterative solvers, Monte Carlo), state it in the test and why.
- Monte Carlo: fix the seed. Assert percentiles within a band, not exact values, for statistical tests.
- Never assert against a value you computed with the code under test. Get expected values from an independent source or a hand calculation, and cite it in the test.

## Must-have cases

- Zero, negative, and very large amounts.
- Multiple currencies and a missing FX rate.
- Dates: month ends, Feb 29, year boundaries, time zones around midnight UTC.
- Effective-dated rules: the day before, on, and after a change.
- Empty inputs and missing optional fields.

## Golden files

- Store in `tests/golden/` as readable text (CSV, JSON, YAML).
- When a golden file changes, the PR explains why the numbers changed.

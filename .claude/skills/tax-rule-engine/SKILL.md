---
name: tax-rule-engine
description: Design, implement, or update a tax calculation engine where rules, rates, brackets, and thresholds are versioned data with effective dates, jurisdictions, and citations. Use for income, capital gains, withholding, VAT/sales tax, or any tax computation code.
---

# Tax rule engine

## Rules are data, not code

A rate or threshold never appears as a literal in calculation code. It lives in a rule record:

```yaml
id: us-federal-ltcg-brackets
jurisdiction: US
authority: IRS
tax_year: 2026
effective_from: 2026-01-01
effective_to: 2026-12-31
filing_status: single
brackets:
  - { up_to: "<amount>", rate: "0.00" }
  - { up_to: "<amount>", rate: "0.15" }
  - { up_to: null,       rate: "0.20" }
source:
  citation: "<Rev. Proc. number, section>"
  url: "<official URL>"
  retrieved: 2026-01-15
```

Fill amounts only from the cited primary source. Never from memory.

## Engine rules

- Lookup by `(jurisdiction, tax type, date or tax year, filing status)`. If no rule matches, raise an error. Never fall back to another year.
- Rules are immutable once published. A correction is a new version with a `supersedes` field.
- Every computed result returns a trace: each rule id applied, the inputs it saw, and the intermediate amounts. A user or auditor must be able to recompute it by hand.
- Rounding follows the jurisdiction's rule for that line (whole currency units, cents, or per-form instructions). Encode the rounding in the rule.
- Decimal arithmetic only.

## Jurisdictions

- Model the hierarchy: country, state or province, locality.
- Residency, source, and treaty rules are separate rule types, not if-statements in the calculator.

## Updating for a new year

1. Find the official publication (use the `regulatory-research` skill).
2. Add new rule records for the new year. Do not edit last year's.
3. Add a test case from the authority's own worked example, if one is published.
4. Diff the new rules against the prior year and list every change in the PR.

## Disclaimer

Outputs shown to end users say the result is an estimate and not tax advice.

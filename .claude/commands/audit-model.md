---
description: Audit a financial model for formula errors, hardcodes, broken links, and failed integrity checks.
argument-hint: "[path to the model file or module]"
allowed-tools: Read, Grep, Glob, Bash, Agent
---

Audit this model: $ARGUMENTS

If no path is given, look for models in the repo, list them, and ask which to audit. Then stop.

Use the `financial-analyst` agent and the `financial-modeling` skill. Read only. Don't edit the model.

Check:

1. **Integrity:** balance sheet balances, cash ties, retained earnings rolls forward, every period.
2. **Hardcodes:** numbers in drivers or statements that should be inputs.
3. **Inputs:** each has a source, date, and unit.
4. **Formulas:** inconsistent formulas across periods, wrong sign, wrong period referenced, annual and monthly mixed.
5. **Arithmetic:** floats used for money, rounding mid-calculation.
6. **Circularity:** present, intended, and converging.
7. **Reasonableness:** growth, margins, and multiples against sourced benchmarks.

Report findings ranked by impact on the output, each with location, issue, evidence, and fix. Then list the checks that passed.

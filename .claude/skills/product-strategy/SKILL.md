---
name: product-strategy
description: Shape product direction for a fintech or wealth product, including users, jobs to be done, prioritization, regulatory constraints on features, trust, and metrics. Use when deciding what to build next, scoping a feature, or writing a product brief for a financial product.
---

# Product strategy

## Start from the user's money decision

For each feature, write one line: "When [situation], [user] wants to [decision], so they [outcome]." If the feature doesn't serve a real decision, cut it.

## Constraints to check before scoping

| Constraint | Question |
|:-----------|:---------|
| Regulatory | Does this make it advice, brokerage, lending, payments, or tax preparation? Which licenses apply? Run `/regulatory-check` |
| Data | Do we have the data, at the right freshness, with rights to use it? |
| Accuracy | What happens to the user if the number is wrong? Higher stakes need more tests and review |
| Trust | Can the user see how the number was produced? |

## Prioritization

Score each candidate 1 to 5 on user value, confidence (evidence, not opinion), regulatory risk (inverted), and effort (inverted). Show the scores in a table. Ship the smallest version that answers the user's decision.

## Metrics

- One north-star metric tied to user outcomes (for example, users with a complete financial picture), not vanity counts.
- Guardrails: calculation error reports, support tickets about numbers, data freshness.

## Facts

User counts, market sizes, competitor features, and prices need sources. Mark anything else as an estimate with its arithmetic.

---
description: Check a feature, change, or calculation against current regulations in the relevant jurisdictions.
argument-hint: "[feature or change, and the jurisdictions it serves]"
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch, Agent
---

Check this against current regulation: $ARGUMENTS

Use the `tax-researcher` agent for tax questions and the `regulatory-research` skill for everything else.

1. Restate the feature, the user type, and each jurisdiction. If the jurisdiction is missing, ask and stop.
2. Classify what the feature could count as: investment advice, brokerage, payments, lending, tax preparation, data processing, marketing of financial products.
3. For each applicable regime, find the primary source and record citation, URL, effective dates, and retrieval date.
4. List requirements the feature must meet (licenses, disclosures, record keeping, consent, suitability).
5. Mark each requirement as met, not met, or unclear, with the evidence from the repo.

Report the table of requirements, the gaps, and the open questions for a lawyer or tax advisor. End with: "This is research, not legal or tax advice."

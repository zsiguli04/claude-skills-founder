# .claude/

Project-scoped Claude Code configuration for building a financial engine: models, valuation, tax rules, wealth projections, and the data, security, and reporting work around them.

This folder is separate from the `founder` plugin in `skills/`. Claude Code loads it automatically when you open this repo. The engine these skills describe lives in [`engine/`](../engine/README.md).

```
.claude/
├── skills/      domain knowledge Claude loads when a task matches
├── agents/      subagents with a narrow role and tool set
└── commands/    slash commands that chain skills and agents
```

## Skills

| Skill | Use it for |
|:------|:-----------|
| `financial-modeling` | Three-statement models, drivers, scenarios, integrity checks |
| `valuation-engine` | DCF, comparables, precedent transactions, sensitivity tables |
| `tax-rule-engine` | Tax rules as versioned, effective-dated, sourced data |
| `wealth-modeling` | Net worth, projections, Monte Carlo, withdrawal strategies |
| `data-engineering` | Market and account data pipelines, point-in-time correctness |
| `regulatory-research` | Finding, citing, and tracking primary regulatory sources |
| `ai-engineering` | LLM features that explain numbers but never compute them |
| `database-architecture` | Money types, double-entry ledgers, bitemporal tables |
| `security` | PII, secrets, authorization, audit trails |
| `testing` | Golden files, property tests, reconciliation tests |
| `frontend` | Displaying money, percentages, dates, and charts correctly |
| `reporting` | Reproducible reports with as-of dates and stated assumptions |
| `product-strategy` | Prioritizing features under regulatory and trust constraints |

## Agents

| Agent | Role |
|:------|:-----|
| `financial-analyst` | Builds and reviews models and valuations |
| `tax-researcher` | Researches tax rules and turns them into rule data |
| `data-engineer` | Designs and debugs pipelines and schemas |
| `security-reviewer` | Reviews changes for security and privacy defects |
| `qa-engineer` | Writes and runs tests for the financial engine |

## Commands

| Command | What it does |
|:--------|:-------------|
| `/valuation` | Values a company and saves the workings |
| `/test-financial-engine` | Runs and extends the engine's test suite |
| `/audit-model` | Audits a model for errors, hardcodes, and broken links |
| `/regulatory-check` | Checks a feature or change against current rules |

## Rules every skill shares

1. Money is never a binary float. Use decimal types end to end.
2. Every rate, threshold, and price has a source and an effective date.
3. Every output states its as-of date and its assumptions.
4. An LLM may explain a number. A deterministic engine computes it.
5. Nothing in this repo is tax, legal, or investment advice. Outputs that a user could act on say so.

# Phase 0: skills and tools

The smallest set that covers the work. Existing skills are used instead of writing duplicates.

## Project skills (in `../.claude/skills/`, written earlier on this branch)

| Skill | Purpose | Needed for | Required |
|:------|:--------|:-----------|:---------|
| `financial-modeling` | Three-statement models, drivers, integrity checks | phases 5, 6, 17 | yes |
| `valuation-engine` | DCF, WACC, multiples, sensitivity | phases 5, 6 | yes |
| `tax-rule-engine` | Rules as versioned, sourced data | phase 7 | yes |
| `regulatory-research` | Primary sources, citations, effective dates | phases 7, 8 | yes |
| `wealth-modeling` | Net worth, projections | phase 9 | yes |
| `database-architecture` | Money types, ledgers, bitemporal tables, RLS | phase 4 | yes |
| `data-engineering` | Ingestion, idempotency, point-in-time data | phases 14, 18 | yes |
| `ai-engineering` | LLM calls only through deterministic tools | phase 13 | yes |
| `security` | PII, authz, audit | phase 16, reviews | yes |
| `testing` | Worked examples, golden files, property tests | every phase | yes |
| `frontend` | Formatting money, accessible charts | phase 12 | yes |
| `reporting` | Reproducible reports | phase 15 | yes |
| `product-strategy` | Prioritization under regulatory constraints | MVP scope, pricing | yes |

Project agents: `financial-analyst`, `tax-researcher`, `data-engineer`, `security-reviewer`, `qa-engineer`. Project commands: `/valuation`, `/test-financial-engine`, `/audit-model`, `/regulatory-check`.

## Built-in skills used

| Skill | Purpose | When |
|:------|:--------|:-----|
| `claude-api` | Current Claude model ids, pricing, tool use, caching | phase 13 |
| `dataviz` | Chart design rules and palette | phase 12 |
| `security-review` | Review of pending changes | before each merge |
| `code-review` | Correctness review of a diff | before each merge |
| `pdf` | Checking generated PDF reports | phase 15 |
| `xlsx` | XLSX export checks | export work |
| `run` | Launching the app to verify changes | phases 11, 12 |

Not needed: the SEO, social media, and content skills; the presentation skills.

## Tools

| Tool | Use | Limits |
|:-----|:----|:-------|
| Bash, file tools | building and testing | none |
| WebSearch | regulatory status, source discovery | summaries only; cite and mark confidence |
| WebFetch, curl | reading primary sources | Hungarian official hosts blocked (see `00-environment.md`) |
| GitHub tools | PRs, CI status | scoped to this repository |
| Playwright + Chromium | E2E tests, screenshots | none |

## Not installed on purpose

Celery, SQLAlchemy, FastAPI, Next.js, and other libraries are installed per package when the phase that needs them starts, pinned in that package's lockfile. Nothing is installed globally.

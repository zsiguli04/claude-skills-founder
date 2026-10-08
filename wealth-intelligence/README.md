# Wealth Intelligence

Financial intelligence for the Hungarian market: modelled company value, personal wealth, ownership structures, potential wealth-tax exposure, regulatory change, liquidity risk, and questions to take to tax, legal, and accounting professionals.

It is decision support and compliance support. It is not legal advice, not tax evasion software, and never promises a tax reduction. Every number comes from a deterministic engine or a sourced data point; the AI only explains.

> **Status: phases 0 to 3 done (environment, architecture, repository structure, `CLAUDE.md`). No application code yet.** See [`docs/06-roadmap.md`](docs/06-roadmap.md) for the honest status of every phase.

## Read first

| Document | What it covers |
|:---------|:---------------|
| [`CLAUDE.md`](CLAUDE.md) | Engineering constitution: the rules every change follows |
| [`docs/00-environment.md`](docs/00-environment.md) | What is installed, what is missing, what is blocked |
| [`docs/01-skills-and-tools.md`](docs/01-skills-and-tools.md) | Skills and tools used, and why |
| [`docs/02-architecture.md`](docs/02-architecture.md) | Components, flows, cross-cutting decisions, risks |
| [`docs/03-database-design.md`](docs/03-database-design.md) | PostgreSQL schema, tenancy, provenance, integrity |
| [`docs/04-financial-engine-spec.md`](docs/04-financial-engine-spec.md) | Formulas, issue codes, conventions, gap analysis |
| [`docs/05-test-strategy.md`](docs/05-test-strategy.md) | Test layers, edge cases, golden dataset, CI gates |
| [`docs/06-roadmap.md`](docs/06-roadmap.md) | Phases, status, quality gate |
| [`docs/07-regulatory-status.md`](docs/07-regulatory-status.md) | Hungarian rules and their confidence |
| [`docs/08-data-sources.md`](docs/08-data-sources.md) | Candidate data sources and licence checks |
| [`docs/adr/`](docs/adr/) | Architecture decisions |
| [`docs/reviews/`](docs/reviews/) | Milestone reviews and open decisions |

## Layout

```
apps/        web (Next.js), api (FastAPI)
packages/    financial-engine, tax-engine, regulatory-engine, wealth-engine, schemas, ui, config
services/    data-ingestion, document-processing, reporting, ai
tests/       golden, integration, E2E, security, performance
docs/        architecture and decisions
scripts/     check_env.py and tooling
migrations/  Alembic
infra/       Docker and deployment
```

## Check your environment

```bash
python3 scripts/check_env.py --phase 4
```

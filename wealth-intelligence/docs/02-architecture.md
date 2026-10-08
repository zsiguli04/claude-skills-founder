# Phase 1: architecture

Status: proposed, 2026-10-08. Decisions with trade-offs are recorded in `adr/`.

## 1. Context

```
                 ┌──────────────┐        ┌──────────────────────────┐
  users ───────► │  web (Next)  │ ─────► │  api (FastAPI)           │
  advisors       └──────────────┘  JSON  │  auth, validation, RBAC  │
                                         └────────────┬─────────────┘
                                                      │
                                         ┌────────────▼─────────────┐
                                         │  domain services         │
                                         │  companies, valuations,  │
                                         │  wealth, exposure,       │
                                         │  regulations, reports    │
                                         └──┬─────────┬─────────┬───┘
                     ┌──────────────────────┘         │         └────────────────┐
          ┌──────────▼─────────┐  ┌──────────────────▼──┐  ┌──────────────────▼──┐
          │ engines (pure)     │  │ PostgreSQL          │  │ job queue (Redis +  │
          │ financial, tax,    │  │ RLS per organization│  │ Celery workers)     │
          │ regulatory, wealth │  │ append-only audit   │  │ ingestion, batch    │
          └────────────────────┘  └─────────────────────┘  │ valuation, reports, │
                                                           │ regulatory monitor  │
                                                           └──────────┬──────────┘
                                                                      │
                                         ┌────────────────────────────▼──────┐
                                         │ AI service: structured results in,│
                                         │ validated JSON explanation out    │
                                         └───────────────────────────────────┘
```

The AI sits beside the pipeline, never inside it: it reads stored results and writes explanations. It cannot change a number.

## 2. Components

| Component | Path | Responsibility | Depends on |
|:----------|:-----|:---------------|:-----------|
| Financial engine | `packages/financial-engine` | Metrics, FCFF, DCF, WACC, CAPM, multiples, asset-based and weighted valuation, scenarios, sensitivity, 3 and 5 year statistics | nothing |
| Tax engine | `packages/tax-engine` | Applying a rule version to a tax base: brackets, exemptions, statutory valuation formulas | `schemas` |
| Regulatory engine | `packages/regulatory-engine` | Rule records, statuses, versions, supersession, source types, diffing two versions, impact selection | `schemas` |
| Wealth engine | `packages/wealth-engine` | Ownership graph, look-through values, gross wealth, eligible liabilities, modelled net wealth, liquidity gap, what-if | `financial-engine` |
| Schemas | `packages/schemas` | Pydantic models shared by API, services, and AI contract; JSON Schema export for the frontend | nothing |
| Config | `packages/config` | Typed settings from environment variables | nothing |
| UI kit | `packages/ui` | React components, money and percent formatting, chart wrappers | nothing |
| API | `apps/api` | REST endpoints, OpenAPI, auth, RBAC, rate limits | services |
| Web | `apps/web` | Dashboard, wealth exposure map, company pages, wealth check | API |
| Data ingestion | `services/data-ingestion` | Source to raw to parsed to validated to normalized to deduplicated to database, quality score | `schemas` |
| Document processing | `services/document-processing` | Upload, OCR or parse, classify, extract, validate, user confirmation | `schemas` |
| Reporting | `services/reporting` | Report assembly, PDF, XLSX, CSV, JSON, versioned report snapshots | engines, `schemas` |
| AI | `services/ai` | Prompt building from stored results, Anthropic API calls, output validation, cost tracking | `schemas` |

Engines are plain Python libraries: no database, no network, no clock, no randomness without an explicit seed. That makes them fast to test, reproducible, and reusable in batch jobs.

## 3. Two kinds of value, two kinds of wealth

The single most important modelling rule:

| Concept | Meaning | Produced by |
|:--------|:--------|:------------|
| Modelled company value | Economic estimate: DCF, multiples, asset-based, as a low, base, high range | financial engine |
| Statutory company value | The value a tax rule prescribes, for example the vagyonadó draft formula `(equity + 2 x earning value) / 3` | tax engine, from a rule version |
| Modelled net wealth | Gross wealth minus modelled eligible liabilities, with modelled values | wealth engine |
| Legal tax base | What a specific rule version taxes, with its own valuation methods, exemptions, and deductions | tax engine |

They are different numbers with different names in the schema, the API, the UI, and reports. A user can see both side by side ("modelled value 4.2 to 5.1bn; value under the draft formula 3.6bn"), which is itself one of the product's most useful insights.

## 4. Key flows

### Company valuation

1. Service loads financial periods and their provenance, plus market parameters (risk-free rate, ERP, peer multiples) with their versions.
2. Validation: periods unique, balance sheet consistent, required fields present. Failures return structured errors (`docs/04-financial-engine-spec.md`).
3. Financial engine computes DCF, multiples, and optional asset-based values, each as low, base, high, then a weighted range.
4. Service stores `valuations`, `valuation_inputs`, `valuation_results` with all versions and `calculation_hash`.
5. Data quality score and confidence are attached.

### Wealth exposure map (flagship)

1. Wealth engine walks the ownership graph from the person: direct holdings, then look-through to company values (modelled and statutory).
2. Adds real estate, financial assets, other assets; subtracts eligible liabilities: modelled net wealth.
3. For each applicable rule version (for example vagyonadó DRAFT v2), the tax engine computes the legal tax base and potential exposure.
4. Liquidity gap = potential exposure minus liquid assets. Illiquid holdings (private shares, real estate) are never counted as liquid.
5. Every step is shown, with the rule status on screen.

### Regulatory monitoring (V2)

Scheduled job fetches official sources, stores each document version with a content hash, diffs against the previous version, maps changed sections to rule records, flags affected rules as needing review, and alerts the users whose profiles those rules touch. A human approves every new rule version. The system never promotes a draft to enacted on its own.

### Batch valuation (V3: 10,000 to 100,000 companies)

- Workers pull company ids from the queue in chunks, value each with the pure engine, and bulk-insert results with one transaction per chunk.
- "How many companies exceed 1bn at WACC 10%, 12%, 14%" is answered from stored valuation results per parameter set, indexed by `(parameter_set_id, base_value)`, not by recomputing on request.
- Results are keyed by data version and parameter set, so reruns are idempotent.
- Scale is claimed only after the phase 18 benchmark measures it.

## 5. Cross-cutting decisions

| Topic | Decision |
|:------|:---------|
| Money | `Decimal` and `NUMERIC`; strings in JSON; float rejected (ADR 0005) |
| Versioning | engine, data, rule, assumption, and source versions on every result; SHA-256 calculation hash over canonical JSON |
| Tenancy | `organization_id` on every tenant row, PostgreSQL row-level security, service-level checks, tests for both |
| Auth | managed identity provider with EU data residency, JWT verified by the API (ADR 0002, proposed) |
| Queue | Celery with Redis broker, PostgreSQL as the record of job outcomes (ADR 0003) |
| Migrations | Alembic, forward-only, in `migrations/` |
| API docs | OpenAPI generated from FastAPI and Pydantic models, with examples and error schemas |
| PDF | server-side HTML to PDF in `services/reporting` (engine chosen in phase 15) |
| Charts | ECharts (handles large series and graph layouts for ownership) |
| Observability | OpenTelemetry traces and metrics; structured JSON logs without personal data; AI token and cost metrics |
| Hosting | EU region (client wealth data); decision in phase 19 |

## 6. Environments

`development` (local, demo data), `staging` (production-like, synthetic and demo data only), `production`. Configuration only through environment variables (`.env.example`). No production data outside production.

## 7. Existing work on this branch

| Existing | Becomes |
|:---------|:--------|
| `engine/` (`finengine`: money, DCF, WACC, comps, bridge, sensitivity, tax rules, vagyonadó draft, wealth projection; 97 tests) | Starting point, split into `packages/financial-engine`, `packages/tax-engine`, `packages/regulatory-engine`, `packages/wealth-engine` in phase 5 (ADR 0004). Gaps are listed in `04-financial-engine-spec.md` |
| `engine/rules/hu/` (SZJA 2026, vagyonadó draft v1, v2, trusts; research record) | Seed data for the rule database in phase 7, with statuses mapped to the new status set |
| `apps/vagyonado/` (internal advisory web app; 56 tests) | Kept running as is for the office. Its features (statutory valuation, findings, liquidity check) are re-implemented on the new platform, then it is retired |

## 8. Risks

| Risk | Mitigation |
|:-----|:-----------|
| Draft law changes or is not passed | Rule versions and statuses; every exposure labelled with rule status; recalculation on new versions |
| Company data licensing (registry and financial statements) | Licence review per source before ingestion (`08-data-sources.md`); no scraping against terms |
| Official sources blocked in the build environment | Allow-list the hosts; until then, mark regulatory facts as secondary-source |
| Wrong numbers damage trust | Engine-first build, independent expected values, golden dataset, property tests, provenance on every number |
| Misuse for evasion | Product rules in `CLAUDE.md` section 0; structure scenarios always show legal uncertainty and require professional review; no "minimize tax" optimizer |
| Sensitive data breach | RLS, encryption of restricted fields, minimal AI context, audit log, EU hosting |

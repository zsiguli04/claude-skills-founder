# Milestone review: phases 0 to 3

2026-10-08. Reviewed the environment findings, architecture, database design, engine spec, test strategy, and `CLAUDE.md` from each role in the brief.

| Role | Finding | Action |
|:-----|:--------|:-------|
| CTO | The repository is a **public** fork of a plugin repo | ADR 0001 updated: only code, docs, and demo data here; private repository required before real data or deployment config |
| CTO | Official Hungarian hosts (njt.hu, kormany.hu, nav.gov.hu, mnb.hu, e-beszamolo, e-cegjegyzek) are blocked from the build environment | Recorded in `00-environment.md`; phase 8 and data ingestion depend on allow-listing them |
| CFO | Economic value and statutory (tax formula) value could be confused, as could modelled net wealth and the legal tax base | Made a first-class rule: separate fields, functions, labels (`CLAUDE.md` section 3, architecture section 3) |
| Financial modeller | The confidence score has no formula yet | Spec requires a documented, versioned function of data quality, method dispersion, and history depth; to be defined and tested in phase 5 |
| Financial modeller | CAGR is undefined for non-positive starting values | Spec returns no value with a warning, never a made-up number |
| Tax specialist | All vagyonadó details come from secondary sources | Status `DRAFT`, source type `EXPERT_INTERPRETATION`, confidence recorded (`07-regulatory-status.md`); no rule may become `ENACTED` without the official text |
| Security engineer | National batch valuations are shared, tenant valuations are private; a single `valuations` table could leak | Batch results stored under a reserved platform organization and exposed through a read-only view; RLS on everything else; cross-tenant tests mandatory |
| Security engineer | The container has unrelated cloud credentials in its environment | `00-environment.md` notes the project must not read or use them; `.env.example` lists only project variables |
| QA engineer | The prior engine raises exceptions; the brief needs structured error codes | Gap analysis in the spec; phase 5 adds the result envelope and migrates function by function |
| Product manager | Structure scenarios could drift into "pick the lowest tax" | No optimizer; every structure scenario shows legal uncertainty, costs, control, compliance risk, and "Professional review required" |
| Data licensing | No source's terms have been read | `08-data-sources.md` blocks ingestion until each row is verified |

Open decisions for the owner:

1. Create a private repository for the platform (ADR 0001).
2. Authentication provider (ADR 0002).
3. Allow-list the official Hungarian hosts in the environment.
4. Company data source and budget (free registry data versus a commercial provider).

# Roadmap and status

Status is updated at the end of each phase. "Done" means built, tested, and verified in this repository, with the test command and its output recorded in the phase notes.

| Phase | Scope | Status |
|:------|:------|:-------|
| 0 | Environment inspection | **done** (`00-environment.md`, `scripts/check_env.py`) |
| 1 | Architecture | **done** as a proposal (`02-architecture.md`, ADRs 0001 to 0005) |
| 2 | Repository structure | **started**: directory skeleton, root files. Workspace tooling (uv workspace, pnpm workspace, lint config, CI) comes with the first code in each area |
| 3 | `CLAUDE.md` | **done** |
| 4 | Database schema | designed (`03-database-design.md`); **next to implement** |
| 5 | Financial engine | specified (`04-financial-engine-spec.md`); partial prior work in `../engine` |
| 6 | Financial tests | strategy written (`05-test-strategy.md`) |
| 7 | Tax rule engine | partial prior work in `../engine/src/finengine/tax` |
| 8 | Regulatory engine | not started |
| 9 | Wealth engine | partial prior work (projection only) |
| 10 | Ownership graph | not started |
| 11 | Backend API | not started |
| 12 | Frontend | not started |
| 13 | AI layer | not started |
| 14 | Document intelligence | not started |
| 15 | Reporting | not started |
| 16 | Security | not started (rules in `CLAUDE.md`) |
| 17 | Performance | not started |
| 18 | 10,000-company benchmark | not started |
| 19 | Deployment | not started |
| 20 | Production audit | not started |

## MVP (from the brief, section 60)

Authentication, company creation and search, financial input, DCF, WACC, multiples, valuation range, sensitivity, scenarios, personal wealth profile, ownership graph, regulatory rule engine foundation, exposure model, liquidity gap, AI explanation, PDF report, audit trail.

## Final quality gate

Copied from the brief; ticked only with evidence.

- [x] Environment verified
- [x] Skills verified
- [x] Architecture documented
- [ ] Database works
- [ ] Financial engine works
- [ ] Financial tests pass
- [ ] Tax rule engine works
- [ ] Regulatory versioning works
- [ ] Wealth engine works
- [ ] Ownership graph works
- [ ] API works
- [ ] Frontend works
- [ ] AI works
- [ ] PDF works
- [ ] Security checks pass
- [ ] E2E passes
- [ ] Regression tests pass
- [ ] Demo works
- [ ] No fake production data
- [ ] No hardcoded tax assumptions
- [ ] No hardcoded valuation results
- [ ] Audit trail works
- [ ] README complete
- [ ] Deployment documented

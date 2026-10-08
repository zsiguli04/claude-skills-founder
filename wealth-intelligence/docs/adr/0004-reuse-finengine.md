# ADR 0004: reuse the existing finengine

Status: accepted.

## Context

`engine/` on this branch already has a tested Decimal-based engine (97 tests): DCF, WACC, multiples summary, equity bridge, sensitivity, versioned tax rules with statuses and parameters, the vagyonadó draft rules and calculator, and wealth projections.

## Decision

Phase 5 moves it with `git mv` into `wealth-intelligence/packages/`, split by responsibility (financial, tax, regulatory, wealth), keeping its tests and history, then extends it to the spec in `04-financial-engine-spec.md`. The legacy `apps/vagyonado` app is pinned to the old import path until it is retired, through a thin compatibility module.

## Consequences

No rewrite of working, tested code. The new result envelope (issues instead of exceptions) is added as a layer, then the old exception paths are migrated function by function with tests.

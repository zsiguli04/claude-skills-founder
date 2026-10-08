# finengine

The deterministic engine behind the `.claude/` skills. It computes every number. An LLM may explain the results, but never produces them.

## Rules

- Every amount is a `Decimal`. Passing a `float` raises `TypeError`.
- No network calls. Market inputs (risk-free rate, betas, peer multiples) are arguments, sourced by the caller.
- Tax rates live in YAML rule files with a citation and effective dates, never in code.
- Results carry their workings: discount factors, bracket lines, year-by-year rows.

## Modules

| Module | What it does |
|:-------|:-------------|
| `finengine.money` | `Money` with currency checks, `to_decimal`, rounding by ISO minor units |
| `finengine.valuation` | CAPM, beta relevering, WACC, DCF (Gordon growth or exit multiple, end or mid-year), comps percentiles, EV to equity bridge, treasury stock method, sensitivity grids |
| `finengine.tax` | Rule loader with strict validation, versioned rules with `supersedes`, lookup with no fallback year, progressive tax with a trace |
| `finengine.wealth` | Annual projection (contributions, returns, fees, inflation-indexed withdrawals), lognormal Monte Carlo with a fixed seed |

## Use

```python
from finengine.valuation import dcf, GordonGrowth, wacc

rate = wacc(600, 400, "0.10", "0.06", "0.25")          # 0.078
result = dcf([100, 110, 121], rate, GordonGrowth("0.02"), mid_year=True)
result.enterprise_value, result.terminal_share, result.warnings
```

```python
from finengine.tax import load_rules, progressive_tax

rules = load_rules("path/to/rules")
rule = rules.find("ZZ", "income", 2026, "single")
print(progressive_tax(rule, "50000").explain())
```

## Tax rule files

Real rules live in `rules/<country>/`, each with a research record. `tests/fixtures/tax/` holds `ZZ`, a made-up jurisdiction for tests only.

Rules can carry named `parameters` (limits, ratios) that tax-specific modules read with `rule.param(name)`, so no threshold lives in code. Every rule has a `status`: `enacted`, `draft` (a published bill), or `proposed` (announced, no text). `RuleSet.find` skips anything not enacted unless you pass `allow_unenacted=True`, and the result's `explain()` starts with a warning.

### Hungary (`rules/hu/`)

| Rule | Status | Notes |
|:-----|:-------|:------|
| SZJA 2026, flat 15% | enacted | Allowances not modeled |
| Vagyonadó 2026, individuals (v2) and trusts | **draft** | Bill under public consultation until 2026-10-14. 1% on net wealth above HUF 1bn, 1.5% on the base above HUF 100bn. Spouses assessed separately; linked trusts share one threshold |

`finengine.tax.hu_vagyonado` turns a list of assets and debts into the tax: real estate by the draft's purchase-price rules, unlisted company shares by the draft formula (with hidden reserves, holding companies, and minority discounts), exemption limits, ownership shares, the non-resident scope by asset type, and a line-by-line explanation. Every limit and ratio is a parameter in the rule file. Read `rules/hu/RESEARCH.md` first: the bill text was not read directly, and six questions are open.

```python
from finengine.tax import load_rules
from finengine.tax.hu_vagyonado import Asset, Debt, compute

rule = load_rules("rules/hu").find("HU", "wealth", 2026, "individual", allow_unenacted=True)
result = compute(rule, [Asset.of("Budapest flat", "1800000000", "purchase price")], [Debt.of("Mortgage", "300000000")])
print(result.explain())   # net 1.5bn, tax 5,000,000 HUF, marked DRAFT
```

## Tests

```
cd engine
pip install -e ".[dev]"
pytest -q
```

Expected values come from hand calculations, `fractions.Fraction`, or the `statistics` module, never from the code under test.

## Not built yet

- Three-statement model with integrity checks (`financial-modeling` skill)
- Multi-asset Monte Carlo with a correlation matrix
- Withdrawal strategies beyond fixed real amount, and taxes inside projections
- Vagyonadó: FX conversion, deferral, exit tax
- Precedent transactions, report generation

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

See `tests/fixtures/tax/zz-income-2026.yaml` for the format. `ZZ` is a made-up jurisdiction for tests. There are no real tax rules here yet. Add them with the `tax-researcher` agent so each one is cited from a primary source.

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
- Precedent transactions, real tax rule sets, report generation

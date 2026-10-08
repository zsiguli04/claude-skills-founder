# ADR 0005: money and precision

Status: accepted.

| Place | Representation |
|:------|:---------------|
| Python | `decimal.Decimal`, context precision 34, `ROUND_HALF_EVEN`; floats raise |
| PostgreSQL | `numeric(24,6)` for amounts, `numeric(12,10)` for rates |
| JSON (API, AI, reports) | strings, for example `"1500000000.50"` |
| TypeScript | strings in transport; formatting with `Intl.NumberFormat` on a decimal library value; no arithmetic on money in the browser |

Rounding happens only for display, or where a rule prescribes it (the rule says how). Totals are computed from unrounded values.

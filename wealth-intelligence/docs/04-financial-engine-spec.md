# Financial engine specification

Package: `packages/financial-engine` (Python, import name `wi_financial`). Pure functions, `Decimal` only, no I/O. Built in phase 5, tested in phase 6.

## 1. Result envelope

Every public function returns a result or a structured error, never raises for bad business input:

```python
@dataclass(frozen=True)
class Issue:
    code: str            # see section 2
    field: str | None    # input path, for example "periods[2].ebitda"
    message: str         # plain English; the UI translates by code
    severity: str        # "error" blocks the result; "warning" and "info" do not

@dataclass(frozen=True)
class Result(Generic[T]):
    value: T | None      # None when any error-level issue exists
    issues: tuple[Issue, ...]
    assumptions: tuple[Assumption, ...]   # every value the engine did not receive but used
    trace: tuple[Step, ...]               # formula, inputs, output for each intermediate
    engine_version: str
```

`calculation_hash` is computed by the service layer over the canonical JSON of the inputs plus `engine_version`, rule, data, and assumption versions. Canonical JSON: sorted keys, `Decimal` as normalized strings, no whitespace.

## 2. Issue codes

| Code | Severity | When |
|:-----|:---------|:-----|
| `MISSING_DATA` | error | a required input is absent |
| `ASSUMPTION_USED` | warning | an optional input defaulted (always listed in `assumptions`) |
| `REGULATORY_UNCERTAINTY` | warning | a rule is not `EFFECTIVE`, or a rule note marks a point as unconfirmed |
| `SOURCE_UNAVAILABLE` | error or warning | a market parameter or source could not be loaded (service layer) |
| `INVALID_INPUT` | error | wrong type, float, NaN, infinity |
| `INVALID_PERCENTAGE` | error | a rate or share outside its allowed range |
| `NEGATIVE_NOT_ALLOWED` | error | negative where impossible (shares outstanding, capex as a positive outflow, price) |
| `WACC_NOT_ABOVE_GROWTH` | error | `wacc <= g` for Gordon growth |
| `INCONSISTENT_BALANCE_SHEET` | error | assets differ from liabilities plus equity by more than the stated tolerance |
| `INCONSISTENT_INPUT` | warning | related metrics disagree (for example EBITDA is not EBIT plus D&A) |
| `DUPLICATE_PERIOD` | error | two periods with the same end date and consolidation flag |
| `INSUFFICIENT_HISTORY` | warning | fewer periods than a statistic needs (for example CAGR with one year) |
| `INVALID_OWNERSHIP` | error | ownership share outside 0 to 100%, or total above 100% |
| `CIRCULAR_OWNERSHIP` | error | a cycle in the ownership graph |
| `INVALID_CURRENCY` | error | unknown code, or currencies mixed without an FX rate |
| `STALE_DATA` | warning | input older than its freshness limit at the valuation date |
| `TERMINAL_VALUE_DOMINANT` | warning | PV of terminal value above 75% of enterprise value |
| `NEGATIVE_METRIC_MULTIPLE` | warning | a multiple applied to a non-positive metric is skipped |

## 3. Conventions

- Rates are decimals: `0.12` is 12%.
- Periods are explicit dates. Year `t` of the forecast is the year ending `t` years after the valuation date.
- Discounting: end-of-year by default; mid-year (`t - 0.5`) when `mid_year=True`. Terminal value is discounted at `n` in both cases. Stated in every result.
- `Decimal` context precision 34, `ROUND_HALF_EVEN`. No rounding inside the engine.
- Capex and changes in net working capital are inputs with explicit sign conventions: `capex` is a positive outflow; `delta_nwc` positive means cash consumed.

## 4. Formulas

### Metrics

- `EBITDA = EBIT + D&A`; `EBT = EBIT - net interest`; checked when all three are present, `INCONSISTENT_INPUT` warning if not equal within tolerance.
- `Net debt = debt - cash` (debt includes leases if the input says so; recorded as an assumption otherwise).
- `FCFF = EBIT x (1 - T) + D&A - CapEx - ΔNWC`.

### History statistics (current year, 3 and 5 year windows)

- Averages of revenue, EBITDA, EBIT, FCF over the window.
- `CAGR = (last / first) ^ (1 / (years - 1)) - 1`; undefined when `first <= 0` or `last < 0`: return `None` with an `INSUFFICIENT_HISTORY` or `INVALID_INPUT` warning, never a made-up value.
- Margins and their trend (slope of margin by year, ordinary least squares).

### WACC and CAPM

- `Ke = Rf + Beta x ERP + size premium + country risk premium + company-specific premium` (premiums optional, default 0 recorded as `ASSUMPTION_USED`).
- `WACC = E/(D+E) x Ke + D/(D+E) x Kd x (1 - T)`; market values; `D + E > 0`.
- Beta relevering (Hamada) as helper functions.

### DCF

- `PV(FCF_t) = FCF_t / (1 + WACC)^t`.
- Gordon: `TV = FCF_{n+1} / (WACC - g)` with `FCF_{n+1} = FCF_n x (1 + g)` unless `FCF_{n+1}` is given. Requires `WACC > g`.
- Exit multiple alternative: `TV = metric_n x multiple`.
- `EV = Σ PV(FCF_t) + PV(TV)`.
- `Equity = EV - net debt` by default. Optional bridge items (minorities, preferred, non-operating assets) are explicit inputs; when absent they are 0 and recorded as `ASSUMPTION_USED`.

### Multiples

- `EV/EBITDA`, `EV/Revenue`, `EV/EBIT`, `P/E` (P/E only when net income is positive; equity value results directly).
- Peer statistics: count, min, 25th percentile, median, 75th percentile, max (inclusive method). Range = target metric x (p25, median, p75).
- Non-positive peer multiples are excluded with a warning.

### Asset-based

- `Adjusted net assets = book equity + Σ revaluation adjustments`, each adjustment an explicit, sourced input.

### Range and weighting

- Each method returns low, base, high. DCF range comes from the scenario set (bear, base, bull) or a stated sensitivity band; multiples from the peer interquartile range.
- Weighted valuation: weights are inputs, must sum to 1; result per bound is the weighted sum of that bound.
- Confidence (0 to 100) is a documented function of data quality score, method dispersion (high minus low over base), and history depth. Its formula is versioned with the engine.

### Scenarios

A scenario is a named set of overrides on: revenue growth, EBITDA margin, WACC, terminal growth, debt, capex, working capital, multiple. Bear, base, bull run through the same pipeline; overrides are validated with the same rules as base inputs.

### Sensitivity

Two-way grids, each cell an independent engine call, invalid cells carry the issue code:

- WACC x terminal growth -> enterprise value
- WACC -> company value (one-way) and WACC x company value -> equity value
- company value x potential exposure (via the tax engine and a rule version)

## 5. Property tests required

For normal inputs (positive cash flows, `WACC > g`):

- higher WACC never increases DCF value;
- higher FCF never decreases DCF value;
- higher debt never increases equity value; lower debt never decreases it;
- higher terminal growth never decreases DCF value while `g < WACC`;
- `EV = Σ PV(FCF) + PV(TV)` exactly;
- weighted range with one method at weight 1 equals that method's range;
- low <= base <= high for every method and the weighted result.

## 6. Gap analysis against the existing `engine/` (finengine 0.1.0)

| Area | Exists | Missing |
|:-----|:-------|:--------|
| Money, Decimal, float rejection | yes | currency conversion with FX inputs |
| DCF, Gordon, exit multiple, mid-year | yes | result envelope, issue codes instead of exceptions, trace steps, explicit `FCF_{n+1}` input |
| WACC, CAPM, Hamada | yes | size, country, company-specific premiums |
| Multiples | EV-based summary | EV/EBIT, P/E, per-method low/base/high objects |
| Equity bridge, treasury stock method | yes | `ASSUMPTION_USED` for defaulted bridge items |
| Sensitivity grid | yes | named grids from section 4, error codes in cells |
| Metrics, FCFF from statements | FCFF helper only | metrics from periods, consistency checks, duplicate period detection, balance sheet check |
| History statistics, CAGR, margins | no | all |
| Asset-based, weighted valuation, confidence | no | all |
| Scenarios | no | all |
| Tax rules | statuses `enacted`, `draft`, `proposed`; parameters; localized notes | `EFFECTIVE`, `EXPIRED`, `REPEALED`; source types; confidence; DB storage |
| Wealth | single-portfolio projection, Monte Carlo | ownership graph, look-through, liquidity gap, modelled net wealth vs legal tax base split |
| Tests | 97 passing | property tests listed in section 5, golden dataset |

Phase 5 moves `engine/` into the new packages with `git mv` (history kept), adds the result envelope and issue codes, and fills the gaps in this order: metrics and validation, history statistics, DCF and WACC envelope, multiples, asset-based, weighted range, scenarios, sensitivity grids.

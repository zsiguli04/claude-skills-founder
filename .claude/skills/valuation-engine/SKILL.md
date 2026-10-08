---
name: valuation-engine
description: Implement or run company valuations with DCF, trading comparables, and precedent transactions, including WACC, terminal value, and sensitivity tables. Use when valuing a business, building valuation code, or checking a valuation's math.
---

# Valuation engine

## Methods

Use at least two methods and show where they agree.

### Discounted cash flow

- Unlevered free cash flow = EBIT x (1 - tax rate) + D&A - capex - change in net working capital.
- Discount at WACC. Use mid-year convention unless told otherwise, and say which.
- Terminal value, two ways:
  - Gordon growth: `FCF_{n+1} / (WACC - g)`. Require `g < WACC` and `g` at or below long-run nominal GDP growth. Reject the input otherwise.
  - Exit multiple: terminal EBITDA x a multiple taken from the comps set.
- Flag it when terminal value is more than 75% of enterprise value.

### WACC

- Cost of equity via CAPM: `rf + beta x ERP (+ size or country premium if used, stated)`.
- Risk-free rate: government bond yield matching the currency and horizon, with source and date.
- Beta: relevered from peer unlevered betas at the target capital structure.
- Cost of debt: after tax, from current yields or credit spread, not the coupon.
- Weights: market values, target structure if the current one is temporary.

### Trading comparables

- 5 to 10 peers. State the selection criteria (sector, size, growth, geography).
- Multiples: EV/Revenue, EV/EBITDA, P/E as relevant. Use the same period (LTM or NTM) for every peer.
- Report min, 25th percentile, median, 75th percentile, max. Use the interquartile range, not the mean.

### Precedent transactions

- Deals in the last 5 years, with date, acquirer, target, EV, and multiple.
- Note control premiums and market conditions at deal time.

## Bridge to equity

Enterprise value - net debt - minorities - preferred + non-operating assets = equity value. Divide by fully diluted shares (treasury stock method for options).

## Outputs

- A football field: each method's range on one chart.
- Sensitivity tables: WACC vs. terminal growth, WACC vs. exit multiple.
- Every market input (rf, ERP, beta, peer multiples) with a source and an as-of date.

## Code rules

- Pure functions: inputs in, valuation out. No network calls inside the math.
- Validate inputs: WACC > g, shares > 0, no negative discount factors.
- Test against at least one worked example with a known answer.

---
name: wealth-modeling
description: Model personal or household wealth, including net worth, cash flow, portfolio projections, retirement planning, Monte Carlo simulation, withdrawal strategies, fees, and inflation. Use when building or reviewing wealth projection logic.
---

# Wealth modeling

## Inputs

- Accounts: type (taxable, tax-deferred, tax-free, cash, property, liability), balance, holdings, cost basis.
- Cash flows: income, expenses, contributions, withdrawals, one-off events, each with start date, end date, and growth rate.
- Assumptions: expected return and volatility per asset class, inflation, fees, tax treatment. Every assumption sourced or labeled as the user's choice.

## Nominal vs. real

Pick one and label every output. Converting: `real = (1 + nominal) / (1 + inflation) - 1`. Do not subtract.

## Deterministic projection

- Monthly or annual steps, stated.
- Order of operations each period: income, contributions, returns, fees, taxes, withdrawals. Document the order. It changes results.
- Fees compound. Show the lifetime cost of fees in currency.

## Monte Carlo

- At least 10,000 paths for published results. Fixed seed for tests.
- Return model stated: normal, lognormal, bootstrapped historical, or regime-switching. Lognormal or bootstrap avoids returns below -100%.
- Correlation between asset classes via a covariance matrix. Check it is positive semi-definite.
- Report percentiles (5th, 25th, 50th, 75th, 95th) and probability of success. Define "success" in the output.

## Withdrawal strategies

Implement as interchangeable strategies: fixed real amount, fixed percentage, guardrails, required minimum distributions. Withdrawal order across account types is a parameter, because it drives taxes.

## Taxes

Call the tax rule engine. Never hardcode a rate here.

## Disclaimer

Projections are illustrations under stated assumptions, not predictions or investment advice. Say so in every user-facing output.

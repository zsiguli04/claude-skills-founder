"""Cost of capital. Rates are decimals: 0.045 means 4.5%."""

from __future__ import annotations

from decimal import Decimal

from finengine.money import Number, to_decimal


def cost_of_equity(risk_free: Number, beta: Number, equity_risk_premium: Number, extra_premium: Number = 0) -> Decimal:
    """CAPM: rf + beta x ERP + any size or country premium."""
    return to_decimal(risk_free) + to_decimal(beta) * to_decimal(equity_risk_premium) + to_decimal(extra_premium)


def unlever_beta(levered: Number, debt_to_equity: Number, tax_rate: Number) -> Decimal:
    """Hamada: beta_u = beta_l / (1 + (1 - t) x D/E)."""
    return to_decimal(levered) / (1 + (1 - to_decimal(tax_rate)) * to_decimal(debt_to_equity))


def relever_beta(unlevered: Number, debt_to_equity: Number, tax_rate: Number) -> Decimal:
    """Hamada: beta_l = beta_u x (1 + (1 - t) x D/E)."""
    return to_decimal(unlevered) * (1 + (1 - to_decimal(tax_rate)) * to_decimal(debt_to_equity))


def wacc(
    equity_value: Number,
    debt_value: Number,
    cost_of_equity: Number,
    pre_tax_cost_of_debt: Number,
    tax_rate: Number,
) -> Decimal:
    """Weighted average cost of capital from market values."""
    e, d = to_decimal(equity_value), to_decimal(debt_value)
    if e < 0 or d < 0 or e + d == 0:
        raise ValueError("equity and debt values must be non-negative and not both zero")
    total = e + d
    after_tax_debt = to_decimal(pre_tax_cost_of_debt) * (1 - to_decimal(tax_rate))
    return e / total * to_decimal(cost_of_equity) + d / total * after_tax_debt

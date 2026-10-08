"""Discounted cash flow on unlevered free cash flow."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from finengine.money import Number, to_decimal

TERMINAL_SHARE_WARNING = Decimal("0.75")


def unlevered_fcf(ebit: Number, tax_rate: Number, d_and_a: Number, capex: Number, change_in_nwc: Number) -> Decimal:
    """EBIT x (1 - t) + D&A - capex - change in net working capital. Capex is a positive number."""
    return (
        to_decimal(ebit) * (1 - to_decimal(tax_rate))
        + to_decimal(d_and_a)
        - to_decimal(capex)
        - to_decimal(change_in_nwc)
    )


@dataclass(frozen=True)
class GordonGrowth:
    growth: Decimal

    def __init__(self, growth: Number) -> None:
        object.__setattr__(self, "growth", to_decimal(growth))


@dataclass(frozen=True)
class ExitMultiple:
    multiple: Decimal
    terminal_metric: Decimal  # usually final-year EBITDA

    def __init__(self, multiple: Number, terminal_metric: Number) -> None:
        object.__setattr__(self, "multiple", to_decimal(multiple))
        object.__setattr__(self, "terminal_metric", to_decimal(terminal_metric))


@dataclass(frozen=True)
class DCFResult:
    discount_factors: tuple[Decimal, ...]
    pv_cash_flows: tuple[Decimal, ...]
    sum_pv_cash_flows: Decimal
    terminal_value: Decimal
    pv_terminal_value: Decimal
    enterprise_value: Decimal
    terminal_share: Decimal
    warnings: tuple[str, ...] = field(default=())


def discount_factor(rate: Decimal, t: Decimal) -> Decimal:
    return 1 / (1 + rate) ** t


def dcf(
    cash_flows: Sequence[Number],
    discount_rate: Number,
    terminal: GordonGrowth | ExitMultiple,
    mid_year: bool = False,
) -> DCFResult:
    """Enterprise value from explicit-period cash flows plus a terminal value.

    Cash flow i (0-based) is discounted at t = i + 1, or i + 0.5 with mid_year.
    The terminal value is discounted at the end of the final year in both cases.
    """
    flows = [to_decimal(cf) for cf in cash_flows]
    if not flows:
        raise ValueError("need at least one cash flow")
    rate = to_decimal(discount_rate)
    if rate <= -1:
        raise ValueError("discount rate must be above -100%")

    offset = Decimal("0.5") if mid_year else Decimal(0)
    factors = tuple(discount_factor(rate, Decimal(i + 1) - offset) for i in range(len(flows)))
    pvs = tuple(cf * f for cf, f in zip(flows, factors))

    if isinstance(terminal, GordonGrowth):
        if terminal.growth >= rate:
            raise ValueError(f"terminal growth {terminal.growth} must be below the discount rate {rate}")
        tv = flows[-1] * (1 + terminal.growth) / (rate - terminal.growth)
    elif isinstance(terminal, ExitMultiple):
        tv = terminal.terminal_metric * terminal.multiple
    else:
        raise TypeError("terminal must be GordonGrowth or ExitMultiple")

    pv_tv = tv * discount_factor(rate, Decimal(len(flows)))
    total_pv = sum(pvs, Decimal(0))
    ev = total_pv + pv_tv

    warnings = []
    share = pv_tv / ev if ev != 0 else Decimal(0)
    if ev > 0 and share > TERMINAL_SHARE_WARNING:
        warnings.append(f"terminal value is {share:.1%} of enterprise value (above 75%)")
    if ev <= 0:
        warnings.append("enterprise value is not positive")

    return DCFResult(factors, pvs, total_pv, tv, pv_tv, ev, share, tuple(warnings))

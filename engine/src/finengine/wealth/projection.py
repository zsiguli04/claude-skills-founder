"""Deterministic annual projection of one portfolio.

Order of operations each year (it changes results, so it is fixed and documented):
1. contribution at the start of the year
2. investment return on the balance after the contribution
3. fee on the balance after the return
4. withdrawal at the end of the year, capped at what is left

Withdrawals are given in today's money and grow with inflation, so they hold
their real value. All values in the output are nominal unless named *_real.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from finengine.money import Number, to_decimal


@dataclass(frozen=True)
class PlanInputs:
    start_balance: Decimal
    years: int
    expected_return: Decimal
    inflation: Decimal
    fee_rate: Decimal = Decimal(0)
    annual_contribution: Decimal = Decimal(0)
    contribution_growth: Decimal = Decimal(0)
    contribution_years: int = 0
    annual_withdrawal_real: Decimal = Decimal(0)
    withdrawal_start_year: int = 1

    @classmethod
    def of(cls, **kwargs: Number) -> PlanInputs:
        ints = {"years", "contribution_years", "withdrawal_start_year"}
        values = {k: (int(v) if k in ints else to_decimal(v)) for k, v in kwargs.items()}
        return cls(**values)

    def __post_init__(self) -> None:
        if self.years < 1:
            raise ValueError("years must be at least 1")
        if self.start_balance < 0:
            raise ValueError("start balance must not be negative")
        if not 0 <= self.fee_rate < 1:
            raise ValueError("fee rate must be between 0 and 1")
        if self.inflation <= -1:
            raise ValueError("inflation must be above -100%")


@dataclass(frozen=True)
class YearRow:
    year: int
    start: Decimal
    contribution: Decimal
    growth: Decimal
    fee: Decimal
    withdrawal: Decimal
    shortfall: Decimal
    end: Decimal
    end_real: Decimal


@dataclass(frozen=True)
class Projection:
    rows: tuple[YearRow, ...]
    total_fees: Decimal
    depleted_year: int | None

    @property
    def ending_balance(self) -> Decimal:
        return self.rows[-1].end

    @property
    def succeeded(self) -> bool:
        return self.depleted_year is None


def to_real(nominal: Decimal, inflation: Decimal, years: int) -> Decimal:
    """Deflate a nominal amount received after `years` years to today's money."""
    return nominal / (1 + inflation) ** years


def project(inputs: PlanInputs, returns: Sequence[Decimal] | None = None) -> Projection:
    """Run the projection. `returns` overrides the expected return year by year (used by Monte Carlo)."""
    if returns is not None and len(returns) != inputs.years:
        raise ValueError("need one return per year")

    balance = inputs.start_balance
    rows = []
    total_fees = Decimal(0)
    depleted_year = None
    for year in range(1, inputs.years + 1):
        start = balance
        r = inputs.expected_return if returns is None else returns[year - 1]

        contribution = Decimal(0)
        if year <= inputs.contribution_years:
            contribution = inputs.annual_contribution * (1 + inputs.contribution_growth) ** (year - 1)
        balance += contribution

        growth = balance * r
        balance = max(balance + growth, Decimal(0))

        fee = balance * inputs.fee_rate
        balance -= fee
        total_fees += fee

        wanted = Decimal(0)
        if year >= inputs.withdrawal_start_year:
            wanted = inputs.annual_withdrawal_real * (1 + inputs.inflation) ** year
        withdrawal = min(wanted, balance)
        shortfall = wanted - withdrawal
        balance -= withdrawal
        if shortfall > 0 and depleted_year is None:
            depleted_year = year

        rows.append(
            YearRow(
                year=year,
                start=start,
                contribution=contribution,
                growth=growth,
                fee=fee,
                withdrawal=withdrawal,
                shortfall=shortfall,
                end=balance,
                end_real=to_real(balance, inputs.inflation, year),
            )
        )
    return Projection(tuple(rows), total_fees, depleted_year)

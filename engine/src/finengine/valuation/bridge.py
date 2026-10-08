"""From enterprise value to equity value per share."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from finengine.money import Number, to_decimal


def equity_value(
    enterprise_value: Number,
    net_debt: Number,
    minority_interest: Number = 0,
    preferred_equity: Number = 0,
    non_operating_assets: Number = 0,
) -> Decimal:
    """EV - net debt - minorities - preferred + non-operating assets."""
    return (
        to_decimal(enterprise_value)
        - to_decimal(net_debt)
        - to_decimal(minority_interest)
        - to_decimal(preferred_equity)
        + to_decimal(non_operating_assets)
    )


def diluted_shares(basic_shares: Number, share_price: Number, options: Iterable[tuple[Number, Number]] = ()) -> Decimal:
    """Treasury stock method. options is (count, strike) pairs; only in-the-money ones dilute."""
    basic = to_decimal(basic_shares)
    price = to_decimal(share_price)
    if basic <= 0 or price <= 0:
        raise ValueError("basic shares and share price must be positive")
    added = Decimal(0)
    for count, strike in options:
        n, k = to_decimal(count), to_decimal(strike)
        if k < price:
            added += n - n * k / price
    return basic + added

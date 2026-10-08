"""Order statistics on Decimals."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal


def percentile(values: Sequence[Decimal], p: Decimal | int) -> Decimal:
    """Linear interpolation between closest ranks (the 'inclusive' method). p is 0 to 100."""
    if not values:
        raise ValueError("percentile of an empty sequence")
    p = Decimal(p)
    if not 0 <= p <= 100:
        raise ValueError("p must be between 0 and 100")
    ordered = sorted(values)
    position = (len(ordered) - 1) * p / 100
    lower = int(position)
    fraction = position - lower
    if lower + 1 >= len(ordered):
        return ordered[-1]
    return ordered[lower] + (ordered[lower + 1] - ordered[lower]) * fraction

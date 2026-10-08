"""Trading comparables and precedent transactions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from finengine.money import Number, to_decimal
from finengine.stats import percentile


@dataclass(frozen=True)
class MultipleSummary:
    count: int
    minimum: Decimal
    p25: Decimal
    median: Decimal
    p75: Decimal
    maximum: Decimal


def summarize_multiples(multiples: Mapping[str, Number]) -> MultipleSummary:
    """Summary of peer multiples, keyed by peer name. Non-positive multiples are excluded as not meaningful."""
    values = [to_decimal(v) for v in multiples.values()]
    values = [v for v in values if v > 0]
    if not values:
        raise ValueError("no positive multiples to summarize")
    return MultipleSummary(
        count=len(values),
        minimum=min(values),
        p25=percentile(values, 25),
        median=percentile(values, 50),
        p75=percentile(values, 75),
        maximum=max(values),
    )


def implied_values(metric: Number, summary: MultipleSummary) -> dict[str, Decimal]:
    """The target's metric times the interquartile range and median of the peer multiples."""
    m = to_decimal(metric)
    return {"low": m * summary.p25, "mid": m * summary.median, "high": m * summary.p75}

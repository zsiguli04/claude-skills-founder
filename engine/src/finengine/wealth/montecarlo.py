"""Monte Carlo over the deterministic projection with lognormal annual returns.

The random draws are floats (they are probabilities, not money). Each drawn
return is converted to a Decimal rounded to 12 places before it touches a
balance, so all money arithmetic stays decimal.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from decimal import Decimal

from finengine.money import Number, to_decimal
from finengine.stats import percentile
from finengine.wealth.projection import PlanInputs, project

PERCENTILES = (5, 25, 50, 75, 95)


@dataclass(frozen=True)
class SimulationResult:
    paths: int
    seed: int
    success_rate: Decimal  # share of paths that never had a withdrawal shortfall
    ending_balance: dict[int, Decimal]  # nominal, by percentile
    ending_balance_real: dict[int, Decimal]


def _lognormal_params(mean: Decimal, volatility: Decimal) -> tuple[float, float]:
    """Parameters of ln(1 + R) so that R has the given arithmetic mean and standard deviation."""
    m, s = float(mean), float(volatility)
    sigma2 = math.log(1 + s * s / ((1 + m) ** 2))
    mu = math.log(1 + m) - sigma2 / 2
    return mu, math.sqrt(sigma2)


def simulate(inputs: PlanInputs, volatility: Number, paths: int = 10_000, seed: int = 0) -> SimulationResult:
    vol = to_decimal(volatility)
    if vol < 0:
        raise ValueError("volatility must not be negative")
    if paths < 1:
        raise ValueError("paths must be at least 1")

    mu, sigma = _lognormal_params(inputs.expected_return, vol)
    rng = random.Random(seed)
    quantum = Decimal("1e-12")

    endings, endings_real, successes = [], [], 0
    for _ in range(paths):
        returns = [
            Decimal(repr(math.exp(mu + sigma * rng.gauss(0, 1)) - 1)).quantize(quantum)
            for _ in range(inputs.years)
        ]
        result = project(inputs, returns)
        endings.append(result.ending_balance)
        endings_real.append(result.rows[-1].end_real)
        successes += result.succeeded

    return SimulationResult(
        paths=paths,
        seed=seed,
        success_rate=Decimal(successes) / paths,
        ending_balance={p: percentile(endings, p) for p in PERCENTILES},
        ending_balance_real={p: percentile(endings_real, p) for p in PERCENTILES},
    )

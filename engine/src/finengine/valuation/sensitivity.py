"""Two-way sensitivity tables."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from decimal import Decimal


def grid(
    func: Callable[[Decimal, Decimal], Decimal],
    rows: Sequence[Decimal],
    cols: Sequence[Decimal],
) -> list[list[Decimal | None]]:
    """func(row, col) for every pair. Cells where the inputs are invalid (ValueError) are None."""
    table: list[list[Decimal | None]] = []
    for r in rows:
        line: list[Decimal | None] = []
        for c in cols:
            try:
                line.append(func(r, c))
            except ValueError:
                line.append(None)
        table.append(line)
    return table

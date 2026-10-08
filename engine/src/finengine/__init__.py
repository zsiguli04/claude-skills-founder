"""Deterministic financial engine.

Every amount is a Decimal. No function here makes a network call.
"""

from finengine.money import Money, to_decimal

__all__ = ["Money", "to_decimal"]
__version__ = "0.1.0"

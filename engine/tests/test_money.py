from decimal import Decimal

import pytest

from finengine.money import Money, to_decimal


def test_float_rejected():
    with pytest.raises(TypeError):
        to_decimal(0.1)
    with pytest.raises(TypeError):
        Money(0.1, "USD")


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "abc"])
def test_non_finite_and_garbage_rejected(bad):
    with pytest.raises(ValueError):
        to_decimal(bad)


def test_exact_decimal_addition():
    # 0.1 + 0.2 is 0.30000000000000004 in binary floating point.
    assert (Money("0.1", "USD") + Money("0.2", "USD")).amount == Decimal("0.3")


def test_currency_mismatch():
    with pytest.raises(ValueError):
        Money("1", "USD") + Money("1", "EUR")


def test_bad_currency_code():
    with pytest.raises(ValueError):
        Money("1", "usd")


def test_banker_rounding_by_default():
    assert Money("2.345", "USD").rounded().amount == Decimal("2.34")
    assert Money("2.355", "USD").rounded().amount == Decimal("2.36")


def test_zero_minor_unit_currency():
    assert Money("1234.5", "JPY").rounded().amount == Decimal("1234")

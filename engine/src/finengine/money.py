"""Money and decimal helpers. Binary floats are rejected everywhere."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

Number = Decimal | int | str

# ISO 4217 minor units for currencies that differ from 2.
_MINOR_UNITS = {"JPY": 0, "KRW": 0, "HUF": 2, "BHD": 3, "KWD": 3, "JOD": 3}


def to_decimal(value: Number) -> Decimal:
    """Convert to Decimal. Floats raise, because they can't hold most decimal amounts exactly."""
    if isinstance(value, bool):
        raise TypeError("bool is not a number")
    if isinstance(value, float):
        raise TypeError(f"float {value!r} rejected: pass a str, int, or Decimal")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, (int, str)):
        try:
            result = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"not a number: {value!r}") from exc
    else:
        raise TypeError(f"unsupported type {type(value).__name__}")
    if not result.is_finite():
        raise ValueError(f"not a finite number: {value!r}")
    return result


def quantize(value: Decimal, places: int, rounding: str = ROUND_HALF_EVEN) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places), rounding=rounding)


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __init__(self, amount: Number, currency: str) -> None:
        if len(currency) != 3 or not currency.isalpha() or not currency.isupper():
            raise ValueError(f"currency must be an ISO 4217 code, got {currency!r}")
        object.__setattr__(self, "amount", to_decimal(amount))
        object.__setattr__(self, "currency", currency)

    @property
    def minor_units(self) -> int:
        return _MINOR_UNITS.get(self.currency, 2)

    def rounded(self, rounding: str = ROUND_HALF_EVEN) -> Money:
        return Money(quantize(self.amount, self.minor_units, rounding), self.currency)

    def _same(self, other: Money) -> None:
        if not isinstance(other, Money):
            raise TypeError("can only combine Money with Money")
        if other.currency != self.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._same(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same(other)
        return Money(self.amount - other.amount, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __mul__(self, factor: Number) -> Money:
        return Money(self.amount * to_decimal(factor), self.currency)

    __rmul__ = __mul__

    def __lt__(self, other: Money) -> bool:
        self._same(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._same(other)
        return self.amount <= other.amount

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

"""Hungarian number input and output. Amounts stay Decimal; floats never appear."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_THOUSANDS_DOTS = re.compile(r"^-?\d{1,3}(\.\d{3})+$")


class ParseError(ValueError):
    pass


def parse_amount(text: str) -> Decimal:
    """Parse '1 500 000', '1.500.000', '1500000,50', '0,15' or '1500000.5' into a Decimal.

    Spaces (including non-breaking) are thousand separators. A comma is the
    decimal mark. Dots are thousand separators when they group digits by three
    and there is no comma; otherwise a single dot is the decimal mark.
    """
    s = (text or "").strip().replace(" ", "").replace(" ", "").replace(" ", "")
    s = s.removesuffix("Ft").removesuffix("HUF").strip()
    if not s:
        raise ParseError("Hiányzó szám.")
    if "," in s:
        if s.count(",") > 1:
            raise ParseError(f"Érvénytelen szám: {text!r}")
        s = s.replace(".", "").replace(",", ".")
    elif _THOUSANDS_DOTS.match(s):
        s = s.replace(".", "")
    try:
        value = Decimal(s)
    except InvalidOperation as exc:
        raise ParseError(f"Érvénytelen szám: {text!r}") from exc
    if not value.is_finite():
        raise ParseError(f"Érvénytelen szám: {text!r}")
    return value


def parse_percent(text: str) -> Decimal:
    """'50' or '50%' or '33,3' -> 0.5 / 0.333. Values are percentages."""
    s = (text or "").strip().removesuffix("%")
    return parse_amount(s) / 100


def _group(digits: str) -> str:
    parts = []
    while len(digits) > 3:
        parts.insert(0, digits[-3:])
        digits = digits[:-3]
    parts.insert(0, digits)
    return " ".join(parts)


def huf(value: Decimal | str | int | None, places: int = 0) -> str:
    """1500000 -> '1 500 000 Ft' with non-breaking spaces, rounded half up."""
    if value is None or value == "":
        return ""
    d = Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    sign = "-" if d < 0 else ""
    whole, _, frac = f"{abs(d):f}".partition(".")
    text = _group(whole) + ("," + frac if frac else "")
    return f"{sign}{text} Ft"


def percent(value: Decimal | str | None, places: int = 2) -> str:
    if value is None or value == "":
        return ""
    d = (Decimal(value) * 100).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP).normalize()
    whole, _, frac = f"{d:f}".partition(".")
    return whole + ("," + frac if frac else "") + " %"

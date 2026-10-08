"""Hungarian wording for the English texts the engine returns (methods, exclusion reasons)."""

from __future__ import annotations

import re
from decimal import Decimal

from vagyonado_app.formatting import huf, percent

_CATEGORY = {
    "personal_movable": "személyes használatú ingóság",
    "car": "személygépkocsi",
    "art_jewelry": "műtárgy, gyűjtemény, ékszer",
}

_EXACT = {
    "purchase price (acquired within 12 months)": "vételár (12 hónapon belüli szerzés)",
    "purchase price indexed by the MNB house price index": "MNB lakásárindexszel korrigált vételár",
    "outstanding balance": "fennálló összeg",
    "non-resident: not a Hungarian real estate, property right, or company share":
        "külföldi illetőség: nem magyar ingatlan, vagyoni értékű jog vagy cégrészesedés",
    "non-resident: not tied to a HU asset": "külföldi illetőség: nem figyelembe vett vagyonelemhez kötött",
}

_COMPANY = "unlisted company formula (equity + 2 x earning value) / 3"
_COMPANY_PARTS = {
    "equity incl. hidden reserves": "saját tőke rejtett tartalékkal",
    "holding company: equity only": "holdingtársaság: csak saját tőke",
}
_EXEMPT = re.compile(r"^exempt: (\w+) worth at most ([\d.]+)$")
_DISCOUNT = re.compile(r"^minority discount ([\d.]+)$")


def hu(text: str | None) -> str:
    """Translate an engine text. Unknown text (for example a method the user typed) is returned as is."""
    if not text:
        return ""
    if text in _EXACT:
        return _EXACT[text]
    m = _EXEMPT.match(text)
    if m:
        return f"mentes: {_CATEGORY.get(m.group(1), m.group(1))}, legfeljebb {huf(Decimal(m.group(2)))} értékig"
    if text.startswith(_COMPANY):
        parts = ["nem tőzsdei cég képlete: (saját tőke + 2 × hozamérték) / 3"]
        for part in filter(None, (p.strip() for p in text[len(_COMPANY):].split(";"))):
            d = _DISCOUNT.match(part)
            parts.append(f"kisebbségi kedvezmény {percent(Decimal(d.group(1)))}" if d else _COMPANY_PARTS.get(part, part))
        return "; ".join(parts)
    return text

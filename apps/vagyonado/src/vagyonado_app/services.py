"""The bridge between stored data and the finengine motor.

Values are recomputed from the stored valuation inputs at calculation time, so
a calculation always uses the current rule version. Every calculation is
saved with a full snapshot of its inputs and results.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import finengine
from finengine.tax import RuleSet, load_rules
from finengine.tax.hu_vagyonado import (
    CATEGORIES,
    Asset,
    Debt,
    NeedsValuation,
    VagyonadoResult,
    compute,
    real_estate_value,
    unlisted_company_value,
)
from finengine.tax.rules import Rule

from vagyonado_app import __version__ as APP_VERSION

CATEGORY_LABELS = {
    "real_estate": "Ingatlan",
    "property_right": "Vagyoni értékű jog (pl. haszonélvezet)",
    "company_share": "Cégrészesedés",
    "hu_property_company": "Külföldi társaság magyar ingatlanvagyonnal",
    "listed_security": "Tőzsdei értékpapír",
    "cash": "Pénz, betét, állampapír",
    "crypto": "Kriptoeszköz",
    "personal_movable": "Személyes használatú ingóság",
    "car": "Személygépkocsi",
    "art_jewelry": "Műtárgy, gyűjtemény, ékszer",
    "other": "Egyéb",
}
assert set(CATEGORY_LABELS) == CATEGORIES

VALUATION_KINDS = {
    "manual": "Megadott érték (pl. záróárfolyam, egyenleg, NAV-modell, értékbecslés)",
    "real_estate_purchase": "Ingatlan vételár alapján (12 hónapon belüli vagy MNB-indexált)",
    "unlisted_company": "Nem tőzsdei cégrészesedés képlettel",
}

KIND_LABELS = {"individual": "Magánszemély", "trust": "Vagyonkezelési adóalany (bizalmi vagyonkezelés, magánalapítvány)"}


class ValidationError(ValueError):
    """Bad input, with a message to show the user (Hungarian)."""


def _s(d: Decimal | None) -> str | None:
    return None if d is None else str(d)


class RuleBook:
    """Loads the Hungarian rules once and hands out the vagyonadó rule for a client kind."""

    def __init__(self, rules_dir: Path) -> None:
        self.rules: RuleSet = load_rules(rules_dir)

    def wealth_rule(self, kind: str, tax_year: int = 2026) -> Rule:
        if kind not in KIND_LABELS:
            raise ValidationError("Ismeretlen ügyféltípus.")
        return self.rules.find("HU", "wealth", tax_year, kind, allow_unenacted=True)


@dataclass(frozen=True)
class Valuation:
    value: Decimal
    method: str
    ownership_share: Decimal
    inputs: dict[str, Any]


def value_asset(rule: Rule, kind: str, f: dict[str, Any]) -> Valuation:
    """Turn parsed form fields into a value with the engine. f holds Decimals, dates, and strings."""
    if kind == "manual":
        method = (f.get("method") or "").strip()
        if not method:
            raise ValidationError("Add meg, hogyan határoztad meg az értéket (a bevallásban szerepelnie kell).")
        value = f["value"]
        if value < 0:
            raise ValidationError("Az érték nem lehet negatív.")
        share = f.get("ownership_share", Decimal(1))
        return Valuation(value, method, share, {"value": str(value), "method": method})

    if kind == "real_estate_purchase":
        valuation_date = rule.valuation_date or date(rule.tax_year, 12, 31)
        try:
            value, method = real_estate_value(
                valuation_date,
                f["acquired_on"],
                f["purchase_price"],
                f.get("index_at_purchase"),
                f.get("index_at_valuation"),
            )
        except NeedsValuation as exc:
            raise ValidationError(
                "10 évnél régebben szerzett ingatlan: a NAV értékelési modellje vagy értékbecslés kell. "
                "Vedd fel „Megadott érték” módszerrel."
            ) from exc
        except ValueError as exc:
            raise ValidationError(_hu_engine_error(exc)) from exc
        share = f.get("ownership_share", Decimal(1))
        inputs = {
            "acquired_on": f["acquired_on"].isoformat(),
            "purchase_price": str(f["purchase_price"]),
            "index_at_purchase": _s(f.get("index_at_purchase")),
            "index_at_valuation": _s(f.get("index_at_valuation")),
        }
        return Valuation(value, method, share, inputs)

    if kind == "unlisted_company":
        try:
            value, method = unlisted_company_value(
                rule,
                f["equity"],
                [f["profit_1"], f["profit_2"], f["profit_3"]],
                f["ownership_share"],
                f.get("hidden_reserves"),
                f.get("participations_to_assets", Decimal(0)),
            )
        except ValueError as exc:
            raise ValidationError(_hu_engine_error(exc)) from exc
        inputs = {
            "equity": str(f["equity"]),
            "profits": [str(f["profit_1"]), str(f["profit_2"]), str(f["profit_3"])],
            "ownership_share": str(f["ownership_share"]),
            "hidden_reserves": _s(f.get("hidden_reserves")),
            "participations_to_assets": str(f.get("participations_to_assets", Decimal(0))),
        }
        # The formula already applies the holder's share and any minority discount.
        return Valuation(value, method, Decimal(1), inputs)

    raise ValidationError("Ismeretlen értékelési mód.")


def _hu_engine_error(exc: ValueError) -> str:
    text = str(exc)
    translations = {
        "hidden reserves": "500 millió Ft feletti saját tőkénél add meg a könyvvizsgáló által felülvizsgált rejtett tartalékot (ha nincs, 0).",
        "MNB house price index": "1-10 éve szerzett ingatlannál add meg mindkét MNB lakásárindex-értéket.",
        "acquired after": "A szerzés dátuma nem lehet a fordulónap után.",
        "ownership share": "A tulajdoni hányad 0-nál nagyobb és legfeljebb 100% lehet.",
        "index values": "Az indexértékek legyenek pozitívak.",
    }
    for key, message in translations.items():
        if key in text:
            return message
    return f"Hibás adat: {text}"


def stored_valuation(rule: Rule, row: Any) -> Valuation:
    """Recompute an asset's value from its stored inputs with the current rule."""
    inputs = json.loads(row["valuation_inputs"])
    kind = row["valuation_kind"]
    share = Decimal(row["ownership_share"])
    if kind == "manual":
        return value_asset(rule, kind, {"value": Decimal(inputs["value"]), "method": inputs["method"], "ownership_share": share})
    if kind == "real_estate_purchase":
        opt = lambda k: None if inputs.get(k) is None else Decimal(inputs[k])
        return value_asset(rule, kind, {
            "acquired_on": date.fromisoformat(inputs["acquired_on"]),
            "purchase_price": Decimal(inputs["purchase_price"]),
            "index_at_purchase": opt("index_at_purchase"),
            "index_at_valuation": opt("index_at_valuation"),
            "ownership_share": share,
        })
    if kind == "unlisted_company":
        p = inputs["profits"]
        return value_asset(rule, kind, {
            "equity": Decimal(inputs["equity"]),
            "profit_1": Decimal(p[0]), "profit_2": Decimal(p[1]), "profit_3": Decimal(p[2]),
            "ownership_share": Decimal(inputs["ownership_share"]),
            "hidden_reserves": None if inputs.get("hidden_reserves") is None else Decimal(inputs["hidden_reserves"]),
            "participations_to_assets": Decimal(inputs.get("participations_to_assets", "0")),
        })
    raise ValidationError(f"Ismeretlen értékelési mód: {kind}")


@dataclass(frozen=True)
class Calculation:
    rule: Rule
    result: VagyonadoResult
    inputs: dict[str, Any]
    output: dict[str, Any]


def calculate(
    rule: Rule,
    client: Any,
    asset_rows: list[Any],
    debt_rows: list[Any],
    scale: dict[str, Decimal] | None = None,
) -> Calculation:
    """Run the engine. `scale` multiplies asset values by category, for what-if analysis."""
    assets, asset_inputs, names = [], [], {}
    for row in asset_rows:
        v = stored_valuation(rule, row)
        factor = (scale or {}).get(row["category"], Decimal(1))
        assets.append(Asset.of(row["name"], v.value * factor, v.method, row["location"], v.ownership_share, row["category"]))
        names[row["id"]] = row["name"]
        asset_inputs.append({
            "name": row["name"], "category": row["category"], "location": row["location"],
            "valuation_kind": row["valuation_kind"], "valuation_inputs": v.inputs,
            "ownership_share": str(v.ownership_share), "value": str(v.value), "method": v.method,
        })
    debts, debt_inputs = [], []
    for row in debt_rows:
        secured = names.get(row["secured_on_asset_id"])
        debts.append(Debt.of(row["name"], Decimal(row["amount"]), secured))
        debt_inputs.append({"name": row["name"], "amount": row["amount"], "secured_on": secured})

    result = compute(rule, assets, debts, resident=bool(client["resident"]))
    inputs = {
        "client": {"name": client["name"], "kind": client["kind"], "resident": bool(client["resident"])},
        "assets": asset_inputs,
        "debts": debt_inputs,
    }
    output = {
        "gross_assets": str(result.gross_assets),
        "debts": str(result.debts),
        "net_wealth": str(result.net_wealth),
        "tax_base": str(result.tax_base),
        "tax": str(result.tax.tax),
        "tax_unrounded": str(result.tax.tax_unrounded),
        "effective_rate_on_net_wealth": str(result.tax.effective_rate),
        "marginal_rate": str(result.tax.marginal_rate),
        "lines": [
            {"name": l.name, "kind": l.kind, "amount": str(l.amount), "method": l.method,
             "included": l.included, "reason": l.reason}
            for l in result.lines
        ],
        "brackets": [
            {"lower": str(b.lower), "upper": _s(b.upper), "rate": str(b.rate),
             "taxed_amount": str(b.taxed_amount), "tax": str(b.tax)}
            for b in result.tax.lines
        ],
        "rule": {
            "key": rule.key, "status": rule.status, "citation": rule.source.citation,
            "url": rule.source.url, "retrieved": rule.source.retrieved.isoformat(),
            "valuation_date": rule.valuation_date.isoformat() if rule.valuation_date else None,
            "filing_due": rule.filing_due.isoformat() if rule.filing_due else None,
            "notes": list(rule.notes),
            "notes_hu": list(rule.localized_notes.get("hu", ())),
        },
        "engine_version": finengine.__version__,
        "app_version": APP_VERSION,
    }
    return Calculation(rule, result, inputs, output)

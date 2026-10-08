"""Hungarian wealth tax (vagyonadó) from a list of assets and debts.

Modeled on the DRAFT bill published for consultation on 2026-10-06. See
engine/rules/hu/RESEARCH.md for sources and open questions. All amounts are HUF.

What this module does:
- values Hungarian real estate by the draft's purchase-price rules
- values unlisted company shares by the draft's formula (1. melléklet)
- leaves out exempt items (cheap personal movables, cars, art and jewelry)
- sums assets (times ownership share), deducts debts, applies the residency scope
- runs the net wealth through the rule's brackets

Every threshold and ratio comes from rule.parameters, not from this file.

What it does not do yet: FX conversion (give foreign assets in HUF and say which
rate you used in `method`), deferral, and the exit tax. Residency, including the
draft's 10-years-abroad test for Hungarian citizens, is the caller's call.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from finengine.money import Number, to_decimal
from finengine.tax.calculator import TaxResult, progressive_tax
from finengine.tax.rules import Rule


class NeedsValuation(ValueError):
    """The draft's simple rules don't apply; the value must come from the NAV model or an appraiser."""


def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:  # 29 February
        return d.replace(year=d.year + years, day=28)


def real_estate_value(
    valuation_date: date,
    acquired_on: date,
    purchase_price: Number,
    index_at_purchase: Number | None = None,
    index_at_valuation: Number | None = None,
) -> tuple[Decimal, str]:
    """Value of Hungarian real estate under the draft rules. Returns (value, method).

    - acquired within 12 months before the valuation date: the purchase price
    - acquired 1 to 10 years before: the purchase price times the MNB house
      price index ratio (index on the valuation date / index at purchase)
    - otherwise: raises NeedsValuation

    The exact boundary wording ("12 hónapon belül", "egy és tíz év között") is
    from summaries. Confirm against the bill.
    """
    if acquired_on > valuation_date:
        raise ValueError("acquired after the valuation date")
    price = to_decimal(purchase_price)
    if price < 0:
        raise ValueError("purchase price must not be negative")

    if acquired_on > _add_years(valuation_date, -1):
        return price, "purchase price (acquired within 12 months)"
    if acquired_on > _add_years(valuation_date, -10):
        if index_at_purchase is None or index_at_valuation is None:
            raise ValueError("acquired 1 to 10 years ago: both MNB house price index values are needed")
        start, end = to_decimal(index_at_purchase), to_decimal(index_at_valuation)
        if start <= 0 or end <= 0:
            raise ValueError("index values must be positive")
        return price * end / start, "purchase price indexed by the MNB house price index"
    raise NeedsValuation("acquired more than 10 years ago: use the NAV valuation model or an appraiser")


def unlisted_company_value(
    rule: Rule,
    equity: Number,
    after_tax_profits: Sequence[Number],
    ownership_share: Number,
    hidden_reserves: Number | None = None,
    participations_to_assets: Number = 0,
) -> tuple[Decimal, str]:
    """Value of a holding in an unlisted company under the draft formula. Returns (value, method).

    value = (equity + 2 x earning value) / 3 x ownership share, less any minority discount
    earning value = average after-tax profit of the last 3 closed years / capitalization rate,
                    zero when the average is negative

    - equity is from the last closed year's accounts
    - above the hidden-reserves threshold, audited hidden reserves must be given (0 is allowed)
    - a holding company (participations at least 90% of assets) is valued on equity alone

    The value returned is for the holder's share. Use it with ownership_share=1 on the Asset.
    """
    eq = to_decimal(equity)
    profits = [to_decimal(x) for x in after_tax_profits]
    if len(profits) != 3:
        raise ValueError("give the after-tax profit of the last 3 closed years")
    share = to_decimal(ownership_share)
    if not 0 < share <= 1:
        raise ValueError("ownership share must be above 0 and at most 1")

    notes = []
    if eq > rule.param("hidden_reserves_equity_over"):
        if hidden_reserves is None:
            raise ValueError("equity above the threshold: give audited hidden reserves (0 if none)")
        eq += to_decimal(hidden_reserves)
        notes.append("equity incl. hidden reserves")

    if to_decimal(participations_to_assets) >= rule.param("holding_participation_ratio"):
        whole = eq
        notes.append("holding company: equity only")
    else:
        average = sum(profits, Decimal(0)) / 3
        earning = max(average, Decimal(0)) / rule.param("capitalization_rate")
        whole = (eq + 2 * earning) / 3

    value = whole * share
    if share < rule.param("minority_small_below"):
        value *= 1 - rule.param("minority_small_discount")
        notes.append(f"minority discount {rule.param('minority_small_discount')}")
    elif share <= rule.param("minority_mid_up_to"):
        value *= 1 - rule.param("minority_mid_discount")
        notes.append(f"minority discount {rule.param('minority_mid_discount')}")

    method = "unlisted company formula (equity + 2 x earning value) / 3"
    return value, method + ("; " + "; ".join(notes) if notes else "")


# Asset categories. Non-residents are taxed only on the first group.
NON_RESIDENT_CATEGORIES = {"real_estate", "property_right", "company_share"}
CATEGORIES = NON_RESIDENT_CATEGORIES | {
    "hu_property_company",  # foreign-registered company holding Hungarian real estate: taxable for non-residents too
    "listed_security",
    "cash",
    "crypto",
    "personal_movable",
    "car",
    "art_jewelry",
    "other",
}


@dataclass(frozen=True)
class Asset:
    name: str
    value: Decimal  # value of the whole asset in HUF, by `method`
    method: str  # how the value was set, as the return must state it
    location: str = "HU"  # ISO 3166 country code; for company shares, where the company is registered
    ownership_share: Decimal = Decimal(1)
    category: str = "other"

    @classmethod
    def of(
        cls,
        name: str,
        value: Number,
        method: str,
        location: str = "HU",
        ownership_share: Number = 1,
        category: str = "other",
    ) -> Asset:
        if category not in CATEGORIES:
            raise ValueError(f"{name}: unknown category {category!r}")
        share = to_decimal(ownership_share)
        if not 0 < share <= 1:
            raise ValueError(f"{name}: ownership share must be above 0 and at most 1")
        amount = to_decimal(value)
        if amount < 0:
            raise ValueError(f"{name}: value must not be negative")
        return cls(name, amount, method, location.upper(), share, category)

    @property
    def owned_value(self) -> Decimal:
        return self.value * self.ownership_share


@dataclass(frozen=True)
class Debt:
    name: str
    amount: Decimal
    secured_on: str | None = None  # Asset.name this debt finances or is secured on

    @classmethod
    def of(cls, name: str, amount: Number, secured_on: str | None = None) -> Debt:
        value = to_decimal(amount)
        if value < 0:
            raise ValueError(f"{name}: debt must not be negative")
        return cls(name, value, secured_on)


@dataclass(frozen=True)
class WealthLine:
    name: str
    kind: str  # "asset" or "debt"
    amount: Decimal  # positive for assets, negative for debts
    method: str
    included: bool
    reason: str = ""


@dataclass(frozen=True)
class VagyonadoResult:
    resident: bool
    gross_assets: Decimal
    debts: Decimal
    net_wealth: Decimal
    tax_base: Decimal  # net wealth above the zero-rate band
    lines: tuple[WealthLine, ...]
    tax: TaxResult

    def explain(self) -> str:
        out = [f"{'Resident' if self.resident else 'Non-resident'} individual"]
        for line in self.lines:
            mark = "+" if line.included else "excluded:"
            extra = f" ({line.reason})" if line.reason else ""
            out.append(f"  {mark} {line.kind} {line.name}: {line.amount} HUF, {line.method}{extra}")
        out.append(f"  Net wealth {self.net_wealth} HUF, tax base {self.tax_base} HUF")
        out.append(self.tax.explain())
        return "\n".join(out)


def _in_scope(rule: Rule, a: Asset, resident: bool) -> tuple[bool, str]:
    exempt_limits = {
        "personal_movable": "personal_movable_exempt_up_to",
        "car": "car_exempt_up_to",
        "art_jewelry": "art_jewelry_exempt_up_to",
    }
    if a.category in exempt_limits:
        limit = rule.param(exempt_limits[a.category])
        if a.value <= limit:
            return False, f"exempt: {a.category} worth at most {limit}"
    if resident:
        return True, ""
    if a.category == "hu_property_company":
        return True, ""
    if a.category in NON_RESIDENT_CATEGORIES and a.location == "HU":
        return True, ""
    return False, "non-resident: not a Hungarian real estate, property right, or company share"


def compute(rule: Rule, assets: Iterable[Asset], debts: Iterable[Debt] = (), resident: bool = True) -> VagyonadoResult:
    """Wealth tax for one individual. Assess spouses separately with their own assets.

    Residents: all assets and debts count, less exempt items.
    Non-residents: Hungarian real estate, related property rights, shares in
    Hungarian companies, and shares in foreign companies holding Hungarian real
    estate. Only debts secured on an included asset are deducted (assumption).
    For linked trusts and foundations, pass all their assets in one call: they
    share one threshold.
    """
    if rule.tax_type != "wealth" or rule.jurisdiction != "HU":
        raise ValueError(f"{rule.key} is not a Hungarian wealth tax rule")

    lines: list[WealthLine] = []
    included_assets: set[str] = set()
    gross = Decimal(0)
    for a in assets:
        if any(line.kind == "asset" and line.name == a.name for line in lines):
            raise ValueError(f"duplicate asset name {a.name!r}")
        ok, reason = _in_scope(rule, a, resident)
        lines.append(WealthLine(a.name, "asset", a.owned_value, a.method, ok, reason))
        if ok:
            included_assets.add(a.name)
            gross += a.owned_value

    total_debt = Decimal(0)
    for d in debts:
        ok = resident or d.secured_on in included_assets
        lines.append(
            WealthLine(d.name, "debt", -d.amount, "outstanding balance", ok, "" if ok else "non-resident: not tied to a HU asset")
        )
        if ok:
            total_debt += d.amount

    net = max(gross - total_debt, Decimal(0))
    first = rule.brackets[0]
    threshold = first.up_to if first.rate == 0 and first.up_to is not None else Decimal(0)
    return VagyonadoResult(
        resident=resident,
        gross_assets=gross,
        debts=total_debt,
        net_wealth=net,
        tax_base=max(net - threshold, Decimal(0)),
        lines=tuple(lines),
        tax=progressive_tax(rule, net),
    )

"""Material for the advisor: findings, what-if tables, and a multi-year view.

Nothing here is advice in itself. Findings point at facts in the client's data
that an advisor should look at; the advisor writes the recommendation.

Tax thresholds come from the rule. The "near a limit" bands below are review
heuristics of this app, not tax law.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from finengine.tax import progressive_tax
from finengine.tax.rules import Rule

from vagyonado_app.formatting import huf, percent
from vagyonado_app.services import Calculation, calculate

NEAR_THRESHOLD = Decimal("0.10")  # net wealth within 10% of the threshold
NEAR_LIMIT = Decimal("0.20")  # item value within 20% of an exemption limit
NEAR_SHARE = Decimal("0.03")  # ownership within 3 percentage points of a discount edge
LIQUID = {"cash", "listed_security", "crypto"}
FOREIGN_CHECK = {"real_estate", "property_right", "company_share", "listed_security", "cash", "crypto", "other"}

SCENARIO_GROUPS = {
    "Ingatlanok": {"real_estate", "property_right", "hu_property_company"},
    "Cégrészesedések": {"company_share"},
    "Értékpapírok és kripto": {"listed_security", "crypto"},
}
SCENARIO_STEPS = [Decimal("-0.2"), Decimal("-0.1"), Decimal("0"), Decimal("0.1"), Decimal("0.2")]
EXEMPT_LIMITS = {
    "personal_movable": "personal_movable_exempt_up_to",
    "car": "car_exempt_up_to",
    "art_jewelry": "art_jewelry_exempt_up_to",
}


@dataclass(frozen=True)
class Finding:
    level: str  # "action" (do something), "warning" (risk), "info" (keep in mind)
    title: str
    detail: str


def findings(rule: Rule, client: Any, calc: Calculation) -> list[Finding]:
    out: list[Finding] = []
    result = calc.result
    threshold = rule.brackets[0].up_to if rule.brackets[0].rate == 0 else Decimal(0)
    net, tax = result.net_wealth, result.tax.tax
    included = {l.name: l for l in result.lines if l.kind == "asset" and l.included}
    assets = {a["name"]: a for a in calc.inputs["assets"]}

    # Status of the law
    if not rule.is_enacted:
        out.append(Finding("warning", "Tervezet alapján készült",
                           "A vagyonadó még nem törvény. A végleges szöveg megjelenése után a számítást meg kell ismételni."))

    # Threshold
    if threshold and abs(net - threshold) <= threshold * NEAR_THRESHOLD:
        side = "alatta" if net <= threshold else "felette"
        out.append(Finding("action", f"A nettó vagyon az 1 milliárdos határ közelében van ({side})",
                           f"Nettó vagyon {huf(net)}. Itt minden értékelési döntés és a tartozások pontos összege "
                           "eldöntheti az adókötelezettséget: minden értéket dokumentáltan, a tervezet módszereivel kell meghatározni."))
    elif net <= threshold:
        out.append(Finding("info", "A jelenlegi adatok alapján nincs fizetendő adó",
                           f"Nettó vagyon {huf(net)}, a határ {huf(threshold)}. A vagyon változását évente, a fordulónapon érdemes újra ellenőrizni."))

    # Liquidity
    liquid = sum((l.amount for n, l in included.items() if assets[n]["category"] in LIQUID), Decimal(0))
    if tax > 0 and tax > liquid:
        out.append(Finding("warning", "Likviditási kockázat",
                           f"A becsült adó ({huf(tax)}) több, mint a likvid vagyon (pénz, betét, értékpapír, kripto: {huf(liquid)}). "
                           "A befizetéshez szükséges forrást előre meg kell tervezni. A tervezet likviditási gond esetén halasztást ígér, "
                           "ennek feltételei a végleges szövegből derülnek ki."))
    elif tax > 0 and tax * 2 > liquid:
        out.append(Finding("info", "Az adó a likvid vagyon jelentős része",
                           f"Az adó {huf(tax)}, a likvid vagyon {huf(liquid)}."))

    # Valuation details per asset
    for name, a in assets.items():
        inputs = a["valuation_inputs"]
        cat = a["category"]
        if a["valuation_kind"] == "unlisted_company":
            equity = Decimal(inputs["equity"])
            if equity > rule.param("hidden_reserves_equity_over") and inputs.get("hidden_reserves") in ("0", None):
                out.append(Finding("action", f"{name}: rejtett tartalék nulla",
                                   "500 millió Ft feletti saját tőkénél a tervezet könyvvizsgáló által felülvizsgált rejtett tartalékot ír elő. "
                                   "A nulla értéket is alá kell támasztani (ingatlanok, részesedések, értékpapírok piaci és könyv szerinti értéke)."))
            share = Decimal(inputs["ownership_share"])
            for edge in (rule.param("minority_small_below"), rule.param("minority_mid_up_to")):
                if abs(share - edge) <= NEAR_SHARE:
                    out.append(Finding("info", f"{name}: tulajdoni hányad a kedvezményhatár közelében",
                                       f"Hányad {percent(share)}, határ {percent(edge)}. A kisebbségi kedvezmény mértéke ezen múlik, "
                                       "és a pontos határesetek a tervezetből még nem egyértelműek."))
            if Decimal(inputs.get("participations_to_assets", "0")) >= rule.param("holding_participation_ratio"):
                out.append(Finding("info", f"{name}: holdingként értékelve",
                                   "Csak a saját tőke számít. Az eszközarány számítását dokumentálni kell."))
        if a["valuation_kind"] == "manual" and cat == "real_estate" and a["location"] == "HU":
            out.append(Finding("info", f"{name}: megadott értékű magyar ingatlan",
                               "A tervezet sorrendje: 12 hónapon belüli ügyleti érték, indexált korábbi ügyleti érték, NAV-modell, "
                               "végül értékbecslés. Dokumentáld, miért ez a módszer alkalmazható."))
        if cat in EXEMPT_LIMITS:
            limit = rule.param(EXEMPT_LIMITS[cat])
            value = Decimal(a["value"])
            if limit * (1 - NEAR_LIMIT) <= value <= limit * (1 + NEAR_LIMIT):
                out.append(Finding("info", f"{name}: érték a mentességi határ közelében",
                                   f"Érték {huf(value)}, határ {huf(limit)}. Az értékelés alátámasztása dönti el, hogy beleszámít-e."))
        if client["resident"] and a["location"] != "HU" and name in included and cat in FOREIGN_CHECK:
            out.append(Finding("info", f"{name}: külföldi vagyonelem",
                               "Rögzítsd az átváltási árfolyamot és forrását. A tervezet szerint a külföldön fizetett vagyonadó-jellegű adó "
                               "nem számítható be, csak a helyi, ingatlanadó jellegű adók."))

    # Residency
    if not client["resident"]:
        out.append(Finding("info", "Külföldi illetőség",
                           "Magyar állampolgárnál a tervezet legalább 10 év külföldi életvitelszerű tartózkodást kíván. "
                           "Az illetőség megállapítását dokumentálni kell."))
        if any(l.kind == "debt" and not l.included for l in result.lines):
            out.append(Finding("info", "Nem levont tartozás",
                               "Külföldi illetőségűnél csak a figyelembe vett vagyonelemhez kötött tartozást vontuk le (feltételezés)."))

    # Spouses and family
    if client["kind"] == "individual" and net > threshold:
        out.append(Finding("info", "Házastárs és családtagok",
                           "Mindenkinek saját 1 milliárdos határa van, a közös tulajdont a tulajdoni hányad szerint kell megosztani. "
                           "Ellenőrizd, hogy a hányadok a tényleges tulajdoni helyzetet tükrözik-e (ingatlan-nyilvántartás, cégjegyzék, "
                           "vagyonjogi szerződés). A kiskorú gyermeknek juttatott vagyon a szülőnél számít."))

    # Dates
    if rule.valuation_date and rule.filing_due:
        out.append(Finding("info", "Határidők",
                           f"Fordulónap: {rule.valuation_date.isoformat()}. Bevallás és befizetés: {rule.filing_due.isoformat()}. "
                           "A fordulónapi záróárfolyamokat, egyenlegeket és a lezárt beszámolókat időben össze kell gyűjteni."))
    order = {"action": 0, "warning": 1, "info": 2}
    return sorted(out, key=lambda f: order[f.level])


def scenarios(rule: Rule, client: Any, asset_rows: list[Any], debt_rows: list[Any], calc: Calculation) -> list[dict[str, Any]]:
    """Tax if one asset group's value changes by -20% to +20%, all else equal."""
    present = {a["category"] for a in calc.inputs["assets"]}
    rows = []
    for label, cats in SCENARIO_GROUPS.items():
        if not present & cats:
            continue
        taxes = []
        for step in SCENARIO_STEPS:
            factor = 1 + step
            c = calculate(rule, client, asset_rows, debt_rows, scale={cat: factor for cat in cats})
            taxes.append(str(c.result.tax.tax))
        rows.append({"group": label, "taxes": taxes})
    return rows


def projection(rule: Rule, net_wealth: Decimal, growth: Decimal, years: int = 5) -> list[dict[str, str]]:
    """Net wealth and tax year by year if wealth grows at `growth` after tax and the same rule applies every year."""
    rows = []
    wealth = net_wealth
    total = Decimal(0)
    for i in range(years):
        tax = progressive_tax(rule, max(wealth, Decimal(0))).tax
        total += tax
        rows.append({"year": str(rule.tax_year + i), "wealth": str(wealth), "tax": str(tax), "cumulative": str(total)})
        wealth = (wealth - tax) * (1 + growth)
    return rows


def analysis(rule: Rule, client: Any, asset_rows: list[Any], debt_rows: list[Any], calc: Calculation,
             growth: Decimal = Decimal("0.05")) -> dict[str, Any]:
    return {
        "findings": [asdict(f) for f in findings(rule, client, calc)],
        "scenario_steps": [str(s) for s in SCENARIO_STEPS],
        "scenarios": scenarios(rule, client, asset_rows, debt_rows, calc),
        "projection_growth": str(growth),
        "projection": projection(rule, calc.result.net_wealth, growth),
    }

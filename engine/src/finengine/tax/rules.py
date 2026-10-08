"""Loading and looking up tax rule records.

A rule record is a YAML mapping. Amounts and rates must be quoted strings so
YAML never turns them into floats. See tests/fixtures/tax/ for the format.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP, Decimal
from pathlib import Path

import yaml

from finengine.money import to_decimal

ROUNDING_MODES = {
    "half_even": ROUND_HALF_EVEN,
    "half_up": ROUND_HALF_UP,
    "down": ROUND_DOWN,
    "up": ROUND_UP,
}


class RuleError(ValueError):
    """A rule record is malformed."""


class NoRuleError(LookupError):
    """No rule matches the lookup. The engine never falls back to another year."""


@dataclass(frozen=True)
class Source:
    citation: str
    url: str
    retrieved: date


@dataclass(frozen=True)
class Bracket:
    up_to: Decimal | None  # None means no upper limit
    rate: Decimal


@dataclass(frozen=True)
class Rule:
    id: str
    version: int
    jurisdiction: str
    tax_type: str
    tax_year: int
    filing_status: str
    effective_from: date
    effective_to: date
    brackets: tuple[Bracket, ...]
    rounding_quantum: Decimal
    rounding_mode: str
    source: Source
    supersedes: str | None = None

    @property
    def key(self) -> str:
        return f"{self.id}@{self.version}"


def _decimal(value: object, where: str) -> Decimal:
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise RuleError(f"{where}: amounts must be quoted strings, got {value!r}")
    try:
        return to_decimal(value)
    except (TypeError, ValueError) as exc:
        raise RuleError(f"{where}: {exc}") from exc


def _date(value: object, where: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise RuleError(f"{where}: {exc}") from exc
    raise RuleError(f"{where}: expected a date, got {value!r}")


def _required(raw: dict, name: str, where: str) -> object:
    if raw.get(name) in (None, ""):
        raise RuleError(f"{where}: missing {name}")
    return raw[name]


def parse_rule(raw: dict, origin: str = "<rule>") -> Rule:
    if not isinstance(raw, dict):
        raise RuleError(f"{origin}: a rule must be a mapping")
    rid = str(_required(raw, "id", origin))
    where = f"{origin}:{rid}"

    src = _required(raw, "source", where)
    if not isinstance(src, dict):
        raise RuleError(f"{where}: source must be a mapping")
    source = Source(
        citation=str(_required(src, "citation", f"{where}.source")),
        url=str(_required(src, "url", f"{where}.source")),
        retrieved=_date(_required(src, "retrieved", f"{where}.source"), f"{where}.source.retrieved"),
    )

    raw_brackets = _required(raw, "brackets", where)
    if not isinstance(raw_brackets, list):
        raise RuleError(f"{where}: brackets must be a list")
    brackets = []
    previous = Decimal(0)
    for i, b in enumerate(raw_brackets):
        bw = f"{where}.brackets[{i}]"
        rate = _decimal(_required(b, "rate", bw), f"{bw}.rate")
        if not 0 <= rate <= 1:
            raise RuleError(f"{bw}: rate {rate} is outside 0 to 1")
        up_to = None if b.get("up_to") is None else _decimal(b["up_to"], f"{bw}.up_to")
        if up_to is None and i != len(raw_brackets) - 1:
            raise RuleError(f"{bw}: only the last bracket may be open-ended")
        if up_to is not None and up_to <= previous:
            raise RuleError(f"{bw}: up_to must increase")
        if up_to is not None:
            previous = up_to
        brackets.append(Bracket(up_to, rate))
    if not brackets or brackets[-1].up_to is not None:
        raise RuleError(f"{where}: the last bracket must have up_to: null")

    rounding = raw.get("rounding") or {}
    mode = rounding.get("mode", "half_even")
    if mode not in ROUNDING_MODES:
        raise RuleError(f"{where}: unknown rounding mode {mode!r}")

    effective_from = _date(_required(raw, "effective_from", where), f"{where}.effective_from")
    effective_to = _date(_required(raw, "effective_to", where), f"{where}.effective_to")
    if effective_to < effective_from:
        raise RuleError(f"{where}: effective_to is before effective_from")

    return Rule(
        id=rid,
        version=int(raw.get("version", 1)),
        jurisdiction=str(_required(raw, "jurisdiction", where)),
        tax_type=str(_required(raw, "tax_type", where)),
        tax_year=int(_required(raw, "tax_year", where)),
        filing_status=str(_required(raw, "filing_status", where)),
        effective_from=effective_from,
        effective_to=effective_to,
        brackets=tuple(brackets),
        rounding_quantum=_decimal(rounding.get("quantum", "0.01"), f"{where}.rounding.quantum"),
        rounding_mode=mode,
        source=source,
        supersedes=raw.get("supersedes"),
    )


class RuleSet:
    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules: dict[str, Rule] = {}
        for rule in rules:
            if rule.key in self._rules:
                raise RuleError(f"duplicate rule {rule.key}")
            self._rules[rule.key] = rule
        for rule in self._rules.values():
            if rule.supersedes and rule.supersedes not in self._rules:
                raise RuleError(f"{rule.key} supersedes unknown rule {rule.supersedes}")
        self._superseded = {r.supersedes for r in self._rules.values() if r.supersedes}

    def __len__(self) -> int:
        return len(self._rules)

    def find(self, jurisdiction: str, tax_type: str, tax_year: int, filing_status: str) -> Rule:
        matches = [
            r
            for r in self._rules.values()
            if r.key not in self._superseded
            and (r.jurisdiction, r.tax_type, r.tax_year, r.filing_status)
            == (jurisdiction, tax_type, tax_year, filing_status)
        ]
        if not matches:
            raise NoRuleError(f"no {tax_type} rule for {jurisdiction} {tax_year} {filing_status}")
        if len(matches) > 1:
            keys = ", ".join(sorted(r.key for r in matches))
            raise RuleError(f"ambiguous rules: {keys}. Mark the older one as superseded.")
        return matches[0]


def load_rules(directory: str | Path) -> RuleSet:
    """Load every *.yaml file under directory. Each file holds one rule or a list of rules."""
    rules = []
    for path in sorted(Path(directory).rglob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for raw in data if isinstance(data, list) else [data]:
            rules.append(parse_rule(raw, str(path)))
    return RuleSet(rules)

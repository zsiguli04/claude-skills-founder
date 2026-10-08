"""Progressive bracket tax with a full trace."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from finengine.money import Number, to_decimal
from finengine.tax.rules import ROUNDING_MODES, Rule


@dataclass(frozen=True)
class BracketLine:
    lower: Decimal
    upper: Decimal | None
    rate: Decimal
    taxed_amount: Decimal
    tax: Decimal


@dataclass(frozen=True)
class TaxResult:
    rule_key: str
    citation: str
    taxable_amount: Decimal
    tax_unrounded: Decimal
    tax: Decimal
    effective_rate: Decimal
    marginal_rate: Decimal
    lines: tuple[BracketLine, ...]

    def explain(self) -> str:
        out = [f"Rule {self.rule_key} ({self.citation}) on {self.taxable_amount}:"]
        for line in self.lines:
            upper = "and above" if line.upper is None else f"to {line.upper}"
            out.append(f"  {line.lower} {upper} at {line.rate}: {line.taxed_amount} taxed, {line.tax} tax")
        out.append(f"  Total {self.tax_unrounded}, rounded to {self.tax}")
        return "\n".join(out)


def progressive_tax(rule: Rule, taxable_amount: Number) -> TaxResult:
    amount = to_decimal(taxable_amount)
    if amount < 0:
        raise ValueError("taxable amount must not be negative")

    lines = []
    lower = Decimal(0)
    total = Decimal(0)
    marginal = rule.brackets[0].rate
    for bracket in rule.brackets:
        if amount <= lower:
            break
        top = amount if bracket.up_to is None else min(amount, bracket.up_to)
        taxed = top - lower
        tax = taxed * bracket.rate
        lines.append(BracketLine(lower, bracket.up_to, bracket.rate, taxed, tax))
        total += tax
        marginal = bracket.rate
        if bracket.up_to is None:
            break
        lower = bracket.up_to

    rounded = total.quantize(rule.rounding_quantum, rounding=ROUNDING_MODES[rule.rounding_mode])
    effective = total / amount if amount else Decimal(0)
    return TaxResult(
        rule_key=rule.key,
        citation=rule.source.citation,
        taxable_amount=amount,
        tax_unrounded=total,
        tax=rounded,
        effective_rate=effective,
        marginal_rate=marginal,
        lines=tuple(lines),
    )

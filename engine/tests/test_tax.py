from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from finengine.tax import NoRuleError, RuleError, load_rules, progressive_tax
from finengine.tax.rules import parse_rule

FIXTURES = Path(__file__).parent / "fixtures" / "tax"
D = Decimal


@pytest.fixture(scope="module")
def rule():
    return load_rules(FIXTURES).find("ZZ", "income", 2026, "single")


def test_superseded_version_is_not_used(rule):
    assert rule.key == "zz-income-single@2"


def test_no_fallback_to_another_year():
    rules = load_rules(FIXTURES)
    with pytest.raises(NoRuleError):
        rules.find("ZZ", "income", 2027, "single")


@pytest.mark.parametrize(
    "income, expected",
    [
        # Version 2 brackets: 10% to 10,000; 25% to 40,000; 35% above.
        ("0", "0"),
        ("10000", "1000"),        # exactly at the first edge
        ("10001", "1000.25"),     # one unit into the second bracket
        ("40000", "8500"),        # 1,000 + 30,000 x 25%
        ("50000", "12000"),       # 8,500 + 10,000 x 35%
    ],
)
def test_bracket_edges(rule, income, expected):
    result = progressive_tax(rule, income)
    assert result.tax_unrounded == D(expected)


def test_rounding_follows_the_rule(rule):
    # 1,000.25 rounds half up to whole units: 1,000
    assert progressive_tax(rule, "10001").tax == D("1000")
    # 1,000.50 rounds half up: 1,001
    assert progressive_tax(rule, "10002").tax == D("1001")


def test_trace_reconciles_and_cites(rule):
    result = progressive_tax(rule, "50000")
    assert sum(line.tax for line in result.lines) == result.tax_unrounded
    assert sum(line.taxed_amount for line in result.lines) == D("50000")
    assert result.marginal_rate == D("0.35")
    assert "Test fixture, version 2" in result.explain()


def test_negative_income_rejected(rule):
    with pytest.raises(ValueError):
        progressive_tax(rule, "-1")


amounts = st.decimals(min_value=0, max_value=10_000_000, places=2, allow_nan=False, allow_infinity=False)


@given(a=amounts, b=amounts)
def test_tax_never_decreases_with_income(rule, a, b):
    low, high = sorted((a, b))
    assert progressive_tax(rule, low).tax_unrounded <= progressive_tax(rule, high).tax_unrounded


@given(a=amounts)
def test_effective_rate_bounded_by_top_rate(rule, a):
    assert 0 <= progressive_tax(rule, a).effective_rate <= D("0.35")


def _raw(**overrides):
    base = {
        "id": "x",
        "jurisdiction": "ZZ",
        "tax_type": "income",
        "tax_year": 2026,
        "filing_status": "single",
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "brackets": [{"up_to": None, "rate": "0.1"}],
        "source": {"citation": "c", "url": "u", "retrieved": "2026-01-01"},
    }
    base.update(overrides)
    return base


def test_float_amounts_in_rule_files_are_rejected():
    with pytest.raises(RuleError, match="quoted strings"):
        parse_rule(_raw(brackets=[{"up_to": None, "rate": 0.1}]))


def test_rule_without_source_is_rejected():
    with pytest.raises(RuleError, match="source"):
        parse_rule(_raw(source=None))


@pytest.mark.parametrize(
    "brackets",
    [
        [{"up_to": "100", "rate": "0.1"}],  # last bracket not open-ended
        [{"up_to": None, "rate": "0.1"}, {"up_to": None, "rate": "0.2"}],
        [{"up_to": "100", "rate": "0.1"}, {"up_to": "50", "rate": "0.2"}, {"up_to": None, "rate": "0.3"}],
        [{"up_to": None, "rate": "1.5"}],
    ],
)
def test_malformed_brackets_rejected(brackets):
    with pytest.raises(RuleError):
        parse_rule(_raw(brackets=brackets))

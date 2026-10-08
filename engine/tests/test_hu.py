"""Hungarian rules from engine/rules/hu. Expected values are hand calculations shown inline."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from finengine.tax import NoRuleError, RuleError, load_rules, progressive_tax
from finengine.tax.hu_vagyonado import Asset, Debt, NeedsValuation, compute, real_estate_value
from finengine.tax.rules import parse_rule

RULES = Path(__file__).parents[1] / "rules" / "hu"
D = Decimal
BN = D(1_000_000_000)


@pytest.fixture(scope="module")
def rules():
    return load_rules(RULES)


@pytest.fixture(scope="module")
def wealth_rule(rules):
    return rules.find("HU", "wealth", 2026, "individual", allow_unenacted=True)


def test_hungarian_rules_load(rules):
    assert len(rules) == 2


def test_draft_wealth_tax_is_refused_by_default(rules):
    with pytest.raises(NoRuleError, match="draft"):
        rules.find("HU", "wealth", 2026, "individual")


def test_draft_rule_carries_its_status_and_dates(wealth_rule):
    assert wealth_rule.status == "draft"
    assert wealth_rule.valuation_date == date(2026, 12, 31)
    assert wealth_rule.filing_due == date(2027, 8, 31)
    assert any("consultation" in n for n in wealth_rule.notes)
    assert progressive_tax(wealth_rule, 2 * BN).explain().startswith("DRAFT RULE")


def test_szja_is_flat_15_percent(rules):
    rule = rules.find("HU", "income", 2026, "individual")
    assert rule.is_enacted
    # 10,000,000 x 15% = 1,500,000
    assert progressive_tax(rule, "10000000").tax == D("1500000")


def test_no_hungarian_wealth_rule_for_2027_yet(rules):
    with pytest.raises(NoRuleError):
        rules.find("HU", "wealth", 2027, "individual", allow_unenacted=True)


@pytest.mark.parametrize(
    "net_wealth, expected",
    [
        ("999999999", "0"),
        ("1000000000", "0"),               # exactly at the threshold
        ("1000000001", "0.01"),            # 1 forint over, 1%
        ("1500000000", "5000000"),         # 500m x 1%
        ("101000000000", "1000000000"),    # top of the 1% band: 100bn x 1%
        ("111000000000", "1150000000"),    # 1bn + 10bn x 1.5%
    ],
)
def test_vagyonado_bands(wealth_rule, net_wealth, expected):
    assert progressive_tax(wealth_rule, net_wealth).tax_unrounded == D(expected)


@given(st.decimals(min_value=0, max_value=D("1e12"), places=0, allow_nan=False, allow_infinity=False))
def test_vagyonado_never_above_top_rate_on_the_base(wealth_rule, w):
    tax = progressive_tax(wealth_rule, w).tax_unrounded
    assert 0 <= tax <= max(w - BN, 0) * D("0.015")


VAL = date(2026, 12, 31)


def test_real_estate_bought_within_12_months_uses_price():
    assert real_estate_value(VAL, date(2026, 3, 1), "800000000")[0] == D("800000000")


def test_real_estate_bought_1_to_10_years_ago_is_indexed():
    # 400m x 150 / 120 = 500m
    value, method = real_estate_value(VAL, date(2020, 6, 1), "400000000", "120", "150")
    assert value == D("500000000")
    assert "MNB" in method


def test_real_estate_indexing_needs_both_index_values():
    with pytest.raises(ValueError, match="index"):
        real_estate_value(VAL, date(2020, 6, 1), "400000000")


def test_real_estate_older_than_10_years_needs_nav_model_or_appraiser():
    with pytest.raises(NeedsValuation):
        real_estate_value(VAL, date(2010, 1, 1), "100000000")


def test_resident_counts_foreign_assets_and_all_debts(wealth_rule):
    assets = [
        Asset.of("Budapest flat", "900000000", "purchase price"),
        Asset.of("Vienna flat", "700000000", "valuation", location="AT"),
        Asset.of("Listed shares", "600000000", "year-end closing price", ownership_share="0.5"),
    ]
    debts = [Debt.of("Mortgage", "200000000", secured_on="Vienna flat")]
    result = compute(wealth_rule, assets, debts, resident=True)
    # 900m + 700m + 300m - 200m = 1,700m; base 700m; tax 7m
    assert result.net_wealth == D("1700000000")
    assert result.tax_base == D("700000000")
    assert result.tax.tax == D("7000000")
    assert "Vienna flat" in result.explain()


def test_non_resident_counts_only_hungarian_assets_and_their_debts(wealth_rule):
    assets = [
        Asset.of("Budapest office", "2500000000", "valuation"),
        Asset.of("London house", "3000000000", "valuation", location="GB"),
    ]
    debts = [
        Debt.of("Office loan", "500000000", secured_on="Budapest office"),
        Debt.of("UK mortgage", "1000000000", secured_on="London house"),
    ]
    result = compute(wealth_rule, assets, debts, resident=False)
    # 2,500m - 500m = 2,000m; base 1,000m; tax 10m
    assert result.net_wealth == D("2000000000")
    assert result.tax.tax == D("10000000")
    assert sum(1 for line in result.lines if not line.included) == 2


def test_debts_larger_than_assets_give_zero(wealth_rule):
    result = compute(wealth_rule, [Asset.of("Flat", "100", "price")], [Debt.of("Loan", "500")])
    assert result.net_wealth == 0 and result.tax.tax == 0


def test_spouses_each_get_their_own_threshold(wealth_rule):
    # Couple with 3bn split equally: each 1.5bn, each pays 5m, together 10m.
    # Assessed as one 3bn estate it would be 20m.
    half = compute(wealth_rule, [Asset.of("Shared house", "3000000000", "price", ownership_share="0.5")])
    assert half.tax.tax * 2 == D("10000000")


def test_duplicate_asset_names_rejected(wealth_rule):
    with pytest.raises(ValueError, match="duplicate"):
        compute(wealth_rule, [Asset.of("A", "1", "x"), Asset.of("A", "2", "x")])


def test_wrong_rule_rejected(rules):
    with pytest.raises(ValueError):
        compute(rules.find("HU", "income", 2026, "individual"), [])


def test_unenacted_rule_must_explain_itself():
    raw = {
        "id": "x", "status": "draft", "jurisdiction": "ZZ", "tax_type": "wealth", "tax_year": 2026,
        "filing_status": "individual", "effective_from": "2026-01-01", "effective_to": "2026-12-31",
        "brackets": [{"up_to": None, "rate": "0.01"}],
        "source": {"citation": "c", "url": "u", "retrieved": "2026-01-01"},
    }
    with pytest.raises(RuleError, match="notes"):
        parse_rule(raw)
    with pytest.raises(RuleError, match="status"):
        parse_rule({**raw, "status": "rumoured", "notes": ["n"]})

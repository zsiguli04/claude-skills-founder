from decimal import Decimal
from fractions import Fraction
import statistics

import pytest

from finengine.valuation import (
    ExitMultiple,
    GordonGrowth,
    cost_of_equity,
    dcf,
    diluted_shares,
    equity_value,
    grid,
    implied_values,
    relever_beta,
    summarize_multiples,
    unlever_beta,
    unlevered_fcf,
    wacc,
)

D = Decimal


def close(a: Decimal, b, places: int = 18) -> bool:
    return abs(a - Decimal(b)) < Decimal(10) ** -places


def test_capm():
    # 4% + 1.2 x 5% + 1% = 11%
    assert cost_of_equity("0.04", "1.2", "0.05", "0.01") == D("0.110")


def test_beta_round_trip():
    # Hand: 1.0 x (1 + 0.75 x 0.5) = 1.375
    assert relever_beta("1.0", "0.5", "0.25") == D("1.375")
    assert unlever_beta("1.375", "0.5", "0.25") == D("1")


def test_wacc_hand_calculation():
    # E 600, D 400: 0.6 x 10% + 0.4 x 6% x (1 - 25%) = 6% + 1.8% = 7.8%
    assert wacc(600, 400, "0.10", "0.06", "0.25") == D("0.078")


def test_wacc_rejects_zero_capital():
    with pytest.raises(ValueError):
        wacc(0, 0, "0.1", "0.05", "0.2")


def test_unlevered_fcf():
    # 200 x 0.75 + 30 - 50 - 10 = 120
    assert unlevered_fcf(200, "0.25", 30, 50, 10) == D("120")


def test_dcf_gordon_matches_independent_fraction_calculation():
    flows = [100, 110, 121]
    r, g = Fraction(1, 10), Fraction(2, 100)
    pv = sum(Fraction(cf) / (1 + r) ** (i + 1) for i, cf in enumerate(flows))
    tv = Fraction(121) * (1 + g) / (r - g)
    expected_ev = pv + tv / (1 + r) ** 3

    result = dcf(flows, "0.10", GordonGrowth("0.02"))
    assert close(result.terminal_value, D(tv.numerator) / D(tv.denominator))
    assert close(result.enterprise_value, D(expected_ev.numerator) / D(expected_ev.denominator))
    assert result.sum_pv_cash_flows + result.pv_terminal_value == result.enterprise_value


def test_dcf_mid_year_discounts_cash_flows_half_a_year_earlier():
    end = dcf([100], "0.10", ExitMultiple(0, 0))
    mid = dcf([100], "0.10", ExitMultiple(0, 0), mid_year=True)
    assert close(mid.pv_cash_flows[0] / end.pv_cash_flows[0], D("1.1").sqrt())


def test_dcf_exit_multiple():
    result = dcf([50], "0.25", ExitMultiple(8, 100))
    # TV 800, discounted one year at 25%: 640. Cash flow 50 / 1.25 = 40.
    assert result.terminal_value == D("800")
    assert close(result.enterprise_value, 680)


@pytest.mark.parametrize("g", ["0.10", "0.12"])
def test_gordon_growth_must_be_below_discount_rate(g):
    with pytest.raises(ValueError):
        dcf([100], "0.10", GordonGrowth(g))


def test_terminal_share_warning():
    result = dcf([10, 10], "0.08", GordonGrowth("0.03"))
    assert result.terminal_share > D("0.75")
    assert any("terminal value" in w for w in result.warnings)


def test_multiples_summary_matches_statistics_module():
    peers = {"A": "8.0", "B": "10.5", "C": "12.0", "D": "9.1", "E": "15.2", "F": "-3"}
    summary = summarize_multiples(peers)
    positives = [D(v) for v in peers.values() if D(v) > 0]
    q1, q2, q3 = statistics.quantiles(positives, n=4, method="inclusive")
    assert summary.count == 5
    assert (summary.p25, summary.median, summary.p75) == (q1, q2, q3)
    assert implied_values(10, summary)["mid"] == 10 * q2


def test_equity_bridge():
    # 1000 - 200 - 50 - 30 + 80 = 800
    assert equity_value(1000, 200, 50, 30, 80) == D("800")


def test_treasury_stock_method():
    # In the money: 100 options at strike 5, price 10 -> 100 - 100 x 5 / 10 = 50 new shares.
    # Out of the money (strike 12) adds nothing.
    assert diluted_shares(1000, 10, [(100, 5), (100, 12)]) == D("1050")


def test_sensitivity_grid_marks_invalid_cells():
    table = grid(
        lambda r, g: dcf([100], r, GordonGrowth(g)).enterprise_value,
        [D("0.08"), D("0.10")],
        [D("0.02"), D("0.09")],
    )
    assert table[0][1] is None  # g 9% > r 8%
    assert table[1][1] is not None
    assert table[0][0] > table[1][0]  # higher discount rate, lower value

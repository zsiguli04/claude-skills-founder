from decimal import Decimal

import pytest

from finengine.wealth import PlanInputs, project, simulate, to_real

D = Decimal


def test_zero_return_balance_is_sum_of_contributions():
    plan = PlanInputs.of(start_balance=1000, years=5, expected_return=0, inflation=0, annual_contribution=100, contribution_years=5)
    assert project(plan).ending_balance == D("1500")


def test_one_year_order_of_operations():
    # Hand: (1000 + 100) x 1.10 = 1210; fee 1% = 12.10 -> 1197.90; withdraw 50 x 1.02 = 51 -> 1146.90
    plan = PlanInputs.of(
        start_balance=1000, years=1, expected_return="0.10", inflation="0.02", fee_rate="0.01",
        annual_contribution=100, contribution_years=1, annual_withdrawal_real=50,
    )
    row = project(plan).rows[0]
    assert (row.growth, row.fee, row.withdrawal, row.end) == (D("110.0"), D("12.100"), D("51.00"), D("1146.900"))


def test_fees_compound_over_time():
    plan = PlanInputs.of(start_balance=100000, years=30, expected_return="0.06", inflation=0, fee_rate="0.01")
    no_fee = PlanInputs.of(start_balance=100000, years=30, expected_return="0.06", inflation=0)
    gap = project(no_fee).ending_balance - project(plan).ending_balance
    assert gap > project(plan).total_fees  # lost growth on fees costs more than the fees themselves


def test_depletion_is_reported():
    plan = PlanInputs.of(start_balance=100, years=5, expected_return=0, inflation=0, annual_withdrawal_real=40)
    result = project(plan)
    assert result.depleted_year == 3
    assert result.rows[2].shortfall == D("20")
    assert result.ending_balance == 0


def test_real_conversion_divides_by_compounded_inflation():
    assert to_real(D("121"), D("0.10"), 2) == D("100")


def test_invalid_inputs():
    with pytest.raises(ValueError):
        PlanInputs.of(start_balance=-1, years=1, expected_return=0, inflation=0)
    with pytest.raises(TypeError):
        PlanInputs.of(start_balance=1.0, years=1, expected_return=0, inflation=0)


PLAN = PlanInputs.of(
    start_balance=500000, years=30, expected_return="0.05", inflation="0.02", fee_rate="0.005",
    annual_withdrawal_real=20000,
)


def test_monte_carlo_is_reproducible_with_a_seed():
    a = simulate(PLAN, "0.12", paths=300, seed=7)
    b = simulate(PLAN, "0.12", paths=300, seed=7)
    assert a == b


def test_zero_volatility_matches_deterministic_projection():
    sim = simulate(PLAN, 0, paths=5, seed=1)
    expected = project(PLAN).ending_balance
    assert all(abs(v - expected) < D("0.0001") for v in sim.ending_balance.values())


def test_more_volatility_widens_the_range_and_lowers_success():
    calm = simulate(PLAN, "0.05", paths=2000, seed=3)
    wild = simulate(PLAN, "0.20", paths=2000, seed=3)
    spread = lambda s: s.ending_balance[95] - s.ending_balance[5]
    assert spread(wild) > spread(calm)
    assert wild.success_rate <= calm.success_rate
    assert calm.ending_balance[5] <= calm.ending_balance[50] <= calm.ending_balance[95]

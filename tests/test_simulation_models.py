import pytest
np = pytest.importorskip("numpy")
from typing import Optional, List

from src.simulation_models import (
    monte_carlo_normal,
    monte_carlo_bootstrap,
    backtest_rolling_windows,
    load_historical_annual_returns,
    load_historical_annual_series,
)


def test_historical_returns_load():
    hist = load_historical_annual_returns()
    assert hist.size >= 50


def test_monte_carlo_normal_output_shape():
    result = monte_carlo_normal(
        initial_wealth=100_000,
        monthly_contribution=1_000,
        years=20,
        mean_return=0.06,
        volatility=0.15,
        inflation_rate=0.02,
        annual_spending=30_000,
        safe_withdrawal_rate=0.04,
        num_simulations=500,
        seed=42,
    )
    assert result["paths"].shape == (500, 21)
    assert 0 <= result["success_rate_final"] <= 100


def test_bootstrap_output_shape():
    hist = load_historical_annual_returns()
    result = monte_carlo_bootstrap(
        initial_wealth=100_000,
        monthly_contribution=1_000,
        years=20,
        inflation_rate=0.02,
        annual_spending=30_000,
        safe_withdrawal_rate=0.04,
        historical_returns=hist,
        num_simulations=500,
        seed=42,
    )
    assert result["paths"].shape == (500, 21)
    assert 0 <= result["success_rate_final"] <= 100


def test_backtesting_rolling_windows():
    hist = load_historical_annual_returns()
    years = 20
    result = backtest_rolling_windows(
        initial_wealth=100_000,
        monthly_contribution=1_000,
        years=years,
        inflation_rate=0.02,
        annual_spending=30_000,
        safe_withdrawal_rate=0.04,
        historical_returns=hist,
    )
    expected_windows = hist.size - years + 1
    assert result["paths"].shape == (expected_windows, years + 1)
    assert result["windows_count"] == expected_windows


def _assert_simulation_invariants(result: dict) -> None:
    """Strong invariants that must hold even under stress inputs."""
    percentile_keys = [
        "percentile_5",
        "percentile_25",
        "percentile_50",
        "percentile_75",
        "percentile_95",
        "real_percentile_5",
        "real_percentile_25",
        "real_percentile_50",
        "real_percentile_75",
        "real_percentile_95",
    ]
    for key in percentile_keys:
        arr = np.asarray(result[key], dtype=float)
        assert np.isfinite(arr).all(), f"{key} contains NaN/inf"
        assert (arr >= 0).all(), f"{key} should not be negative"

    p5 = np.asarray(result["percentile_5"], dtype=float)
    p25 = np.asarray(result["percentile_25"], dtype=float)
    p50 = np.asarray(result["percentile_50"], dtype=float)
    p75 = np.asarray(result["percentile_75"], dtype=float)
    p95 = np.asarray(result["percentile_95"], dtype=float)
    assert np.all(p5 <= p25)
    assert np.all(p25 <= p50)
    assert np.all(p50 <= p75)
    assert np.all(p75 <= p95)

    yearly_success = np.asarray(result["yearly_success"], dtype=float)
    assert np.isfinite(yearly_success).all()
    assert ((yearly_success >= 0) & (yearly_success <= 100)).all()
    assert 0 <= float(result["success_rate_final"]) <= 100

    assert "path_return_percentiles" in result
    pr = result["path_return_percentiles"]
    assert pr["P5"] <= pr["P25"] <= pr["P50"] <= pr["P75"] <= pr["P95"]


@pytest.mark.stress
def test_monte_carlo_normal_extreme_inputs_invariants():
    scenarios = [
        dict(
            initial_wealth=0,
            monthly_contribution=12_000,
            years=45,
            mean_return=0.09,
            volatility=0.35,
            inflation_rate=0.06,
            annual_spending=40_000,
            safe_withdrawal_rate=0.025,
            contribution_growth_rate=0.03,
            num_simulations=1200,
            seed=123,
        ),
        dict(
            initial_wealth=2_500_000,
            monthly_contribution=0,
            years=50,
            mean_return=0.03,
            volatility=0.20,
            inflation_rate=-0.01,
            annual_spending=120_000,
            safe_withdrawal_rate=0.035,
            contribution_growth_rate=0.00,
            num_simulations=1200,
            seed=777,
        ),
    ]
    for cfg in scenarios:
        result = monte_carlo_normal(**cfg)
        _assert_simulation_invariants(result)
        assert result["paths"].shape[1] == cfg["years"] + 1


@pytest.mark.stress
def test_bootstrap_and_backtest_stress_invariants():
    years, hist_returns, months = load_historical_annual_series("sp500_us_total_return")

    bootstrap = monte_carlo_bootstrap(
        initial_wealth=300_000,
        monthly_contribution=2_500,
        years=35,
        inflation_rate=0.03,
        annual_spending=50_000,
        safe_withdrawal_rate=0.03,
        historical_returns=hist_returns,
        contribution_growth_rate=0.02,
        num_simulations=1400,
        seed=99,
    )
    _assert_simulation_invariants(bootstrap)

    backtest = backtest_rolling_windows(
        initial_wealth=300_000,
        monthly_contribution=2_500,
        years=35,
        inflation_rate=0.03,
        annual_spending=50_000,
        safe_withdrawal_rate=0.03,
        historical_returns=hist_returns,
        historical_years=years,
        historical_months_observed=months,
        contribution_growth_rate=0.02,
    )
    _assert_simulation_invariants(backtest)
    assert "backtest_diagnostics" in backtest
    diagnostics = backtest["backtest_diagnostics"]
    assert diagnostics["windows_count"] == backtest["windows_count"]
    assert diagnostics["data_start_year"] <= diagnostics["data_end_year"]


@pytest.mark.stress
def test_randomized_simulation_stress_no_numerical_breaks():
    rng = np.random.default_rng(20260214)
    hist = load_historical_annual_returns()
    for _ in range(40):
        years = int(rng.integers(5, 46))
        model = rng.choice(["normal", "bootstrap"])
        common = dict(
            initial_wealth=float(rng.uniform(0, 3_000_000)),
            monthly_contribution=float(rng.uniform(0, 20_000)),
            years=years,
            inflation_rate=float(rng.uniform(-0.02, 0.10)),
            annual_spending=float(rng.uniform(5_000, 150_000)),
            safe_withdrawal_rate=float(rng.uniform(0.02, 0.06)),
            contribution_growth_rate=float(rng.uniform(0.0, 0.05)),
        )
        if model == "normal":
            result = monte_carlo_normal(
                mean_return=float(rng.uniform(-0.05, 0.15)),
                volatility=float(rng.uniform(0.05, 0.45)),
                num_simulations=700,
                seed=int(rng.integers(1, 1_000_000)),
                **common,
            )
        else:
            result = monte_carlo_bootstrap(
                historical_returns=hist,
                num_simulations=700,
                seed=int(rng.integers(1, 1_000_000)),
                **common,
            )
        _assert_simulation_invariants(result)


def test_rental_drop_applies_from_sale_year_onward():
    result = monte_carlo_normal(
        initial_wealth=0.0,
        monthly_contribution=1_000.0,
        years=5,
        mean_return=0.0,
        volatility=0.0,
        inflation_rate=0.0,
        annual_spending=10_000.0,
        safe_withdrawal_rate=0.04,
        num_simulations=1,
        seed=1,
        rental_drop_enabled=True,
        rental_drop_year=3,
        rental_drop_annual_amount=1_200.0,
    )
    path = result["paths"][0]
    # Annual contribution is 12,000 until year 2, then 10,800 from year 3 onward.
    assert path[1] == pytest.approx(12_000.0)
    assert path[2] == pytest.approx(24_000.0)
    assert path[3] == pytest.approx(34_800.0)
    assert path[4] == pytest.approx(45_600.0)
    assert path[5] == pytest.approx(56_400.0)


@pytest.mark.stress
def test_sensitivity_matrix_monotonic_dominance_invariants():
    """Better return + lower inflation should not worsen years-to-FIRE in matrix cells."""
    rng = np.random.default_rng(20260221)
    return_offsets = np.array([-0.02, -0.01, 0.0, 0.01, 0.02], dtype=float)
    inflation_offsets = np.array([0.02, 0.01, 0.0, -0.01, -0.02], dtype=float)

    def years_to_fire(result: dict) -> Optional[int]:
        target = float(result["fire_target_real"])
        p50 = np.asarray(result["real_percentile_50"], dtype=float)
        hits = np.where(p50 >= target)[0]
        return int(hits[0]) if hits.size else None

    total_pairs = 0
    contradictions = 0

    for _ in range(20):
        base = dict(
            initial_wealth=float(rng.uniform(0.0, 1_500_000.0)),
            monthly_contribution=float(rng.uniform(0.0, 12_000.0)),
            years=int(rng.integers(6, 31)),
            mean_return=float(rng.uniform(0.00, 0.11)),
            volatility=float(rng.uniform(0.08, 0.35)),
            inflation_rate=float(rng.uniform(0.00, 0.06)),
            annual_spending=float(rng.uniform(15_000.0, 90_000.0)),
            safe_withdrawal_rate=float(rng.uniform(0.025, 0.05)),
            contribution_growth_rate=float(rng.uniform(0.0, 0.04)),
            num_simulations=1000,
            seed=42,
        )

        matrix: List[List[Optional[int]]] = [[None for _ in range(5)] for _ in range(5)]
        for i, ioff in enumerate(inflation_offsets):
            for j, roff in enumerate(return_offsets):
                result = monte_carlo_normal(
                    initial_wealth=base["initial_wealth"],
                    monthly_contribution=base["monthly_contribution"],
                    years=base["years"],
                    mean_return=base["mean_return"] + float(roff),
                    volatility=base["volatility"],
                    inflation_rate=max(-0.03, base["inflation_rate"] + float(ioff)),
                    annual_spending=base["annual_spending"],
                    safe_withdrawal_rate=base["safe_withdrawal_rate"],
                    contribution_growth_rate=base["contribution_growth_rate"],
                    num_simulations=base["num_simulations"],
                    seed=base["seed"],
                )
                matrix[i][j] = years_to_fire(result)

        # Dominance: cell (i2, j2) dominates (i1, j1) if it has >= return and <= inflation.
        # Here i grows as inflation decreases because offsets go +2pp ... -2pp.
        for i1 in range(5):
            for j1 in range(5):
                y1 = matrix[i1][j1]
                for i2 in range(5):
                    for j2 in range(5):
                        better_or_equal = (j2 >= j1) and (i2 >= i1)
                        strictly_better = (j2 > j1) or (i2 > i1)
                        if not (better_or_equal and strictly_better):
                            continue
                        y2 = matrix[i2][j2]
                        total_pairs += 1
                        if y1 is not None and y2 is None:
                            contradictions += 1
                        elif y1 is not None and y2 is not None and y2 > y1:
                            contradictions += 1

    assert total_pairs > 0
    contradiction_ratio = contradictions / total_pairs
    # Monte Carlo noise can introduce tiny irregularities, but should be very rare.
    assert contradiction_ratio <= 0.005

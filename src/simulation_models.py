"""Simulation models shared by CLI and web.

Supports:
- Monte Carlo with normal returns
- Monte Carlo with bootstrap from historical annual returns
- Historical rolling-window backtesting
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.tax_engine import calculate_savings_tax, calculate_wealth_taxes


MARKET_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "market_data" / "strategy_returns_1871.csv"

STRATEGY_COLUMN_MAP = {
    "sp500_us_total_return": "sp500_us_total_return",
    "portfolio_100_0_synthetic": "portfolio_100_0_synthetic",
    "portfolio_70_30_synthetic": "portfolio_70_30_synthetic",
    "portfolio_50_50_synthetic": "portfolio_50_50_synthetic",
    "portfolio_30_70_synthetic": "portfolio_30_70_synthetic",
    "portfolio_15_85_synthetic": "portfolio_15_85_synthetic",
    "balanced_60_40_synthetic": "balanced_60_40_synthetic",
    "conservative_40_60_synthetic": "conservative_40_60_synthetic",
}


def load_historical_annual_returns(strategy: str = "sp500_us_total_return") -> np.ndarray:
    """Load bundled historical annual returns as decimal values.

    Parameters
    ----------
    strategy:
        One of:
        - sp500_us_total_return
        - portfolio_100_0_synthetic
        - portfolio_70_30_synthetic
        - portfolio_50_50_synthetic
        - portfolio_30_70_synthetic
        - portfolio_15_85_synthetic
        - balanced_60_40_synthetic
        - conservative_40_60_synthetic
    """
    df = pd.read_csv(MARKET_DATA_PATH)
    column = STRATEGY_COLUMN_MAP.get(strategy, "sp500_us_total_return")
    if column not in df.columns:
        raise ValueError(f"Missing {column} column in {MARKET_DATA_PATH}")
    returns = df[column].astype(float).to_numpy()
    if returns.size < 20:
        raise ValueError("Historical return series too short for robust analysis.")
    return returns


def load_historical_annual_series(
    strategy: str = "sp500_us_total_return",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load yearly series with calendar years and months_observed quality signal.

    Returns
    -------
    years: np.ndarray[int]
    returns: np.ndarray[float]
    months_observed: np.ndarray[int]
    """
    df = pd.read_csv(MARKET_DATA_PATH)
    column = STRATEGY_COLUMN_MAP.get(strategy, "sp500_us_total_return")
    if column not in df.columns:
        raise ValueError(f"Missing {column} column in {MARKET_DATA_PATH}")
    if "year" not in df.columns:
        raise ValueError(f"Missing year column in {MARKET_DATA_PATH}")

    years = df["year"].astype(int).to_numpy()
    returns = df[column].astype(float).to_numpy()
    months_observed = (
        df["months_observed"].astype(int).to_numpy()
        if "months_observed" in df.columns
        else np.full_like(years, 12)
    )
    if returns.size < 20:
        raise ValueError("Historical return series too short for robust analysis.")
    return years, returns, months_observed


def _simulate_from_return_matrix(
    initial_wealth: float,
    annual_contribution: float,
    contribution_growth_rate: float,
    inflation_rate: float,
    annual_spending: float,
    safe_withdrawal_rate: float,
    annual_returns_matrix: np.ndarray,
    tax_pack: Optional[Dict] = None,
    region: Optional[str] = None,
) -> Dict:
    """Simulate all paths from a returns matrix with shape (n_sims, years)."""
    if safe_withdrawal_rate <= 0:
        raise ValueError("safe_withdrawal_rate must be > 0.")

    n_sims, years = annual_returns_matrix.shape
    annual_paths = np.zeros((n_sims, years + 1))
    annual_paths[:, 0] = initial_wealth

    for sim in range(n_sims):
        portfolio = initial_wealth
        for year in range(1, years + 1):
            annual_return = annual_returns_matrix[sim, year - 1]
            annual_contribution_year = annual_contribution * ((1 + contribution_growth_rate) ** (year - 1))
            gross_growth = portfolio * annual_return
            portfolio_pre_tax = portfolio + gross_growth + annual_contribution_year

            if tax_pack and region:
                savings_base = max(0.0, gross_growth)
                savings_tax = calculate_savings_tax(savings_base, tax_pack, region)
                wealth_taxes = calculate_wealth_taxes(portfolio_pre_tax, tax_pack, region)
                portfolio = portfolio_pre_tax - savings_tax - wealth_taxes["total_wealth_tax"]
            else:
                portfolio = portfolio_pre_tax

            annual_paths[sim, year] = max(0.0, portfolio)

    inflation_factors = np.array([(1 + inflation_rate) ** y for y in range(years + 1)])
    real_paths = annual_paths / inflation_factors

    fire_target_real = annual_spending / safe_withdrawal_rate if annual_spending > 0 else 0.0
    final_values = annual_paths[:, -1]
    final_values_real = real_paths[:, -1]
    percent_success = (final_values_real >= fire_target_real).sum() / n_sims * 100

    yearly_success = np.array(
        [(real_paths[:, y] >= fire_target_real).sum() / n_sims * 100 for y in range(years + 1)]
    )

    # Path-level geometric annual returns from market return matrix (independent of contributions).
    safe_returns = np.clip(annual_returns_matrix.astype(float), -0.99, None)
    with np.errstate(invalid="ignore"):
        path_geom_returns = np.exp(np.mean(np.log1p(safe_returns), axis=1)) - 1.0

    return {
        "paths": annual_paths,
        "real_paths": real_paths,
        "percentile_5": np.percentile(annual_paths, 5, axis=0),
        "percentile_25": np.percentile(annual_paths, 25, axis=0),
        "percentile_50": np.percentile(annual_paths, 50, axis=0),
        "percentile_75": np.percentile(annual_paths, 75, axis=0),
        "percentile_95": np.percentile(annual_paths, 95, axis=0),
        "real_percentile_5": np.percentile(real_paths, 5, axis=0),
        "real_percentile_25": np.percentile(real_paths, 25, axis=0),
        "real_percentile_50": np.percentile(real_paths, 50, axis=0),
        "real_percentile_75": np.percentile(real_paths, 75, axis=0),
        "real_percentile_95": np.percentile(real_paths, 95, axis=0),
        "success_rate_final": percent_success,
        "yearly_success": yearly_success,
        "final_values": final_values,
        "final_values_real": final_values_real,
        "final_median": np.median(final_values),
        "final_median_real": np.median(final_values_real),
        "final_percentile_95": np.percentile(final_values, 95),
        "fire_target_real": fire_target_real,
        "fire_target": fire_target_real,
        "n_sims": n_sims,
        "years": years,
        "path_geom_returns": path_geom_returns,
        "path_return_percentiles": {
            "P5": float(np.percentile(path_geom_returns, 5)),
            "P25": float(np.percentile(path_geom_returns, 25)),
            "P50": float(np.percentile(path_geom_returns, 50)),
            "P75": float(np.percentile(path_geom_returns, 75)),
            "P95": float(np.percentile(path_geom_returns, 95)),
        },
    }


def monte_carlo_normal(
    initial_wealth: float,
    monthly_contribution: float,
    years: int,
    mean_return: float,
    volatility: float,
    inflation_rate: float,
    annual_spending: float,
    safe_withdrawal_rate: float,
    contribution_growth_rate: float = 0.0,
    num_simulations: int = 10_000,
    seed: int = 42,
    tax_pack: Optional[Dict] = None,
    region: Optional[str] = None,
) -> Dict:
    """Monte Carlo simulation with normal annual returns."""
    rng = np.random.default_rng(seed)
    annual_returns = rng.normal(mean_return, volatility, size=(num_simulations, years))
    return _simulate_from_return_matrix(
        initial_wealth=initial_wealth,
        annual_contribution=monthly_contribution * 12,
        contribution_growth_rate=contribution_growth_rate,
        inflation_rate=inflation_rate,
        annual_spending=annual_spending,
        safe_withdrawal_rate=safe_withdrawal_rate,
        annual_returns_matrix=annual_returns,
        tax_pack=tax_pack,
        region=region,
    )


def monte_carlo_bootstrap(
    initial_wealth: float,
    monthly_contribution: float,
    years: int,
    inflation_rate: float,
    annual_spending: float,
    safe_withdrawal_rate: float,
    historical_returns: np.ndarray,
    contribution_growth_rate: float = 0.0,
    num_simulations: int = 10_000,
    seed: int = 42,
    tax_pack: Optional[Dict] = None,
    region: Optional[str] = None,
) -> Dict:
    """Monte Carlo simulation by sampling historical annual returns with replacement."""
    rng = np.random.default_rng(seed)
    sampled = rng.choice(historical_returns, size=(num_simulations, years), replace=True)
    return _simulate_from_return_matrix(
        initial_wealth=initial_wealth,
        annual_contribution=monthly_contribution * 12,
        contribution_growth_rate=contribution_growth_rate,
        inflation_rate=inflation_rate,
        annual_spending=annual_spending,
        safe_withdrawal_rate=safe_withdrawal_rate,
        annual_returns_matrix=sampled,
        tax_pack=tax_pack,
        region=region,
    )


def backtest_rolling_windows(
    initial_wealth: float,
    monthly_contribution: float,
    years: int,
    inflation_rate: float,
    annual_spending: float,
    safe_withdrawal_rate: float,
    historical_returns: np.ndarray,
    historical_years: Optional[np.ndarray] = None,
    historical_months_observed: Optional[np.ndarray] = None,
    contribution_growth_rate: float = 0.0,
    tax_pack: Optional[Dict] = None,
    region: Optional[str] = None,
) -> Dict:
    """Run historical rolling-window backtests for a given horizon."""
    if years <= 0:
        raise ValueError("years must be > 0")
    if historical_returns.size < years + 1:
        raise ValueError("Not enough historical data for the selected horizon.")

    windows = []
    for start in range(0, historical_returns.size - years + 1):
        windows.append(historical_returns[start : start + years])
    return_matrix = np.vstack(windows)

    result = _simulate_from_return_matrix(
        initial_wealth=initial_wealth,
        annual_contribution=monthly_contribution * 12,
        contribution_growth_rate=contribution_growth_rate,
        inflation_rate=inflation_rate,
        annual_spending=annual_spending,
        safe_withdrawal_rate=safe_withdrawal_rate,
        annual_returns_matrix=return_matrix,
        tax_pack=tax_pack,
        region=region,
    )
    result["windows_count"] = return_matrix.shape[0]

    final_real = result["real_paths"][:, -1]
    final_nominal = result["paths"][:, -1]
    worst_idx = int(np.argmin(final_real))
    best_idx = int(np.argmax(final_real))

    worst_start_year = None
    worst_end_year = None
    best_start_year = None
    best_end_year = None
    data_start_year = None
    data_end_year = None
    min_months_observed = None
    avg_months_observed = None

    if historical_years is not None and historical_years.size >= years:
        data_start_year = int(historical_years[0])
        data_end_year = int(historical_years[-1])
        worst_start_year = int(historical_years[worst_idx])
        worst_end_year = int(historical_years[worst_idx + years - 1])
        best_start_year = int(historical_years[best_idx])
        best_end_year = int(historical_years[best_idx + years - 1])

    if historical_months_observed is not None and historical_months_observed.size >= years:
        min_months_observed = int(np.min(historical_months_observed))
        avg_months_observed = float(np.mean(historical_months_observed))

    result["backtest_diagnostics"] = {
        "windows_count": int(return_matrix.shape[0]),
        "data_start_year": data_start_year,
        "data_end_year": data_end_year,
        "worst_window_start_year": worst_start_year,
        "worst_window_end_year": worst_end_year,
        "best_window_start_year": best_start_year,
        "best_window_end_year": best_end_year,
        "worst_final_real": float(final_real[worst_idx]),
        "best_final_real": float(final_real[best_idx]),
        "worst_final_nominal": float(final_nominal[worst_idx]),
        "best_final_nominal": float(final_nominal[best_idx]),
        "worst_idx": worst_idx,
        "best_idx": best_idx,
        "min_months_observed": min_months_observed,
        "avg_months_observed": avg_months_observed,
    }
    result["worst_path_nominal"] = result["paths"][worst_idx].copy()
    result["best_path_nominal"] = result["paths"][best_idx].copy()
    result["worst_path_real"] = result["real_paths"][worst_idx].copy()
    result["best_path_real"] = result["real_paths"][best_idx].copy()

    return result

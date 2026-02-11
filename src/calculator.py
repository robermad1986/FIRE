"""FIRE calculator adapted for EUR/UCITS investors.

This module provides core financial projection functions:
- target_fire: compute required portfolio to retire based on desired spending and safe withdrawal rate.
- coast_fire: determine if current savings will reach target by a given horizon without additional contributions.
- project_portfolio: simulate portfolio growth over time with contributions, returns, inflation, and tax considerations.
"""

from typing import Dict, List, Optional
import math

# ----------------------------------------------------------------------
# Core formulas (deterministic)
# ----------------------------------------------------------------------
def target_fire(
    annual_spending: float,
    safe_withdrawal_rate: float = 0.04,
) -> float:
    """
    Compute the portfolio value needed to retire given an annual spending target
    and a safe withdrawal rate (SWR).

    Parameters
    ----------
    annual_spending: float
        Desired annual spending in EUR (post‑tax).
    safe_withdrawal_rate: float, optional
        Withdrawal rate (default 4 % = 0.04).

    Returns
    -------
    float
        Required portfolio value (EUR) to sustain the spending indefinitely.
    """
    if safe_withdrawal_rate <= 0:
        raise ValueError("safe_withdrawal_rate must be positive")
    return annual_spending / safe_withdrawal_rate


def coast_fire_condition(
    current_savings: float,
    annual_contribution: float,
    years_to_target: int,
    expected_return: float,
    target_portfolio: float,
) -> bool:
    """
    Determine whether the current savings path will reach ``target_portfolio``
    within ``years_to_target`` years, assuming a constant ``expected_return``
    and ``annual_contribution``.

    The future value is computed as:
        FV = current_savings * (1+r)^n + annual_contribution *
             (((1+r)^n - 1) / r)

    Parameters
    ----------
    current_savings: float
        Portfolio value today (EUR).
    annual_contribution: float
        Additional savings added each year (EUR). Can be zero.
    years_to_target: int
        Number of years until the desired retirement horizon.
    expected_return: float
        Expected annual return (decimal, e.g. 0.07 for 7 %).
    target_portfolio: float
        The portfolio value needed to retire (e.g. from ``target_fire``).

    Returns
    -------
    bool
        ``True`` if the projected portfolio meets or exceeds ``target_portfolio``,
        ``False`` otherwise.
    """
    if years_to_target < 0:
        raise ValueError("years_to_target must be non‑negative")
    if expected_return == 0:
        fv = current_savings + annual_contribution * years_to_target
    else:
        growth = math.pow(1 + expected_return, years_to_target)
        fv = current_savings * growth + annual_contribution * (growth - 1) / expected_return
    return fv >= target_portfolio


# ----------------------------------------------------------------------
# Portfolio projection with tax & inflation adjustments (simplified)
# ----------------------------------------------------------------------
def project_portfolio(
    current_savings: float,
    annual_contribution: float,
    years: int,
    expected_return: float,
    inflation_rate: float,
    tax_rate_on_gains: float = 0.15,
    tax_rate_on_dividends: float = 0.30,
    tax_rate_on_interest: float = 0.45,
    fund_fees: float = 0.001,
    withholding_tax: float = 0.15,
    social_security_contributions: float = 0.0,
    account_breakdown: Optional[Dict[str, float]] = None,
) -> Dict[int, Dict[str, float]]:
    """
    Project the portfolio year‑by‑year, applying taxes on gains, dividends,
    and interest, fund fees, and UCITS‑specific withholding and social
    contributions, then adjusting for inflation.

    Parameters
    ----------
    current_savings: float
        Portfolio value today (EUR).
    annual_contribution: float
        Additional savings added each year (EUR). Can be zero.
    years: int
        Number of years to project.
    expected_return: float
        Expected annual return (decimal, e.g. 0.06 for 6 %).
    inflation_rate: float
        Expected annual inflation (decimal).
    tax_rate_on_gains: float, optional
        Tax rate applied to realized capital gains (default 15 %).
    tax_rate_on_dividends: float, optional
        Tax rate applied to dividend income (default 30 %).
    tax_rate_on_interest: float, optional
        Tax rate applied to interest income (default 45 %).
    fund_fees: float, optional
        Annual fund management fee expressed as a decimal (e.g. 0.001 for 0.1 %).
    withholding_tax: float, optional
        Additional withholding tax on dividends (default 15 %).
    social_security_contributions: float, optional
        Portion of gains allocated to social security contributions (default 0 %).
    account_breakdown: dict, optional
        Mapping of account types to proportion of portfolio (e.g.
        ``{\"taxable\": 0.3, \"tax_deferred\": 0.5, \"tax_free\": 0.2}``).
        If provided, tax calculations are applied proportionally across
        the specified accounts.

    Returns
    -------
    dict
        Year‑by‑year financial metrics including nominal and real portfolio
        values, tax paid, fee deductions, and account breakdown details.
    """
    if years <= 0:
        raise ValueError("years must be a positive integer")

    # Determine returns and fees
    portfolio = current_savings
    results: Dict[int, Dict[str, float]] = {}

    # Assumed asset allocation for return decomposition
    equity_share = 0.60
    bond_share = 0.30
    cash_share = 0.10

    # Fraction of equity returns that are dividends (rest considered capital gains)
    dividend_yield_fraction = 0.15

    # Normalize account breakdown into proportions. Supports both:
    # - proportions summing to ~1.0
    # - absolute amounts summing to portfolio
    normalized_breakdown: Dict[str, float]
    if account_breakdown:
        positive_items = {
            key: max(0.0, float(value))
            for key, value in account_breakdown.items()
            if value is not None
        }
        total_breakdown = sum(positive_items.values())
        if total_breakdown > 0:
            normalized_breakdown = {
                key: value / total_breakdown for key, value in positive_items.items()
            }
        else:
            normalized_breakdown = {"taxable": 1.0}
    else:
        normalized_breakdown = {"taxable": 1.0}

    for y in range(1, years + 1):
        # Gross returns by asset class (before fees and taxes)
        equity_return = portfolio * equity_share * expected_return
        bond_return = portfolio * bond_share * expected_return
        cash_return = portfolio * cash_share * expected_return
        gross_return = equity_return + bond_return + cash_return

        # Fees charged on assets (approximate)
        fee_paid = portfolio * fund_fees

        # Income decomposition
        dividend_amount = equity_return * dividend_yield_fraction
        capital_gain_amount = gross_return - dividend_amount

        # Taxes by account type:
        # - taxable: pays annual taxes
        # - tax_deferred / tax_free: no annual tax drag in this accumulation model
        taxable_share = max(0.0, normalized_breakdown.get("taxable", 0.0))
        deferred_share = max(0.0, normalized_breakdown.get("tax_deferred", 0.0))
        tax_free_share = max(0.0, normalized_breakdown.get("tax_free", 0.0))
        covered_share = taxable_share + deferred_share + tax_free_share
        if covered_share <= 0:
            taxable_share = 1.0
            covered_share = 1.0

        # Treat any unknown/missing share as taxable by default (conservative).
        residual_taxable_share = max(0.0, 1.0 - covered_share)
        effective_taxable_share = min(1.0, taxable_share + residual_taxable_share)

        effective_div_tax_rate = min(1.0, max(0.0, tax_rate_on_dividends + withholding_tax))

        tax_on_divs = dividend_amount * effective_taxable_share * effective_div_tax_rate
        tax_on_interest = bond_return * effective_taxable_share * max(0.0, tax_rate_on_interest)
        # Capital gains taxation: apply if taxes are intended to be annual (by default callers may pass 0)
        tax_on_gains = (
            capital_gain_amount * effective_taxable_share * max(0.0, tax_rate_on_gains)
        )

        # Social security contributions applied to taxable gross-return share.
        social_security_tax = (
            gross_return * effective_taxable_share * max(0.0, social_security_contributions)
        )

        total_tax = tax_on_divs + tax_on_interest + tax_on_gains + social_security_tax

        # Net growth after fees and taxes
        net_growth = gross_return - fee_paid - total_tax

        # Add new contributions (assumed after‑tax cash)
        portfolio = portfolio + net_growth + annual_contribution

        # Inflation‑adjusted spending power
        inflation_factor = math.pow(1 + inflation_rate, y)
        real_value = portfolio / inflation_factor

        results[y] = {
            "nominal_portfolio": portfolio,
            "real_portfolio": real_value,
            "tax_paid_year": total_tax,
            "fee_paid_year": fee_paid,
            "taxable_share_applied": effective_taxable_share,
        }

    return results


def calculate_gross_target(
    annual_spending: float,
    safe_withdrawal_rate: float = 0.04,
    tax_rate_on_gains: float = 0.15,
) -> float:
    """Calculate gross portfolio target accounting for taxes on capital gains."""
    # Effective SWR after taxes
    effective_swr = safe_withdrawal_rate * (1 - tax_rate_on_gains)
    if effective_swr <= 0:
        return float('inf')
    return annual_spending / effective_swr


def calculate_savings_rate(
    gross_income: float,
    annual_spending: float,
) -> float:
    """Calculate savings rate as a percentage of gross income."""
    if gross_income <= 0:
        return 0.0
    return (gross_income - annual_spending) / gross_income


def calculate_years_saved_per_percent(
    current_savings: float,
    current_savings_rate: float,
    annual_spending: float,
    expected_return: float,
    gross_income: float,
) -> float:
    """Estimate years saved for each additional 1% increase in savings rate."""
    if current_savings_rate >= 0.99:
        return 0.0
    
    additional_annual = gross_income * 0.01
    if expected_return <= 0:
        return 0.0
    
    return additional_annual / max(annual_spending * expected_return, 1)


def project_retirement(
    portfolio_at_retirement: float,
    annual_spending: float,
    years_in_retirement: int = 30,
    expected_return: float = 0.05,
    inflation_rate: float = 0.02,
    tax_rate_on_gains: float = 0.15,
) -> Dict[int, Dict[str, float]]:
    """Project portfolio during retirement (decumulation phase)."""
    portfolio = portfolio_at_retirement
    results: Dict[int, Dict[str, float]] = {}
    inflation_factor = 1.0
    
    for year in range(1, years_in_retirement + 1):
        inflation_adjusted_spending = annual_spending * inflation_factor
        growth = portfolio * expected_return
        tax_on_growth = growth * tax_rate_on_gains
        net_growth = growth - tax_on_growth
        portfolio = portfolio + net_growth - inflation_adjusted_spending
        inflation_factor *= (1 + inflation_rate)
        
        results[year] = {
            "portfolio_value": max(portfolio, 0),
            "annual_withdrawal": inflation_adjusted_spending,
            "portfolio_depleted": portfolio <= 0,
            "years_remaining": max(0, portfolio / inflation_adjusted_spending) if inflation_adjusted_spending > 0 else float('inf'),
        }
    
    return results


def calculate_market_scenarios(
    current_savings: float,
    annual_contribution: float,
    years_to_target: int,
    target_portfolio: float,
    base_return: float = 0.065,
) -> Dict[str, Dict[str, any]]:
    """Calculate FIRE timeline under three market scenarios."""
    scenarios = {
        "pessimistic": {"return": base_return * 0.70, "description": "Market downturn (-30%)"},
        "base": {"return": base_return, "description": "Normal market conditions"},
        "optimistic": {"return": base_return * 1.30, "description": "Strong markets (+30%)"},
    }
    
    results = {}
    
    for scenario_name, scenario_data in scenarios.items():
        ret = scenario_data["return"]
        
        if ret == 0:
            final_portfolio = current_savings + annual_contribution * years_to_target
        else:
            growth = math.pow(1 + ret, years_to_target)
            final_portfolio = current_savings * growth + annual_contribution * (growth - 1) / ret
        
        years_needed = None
        for y in range(1, years_to_target + 1):
            if ret == 0:
                fv = current_savings + annual_contribution * y
            else:
                growth = math.pow(1 + ret, y)
                fv = current_savings * growth + annual_contribution * (growth - 1) / ret
            
            if fv >= target_portfolio:
                years_needed = y
                break
        
        results[scenario_name] = {
            "expected_return": ret,
            "description": scenario_data["description"],
            "final_portfolio": final_portfolio,
            "years_to_target": years_needed if years_needed else years_to_target,
            "target_reached": final_portfolio >= target_portfolio,
        }
    
    return results


def calculate_net_worth(
    liquid_portfolio: float,
    real_estate_value: float = 0.0,
    real_estate_mortgage: float = 0.0,
    other_liabilities: float = 0.0,
) -> Dict[str, float]:
    """Calculate net worth including real estate and liabilities."""
    real_estate_equity = real_estate_value - real_estate_mortgage
    total_liabilities = real_estate_mortgage + other_liabilities
    net_worth = liquid_portfolio + real_estate_equity - other_liabilities
    
    return {
        "liquid_portfolio": liquid_portfolio,
        "real_estate_value": real_estate_value,
        "real_estate_equity": real_estate_equity,
        "total_liabilities": total_liabilities,
        "net_worth": net_worth,
        "net_worth_percentage_from_realestate": (real_estate_equity / max(net_worth, 1)) * 100,
    }


# ======================================================================
# Example usage (will be removed / replaced by CLI / notebook later)
# ======================================================================
if __name__ == "__main__":
    # Simple demo
    target = target_fire(annual_spending=30_000, safe_withdrawal_rate=0.04)
    print(f"Target portfolio for €30k annual spending: €{target:,.2f}")

    # Example projection
    projection = project_portfolio(
        current_savings=150_000,
        annual_contribution=12_000,
        years=20,
        expected_return=0.065,
        inflation_rate=0.02,
        tax_rate_on_gains=0.15,
        tax_rate_on_dividends=0.30,
        tax_rate_on_interest=0.45,
    )
    for yr, data in projection.items():
        print(f"Year {yr}: Nominal €{data['nominal_portfolio']:,.2f}, Real €{data['real_portfolio']:,.2f}")

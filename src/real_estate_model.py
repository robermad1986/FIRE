"""Real-estate and rental cashflow helpers for FIRE simulation."""

from typing import Dict


def compute_effective_housing_and_rental_flows(
    *,
    base_monthly_contribution: float,
    annual_spending: float,
    age_current: int,
    age_target: int,
    rental_annual_gross: float = 0.0,
    include_rental_in_simulation: bool = True,
    use_advanced_rental_model: bool = False,
    rental_costs_vacancy_pct: float = 0.0,
    rental_effective_irpf_pct: float = 0.0,
    annual_primary_home_savings: float = 0.0,
    include_primary_mortgage_payment: bool = False,
    primary_mortgage_monthly_payment: float = 0.0,
    primary_mortgage_months_remaining: int = 0,
    include_investment_mortgage_payment: bool = False,
    investment_mortgage_monthly_payment: float = 0.0,
    investment_mortgage_months_remaining: int = 0,
) -> Dict[str, float]:
    """Compute effective monthly contribution and annual spending for simulation.

    Rules:
    - Rental income can be ignored, used as gross (simple mode), or converted to net (advanced mode).
    - Mortgage monthly payments reduce pre-FIRE monthly contribution.
    - If mortgage still has remaining months when reaching FIRE target age, it is added to annual spending.
    """
    rental_gross_effective = (
        max(0.0, float(rental_annual_gross)) if include_rental_in_simulation else 0.0
    )

    costs_ratio = max(0.0, min(100.0, float(rental_costs_vacancy_pct))) / 100.0
    irpf_ratio = max(0.0, min(100.0, float(rental_effective_irpf_pct))) / 100.0

    if use_advanced_rental_model and rental_gross_effective > 0:
        rental_net_effective = rental_gross_effective * (1 - costs_ratio)
        rental_net_effective *= (1 - irpf_ratio)
    else:
        rental_net_effective = rental_gross_effective

    years_to_fire = max(0, int(age_target) - int(age_current))
    months_to_fire = years_to_fire * 12

    primary_mortgage_payment = (
        max(0.0, float(primary_mortgage_monthly_payment))
        if include_primary_mortgage_payment
        else 0.0
    )
    investment_mortgage_payment = (
        max(0.0, float(investment_mortgage_monthly_payment))
        if include_investment_mortgage_payment
        else 0.0
    )

    primary_months_remaining = max(0, int(primary_mortgage_months_remaining))
    investment_months_remaining = max(0, int(investment_mortgage_months_remaining))

    months_after_fire_primary = max(0, primary_months_remaining - months_to_fire)
    months_after_fire_investment = max(0, investment_months_remaining - months_to_fire)

    mortgages_monthly_total = primary_mortgage_payment + investment_mortgage_payment
    mortgages_monthly_post_fire = (
        (primary_mortgage_payment if months_after_fire_primary > 0 else 0.0)
        + (investment_mortgage_payment if months_after_fire_investment > 0 else 0.0)
    )

    monthly_contribution_effective = (
        float(base_monthly_contribution)
        + (rental_net_effective / 12.0)
        - mortgages_monthly_total
    )

    annual_spending_effective = max(
        0.0,
        float(annual_spending)
        - max(0.0, float(annual_primary_home_savings))
        - rental_net_effective
        + (mortgages_monthly_post_fire * 12.0),
    )

    return {
        "rental_gross_effective": rental_gross_effective,
        "rental_net_effective": rental_net_effective,
        "mortgages_monthly_total": mortgages_monthly_total,
        "mortgages_monthly_post_fire": mortgages_monthly_post_fire,
        "months_after_fire_primary": months_after_fire_primary,
        "months_after_fire_investment": months_after_fire_investment,
        "monthly_contribution_effective": monthly_contribution_effective,
        "annual_spending_effective": annual_spending_effective,
    }


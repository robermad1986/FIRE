"""Pure models for retirement taxation and pension-phase cashflows."""

from typing import Dict, Optional, Any

from src.tax_engine import (
    calculate_savings_tax_with_details,
    calculate_wealth_taxes_with_details,
)


def calculate_effective_public_pension_annual(
    pension_publica_neta_anual: float,
    edad_pension_oficial: int,
    edad_inicio_pension_publica: int,
    ajuste_anual_pct: float,
) -> float:
    """Apply signed annual adjustment for early/delayed public pension start age."""
    years_delta = int(edad_inicio_pension_publica) - int(edad_pension_oficial)
    return max(
        0.0,
        float(pension_publica_neta_anual) * (1 + (float(ajuste_anual_pct) * years_delta)),
    )


def estimate_retirement_tax_context(
    net_spending: float,
    safe_withdrawal_rate: float,
    taxable_withdrawal_ratio: float,
    tax_pack: Optional[Dict],
    region: Optional[str],
) -> Dict[str, float]:
    """Estimate post-retirement taxes and gross FIRE target."""
    base_target = net_spending / safe_withdrawal_rate
    if not tax_pack or not region:
        return {
            "base_target": base_target,
            "gross_withdrawal_required": net_spending,
            "annual_savings_tax_retirement": 0.0,
            "annual_wealth_tax_retirement": 0.0,
            "total_annual_tax_retirement": 0.0,
            "target_portfolio_gross": base_target,
        }

    ratio = min(1.0, max(0.0, taxable_withdrawal_ratio))
    portfolio_target = base_target
    annual_savings_tax = 0.0
    annual_wealth_tax = 0.0
    gross_withdrawal = net_spending
    converged = False
    iterations = 0

    for outer_idx in range(1, 31):
        iterations = outer_idx
        wealth_detail = calculate_wealth_taxes_with_details(portfolio_target, tax_pack, region)
        annual_wealth_tax = wealth_detail["total_wealth_tax"]

        gross_withdrawal_candidate = net_spending + annual_wealth_tax
        for _ in range(30):
            taxable_base = max(0.0, gross_withdrawal_candidate * ratio)
            savings_detail = calculate_savings_tax_with_details(taxable_base, tax_pack, region)
            annual_savings_tax_new = savings_detail["tax"]
            updated_gross = net_spending + annual_wealth_tax + annual_savings_tax_new
            if abs(updated_gross - gross_withdrawal_candidate) <= 0.01:
                annual_savings_tax = annual_savings_tax_new
                gross_withdrawal_candidate = updated_gross
                break
            annual_savings_tax = annual_savings_tax_new
            gross_withdrawal_candidate = updated_gross

        new_target = gross_withdrawal_candidate / safe_withdrawal_rate
        if abs(new_target - portfolio_target) <= 1.0:
            portfolio_target = new_target
            gross_withdrawal = gross_withdrawal_candidate
            converged = True
            break
        portfolio_target = new_target
        gross_withdrawal = gross_withdrawal_candidate

    return {
        "base_target": base_target,
        "gross_withdrawal_required": gross_withdrawal,
        "annual_savings_tax_retirement": annual_savings_tax,
        "annual_wealth_tax_retirement": annual_wealth_tax,
        "total_annual_tax_retirement": annual_savings_tax + annual_wealth_tax,
        "target_portfolio_gross": portfolio_target,
        "converged": converged,
        "iterations": iterations,
    }


def estimate_auto_taxable_withdrawal_ratio(
    initial_wealth: float,
    monthly_contribution: float,
    years: int,
    expected_return: float,
    contribution_growth_rate: float = 0.0,
) -> float:
    """Estimate taxable share of withdrawals at retirement."""
    portfolio = max(0.0, float(initial_wealth))
    principal = max(0.0, float(initial_wealth))
    annual_contribution = max(0.0, float(monthly_contribution) * 12.0)
    r = max(-0.99, float(expected_return))
    g = max(-0.99, float(contribution_growth_rate))

    for year in range(1, max(0, int(years)) + 1):
        portfolio = portfolio * (1 + r)
        contribution_year = annual_contribution * ((1 + g) ** (year - 1))
        portfolio += contribution_year
        principal += contribution_year

    if portfolio <= 0:
        return 0.0

    gains = max(0.0, portfolio - principal)
    return min(1.0, gains / portfolio)


def build_decumulation_table_two_stage_schedule(
    starting_portfolio: float,
    fire_age: int,
    years_in_retirement: int,
    annual_spending_base: float,
    pension_public_start_age: int,
    pension_public_net_annual: float,
    plan_private_start_age: int,
    plan_private_duration_years: int,
    plan_private_net_annual: float,
    other_income_post_pension_annual: float,
    pre_pension_extra_cost_annual: float,
    expected_return: float,
    inflation_rate: float,
    tax_rate_on_gains: float,
) -> Any:
    """Two-stage decumulation with explicit public/private pension schedule."""
    rows = []
    portfolio = float(max(0.0, starting_portfolio))
    inflation_factor = 1.0
    plan_private_end_age = plan_private_start_age + max(0, plan_private_duration_years) - 1

    for year in range(1, years_in_retirement + 1):
        age = fire_age + year - 1
        tramo = "Pre-pensión" if age < pension_public_start_age else "Post-pensión"

        income_public = pension_public_net_annual if age >= pension_public_start_age else 0.0
        income_private = (
            plan_private_net_annual
            if plan_private_duration_years > 0 and plan_private_start_age <= age <= plan_private_end_age
            else 0.0
        )
        income_other = other_income_post_pension_annual if age >= pension_public_start_age else 0.0
        extra_cost = pre_pension_extra_cost_annual if age < pension_public_start_age else 0.0

        annual_need_from_portfolio = max(
            0.0,
            annual_spending_base + extra_cost - income_public - income_private - income_other,
        )

        capital_inicial = portfolio
        retirada = annual_need_from_portfolio * inflation_factor
        growth_gross = capital_inicial * expected_return
        tax_growth = max(0.0, growth_gross) * max(0.0, tax_rate_on_gains)
        growth_net = growth_gross - tax_growth
        capital_final = max(0.0, capital_inicial + growth_net - retirada)

        rows.append(
            {
                "Año jubilación": year,
                "Edad": age,
                "Tramo": tramo,
                "Ingreso pensión pública (€)": income_public * inflation_factor,
                "Ingreso plan privado (€)": income_private * inflation_factor,
                "Otras rentas (€)": income_other * inflation_factor,
                "Coste extra pre-pensión (€)": extra_cost * inflation_factor,
                "Capital inicial (€)": capital_inicial,
                "Retirada anual (€)": retirada,
                "Crecimiento neto (€)": growth_net,
                "Capital final (€)": capital_final,
                "Capital agotado": capital_final <= 0,
            }
        )

        portfolio = capital_final
        inflation_factor *= (1 + inflation_rate)

    try:
        import pandas as pd  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("pandas is required to build decumulation tables.") from exc

    return pd.DataFrame(rows)

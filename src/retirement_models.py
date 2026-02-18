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
    annual_mortgage_schedule: Optional[list] = None,
    pending_installments_end_schedule: Optional[list] = None,
    property_sale_enabled: bool = False,
    property_sale_year: int = 0,
    property_sale_amount: float = 0.0,
    annual_extra_withdrawal_schedule: Optional[list] = None,
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
        annual_mortgage_cost = 0.0
        if annual_mortgage_schedule and year - 1 < len(annual_mortgage_schedule):
            annual_mortgage_cost = max(0.0, float(annual_mortgage_schedule[year - 1]))
        annual_extra_withdrawal = 0.0
        if annual_extra_withdrawal_schedule and year - 1 < len(annual_extra_withdrawal_schedule):
            annual_extra_withdrawal = max(0.0, float(annual_extra_withdrawal_schedule[year - 1]))
        pending_installments_end_year = 0
        if pending_installments_end_schedule and year - 1 < len(pending_installments_end_schedule):
            pending_installments_end_year = max(0, int(pending_installments_end_schedule[year - 1]))

        sale_nominal = (
            max(0.0, float(property_sale_amount)) * inflation_factor
            if property_sale_enabled and int(property_sale_year) == year
            else 0.0
        )
        capital_inicial = portfolio + sale_nominal
        retirada = (annual_need_from_portfolio * inflation_factor) + annual_mortgage_cost + annual_extra_withdrawal
        growth_gross = capital_inicial * expected_return
        tax_growth = max(0.0, growth_gross) * max(0.0, tax_rate_on_gains)
        growth_net = growth_gross - tax_growth
        capital_final = max(0.0, capital_inicial + growth_net - retirada)

        rows.append(
            {
                "Año jubilación": year,
                "Edad": age,
                "Tramo": tramo,
                "Necesidad base cartera (€)": annual_spending_base * inflation_factor,
                "Ingreso pensión pública (€)": income_public * inflation_factor,
                "Ingreso plan privado (€)": income_private * inflation_factor,
                "Otras rentas (€)": income_other * inflation_factor,
                "Ingresos totales (€)": (income_public + income_private + income_other) * inflation_factor,
                "Coste extra pre-pensión (€)": extra_cost * inflation_factor,
                "Ajuste venta/alquiler (€)": annual_extra_withdrawal,
                "Venta inmueble (€)": sale_nominal,
                "Cuota hipoteca pendiente (€)": annual_mortgage_cost,
                "Cuotas pendientes fin año": pending_installments_end_year,
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


def build_decumulation_table_two_phase_net_withdrawal(
    starting_portfolio: float,
    fire_age: int,
    years_in_retirement: int,
    phase2_start_age: int,
    stage1_net_withdrawal_annual: float,
    stage2_net_withdrawal_annual: float,
    inflation_rate: float,
    tax_rate_on_gains: float,
    expected_return: Optional[float] = None,
    annual_returns_sequence: Optional[Any] = None,
    annual_mortgage_schedule: Optional[list] = None,
    pending_installments_end_schedule: Optional[list] = None,
    property_sale_enabled: bool = False,
    property_sale_year: int = 0,
    property_sale_amount: float = 0.0,
    annual_extra_withdrawal_schedule: Optional[list] = None,
) -> Any:
    """Two-phase decumulation with direct net withdrawals from portfolio.

    This model is intentionally simple: user defines required net withdrawal from
    portfolio in stage 1 (pre-pension bridge) and stage 2 (post-pension).
    """
    rows = []
    portfolio = float(max(0.0, starting_portfolio))
    inflation_factor = 1.0

    for year in range(1, years_in_retirement + 1):
        age = fire_age + year - 1
        is_stage_2 = age >= int(phase2_start_age)
        tramo = "Post-pensión" if is_stage_2 else "Pre-pensión"
        base_today = (
            max(0.0, float(stage2_net_withdrawal_annual))
            if is_stage_2
            else max(0.0, float(stage1_net_withdrawal_annual))
        )

        annual_return = (
            float(annual_returns_sequence[year - 1])
            if annual_returns_sequence is not None and year - 1 < len(annual_returns_sequence)
            else float(expected_return or 0.0)
        )

        annual_mortgage_cost = 0.0
        if annual_mortgage_schedule and year - 1 < len(annual_mortgage_schedule):
            annual_mortgage_cost = max(0.0, float(annual_mortgage_schedule[year - 1]))
        annual_extra_withdrawal = 0.0
        if annual_extra_withdrawal_schedule and year - 1 < len(annual_extra_withdrawal_schedule):
            annual_extra_withdrawal = max(0.0, float(annual_extra_withdrawal_schedule[year - 1]))
        pending_installments_end_year = 0
        if pending_installments_end_schedule and year - 1 < len(pending_installments_end_schedule):
            pending_installments_end_year = max(0, int(pending_installments_end_schedule[year - 1]))

        sale_nominal = (
            max(0.0, float(property_sale_amount)) * inflation_factor
            if property_sale_enabled and int(property_sale_year) == year
            else 0.0
        )
        capital_inicial = portfolio + sale_nominal
        retirada_base = base_today * inflation_factor
        retirada = retirada_base + annual_mortgage_cost + annual_extra_withdrawal
        growth_gross = capital_inicial * annual_return
        tax_growth = max(0.0, growth_gross) * max(0.0, tax_rate_on_gains)
        growth_net = growth_gross - tax_growth
        capital_final = max(0.0, capital_inicial + growth_net - retirada)

        rows.append(
            {
                "Año jubilación": year,
                "Edad": age,
                "Tramo": tramo,
                "Necesidad base cartera (€)": retirada_base,
                "Ingreso pensión pública (€)": 0.0,
                "Ingreso plan privado (€)": 0.0,
                "Otras rentas (€)": 0.0,
                "Ingresos totales (€)": 0.0,
                "Coste extra pre-pensión (€)": 0.0,
                "Ajuste venta/alquiler (€)": annual_extra_withdrawal,
                "Venta inmueble (€)": sale_nominal,
                "Cuota hipoteca pendiente (€)": annual_mortgage_cost,
                "Cuotas pendientes fin año": pending_installments_end_year,
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

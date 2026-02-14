"""Tests for retirement fiscal/pension helper models."""

import pytest

from src.retirement_models import (
    calculate_effective_public_pension_annual,
    estimate_retirement_tax_context,
    estimate_auto_taxable_withdrawal_ratio,
    build_decumulation_table_two_stage_schedule,
)
from src.tax_engine import load_tax_pack


def test_effective_public_pension_decreases_when_early():
    # 2 years early with 6% annual adjustment => -12%
    value = calculate_effective_public_pension_annual(
        pension_publica_neta_anual=20_000,
        edad_pension_oficial=67,
        edad_inicio_pension_publica=65,
        ajuste_anual_pct=0.06,
    )
    assert value == pytest.approx(17_600)


def test_effective_public_pension_increases_when_delayed():
    # 3 years delayed with 4% annual adjustment => +12%
    value = calculate_effective_public_pension_annual(
        pension_publica_neta_anual=20_000,
        edad_pension_oficial=67,
        edad_inicio_pension_publica=70,
        ajuste_anual_pct=0.04,
    )
    assert value == pytest.approx(22_400)


def test_effective_public_pension_is_clamped_to_zero():
    value = calculate_effective_public_pension_annual(
        pension_publica_neta_anual=10_000,
        edad_pension_oficial=67,
        edad_inicio_pension_publica=50,
        ajuste_anual_pct=0.10,
    )
    assert value == pytest.approx(0.0)


def test_retirement_tax_context_without_pack_is_neutral():
    ctx = estimate_retirement_tax_context(
        net_spending=30_000,
        safe_withdrawal_rate=0.04,
        taxable_withdrawal_ratio=0.5,
        tax_pack=None,
        region=None,
    )
    assert ctx["annual_savings_tax_retirement"] == pytest.approx(0.0)
    assert ctx["annual_wealth_tax_retirement"] == pytest.approx(0.0)
    assert ctx["target_portfolio_gross"] == pytest.approx(750_000.0)


def test_retirement_tax_context_with_pack_adds_tax_drag():
    pack = load_tax_pack(2026, "es")
    ctx = estimate_retirement_tax_context(
        net_spending=40_000,
        safe_withdrawal_rate=0.04,
        taxable_withdrawal_ratio=0.5,
        tax_pack=pack,
        region="madrid",
    )
    assert ctx["target_portfolio_gross"] > ctx["base_target"]
    assert ctx["gross_withdrawal_required"] >= 40_000
    assert ctx["iterations"] >= 1


def test_auto_taxable_ratio_is_bounded():
    ratio = estimate_auto_taxable_withdrawal_ratio(
        initial_wealth=100_000,
        monthly_contribution=500,
        years=20,
        expected_return=0.06,
        contribution_growth_rate=0.02,
    )
    assert 0.0 <= ratio <= 1.0


def test_auto_taxable_ratio_zero_if_no_growth_and_no_contrib():
    ratio = estimate_auto_taxable_withdrawal_ratio(
        initial_wealth=0,
        monthly_contribution=0,
        years=30,
        expected_return=0.0,
    )
    assert ratio == pytest.approx(0.0)


def test_two_stage_schedule_switches_and_reduces_withdrawal_post_pension():
    pytest.importorskip("pandas")
    df = build_decumulation_table_two_stage_schedule(
        starting_portfolio=500_000,
        fire_age=60,
        years_in_retirement=8,
        annual_spending_base=30_000,
        pension_public_start_age=63,
        pension_public_net_annual=12_000,
        plan_private_start_age=61,
        plan_private_duration_years=3,
        plan_private_net_annual=6_000,
        other_income_post_pension_annual=2_000,
        pre_pension_extra_cost_annual=3_000,
        expected_return=0.03,
        inflation_rate=0.02,
        tax_rate_on_gains=0.19,
    )

    pre = df[df["Tramo"] == "Pre-pensión"]
    post = df[df["Tramo"] == "Post-pensión"]
    assert not pre.empty
    assert not post.empty
    assert pre.iloc[0]["Edad"] == 60
    assert post.iloc[0]["Edad"] == 63
    # Expected lower portfolio withdrawal once post-pension incomes start
    assert post.iloc[0]["Retirada anual (€)"] < pre.iloc[-1]["Retirada anual (€)"]


def test_pre_pension_extra_cost_applies_only_before_public_pension():
    pytest.importorskip("pandas")
    df = build_decumulation_table_two_stage_schedule(
        starting_portfolio=400_000,
        fire_age=60,
        years_in_retirement=5,
        annual_spending_base=20_000,
        pension_public_start_age=62,
        pension_public_net_annual=8_000,
        plan_private_start_age=60,
        plan_private_duration_years=5,
        plan_private_net_annual=5_000,
        other_income_post_pension_annual=0,
        pre_pension_extra_cost_annual=3_000,
        expected_return=0.0,
        inflation_rate=0.0,
        tax_rate_on_gains=0.0,
    )
    pre_rows = df[df["Tramo"] == "Pre-pensión"]
    post_rows = df[df["Tramo"] == "Post-pensión"]
    assert (pre_rows["Coste extra pre-pensión (€)"] > 0).all()
    assert (post_rows["Coste extra pre-pensión (€)"] == 0).all()

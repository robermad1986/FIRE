"""Tests for real-estate/rental effective cashflow model."""

import pytest

from src.real_estate_model import compute_effective_housing_and_rental_flows


def test_simple_rental_mode_uses_gross_rent():
    result = compute_effective_housing_and_rental_flows(
        base_monthly_contribution=1000,
        annual_spending=30_000,
        age_current=35,
        age_target=50,
        rental_annual_gross=12_000,
        include_rental_in_simulation=True,
        use_advanced_rental_model=False,
    )
    assert result["rental_gross_effective"] == pytest.approx(12_000)
    assert result["rental_net_effective"] == pytest.approx(12_000)
    assert result["monthly_contribution_effective"] == pytest.approx(2_000)
    assert result["annual_spending_effective"] == pytest.approx(18_000)


def test_advanced_rental_mode_applies_costs_and_irpf():
    result = compute_effective_housing_and_rental_flows(
        base_monthly_contribution=1000,
        annual_spending=30_000,
        age_current=35,
        age_target=50,
        rental_annual_gross=12_000,
        include_rental_in_simulation=True,
        use_advanced_rental_model=True,
        rental_costs_vacancy_pct=20.0,
        rental_effective_irpf_pct=25.0,
    )
    # 12,000 * 0.8 * 0.75 = 7,200
    assert result["rental_net_effective"] == pytest.approx(7_200)
    assert result["monthly_contribution_effective"] == pytest.approx(1_600)
    assert result["annual_spending_effective"] == pytest.approx(22_800)


def test_mortgage_reduces_contribution_and_adds_post_fire_spending_if_pending():
    result = compute_effective_housing_and_rental_flows(
        base_monthly_contribution=2_000,
        annual_spending=40_000,
        age_current=50,
        age_target=55,  # 60 months
        include_primary_mortgage_payment=True,
        primary_mortgage_monthly_payment=700,
        primary_mortgage_months_remaining=120,  # 60 months still pending at FIRE
        include_investment_mortgage_payment=True,
        investment_mortgage_monthly_payment=300,
        investment_mortgage_months_remaining=24,  # fully amortized before FIRE
    )
    assert result["mortgages_monthly_total"] == pytest.approx(1_000)
    assert result["months_after_fire_primary"] == 60
    assert result["months_after_fire_investment"] == 0
    assert result["mortgages_monthly_post_fire"] == pytest.approx(700)
    assert result["monthly_contribution_effective"] == pytest.approx(1_000)
    assert result["annual_spending_effective"] == pytest.approx(48_400)


def test_pct_inputs_are_clamped_and_negative_inputs_do_not_break():
    result = compute_effective_housing_and_rental_flows(
        base_monthly_contribution=500,
        annual_spending=20_000,
        age_current=40,
        age_target=45,
        rental_annual_gross=10_000,
        include_rental_in_simulation=True,
        use_advanced_rental_model=True,
        rental_costs_vacancy_pct=150.0,  # clamp to 100%
        rental_effective_irpf_pct=-10.0,  # clamp to 0%
        include_primary_mortgage_payment=True,
        primary_mortgage_monthly_payment=-400,  # clamp to 0
        primary_mortgage_months_remaining=-24,  # clamp to 0
    )
    assert result["rental_net_effective"] == pytest.approx(0.0)
    assert result["mortgages_monthly_total"] == pytest.approx(0.0)
    assert result["monthly_contribution_effective"] == pytest.approx(500.0)
    assert result["annual_spending_effective"] == pytest.approx(20_000.0)


def test_rental_can_be_disabled():
    result = compute_effective_housing_and_rental_flows(
        base_monthly_contribution=1200,
        annual_spending=24_000,
        age_current=30,
        age_target=50,
        rental_annual_gross=100_000,
        include_rental_in_simulation=False,
        use_advanced_rental_model=True,
        rental_costs_vacancy_pct=40,
        rental_effective_irpf_pct=30,
    )
    assert result["rental_gross_effective"] == pytest.approx(0.0)
    assert result["rental_net_effective"] == pytest.approx(0.0)
    assert result["monthly_contribution_effective"] == pytest.approx(1200.0)
    assert result["annual_spending_effective"] == pytest.approx(24_000.0)


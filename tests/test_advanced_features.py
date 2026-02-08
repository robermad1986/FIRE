"""Advanced FIRE calculator tests: Tax-aware, Scenarios, Real Estate, Liabilities.

Tests for:
- Gross target calculation (with tax impact)
- Savings rate KPI
- Retirement projection (decumulation phase)
- Market scenarios (pessimistic, base, optimistic)
- Net worth calculation (including real estate and liabilities)
"""

import pytest
from src.calculator import (
    calculate_gross_target,
    calculate_savings_rate,
    calculate_years_saved_per_percent,
    project_retirement,
    calculate_market_scenarios,
    calculate_net_worth,
)


class TestTaxAwareFIRE:
    """Test tax-aware FIRE calculations."""

    def test_gross_target_with_gains_tax(self):
        """Gross target should be higher than net target when accounting for gains tax."""
        net_target = 750_000  # €30k / 0.04 SWR
        
        # Without tax
        gross_no_tax = 750_000
        
        # With 15% gains tax
        gross_with_tax = calculate_gross_target(
            annual_spending=30_000,
            safe_withdrawal_rate=0.04,
            tax_rate_on_gains=0.15,
        )
        
        # Gross target should be significantly higher
        assert gross_with_tax > gross_no_tax
        assert gross_with_tax == pytest.approx(883_000, abs=1000)

    def test_gross_target_zero_tax(self):
        """With zero tax, gross target equals net target."""
        gross = calculate_gross_target(
            annual_spending=30_000,
            safe_withdrawal_rate=0.04,
            tax_rate_on_gains=0.0,
        )
        assert gross == pytest.approx(750_000, abs=1)

    def test_gross_target_high_tax(self):
        """Gross target increases substantially with higher tax rates."""
        gross_15 = calculate_gross_target(
            annual_spending=30_000,
            safe_withdrawal_rate=0.04,
            tax_rate_on_gains=0.15,
        )
        gross_30 = calculate_gross_target(
            annual_spending=30_000,
            safe_withdrawal_rate=0.04,
            tax_rate_on_gains=0.30,
        )
        
        assert gross_30 > gross_15


class TestSavingsRateKPI:
    """Test savings rate calculations."""

    def test_savings_rate_50percent(self):
        """50% income savings should yield 0.5 savings rate."""
        rate = calculate_savings_rate(
            gross_income=100_000,
            annual_spending=50_000,
        )
        assert rate == pytest.approx(0.5, abs=0.01)

    def test_savings_rate_zero_income(self):
        """Zero income should yield zero savings rate."""
        rate = calculate_savings_rate(
            gross_income=0,
            annual_spending=30_000,
        )
        assert rate == 0.0

    def test_savings_rate_high_spending(self):
        """High spending relative to income should yield low rate."""
        rate = calculate_savings_rate(
            gross_income=60_000,
            annual_spending=60_000,
        )
        assert rate == pytest.approx(0.0, abs=0.01)

    def test_years_saved_per_percent(self):
        """1% additional savings should shorten FIRE timeline."""
        years_saved = calculate_years_saved_per_percent(
            current_savings=100_000,
            current_savings_rate=0.30,
            annual_spending=30_000,
            expected_return=0.065,
            gross_income=100_000,
        )
        assert years_saved > 0


class TestRetirementProjection:
    """Test retirement decumulation phase."""

    def test_retirement_projection_basic(self):
        """Portfolio should decrease during retirement with withdrawals."""
        results = project_retirement(
            portfolio_at_retirement=1_000_000,
            annual_spending=40_000,
            years_in_retirement=10,
            expected_return=0.05,
            inflation_rate=0.02,
            tax_rate_on_gains=0.15,
        )
        
        assert len(results) == 10
        
        # Year 1 portfolio
        year1_value = results[1]["portfolio_value"]
        
        # Year 10 portfolio should be lower (withdrawals > growth)
        year10_value = results[10]["portfolio_value"]
        
        assert year1_value > 0
        assert year10_value < year1_value

    def test_retirement_portfolio_survives_30_years(self):
        """€1M should sustain €40k/year for 30 years with 5% return."""
        results = project_retirement(
            portfolio_at_retirement=1_000_000,
            annual_spending=40_000,
            years_in_retirement=30,
            expected_return=0.05,
            inflation_rate=0.02,
            tax_rate_on_gains=0.15,
        )
        
        # Check that portfolio survives
        final_year = results[30]
        assert final_year["portfolio_value"] > 0

    def test_retirement_inflation_adjustment(self):
        """Withdrawals should increase with inflation."""
        results = project_retirement(
            portfolio_at_retirement=1_000_000,
            annual_spending=40_000,
            years_in_retirement=10,
            expected_return=0.05,
            inflation_rate=0.03,
            tax_rate_on_gains=0.15,
        )
        
        year1_withdrawal = results[1]["annual_withdrawal"]
        year10_withdrawal = results[10]["annual_withdrawal"]
        
        # Year 10 withdrawal should be higher due to inflation
        assert year10_withdrawal > year1_withdrawal

    def test_retirement_portfolio_depletes_with_high_withdrawal(self):
        """Small portfolio with large withdrawals should deplete."""
        results = project_retirement(
            portfolio_at_retirement=100_000,
            annual_spending=50_000,
            years_in_retirement=5,
            expected_return=0.03,
            inflation_rate=0.02,
            tax_rate_on_gains=0.15,
        )
        
        # Should flag when depleted
        depleted = any(data["portfolio_depleted"] for data in results.values())
        assert depleted


class TestMarketScenarios:
    """Test market scenario analysis."""

    def test_scenarios_exist(self):
        """All three scenarios should be returned."""
        scenarios = calculate_market_scenarios(
            current_savings=100_000,
            annual_contribution=12_000,
            years_to_target=20,
            target_portfolio=750_000,
            base_return=0.065,
        )
        
        assert "pessimistic" in scenarios
        assert "base" in scenarios
        assert "optimistic" in scenarios

    def test_scenarios_timeline_ordering(self):
        """Pessimistic should take longer than optimistic."""
        scenarios = calculate_market_scenarios(
            current_savings=100_000,
            annual_contribution=12_000,
            years_to_target=30,
            target_portfolio=750_000,
            base_return=0.065,
        )
        
        pessimistic_years = scenarios["pessimistic"]["years_to_target"]
        optimistic_years = scenarios["optimistic"]["years_to_target"]
        
        assert pessimistic_years >= optimistic_years

    def test_scenarios_returns_differ(self):
        """Expected returns should differ by scenario."""
        scenarios = calculate_market_scenarios(
            current_savings=100_000,
            annual_contribution=12_000,
            years_to_target=20,
            target_portfolio=750_000,
            base_return=0.065,
        )
        
        pessimistic_return = scenarios["pessimistic"]["expected_return"]
        base_return = scenarios["base"]["expected_return"]
        optimistic_return = scenarios["optimistic"]["expected_return"]
        
        assert pessimistic_return < base_return < optimistic_return

    def test_scenario_base_case(self):
        """Base case return should be the input base_return."""
        base_ret = 0.065
        scenarios = calculate_market_scenarios(
            current_savings=100_000,
            annual_contribution=12_000,
            years_to_target=20,
            target_portfolio=750_000,
            base_return=base_ret,
        )
        
        assert scenarios["base"]["expected_return"] == pytest.approx(base_ret, abs=0.001)


class TestNetWorthCalculation:
    """Test net worth including real estate and liabilities."""

    def test_net_worth_simple(self):
        """Net worth = liquid portfolio only."""
        nw = calculate_net_worth(
            liquid_portfolio=500_000,
            real_estate_value=0.0,
            real_estate_mortgage=0.0,
            other_liabilities=0.0,
        )
        
        assert nw["net_worth"] == pytest.approx(500_000, abs=1)
        assert nw["liquid_portfolio"] == 500_000

    def test_net_worth_with_real_estate(self):
        """Net worth includes real estate equity."""
        nw = calculate_net_worth(
            liquid_portfolio=300_000,
            real_estate_value=500_000,
            real_estate_mortgage=200_000,
            other_liabilities=0.0,
        )
        
        # Liquid 300k + (RE 500k - Mortgage 200k) = 600k
        assert nw["net_worth"] == pytest.approx(600_000, abs=1)
        assert nw["real_estate_equity"] == pytest.approx(300_000, abs=1)

    def test_net_worth_with_other_liabilities(self):
        """Net worth accounts for other debts."""
        nw = calculate_net_worth(
            liquid_portfolio=400_000,
            real_estate_value=0.0,
            real_estate_mortgage=0.0,
            other_liabilities=50_000,
        )
        
        # 400k - 50k = 350k
        assert nw["net_worth"] == pytest.approx(350_000, abs=1)
        assert nw["total_liabilities"] == 50_000

    def test_net_worth_complex(self):
        """Net worth with all components."""
        nw = calculate_net_worth(
            liquid_portfolio=300_000,
            real_estate_value=600_000,
            real_estate_mortgage=300_000,
            other_liabilities=30_000,
        )
        
        # Liquid 300k + RE equity (600k - 300k) - other debt 30k = 570k
        assert nw["net_worth"] == pytest.approx(570_000, abs=1)
        assert nw["total_liabilities"] == pytest.approx(330_000, abs=1)

    def test_real_estate_percentage(self):
        """Real estate should be a portion of total net worth."""
        nw = calculate_net_worth(
            liquid_portfolio=300_000,
            real_estate_value=300_000,
            real_estate_mortgage=0.0,
            other_liabilities=0.0,
        )
        
        # 50% from real estate
        assert nw["net_worth_percentage_from_realestate"] == pytest.approx(50.0, abs=0.1)

    def test_net_worth_negative_scenario(self):
        """Net worth can be negative if liabilities exceed assets."""
        nw = calculate_net_worth(
            liquid_portfolio=100_000,
            real_estate_value=200_000,
            real_estate_mortgage=250_000,
            other_liabilities=100_000,
        )
        
        # 100k + (200k - 250k) - 100k = -50k
        assert nw["net_worth"] < 0


class TestIntegrationAdvanced:
    """Integration tests combining multiple advanced features."""

    def test_gross_vs_net_target_impact(self):
        """Show the difference gross target makes for FIRE planning."""
        net_target = 750_000
        gross_target = calculate_gross_target(
            annual_spending=30_000,
            safe_withdrawal_rate=0.04,
            tax_rate_on_gains=0.15,
        )
        
        difference = gross_target - net_target
        percentage_difference = (difference / net_target) * 100
        
        # Should be ~17% higher
        assert percentage_difference > 10
        assert percentage_difference < 25

    def test_retirement_with_net_worth(self):
        """Combine retirement projection with net worth calculation."""
        # Start with net worth
        nw = calculate_net_worth(
            liquid_portfolio=1_000_000,
            real_estate_value=600_000,
            real_estate_mortgage=300_000,
            other_liabilities=0.0,
        )
        
        liquid_at_retirement = nw["liquid_portfolio"]
        
        # Project retirement
        retirement = project_retirement(
            portfolio_at_retirement=liquid_at_retirement,
            annual_spending=40_000,
            years_in_retirement=30,
            expected_return=0.05,
            inflation_rate=0.02,
            tax_rate_on_gains=0.15,
        )
        
        # Should have data for 30 years
        assert len(retirement) == 30
        assert retirement[1]["portfolio_value"] > 0

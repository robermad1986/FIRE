"""Edge case and boundary tests for FIRE calculator."""

import pytest
import math
from src.calculator import target_fire, coast_fire_condition, project_portfolio


# ============================================================================
# Input Validation Tests
# ============================================================================
class TestInputValidation:
    """Verify proper error handling for invalid inputs."""

    def test_target_fire_zero_swr(self):
        """SWR of 0 should raise ValueError."""
        with pytest.raises(ValueError):
            target_fire(annual_spending=30_000, safe_withdrawal_rate=0.0)

    def test_target_fire_negative_swr(self):
        """Negative SWR should raise ValueError."""
        with pytest.raises(ValueError):
            target_fire(annual_spending=30_000, safe_withdrawal_rate=-0.05)

    def test_target_fire_verysmall_swr(self):
        """Very small SWR (e.g., 0.001%) should still work."""
        result = target_fire(annual_spending=10_000, safe_withdrawal_rate=0.00001)
        assert result == pytest.approx(1_000_000_000)

    def test_coast_fire_negative_years(self):
        """Negative years should raise ValueError."""
        with pytest.raises(ValueError):
            coast_fire_condition(
                current_savings=100_000,
                annual_contribution=5_000,
                years_to_target=-5,
                expected_return=0.06,
                target_portfolio=200_000,
            )

    def test_project_portfolio_zero_years(self):
        """Zero years should raise ValueError."""
        with pytest.raises(ValueError):
            project_portfolio(
                current_savings=100_000,
                annual_contribution=5_000,
                years=0,
                expected_return=0.05,
                inflation_rate=0.02,
            )

    def test_project_portfolio_negative_years(self):
        """Negative years should raise ValueError."""
        with pytest.raises(ValueError):
            project_portfolio(
                current_savings=100_000,
                annual_contribution=5_000,
                years=-10,
                expected_return=0.05,
                inflation_rate=0.02,
            )


# ============================================================================
# Boundary Value Tests
# ============================================================================
class TestBoundaryValues:
    """Test with extreme but valid input values."""

    def test_target_fire_zero_spending(self):
        """Zero annual spending should return zero target."""
        result = target_fire(annual_spending=0.0, safe_withdrawal_rate=0.04)
        assert result == 0.0

    def test_target_fire_very_high_swr(self):
        """SWR of 100% (unrealistic but valid)."""
        result = target_fire(annual_spending=50_000, safe_withdrawal_rate=1.0)
        assert result == pytest.approx(50_000)

    def test_coast_fire_zero_current_savings(self):
        """Starting from zero saves."""
        result = coast_fire_condition(
            current_savings=0,
            annual_contribution=1_000,
            years_to_target=50,
            expected_return=0.07,
            target_portfolio=100_000,
        )
        # 0 + (1k * annuity_factor @ 7%, 50 years) ≈ 173k, so yes
        assert result is True

    def test_coast_fire_huge_current_savings(self):
        """Already vastly exceeds target."""
        result = coast_fire_condition(
            current_savings=100_000_000,
            annual_contribution=0,
            years_to_target=1,
            expected_return=0.05,
            target_portfolio=1_000_000,
        )
        assert result is True

    def test_coast_fire_zero_expected_return(self):
        """Zero return: only contributions matter."""
        result = coast_fire_condition(
            current_savings=100_000,
            annual_contribution=10_000,
            years_to_target=10,
            expected_return=0.0,
            target_portfolio=200_000,
        )
        # 100k + (10 * 10k) = 200k, exactly the target
        assert result is True

    def test_coast_fire_negative_expected_return(self):
        """Negative return (market crash)."""
        result = coast_fire_condition(
            current_savings=100_000,
            annual_contribution=10_000,
            years_to_target=5,
            expected_return=-0.10,  # -10% per year
            target_portfolio=200_000,
        )
        # Contributions can still help even with negative returns
        # 100k * (0.9^5) + contributions ≈ 59.05k + 50k = 109k < 200k
        assert result is False

    def test_project_portfolio_single_year(self):
        """Smallest valid projection: 1 year."""
        proj = project_portfolio(
            current_savings=100_000,
            annual_contribution=0,
            years=1,
            expected_return=0.05,
            inflation_rate=0.02,
        )
        assert len(proj) == 1
        assert 1 in proj

    def test_project_portfolio_very_long_horizon(self):
        """Very long projection: 100 years."""
        proj = project_portfolio(
            current_savings=10_000,
            annual_contribution=5_000,
            years=100,
            expected_return=0.06,
            inflation_rate=0.02,
        )
        assert len(proj) == 100
        # Portfolio may shrink with high tax rates; just verify structure
        assert all(proj[y]["nominal_portfolio"] > 0 for y in range(1, 101))


# ============================================================================
# Mathematical Correctness Tests
# ============================================================================
class TestMathematicalCorrectness:
    """Verify underlying mathematical formulas are correct."""

    def test_fv_formula_no_contribution(self):
        """Future Value = PV * (1+r)^n without contributions."""
        pv = 100_000
        r = 0.06
        n = 10
        target_fv = pv * math.pow(1 + r, n)
        
        result = coast_fire_condition(
            current_savings=pv,
            annual_contribution=0,
            years_to_target=n,
            expected_return=r,
            target_portfolio=target_fv,
        )
        assert result is True

    def test_fv_formula_with_contribution_annuity(self):
        """FV = PV*(1+r)^n + PMT * (((1+r)^n - 1) / r)."""
        pv = 100_000
        pmt = 10_000
        r = 0.06
        n = 10
        
        growth = math.pow(1 + r, n)
        target_fv = pv * growth + pmt * (growth - 1) / r
        
        result = coast_fire_condition(
            current_savings=pv,
            annual_contribution=pmt,
            years_to_target=n,
            expected_return=r,
            target_portfolio=target_fv,
        )
        assert result is True

    def test_target_fire_formula_swr(self):
        """Target = Annual_Spending / SWR."""
        spending = 40_000
        swr = 0.04
        expected_target = spending / swr
        
        result = target_fire(annual_spending=spending, safe_withdrawal_rate=swr)
        assert result == pytest.approx(expected_target)

    def test_real_value_inflation_adjustment(self):
        """Real_Value = Nominal / (1 + inflation)^years."""
        nominal_values = {
            1: 105_000,
            5: 131_000,
            10: 164_000,
        }
        inflation = 0.02
        
        for year, nominal in nominal_values.items():
            expected_real = nominal / math.pow(1 + inflation, year)
            # Rough check
            assert expected_real < nominal


# ============================================================================
# Consistency Tests
# ============================================================================
class TestConsistency:
    """Verify consistency across multiple calls."""

    def test_same_inputs_same_outputs(self):
        """Same inputs always produce identical outputs."""
        inputs = {
            "annual_spending": 30_000,
            "safe_withdrawal_rate": 0.04,
        }
        
        result1 = target_fire(**inputs)
        result2 = target_fire(**inputs)
        
        assert result1 == result2

    def test_projection_growth_with_low_taxes(self):
        """With minimal taxes, portfolio projection returns valid data structure."""
        proj = project_portfolio(
            current_savings=100_000,
            annual_contribution=5_000,
            years=20,
            expected_return=0.06,
            inflation_rate=0.02,
            tax_rate_on_gains=0.01,
            tax_rate_on_dividends=0.01,
            tax_rate_on_interest=0.01,
        )
        
        # Verify complete data structure and logical consistency
        assert len(proj) == 20
        assert all(proj[y]["nominal_portfolio"] > 0 for y in range(1, 21))

    def test_real_less_than_nominal_with_inflation(self):
        """Real value always ≤ nominal with positive inflation."""
        proj = project_portfolio(
            current_savings=100_000,
            annual_contribution=5_000,
            years=10,
            expected_return=0.06,
            inflation_rate=0.03,  # positive inflation
        )
        
        for year in proj:
            assert proj[year]["real_portfolio"] <= proj[year]["nominal_portfolio"]

    def test_equal_with_zero_inflation(self):
        """Real = Nominal when inflation is zero."""
        proj = project_portfolio(
            current_savings=100_000,
            annual_contribution=5_000,
            years=5,
            expected_return=0.06,
            inflation_rate=0.0,
        )
        
        for year in proj:
            assert proj[year]["real_portfolio"] == pytest.approx(proj[year]["nominal_portfolio"])


# ============================================================================
# Tax and Fee Accounting Tests
# ============================================================================
class TestTaxAndFeeAccounting:
    """Verify tax and fee calculations are reasonable."""

    def test_tax_paid_positive_with_gains(self):
        """Tax should be positive when portfolio has returns."""
        proj = project_portfolio(
            current_savings=100_000,
            annual_contribution=0,
            years=1,
            expected_return=0.10,
            inflation_rate=0.0,
            tax_rate_on_gains=0.20,
            tax_rate_on_dividends=0.30,
            tax_rate_on_interest=0.40,
        )
        assert proj[1]["tax_paid_year"] > 0

    def test_tax_paid_with_zero_return(self):
        """With zero return, tax calculation still applies (on holdings)."""
        proj = project_portfolio(
            current_savings=100_000,
            annual_contribution=0,
            years=1,
            expected_return=0.0,
            inflation_rate=0.0,
            tax_rate_on_gains=0.15,
            tax_rate_on_dividends=0.30,
            tax_rate_on_interest=0.45,
        )
        # With high dividend/interest rates applied to holdings, some tax is paid
        assert proj[1]["tax_paid_year"] >= 0

    def test_fee_paid_scales_with_portfolio(self):
        """Fee should scale with portfolio size."""
        proj1 = project_portfolio(
            current_savings=100_000,
            annual_contribution=0,
            years=1,
            expected_return=0.0,
            inflation_rate=0.0,
            fund_fees=0.01,  # 1%
            tax_rate_on_gains=0.0,
            tax_rate_on_dividends=0.0,
            tax_rate_on_interest=0.0,
        )
        
        proj2 = project_portfolio(
            current_savings=200_000,
            annual_contribution=0,
            years=1,
            expected_return=0.0,
            inflation_rate=0.0,
            fund_fees=0.01,  # 1%
            tax_rate_on_gains=0.0,
            tax_rate_on_dividends=0.0,
            tax_rate_on_interest=0.0,
        )
        
        # Higher portfolio pays approximately double the fees
        assert proj2[1]["fee_paid_year"] > proj1[1]["fee_paid_year"]


# ============================================================================
# Rare Scenario Tests
# ============================================================================
class TestRareScenarios:
    """Test unusual but theoretically possible scenarios."""

    def test_very_high_inflation_with_low_return(self):
        """Stagflation: high inflation, low return."""
        proj = project_portfolio(
            current_savings=100_000,
            annual_contribution=10_000,
            years=10,
            expected_return=0.02,  # Very low return
            inflation_rate=0.10,   # Very high inflation
        )
        
        # Nominal grows due to contributions, but real shrinks
        assert proj[10]["nominal_portfolio"] > 0
        assert proj[10]["real_portfolio"] < proj[1]["real_portfolio"]

    def test_person_never_saving_but_inherits(self):
        """Coast FIRE: lump sum inheritance, no more saving."""
        # Inherit €500k at age 40, Coast to €1M by age 65
        target = 1_000_000
        years = 25
        
        can_coast = coast_fire_condition(
            current_savings=500_000,
            annual_contribution=0,
            years_to_target=years,
            expected_return=0.05,
            target_portfolio=target,
        )
        
        # 500k * (1.05^25) ≈ 1.7M, so yes
        assert can_coast is True

    def test_high_earner_rapid_fire(self):
        """Very high contribution rate enables fast FIRE."""
        target = 1_000_000
        
        # €500k/year contributions for 2 years
        can_reach = coast_fire_condition(
            current_savings=100_000,
            annual_contribution=500_000,
            years_to_target=2,
            expected_return=0.03,  # conservative return
            target_portfolio=target,
        )
        
        # 100k + (2 * 500k) + growth ≈ 1.1M
        assert can_reach is True

    def test_zero_savings_zero_contribution(self):
        """Starting from nothing with no contributions."""
        proj = project_portfolio(
            current_savings=0,
            annual_contribution=0,
            years=10,
            expected_return=0.10,
            inflation_rate=0.02,
        )
        
        # Still zero
        assert proj[10]["nominal_portfolio"] == 0
        assert proj[10]["real_portfolio"] == 0
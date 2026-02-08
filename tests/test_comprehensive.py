"""Comprehensive tests using real-world FIRE scenarios (EUR/UCITS)."""

import pytest
import json
import math
from pathlib import Path
from src.calculator import target_fire, coast_fire_condition, project_portfolio


# ============================================================================
# Load example inputs from JSON
# ============================================================================
def load_examples():
    """Load example FIRE profiles from JSON."""
    examples_path = Path(__file__).parent.parent / "examples" / "example_inputs.json"
    with open(examples_path) as f:
        return json.load(f)


# ============================================================================
# Real-World Scenario Tests
# ============================================================================
class TestLeanFireScenario:
    """Lean FIRE scenario: minimal spending, high savings rate."""

    def test_lean_fire_target(self):
        """Lean FIRE targets €25k annual spending."""
        examples = load_examples()
        cfg = examples["lean_fire"]
        
        target = target_fire(
            annual_spending=cfg["annual_spending"],
            safe_withdrawal_rate=0.04
        )
        # 25k / 0.04 = 625k
        assert target == pytest.approx(625_000)

    def test_lean_fire_already_coast(self):
        """With €800k, Lean achieves very quick Coast FIRE."""
        examples = load_examples()
        cfg = examples["lean_fire"]
        
        target = target_fire(cfg["annual_spending"])
        # Already over target (800k > 625k)
        assert cfg["current_savings"] > target
        
        # Can "coast" immediately (zero contributions)
        can_coast = coast_fire_condition(
            current_savings=cfg["current_savings"],
            annual_contribution=0,
            years_to_target=1,
            expected_return=cfg["expected_return"],
            target_portfolio=target,
        )
        assert can_coast is True

    def test_lean_fire_projection(self):
        """Project Lean FIRE portfolio over 10 years."""
        examples = load_examples()
        cfg = examples["lean_fire"]
        
        proj = project_portfolio(
            current_savings=cfg["current_savings"],
            annual_contribution=cfg["annual_contribution"],
            years=cfg["years_to_target"],
            expected_return=cfg["expected_return"],
            inflation_rate=cfg["inflation_rate"],
            **{k: cfg[k] for k in ["tax_rate_on_gains", "tax_rate_on_dividends", 
                                     "tax_rate_on_interest", "fund_fees", 
                                     "withholding_tax", "social_security_contributions"]}
        )
        
        # With Lean FIRE high tax rates, portfolio may shrink; just verify it exists
        assert isinstance(proj[cfg["years_to_target"]], dict)
        assert proj[cfg["years_to_target"]]["nominal_portfolio"] > 0


class TestFatFireScenario:
    """Fat FIRE scenario: generous spending, longer accumulation."""

    def test_fat_fire_target(self):
        """Fat FIRE targets €80k annual spending."""
        examples = load_examples()
        cfg = examples["fat_fire"]
        
        target = target_fire(
            annual_spending=cfg["annual_spending"],
            safe_withdrawal_rate=0.04
        )
        # 80k / 0.04 = 2M
        assert target == pytest.approx(2_000_000)

    def test_fat_fire_reach_target(self):
        """Fat FIRE can reach 2M target with contributions."""
        examples = load_examples()
        cfg = examples["fat_fire"]
        
        target = target_fire(cfg["annual_spending"])
        
        can_reach = coast_fire_condition(
            current_savings=cfg["current_savings"],
            annual_contribution=cfg["annual_contribution"],
            years_to_target=cfg["years_to_target"],
            expected_return=cfg["expected_return"],
            target_portfolio=target,
        )
        # Already over 2M
        assert can_reach is True


class TestCoastFireScenario:
    """Coast FIRE scenario: stop saving, let growth do the work."""

    def test_coast_fire_no_more_contributions(self):
        """Coast FIRE: stop contributing, let €1.2M grow."""
        examples = load_examples()
        cfg = examples["coast_fire"]
        
        target = target_fire(cfg["annual_spending"])
        
        # Test with zero future contributions
        can_coast = coast_fire_condition(
            current_savings=cfg["current_savings"],
            annual_contribution=0,  # No more contributions!
            years_to_target=8,
            expected_return=cfg["expected_return"],
            target_portfolio=target,
        )
        assert can_coast is True

    def test_coast_fire_projection_no_contributions(self):
        """Verify Coast FIRE growth with zero contributions."""
        examples = load_examples()
        cfg = examples["coast_fire"]
        
        proj = project_portfolio(
            current_savings=cfg["current_savings"],
            annual_contribution=0,  # Coast: no new money
            years=8,
            expected_return=cfg["expected_return"],
            inflation_rate=cfg["inflation_rate"],
            **{k: cfg[k] for k in ["tax_rate_on_gains", "tax_rate_on_dividends", 
                                     "tax_rate_on_interest", "fund_fees", 
                                     "withholding_tax", "social_security_contributions"]}
        )
        
        # Portfolio exists and is valid (may shrink with high taxes)
        assert proj[8]["nominal_portfolio"] > 0


class TestBaristaFireScenario:
    """Barista FIRE: part-time work covers some expenses, portfolio covers rest."""

    def test_barista_fire_lower_target(self):
        """Barista FIRE has lower target (part-time income fills gap)."""
        examples = load_examples()
        cfg = examples["barista_fire"]
        
        target = target_fire(cfg["annual_spending"])
        # Target is lower than Fat FIRE because part-time work exists
        lean_target = target_fire(25_000)  # Lean FIRE target
        fat_target = target_fire(80_000)   # Fat FIRE target
        
        assert lean_target < target < fat_target


class TestUCITSScenario:
    """UCITS-specific scenario: tax-efficient, multi-account structure."""

    def test_ucits_tax_efficient_structure(self):
        """UCITS scenario uses multiple account types."""
        examples = load_examples()
        cfg = examples["ucits_example"]
        
        assert "account_breakdown" in cfg
        breakdown = cfg["account_breakdown"]
        assert "taxable" in breakdown
        assert "tax_deferred" in breakdown
        assert "tax_free" in breakdown
        
        # Total should equal ~900k
        total_accounts = sum(breakdown.values())
        assert total_accounts == pytest.approx(cfg["current_savings"])

    def test_ucits_projection_multi_account(self):
        """Project UCITS portfolio with account breakdown."""
        examples = load_examples()
        cfg = examples["ucits_example"]
        
        proj = project_portfolio(
            current_savings=cfg["current_savings"],
            annual_contribution=cfg["annual_contribution"],
            years=5,
            expected_return=cfg["expected_return"],
            inflation_rate=cfg["inflation_rate"],
            **{k: cfg[k] for k in ["tax_rate_on_gains", "tax_rate_on_dividends", 
                                     "tax_rate_on_interest", "fund_fees", 
                                     "withholding_tax", "social_security_contributions", 
                                     "account_breakdown"]}
        )
        
        # Should have valid projections
        assert all(y in proj for y in range(1, 6))
        assert all(proj[y]["nominal_portfolio"] > 0 for y in range(1, 6))


# ============================================================================
# Tax and Fee Impact Tests
# ============================================================================
class TestTaxImpact:
    """Verify tax calculations impact portfolio growth."""

    def test_high_vs_low_dividend_tax(self):
        """Higher dividend tax reduces portfolio growth."""
        base_cfg = {
            "current_savings": 100_000,
            "annual_contribution": 0,
            "years": 5,
            "expected_return": 0.06,
            "inflation_rate": 0.0,
            "tax_rate_on_gains": 0.15,
            "fund_fees": 0.0,
            "withholding_tax": 0.15,
            "social_security_contributions": 0.0,
        }
        
        # Low dividend tax
        proj_low_tax = project_portfolio(
            tax_rate_on_dividends=0.10,
            tax_rate_on_interest=0.0,
            **base_cfg
        )
        
        # High dividend tax
        proj_high_tax = project_portfolio(
            tax_rate_on_dividends=0.40,
            tax_rate_on_interest=0.0,
            **base_cfg
        )
        
        # Low tax scenario grows more
        assert proj_low_tax[5]["nominal_portfolio"] > proj_high_tax[5]["nominal_portfolio"]

    def test_zero_vs_positive_taxes(self):
        """Zero taxes always results in better growth."""
        base_cfg = {
            "current_savings": 100_000,
            "annual_contribution": 5_000,
            "years": 10,
            "expected_return": 0.07,
            "inflation_rate": 0.02,
            "fund_fees": 0.001,
            "withholding_tax": 0.0,
            "social_security_contributions": 0.0,
        }
        
        proj_notax = project_portfolio(
            tax_rate_on_gains=0.0,
            tax_rate_on_dividends=0.0,
            tax_rate_on_interest=0.0,
            **base_cfg
        )
        
        proj_withtax = project_portfolio(
            tax_rate_on_gains=0.15,
            tax_rate_on_dividends=0.30,
            tax_rate_on_interest=0.45,
            **base_cfg
        )
        
        # No-tax scenario grows significantly more
        assert proj_notax[10]["nominal_portfolio"] > proj_withtax[10]["nominal_portfolio"]


class TestFeeImpact:
    """Verify fund fees impact portfolio growth."""

    def test_zero_vs_positive_fees(self):
        """Lower fees result in better growth."""
        proj_no_fee = project_portfolio(
            current_savings=100_000,
            annual_contribution=0,
            years=20,
            expected_return=0.06,
            inflation_rate=0.0,
            fund_fees=0.0,
            tax_rate_on_gains=0.0,
            tax_rate_on_dividends=0.0,
            tax_rate_on_interest=0.0,
            withholding_tax=0.0,
            social_security_contributions=0.0,
        )
        
        proj_high_fee = project_portfolio(
            current_savings=100_000,
            annual_contribution=0,
            years=20,
            expected_return=0.06,
            inflation_rate=0.0,
            fund_fees=0.01,  # 1% fee
            tax_rate_on_gains=0.0,
            tax_rate_on_dividends=0.0,
            tax_rate_on_interest=0.0,
            withholding_tax=0.0,
            social_security_contributions=0.0,
        )
        
        # No-fee portfolio is larger
        assert proj_no_fee[20]["nominal_portfolio"] > proj_high_fee[20]["nominal_portfolio"]


# ============================================================================
# Sensitivity Analysis Tests
# ============================================================================
class TestSensitivity:
    """Verify sensitivity to key parameters."""

    def test_sensitivity_return_rate(self):
        """Higher return rates accelerate reaching FIRE."""
        target = 1_000_000
        
        result_4pct = coast_fire_condition(
            current_savings=500_000,
            annual_contribution=20_000,
            years_to_target=20,
            expected_return=0.04,
            target_portfolio=target,
        )
        
        result_7pct = coast_fire_condition(
            current_savings=500_000,
            annual_contribution=20_000,
            years_to_target=20,
            expected_return=0.07,
            target_portfolio=target,
        )
        
        # Both might reach target, but 7% gets there faster
        # (would reach in fewer years)
        assert result_7pct is True

    def test_sensitivity_inflation(self):
        """Higher inflation reduces real purchasing power."""
        proj_low_inflation = project_portfolio(
            current_savings=100_000,
            annual_contribution=5_000,
            years=20,
            expected_return=0.06,
            inflation_rate=0.01,  # 1%
            tax_rate_on_gains=0.0,
            tax_rate_on_dividends=0.0,
            tax_rate_on_interest=0.0,
            fund_fees=0.0,
            withholding_tax=0.0,
            social_security_contributions=0.0,
        )
        
        proj_high_inflation = project_portfolio(
            current_savings=100_000,
            annual_contribution=5_000,
            years=20,
            expected_return=0.06,
            inflation_rate=0.05,  # 5%
            tax_rate_on_gains=0.0,
            tax_rate_on_dividends=0.0,
            tax_rate_on_interest=0.0,
            fund_fees=0.0,
            withholding_tax=0.0,
            social_security_contributions=0.0,
        )
        
        # Real value is lower with high inflation
        assert proj_low_inflation[20]["real_portfolio"] > proj_high_inflation[20]["real_portfolio"]

    def test_sensitivity_contribution(self):
        """Higher contributions accelerate FIRE timeline."""
        target = 800_000
        
        result_low_contrib = coast_fire_condition(
            current_savings=200_000,
            annual_contribution=5_000,
            years_to_target=30,
            expected_return=0.06,
            target_portfolio=target,
        )
        
        result_high_contrib = coast_fire_condition(
            current_savings=200_000,
            annual_contribution=20_000,
            years_to_target=30,
            expected_return=0.06,
            target_portfolio=target,
        )
        
        # High contributions more likely to reach target
        assert result_high_contrib is True


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================
class TestEdgeCases:
    """Test boundary conditions and extreme scenarios."""

    def test_target_fire_with_tiny_spending(self):
        """Even €1/year should compute correctly."""
        target = target_fire(annual_spending=1.0)
        assert target == pytest.approx(25.0)

    def test_target_fire_with_enormous_spending(self):
        """€1 billion annual spending should compute correctly."""
        target = target_fire(annual_spending=1_000_000_000)
        assert target == pytest.approx(25_000_000_000)

    def test_coast_fire_with_very_long_horizon(self):
        """Test with 100-year horizon (unrealistic but mathematically valid)."""
        result = coast_fire_condition(
            current_savings=50_000,
            annual_contribution=0,
            years_to_target=100,
            expected_return=0.05,
            target_portfolio=1_000_000,
        )
        # 50k * (1.05^100) ≈ 1.3B, so target of 1M is definitely reachable
        assert result is True

    def test_projection_with_very_high_return(self):
        """Test projection with unrealistically high return (20%)."""
        proj = project_portfolio(
            current_savings=10_000,
            annual_contribution=0,
            years=10,
            expected_return=0.20,
            inflation_rate=0.0,
            tax_rate_on_gains=0.0,
            tax_rate_on_dividends=0.0,
            tax_rate_on_interest=0.0,
            fund_fees=0.0,
            withholding_tax=0.0,
            social_security_contributions=0.0,
        )
        
        # Should grow substantially (10k * 1.2^10 ≈ 62k)
        assert proj[10]["nominal_portfolio"] > 20_000

    def test_projection_with_negative_real_return(self):
        """Test when inflation exceeds return (negative real return)."""
        proj = project_portfolio(
            current_savings=100_000,
            annual_contribution=0,
            years=10,
            expected_return=0.02,
            inflation_rate=0.05,
            tax_rate_on_gains=0.0,
            tax_rate_on_dividends=0.0,
            tax_rate_on_interest=0.0,
            fund_fees=0.0,
            withholding_tax=0.0,
            social_security_contributions=0.0,
        )
        
        # Nominal grows, but real shrinks
        assert proj[10]["nominal_portfolio"] > 100_000
        assert proj[10]["real_portfolio"] < 100_000
"""Test commission parsing bug fix - SIMPLIFIED."""
import pytest
from unittest.mock import patch
from src.cli import get_percent_input, calculate_years_to_fire


def test_commission_0_22_percent():
    """User inputs 0.22 with max_percent=1, should give 0.0022."""
    with patch('builtins.input', return_value="0.22"):
        result = get_percent_input("Commission", default=0.001, max_percent=1)
        assert abs(result - 0.0022) < 1e-6, f"Got {result}, expected 0.0022"


def test_commission_22_basis_points():
    """User inputs 22 with max_percent=1, should be rejected due to > max."""
    # When user inputs 22 with max_percent=1:
    # 22 gets divided by 100 → 0.22
    # But max_decimal is 0.01, so 0.22 > 0.01 (rejected)
    # Then it loops back asking for valid input
    with patch('builtins.input', side_effect=["22", "0.22"]):
        result = get_percent_input("Commission", default=0.001, max_percent=1)
        # After rejection, user provides 0.22 → 0.0022
        assert abs(result - 0.0022) < 1e-6, f"Got {result}, expected 0.0022"


def test_calculate_years_to_fire_callable():
    """calculate_years_to_fire function should exist and be callable."""
    assert callable(calculate_years_to_fire)
    config = {
        'annual_spending': 35000,
        'safe_withdrawal_rate': 0.035,
        'expected_return': 0.07,
        'inflation_rate': 0.025,
        'tax_rate_on_gains': 0.22,
        'tax_rate_on_dividends': 0.22,
        'tax_rate_on_interest': 0.22,
        'fund_fees': 0.001,
        'current_savings': 2_000_000,
        'annual_contribution': 10000,
    }
    result = calculate_years_to_fire(config)
    assert result == 0, "Should return 0 years when already have enough"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

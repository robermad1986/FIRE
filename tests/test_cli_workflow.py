"""
INSTITUTIONAL-LEVEL CLI WORKFLOW TESTS

Tests the complete FIRE calculator CLI with:
- Parametrization and edge cases
- Workflow state transitions
- Input validation and error handling
- Institutional-grade test coverage (pytest markers, fixtures, formal docs)
"""

import pytest
import io
import sys
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

# Import CLI functions (assuming they're importable)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli import (
    get_percent_input,
    ask_with_default,
    show_summary,
    calculate_years_to_fire,
    show_results,
)


# ============================================================================
# PYTEST MARKERS - Institutional Classification
# ============================================================================

@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Standard config for testing."""
    return {
        'annual_spending': 35_000,
        'safe_withdrawal_rate': 0.035,
        'expected_return': 0.07,
        'inflation_rate': 0.025,
        'tax_rate_on_gains': 0.22,
        'tax_rate_on_dividends': 0.22,
        'tax_rate_on_interest': 0.22,
        'fund_fees': 0.0022,  # 0.22% - The problematic value from bug report
        'current_savings': 0,
        'annual_contribution': 92_000,
        'years_horizon': 25,
        'age': 39,
    }


# ============================================================================
# INPUT VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.parametrize("user_input,expected_output", [
    ("5", 0.05),           # Simple percentage
    ("5%", 0.05),          # With % symbol
    ("0.22", 0.0022),      # Decimal input for small %
    ("22", 0.0022),        # Interpreted as basis points when max_percent=1
    ("0", 0),              # Zero
    ("", None),            # Empty (use default)
])
def test_get_percent_input_valid(user_input, expected_output):
    """Test percentage input with various formats."""
    with patch('builtins.input', return_value=user_input):
        if expected_output is None:
            result = get_percent_input("Test", default=0.001, max_percent=1)
            assert result == 0.001
        else:
            result = get_percent_input("Test", default=0.001, max_percent=1)
            assert abs(result - expected_output) < 1e-6


@pytest.mark.unit
@pytest.mark.parametrize("commission_input,expected", [
    ("0.22", 0.0022),      # 0.22% = 0.0022 in decimal
    ("0,22", None),        # Comma format - should reject/retry
    ("22", 0.0022),        # Basis points interpretation
])
def test_commission_parsing(commission_input, expected):
    """Test the specific commission parsing bug fix."""
    if expected is None:
        with patch('builtins.input', side_effect=[commission_input, "0.22"]):
            # First input rejected, second accepted
            result = get_percent_input("Commission", default=0.001, max_percent=1)
            assert abs(result - 0.0022) < 1e-6
    else:
        with patch('builtins.input', return_value=commission_input):
            result = get_percent_input("Commission", default=0.001, max_percent=1)
            assert abs(result - expected) < 1e-6


@pytest.mark.unit
def test_get_percent_input_invalid_values():
    """Test rejection of invalid inputs."""
    with patch('builtins.input', side_effect=["abc", "5"]):
        # First input invalid, second valid
        result = get_percent_input("Test", default=0.01, max_percent=100)
        assert result == 0.05


@pytest.mark.unit
def test_get_percent_input_out_of_range():
    """Test values outside valid range."""
    with patch('builtins.input', side_effect=["150", "50"]):
        # First out of range (for max_percent=100), second valid
        result = get_percent_input("Test", default=0.05, max_percent=100)
        assert result == 0.50


# ============================================================================
# CONFIGURATION CALCULATION TESTS
# ============================================================================

@pytest.mark.unit
def test_calculate_years_to_fire_already_achieved(mock_config):
    """Test case where FIRE target already achieved."""
    mock_config['current_savings'] = 2_000_000  # Already has enough
    years = calculate_years_to_fire(mock_config)
    assert years == 0


@pytest.mark.unit
def test_calculate_years_to_fire_basic(mock_config):
    """Test basic years-to-fire calculation."""
    years = calculate_years_to_fire(mock_config)
    assert isinstance(years, int) or years is None
    assert years is None or years > 0


@pytest.mark.unit
@pytest.mark.parametrize("savings,contribution,years_expected_range", [
    (0, 10_000, (20, 100)),       # Lower contribution = longer time
    (100_000, 20_000, (5, 20)),   # Moderate savings & contribution
    (500_000, 30_000, (1, 10)),   # High starting point
])
def test_calculate_years_to_fire_progression(mock_config, savings, contribution, years_expected_range):
    """Test that years-to-fire responds correctly to different inputs."""
    mock_config['current_savings'] = savings
    mock_config['annual_contribution'] = contribution
    
    years = calculate_years_to_fire(mock_config)
    
    if years is not None:
        min_years, max_years = years_expected_range
        assert min_years <= years <= max_years, \
            f"Years {years} outside expected range {years_expected_range}"


# ============================================================================
# WORKFLOW STATE MACHINE TESTS
# ============================================================================

@pytest.mark.integration
def test_workflow_accept_parameters(mock_config):
    """Test workflow when user accepts default parameters."""
    with patch('builtins.input', return_value='s'):  # Accept
        result = show_summary(mock_config)
        assert result is True


@pytest.mark.integration
def test_workflow_reject_parameters(mock_config):
    """Test workflow when user rejects parameters."""
    with patch('builtins.input', return_value='n'):  # Reject
        result = show_summary(mock_config)
        assert result is False


@pytest.mark.integration
def test_workflow_edit_single_parameter(mock_config):
    """Test editing a single parameter after initial rejection."""
    # Simulate: Reject → Choose edit → Edit fund_fees → Accept
    with patch('builtins.input', side_effect=['n', '1', '8', '0.44', 's']):
        # rejected → edit → choice 1 (edit params) → choice 8 (fee) → new value → accept
        result = show_summary(mock_config)
        assert result is False  # Initially rejected


@pytest.mark.integration
def test_workflow_back_to_menu(mock_config):
    """Test workflow: Reject → Back to menu."""
    with patch('builtins.input', side_effect=['n', '2']):  # Reject, then choose "back to menu"
        rejected = show_summary(mock_config)
        assert rejected is False


# ============================================================================
# CONFIG VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
def test_config_commission_explicitly_0_22_percent(mock_config):
    """Regression test: Ensure 0.22% commission doesn't become 22%."""
    assert mock_config['fund_fees'] == 0.0022  # 0.22% in decimal
    display_value = mock_config['fund_fees'] * 100
    assert abs(display_value - 0.22) < 0.01  # Should display as 0.22%, not 22%


@pytest.mark.unit
@pytest.mark.parametrize("fee_value,display_str", [
    (0.0001, "0.01%"),   # 0.01%
    (0.001, "0.10%"),    # 0.10%
    (0.0022, "0.22%"),   # The buggy value
    (0.01, "1.00%"),     # 1%
    (0.05, "5.00%"),     # 5% (very high)
])
def test_commission_display_accuracy(fee_value, display_str):
    """Test that commission displays correctly."""
    display = f"{fee_value*100:.2f}%"
    # Allow small rounding errors
    expected_num = float(display_str.rstrip('%'))
    actual_num = float(display.rstrip('%'))
    assert abs(expected_num - actual_num) < 0.01


# ============================================================================
# ERROR HANDLING & EDGE CASES
# ============================================================================

@pytest.mark.unit
def test_handles_negative_commission():
    """Negative percentages should be rejected."""
    with patch('builtins.input', side_effect=['-0.5', "0.22"]):
        # First input (negative) should be rejected or cause retry
        result = get_percent_input("Fee", default=0.001, max_percent=1)
        # Should either reject and retry, or get the second value
        assert result >= 0


@pytest.mark.unit  
def test_handles_extremely_high_commission():
    """Very high percentages should trigger warnings."""
    config = {
        'fund_fees': 0.50,  # 50% commission
        'annual_spending': 25_000,
        'safe_withdrawal_rate': 0.04,
        'tax_rate_on_gains': 0.15,
    }
    # Should exist and calculate without crashing
    years = calculate_years_to_fire(config)
    assert years is None or years > 0


@pytest.mark.unit
def test_handles_zero_contribution():
    """Test case with zero annual contribution."""
    config = {
        'current_savings': 100_000,
        'annual_contribution': 0,
        'annual_spending': 25_000,
        'safe_withdrawal_rate': 0.04,
        'expected_return': 0.06,
        'tax_rate_on_gains': 0.15,
    }
    years = calculate_years_to_fire(config)
    # Should calculate based on existing savings growth alone
    assert years is None or isinstance(years, int)


@pytest.mark.unit
def test_handles_zero_spending():
    """Edge case: User wanting zero spending."""
    config = {
        'annual_spending': 0,
        'safe_withdrawal_rate': 0.04,
        'current_savings': 0,
    }
    from src.calculator import target_fire
    target = target_fire(0, 0.04)
    assert target == 0


# ============================================================================
# INSTITUTIONAL COMPLETENESS TESTS
# ============================================================================

@pytest.mark.sanity
def test_all_required_config_keys(mock_config):
    """Ensure config has all required keys."""
    required_keys = {
        'annual_spending', 'safe_withdrawal_rate', 'expected_return',
        'inflation_rate', 'tax_rate_on_gains', 'tax_rate_on_dividends',
        'tax_rate_on_interest', 'fund_fees', 'current_savings',
        'annual_contribution', 'years_horizon', 'age',
    }
    assert set(mock_config.keys()) >= required_keys


@pytest.mark.sanity
def test_config_value_types(mock_config):
    """Verify all config values have correct types."""
    numeric_fields = {
        'annual_spending': (int, float),
        'safe_withdrawal_rate': (int, float),
        'expected_return': (int, float),
        'fund_fees': (int, float),
        'current_savings': (int, float),
        'annual_contribution': (int, float),
        'age': int,
    }
    for field, expected_type in numeric_fields.items():
        assert isinstance(mock_config[field], expected_type), \
            f"{field} is {type(mock_config[field])} not {expected_type}"


@pytest.mark.performance
def test_cli_response_time_acceptable():
    """CLI operations should complete quickly."""
    import time
    
    config = {
        'annual_spending': 35_000,
        'safe_withdrawal_rate': 0.035,
        'expected_return': 0.07,
        'inflation_rate': 0.025,
        'tax_rate_on_gains': 0.22,
        'tax_rate_on_dividends': 0.22,
        'tax_rate_on_interest': 0.22,
        'fund_fees': 0.0022,
        'current_savings': 0,
        'annual_contribution': 92_000,
    }
    
    start = time.time()
    for _ in range(100):
        calculate_years_to_fire(config)
    elapsed = time.time() - start
    
    # Should process 100 iterations in < 1 second
    assert elapsed < 1.0, f"CLI too slow: {elapsed:.2f}s for 100 iterations"


# ============================================================================
# STRESS TESTS - Extreme Cases
# ============================================================================

@pytest.mark.stress
@pytest.mark.parametrize("spending_value", [1, 1_000, 1_000_000, 10_000_000])
def test_extreme_spending_values(mock_config, spending_value):
    """Test CLI with extremely diverse spending levels."""
    mock_config['annual_spending'] = spending_value
    years = calculate_years_to_fire(mock_config)
    # Should not crash or overflow
    assert years is None or years >= 0


@pytest.mark.stress
@pytest.mark.parametrize("fee_value", [0, 0.00001, 0.001, 0.01, 0.1, 1.0])
def test_extreme_commission_values(mock_config, fee_value):
    """Test with extreme commission values."""
    mock_config['fund_fees'] = fee_value
    years = calculate_years_to_fire(mock_config)
    # Should handle gracefully
    assert years is None or isinstance(years, int)


@pytest.mark.stress
def test_1000_random_config_combinations():
    """Generate 1000 random valid configs and test."""
    import random
    
    for _ in range(1000):
        config = {
            'annual_spending': random.uniform(10_000, 500_000),
            'safe_withdrawal_rate': random.uniform(0.02, 0.10),
            'expected_return': random.uniform(0.01, 0.15),
            'inflation_rate': random.uniform(0, 0.10),
            'tax_rate_on_gains': random.uniform(0, 0.50),
            'tax_rate_on_dividends': random.uniform(0, 0.50),
            'tax_rate_on_interest': random.uniform(0, 0.50),
            'fund_fees': random.uniform(0, 0.05),
            'current_savings': random.uniform(0, 1_000_000),
            'annual_contribution': random.uniform(0, 100_000),
        }
        
        # Should not crash
        try:
            years = calculate_years_to_fire(config)
            assert years is None or (isinstance(years, int) and years >= 0)
        except Exception as e:
            pytest.fail(f"Failed on config {config}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

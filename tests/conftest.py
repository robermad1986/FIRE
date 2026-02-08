"""
Centralized test configuration and fixtures for FIRE calculator test suite.

This module provides:
- Standardized fixtures for calculator inputs
- Realistic FIRE scenarios (Lean, Fat, Balanced)
- Validation helpers for numerical assertions
- Performance benchmarking utilities
- Common test data shared across test modules
"""

import pytest
import math
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


# ============================================================================
# PYTEST MARKERS - Categorize tests for selective execution
# ============================================================================

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (isolated calculator functions)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (multiple functions)"
    )
    config.addinivalue_line(
        "markers", "edge_case: Edge case and boundary condition tests"
    )
    config.addinivalue_line(
        "markers", "stress: Stress/monkey tests with random inputs"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and benchmark tests"
    )
    config.addinivalue_line(
        "markers", "invariant: Tests validating mathematical invariants"
    )
    config.addinivalue_line(
        "markers", "sanity: Quick sanity checks"
    )


# ============================================================================
# REALISTIC SCENARIO FIXTURES
# ============================================================================

@pytest.fixture
def lean_fire_config() -> Dict[str, Any]:
    """
    Lean FIRE scenario fixture.
    
    Parameters:
        Minimal spending, very high savings rate (50%+).
        Goal: Achieve FI with €25,000/year spending.
    """
    return {
        "name": "Lean FIRE",
        "age": 25,
        "current_savings": 800_000,
        "annual_contribution": 8_000,
        "annual_spending": 25_000,
        "expected_return": 0.065,
        "inflation_rate": 0.025,
        "tax_rate_on_gains": 0.22,  # Spain: 20% base
        "tax_rate_on_dividends": 0.19,
        "tax_rate_on_interest": 0.19,
        "fund_fees": 0.003,
        "withholding_tax": 0.15,
        "social_security_contributions": 0.06,
        "years_to_target": 10,
        "safe_withdrawal_rate": 0.04,
    }


@pytest.fixture
def fat_fire_config() -> Dict[str, Any]:
    """
    Fat FIRE scenario fixture.
    
    Parameters:
        Generous spending, modest savings rate (30%).
        Goal: Achieve FI with €80,000/year spending.
    """
    return {
        "name": "Fat FIRE",
        "age": 35,
        "current_savings": 200_000,
        "annual_contribution": 25_000,
        "annual_spending": 80_000,
        "expected_return": 0.065,
        "inflation_rate": 0.025,
        "tax_rate_on_gains": 0.22,
        "tax_rate_on_dividends": 0.19,
        "tax_rate_on_interest": 0.19,
        "fund_fees": 0.003,
        "withholding_tax": 0.15,
        "social_security_contributions": 0.06,
        "years_to_target": 25,
        "safe_withdrawal_rate": 0.04,
    }


@pytest.fixture
def balanced_fire_config() -> Dict[str, Any]:
    """
    Balanced FIRE scenario fixture.
    
    Parameters:
        Moderate spending, healthy savings rate (40%).
        Goal: Achieve FI with €50,000/year spending.
    """
    return {
        "name": "Balanced FIRE",
        "age": 30,
        "current_savings": 150_000,
        "annual_contribution": 15_000,
        "annual_spending": 50_000,
        "expected_return": 0.065,
        "inflation_rate": 0.025,
        "tax_rate_on_gains": 0.22,
        "tax_rate_on_dividends": 0.19,
        "tax_rate_on_interest": 0.19,
        "fund_fees": 0.003,
        "withholding_tax": 0.15,
        "social_security_contributions": 0.06,
        "years_to_target": 20,
        "safe_withdrawal_rate": 0.04,
    }


@pytest.fixture(
    params=[
        pytest.param({"return": 0.01, "label": "Pessimistic (1%)"}, 
                     marks=pytest.mark.sanity),
        pytest.param({"return": 0.05, "label": "Conservative (5%)"}, 
                     marks=pytest.mark.unit),
        pytest.param({"return": 0.065, "label": "Base Case (6.5%)"}, 
                     marks=pytest.mark.unit),
        pytest.param({"return": 0.09, "label": "Optimistic (9%)"}, 
                     marks=pytest.mark.unit),
        pytest.param({"return": 0.15, "label": "Aggressive (15%)"}, 
                     marks=pytest.mark.edge_case),
    ]
)
def market_return_scenarios(request) -> Dict[str, Any]:
    """
    Market return scenarios fixture (parametrized).
    
    Yields:
        Dict with 'return' (float) and 'label' (str) for each scenario.
    """
    return request.param


@pytest.fixture(
    params=[
        pytest.param(0.02, marks=pytest.mark.sanity, id="low_inflation"),
        pytest.param(0.025, marks=pytest.mark.unit, id="normal_inflation"),
        pytest.param(0.04, marks=pytest.mark.unit, id="high_inflation"),
        pytest.param(0.06, marks=pytest.mark.edge_case, id="extreme_inflation"),
    ]
)
def inflation_rate_scenarios(request) -> float:
    """
    Inflation rate scenarios fixture (parametrized).
    
    Yields:
        Float (0.02, 0.025, 0.04, 0.06) for each scenario.
    """
    return request.param


@pytest.fixture(
    params=[
        pytest.param(0.00, marks=pytest.mark.edge_case, id="no_tax"),
        pytest.param(0.10, marks=pytest.mark.unit, id="low_tax"),
        pytest.param(0.20, marks=pytest.mark.unit, id="moderate_tax"),
        pytest.param(0.35, marks=pytest.mark.edge_case, id="high_tax"),
        pytest.param(0.50, marks=pytest.mark.stress, id="extreme_tax"),
    ]
)
def tax_rate_scenarios(request) -> float:
    """
    Tax rate scenarios fixture (parametrized).
    
    Yields:
        Float (0.00 to 0.50) representing tax rates.
    """
    return request.param


# ============================================================================
# NUMERICAL ASSERTION HELPERS
# ============================================================================

class NumericValidator:
    """Helper class for strict numerical validations in tests."""

    @staticmethod
    def assert_valid_percentage(value: float, name: str = "Percentage") -> None:
        """
        Validate that value is a valid percentage (0.0 to 1.0).
        
        Args:
            value: The percentage value to validate
            name: Description of the value for error messages
            
        Raises:
            AssertionError: If value is not in [0.0, 1.0]
        """
        assert isinstance(value, (int, float)), f"{name} must be numeric"
        assert 0.0 <= value <= 1.0, f"{name} must be between 0 and 1, got {value}"

    @staticmethod
    def assert_valid_money(value: float, name: str = "Money", minimum: float = 0) -> None:
        """
        Validate that value represents valid currency amount.
        
        Args:
            value: The currency amount to validate
            name: Description of the value for error messages
            minimum: Minimum acceptable value (default 0)
            
        Raises:
            AssertionError: If value is not valid money
        """
        assert isinstance(value, (int, float)), f"{name} must be numeric"
        assert value >= minimum, f"{name} must be ≥ {minimum}, got {value}"
        assert value == value, f"{name} is NaN"  # NaN check
        assert not math.isinf(value), f"{name} is infinite"

    @staticmethod
    def assert_valid_positive_integer(value: int, name: str = "Integer") -> None:
        """
        Validate that value is a positive integer.
        
        Args:
            value: The integer to validate
            name: Description of the value for error messages
            
        Raises:
            AssertionError: If value is not a positive integer
        """
        assert isinstance(value, int), f"{name} must be integer, got {type(value)}"
        assert value > 0, f"{name} must be > 0, got {value}"

    @staticmethod
    def assert_portfolio_growth(initial: float, final: float, years: int, 
                               min_return: float = -0.10, max_return: float = 0.15) -> None:
        """
        Validate that portfolio growth is within expected range.
        
        Args:
            initial: Starting portfolio value
            final: Ending portfolio value
            years: Number of years for projection
            min_return: Minimum acceptable annual return
            max_return: Maximum acceptable annual return
            
        Raises:
            AssertionError: If growth rate is unrealistic
        """
        if initial <= 0 or final <= 0:
            return  # Skip validation for edge cases
        
        if final < initial:
            implied_return = (final / initial) ** (1 / years) - 1
        else:
            implied_return = (final / initial) ** (1 / years) - 1
        
        # Implied return should be within bounds
        assert min_return <= implied_return <= max_return, \
            f"Implied return {implied_return:.2%} outside [{min_return:.2%}, {max_return:.2%}]"


@pytest.fixture
def numeric_validator() -> NumericValidator:
    """Provide numeric validation helper to tests."""
    return NumericValidator()


# ============================================================================
# COMMON TEST DATA
# ============================================================================

@pytest.fixture
def example_fire_profiles() -> Dict[str, Dict[str, Any]]:
    """
    Load and cache example FIRE profiles from JSON.
    
    Returns:
        Dict mapping profile names to their configurations.
    """
    examples_path = Path(__file__).parent.parent / "examples" / "example_inputs.json"
    if examples_path.exists():
        with open(examples_path) as f:
            return json.load(f)
    return {}


@pytest.fixture
def test_tolerance() -> Dict[str, float]:
    """
    Define numerical tolerances for different types of assertions.
    
    Returns:
        Dict mapping tolerance names to their values:
        - 'strict': 0.1% relative tolerance
        - 'normal': 1% relative tolerance  
        - 'loose': 5% relative tolerance
        - 'very_loose': 10% relative tolerance
    """
    return {
        "strict": 0.001,      # 0.1%
        "normal": 0.01,       # 1%
        "loose": 0.05,        # 5%
        "very_loose": 0.10,   # 10%
    }


@pytest.fixture
def mathematical_constants() -> Dict[str, float]:
    """
    Define mathematical constants used in financial calculations.
    
    Returns:
        Dict with constants like euler number, golden ratio, etc.
    """
    return {
        "e": math.e,
        "pi": math.pi,
        "sqrt_2": math.sqrt(2),
    }


# ============================================================================
# PARAMETRIZATION HELPERS
# ============================================================================

def generate_age_scenarios() -> List[int]:
    """
    Generate meaningful age scenarios for parametrized tests.
    
    Returns:
        List of representative ages: young, working, mid-career, late-career
    """
    return [
        25,  # Young adult, early FIRE
        30,  # Career starter
        35,  # Mid-career
        45,  # Peak earnings
        55,  # Late-career / FIRE-ready
        65,  # Retirement age
    ]


def generate_savings_rate_scenarios() -> List[Tuple[float, str]]:
    """
    Generate meaningful savings rate scenarios.
    
    Returns:
        List of (rate, label) tuples covering 0% to 90% savings rate.
    """
    return [
        (0.00, "No savings"),
        (0.10, "Low (10%)"),
        (0.25, "Moderate (25%)"),
        (0.40, "High (40%)"),
        (0.50, "Very high (50%)"),
        (0.70, "Extreme (70%)"),
        (0.90, "Unrealistic (90%)"),
    ]


@pytest.fixture(
    params=generate_age_scenarios(),
    ids=lambda x: f"age_{x}"
)
def age_scenarios(request) -> int:
    """
    Parametrized fixture for various ages.
    
    Yields:
        Integer representing age: 25, 30, 35, 45, 55, 65
    """
    return request.param


@pytest.fixture(
    params=generate_savings_rate_scenarios(),
    ids=lambda x: f"savings_{int(x[0]*100)}pct"
)
def savings_rate_scenarios(request) -> Tuple[float, str]:
    """
    Parametrized fixture for various savings rates.
    
    Yields:
        Tuple of (rate, label) for savings rates.
    """
    return request.param


# ============================================================================
# PERFORMANCE BENCHMARKING
# ============================================================================

@pytest.fixture
def benchmark_params() -> Dict[str, Any]:
    """
    Define parameters for performance benchmarking.
    
    Returns:
        Dict with benchmark thresholds and configuration.
    """
    return {
        "max_time_seconds": {
            "unit_test": 0.01,        # 10ms per unit test
            "integration_test": 0.1,  # 100ms per integration test
            "complex_calculation": 0.5,  # 500ms for complex calcs
        },
        "iterations": {
            "small": 100,
            "medium": 1000,
            "large": 10000,
        },
    }


# ============================================================================
# VALIDATION DECORATORS
# ============================================================================

def validate_fire_config(config: Dict[str, Any]) -> None:
    """
    Validate that a FIRE config has all required fields.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    required_fields = {
        "age": (int, lambda x: 18 <= x <= 120),
        "current_savings": (float, lambda x: x >= 0),
        "annual_contribution": (float, lambda x: x >= 0),
        "annual_spending": (float, lambda x: x > 0),
        "expected_return": (float, lambda x: -0.5 <= x <= 0.5),
        "inflation_rate": (float, lambda x: -0.1 <= x <= 0.2),
        "safe_withdrawal_rate": (float, lambda x: 0.01 <= x <= 0.10),
    }
    
    for field, (expected_type, validator) in required_fields.items():
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
        
        value = config[field]
        if not isinstance(value, expected_type):
            raise ValueError(f"{field} must be {expected_type}, got {type(value)}")
        
        if not validator(value):
            raise ValueError(f"{field}={value} fails validation")

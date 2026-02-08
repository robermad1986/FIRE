"""
Performance benchmarks for FIRE calculator functions.

These tests measure execution time and ensure that the calculator
maintains acceptable performance standards across various scenarios.

Test Markers:
- @pytest.mark.performance: Performance and benchmark tests
"""

import pytest
import time
from typing import Dict, Any, Callable

from src.calculator import (
    target_fire,
    coast_fire_condition, 
    project_portfolio,
)


class TestCalculatorPerformance:
    """
    Performance benchmarks for calculator functions.
    
    Requirement: All unit functions should complete in < 10ms
    Integration functions should complete in < 100ms
    """

    @pytest.mark.performance
    @pytest.mark.unit
    def test_target_fire_performance(self, benchmark_params: Dict[str, Any]) -> None:
        """
        Test: target_fire() executes in acceptable time.
        
        Requirement: < 10ms per invocation
        """
        # Arrange
        max_time = benchmark_params["max_time_seconds"]["unit_test"]
        iterations = benchmark_params["iterations"]["small"]
        
        # Act - Measure time for multiple iterations
        start_time = time.perf_counter()
        for _ in range(iterations):
            target_fire(annual_spending=50_000, safe_withdrawal_rate=0.04)
        elapsed = time.perf_counter() - start_time
        
        # Assert - Performance requirement
        avg_time = elapsed / iterations
        assert avg_time < max_time, \
            f"target_fire() averaged {avg_time * 1000:.2f}ms, max {max_time * 1000:.1f}ms"

    @pytest.mark.performance
    @pytest.mark.unit
    def test_coast_fire_performance(self, benchmark_params: Dict[str, Any]) -> None:
        """
        Test: coast_fire_condition() executes in acceptable time.
        
        Requirement: < 10ms per invocation
        """
        # Arrange
        max_time = benchmark_params["max_time_seconds"]["unit_test"]
        iterations = benchmark_params["iterations"]["small"]
        
        # Act
        start_time = time.perf_counter()
        for _ in range(iterations):
            coast_fire_condition(
                current_savings=100_000,
                annual_contribution=10_000,
                years_to_target=25,
                expected_return=0.06,
                target_portfolio=2_000_000,
            )
        elapsed = time.perf_counter() - start_time
        
        # Assert
        avg_time = elapsed / iterations
        assert avg_time < max_time, \
            f"coast_fire_condition() averaged {avg_time * 1000:.2f}ms, max {max_time * 1000:.1f}ms"

    @pytest.mark.performance
    @pytest.mark.unit
    def test_project_portfolio_performance(self, benchmark_params: Dict[str, Any]) -> None:
        """
        Test: project_portfolio() executes in acceptable time.
        
        Requirement: < 100ms for 30-year projection
        """
        # Arrange
        max_time = benchmark_params["max_time_seconds"]["complex_calculation"]
        iterations = 10  # Fewer iterations due to complexity
        
        # Act
        start_time = time.perf_counter()
        for _ in range(iterations):
            project_portfolio(
                current_savings=100_000,
                annual_contribution=10_000,
                years=30,  # Complex: 30 years of calculations
                expected_return=0.065,
                inflation_rate=0.025,
                tax_rate_on_gains=0.22,
                tax_rate_on_dividends=0.19,
                tax_rate_on_interest=0.19,
                fund_fees=0.003,
            )
        elapsed = time.perf_counter() - start_time
        
        # Assert
        avg_time = elapsed / iterations
        assert avg_time < max_time, \
            f"project_portfolio(30yr) averaged {avg_time * 1000:.2f}ms, max {max_time * 1000:.1f}ms"

    @pytest.mark.performance
    @pytest.mark.edge_case
    def test_project_portfolio_long_term_performance(
        self, 
        benchmark_params: Dict[str, Any]
    ) -> None:
        """
        Test: project_portfolio() for very long horizons (50 years).
        
        Requirement: < 500ms for 50-year projection
        """
        # Arrange
        max_time = benchmark_params["max_time_seconds"]["complex_calculation"]
        
        # Act - Single 50-year projection
        start_time = time.perf_counter()
        proj = project_portfolio(
            current_savings=100_000,
            annual_contribution=10_000,
            years=50,  # Very long horizon
            expected_return=0.065,
            inflation_rate=0.025,
            tax_rate_on_gains=0.22,
            tax_rate_on_dividends=0.19,
            tax_rate_on_interest=0.19,
            fund_fees=0.003,
        )
        elapsed = time.perf_counter() - start_time
        
        # Assert
        assert elapsed < max_time, \
            f"project_portfolio(50yr) took {elapsed * 1000:.2f}ms, max {max_time * 1000:.1f}ms"
        
        # Assert - Data completeness
        assert len(proj) == 50, "Should have 50 years of data"

    @pytest.mark.performance
    @pytest.mark.integration
    def test_full_workflow_performance(self, benchmark_params: Dict[str, Any]) -> None:
        """
        Test: Complete FIRE workflow (3 functions working together).
        
        Workflow:
        1. Calculate target (target_fire)
        2. Check feasibility (coast_fire_condition)
        3. Project portfolio (project_portfolio)
        
        Requirement: < 500ms total
        """
        # Arrange
        max_time = benchmark_params["max_time_seconds"]["complex_calculation"] * 3
        
        # Act
        start_time = time.perf_counter()
        
        # Step 1: Calculate target
        target = target_fire(annual_spending=50_000, safe_withdrawal_rate=0.04)
        
        # Step 2: Check feasibility
        can_reach = coast_fire_condition(
            current_savings=500_000,
            annual_contribution=20_000,
            years_to_target=20,
            expected_return=0.065,
            target_portfolio=target,
        )
        
        # Step 3: Project portfolio
        proj = project_portfolio(
            current_savings=500_000,
            annual_contribution=20_000,
            years=20,
            expected_return=0.065,
            inflation_rate=0.025,
            tax_rate_on_gains=0.22,
            tax_rate_on_dividends=0.19,
            tax_rate_on_interest=0.19,
            fund_fees=0.003,
        )
        
        elapsed = time.perf_counter() - start_time
        
        # Assert
        assert can_reach is True, "Should reach target"
        assert len(proj) == 20, "Should have 20 years"
        assert elapsed < max_time, \
            f"Full workflow took {elapsed * 1000:.2f}ms, max {max_time * 1000:.1f}ms"


class TestPerformanceScaling:
    """
    Test how performance scales with input size.
    """

    @pytest.mark.performance
    @pytest.mark.edge_case
    def test_project_portfolio_scaling_linear(self) -> None:
        """
        Test: project_portfolio() time should scale roughly linearly with years.
        
        Expected: 30 years ≈ 30x single year, not exponential
        """
        # Arrange - Get baseline for 1 year
        start_1 = time.perf_counter()
        project_portfolio(
            current_savings=100_000,
            annual_contribution=5_000,
            years=1,
            expected_return=0.065,
            inflation_rate=0.025,
        )
        time_1 = time.perf_counter() - start_1
        
        # Arrange - Get time for 30 years
        start_30 = time.perf_counter()
        project_portfolio(
            current_savings=100_000,
            annual_contribution=5_000,
            years=30,
            expected_return=0.065,
            inflation_rate=0.025,
        )
        time_30 = time.perf_counter() - start_30
        
        # Assert - Scaling should be roughly linear (not exponential)
        # Allow for ~40x overhead to account for function call overhead, etc.
        assert time_30 < time_1 * 50, \
            f"Scaling is not linear: 1yr={time_1*1000:.2f}ms, 30yr={time_30*1000:.2f}ms"

"""Test CLI input functions - especially percentage handling for edge cases.

This module tests the CLI input functions to ensure they handle:
- Small percentages (commissions 0.001% to 1%)
- Large percentages (taxes, returns 0% to 100%)
- Various input formats (decimals, percentages with %)
- Edge cases and invalid inputs
"""

import pytest
from unittest.mock import patch
from io import StringIO


# Import the functions we're testing
from src.cli import get_percent_input


class TestGetPercentInput:
    """Test percentage input parsing for both small and large percentages."""
    
    def test_commission_22_bps_input(self):
        """Test: User inputs "22" for 22 basis points = 0.22% commission"""
        with patch('builtins.input', return_value='22'):
            result = get_percent_input("Commission", default=0.001, max_percent=1)
            # 22 >= 1, so divide by 10000 → 0.0022 = 0.22%
            assert abs(result - 0.0022) < 0.00001, f"Expected 0.0022, got {result}"
    
    def test_commission_0_22_percent_input_decimal(self):
        """Test: User inputs "0.22" for 0.22% commission (decimal format)"""
        with patch('builtins.input', return_value='0.22'):
            result = get_percent_input("Commission", default=0.001, max_percent=1)
            # 0.22 < 1, so divide by 100 → 0.0022 = 0.22%
            assert abs(result - 0.0022) < 0.00001, f"Expected 0.0022, got {result}"
    
    def test_commission_0_22_percent_input_explicit_percent(self):
        """Test: User inputs "0.22%" for 0.22% commission explicitly"""
        with patch('builtins.input', return_value='0.22%'):
            result = get_percent_input("Commission", default=0.001, max_percent=1)
            # With %, always divide by 100
            assert abs(result - 0.0022) < 0.00001, f"Expected 0.0022, got {result}"
    
    def test_commission_1_bps_input_decimal(self):
        """Test: User inputs "0.01" for 0.01% (1 basis point, decimal format)"""
        with patch('builtins.input', return_value='0.01'):
            result = get_percent_input("Commission", default=0.001, max_percent=1)
            # 0.01 < 1, so divide by 100 → 0.0001 = 0.01%
            assert abs(result - 0.0001) < 0.00001, f"Expected 0.0001, got {result}"
    
    def test_commission_1_bps_input_basis_points(self):
        """Test: User inputs "1" for 1 basis point"""
        with patch('builtins.input', return_value='1'):
            result = get_percent_input("Commission", default=0.001, max_percent=1)
            # 1 >= 1, so divide by 10000 → 0.0001 = 0.01%
            assert abs(result - 0.0001) < 0.00001, f"Expected 0.0001, got {result}"
    
    def test_normal_percentage_5_input(self):
        """Test: User inputs "5" for 5% (normal percentage)"""
        with patch('builtins.input', return_value='5'):
            result = get_percent_input("Return", default=0.06, max_percent=100)
            # 5 > 1 (threshold for max_percent=100), so divide by 100
            assert abs(result - 0.05) < 0.00001, f"Expected 0.05, got {result}"
    
    def test_normal_percentage_0_05_decimal(self):
        """Test: User inputs "0.05" for 5% (already in decimal)"""
        with patch('builtins.input', return_value='0.05'):
            result = get_percent_input("Return", default=0.06, max_percent=100)
            # 0.05 <= 1 (threshold), so keep as is
            assert abs(result - 0.05) < 0.00001, f"Expected 0.05, got {result}"
    
    def test_normal_percentage_with_explicit_symbol(self):
        """Test: User inputs "5%" explicitly"""
        with patch('builtins.input', return_value='5%'):
            result = get_percent_input("Return", default=0.06, max_percent=100)
            # With %, always divide by 100
            assert abs(result - 0.05) < 0.00001, f"Expected 0.05, got {result}"
    
    def test_commission_default_when_empty(self):
        """Test: User presses ENTER, should use default"""
        with patch('builtins.input', return_value=''):
            result = get_percent_input("Commission", default=0.001, max_percent=1)
            assert abs(result - 0.001) < 0.00001, f"Expected 0.001, got {result}"
    
    def test_commission_accepts_valid_range(self):
        """Test: Commission between 0 and 1% is valid"""
        test_cases = [
            # (input, max_percent, expected_result)
            ('1', 1, 0.0001),          # 1 bps
            ('10', 1, 0.001),          # 10 bps = 0.1%
            ('100', 1, 0.01),          # 100 bps = 1%
            ('0.5', 1, 0.005),         # 0.5% in decimal = 0.005
        ]
        for input_val, max_pct, expected in test_cases:
            with patch('builtins.input', return_value=input_val):
                result = get_percent_input("Commission", default=0.001, max_percent=max_pct)
                assert abs(result - expected) < 0.00001, \
                    f"For input '{input_val}': Expected {expected}, got {result}"
    
    @patch('builtins.input')
    def test_invalid_input_retry(self, mock_input):
        """Test: Invalid input shows error and retries"""
        # First call returns invalid, second call returns valid
        mock_input.side_effect = ['invalid', '5']
        
        with patch('builtins.print') as mock_print:
            result = get_percent_input("Return", default=0.06, max_percent=100)
            assert abs(result - 0.05) < 0.00001
            # Check that error was printed
            error_calls = [call for call in mock_print.call_args_list 
                          if '❌' in str(call)]
            assert len(error_calls) > 0, "Error message should be printed"
    
    def test_commission_exceeds_max_rejected(self):
        """Test: Commission > 1% should be rejected when max_percent=1"""
        with patch('builtins.input', side_effect=['200', '50']):
            # First input (200 bps = 2%) exceeds 1%, should be rejected
            # Second input (50 bps = 0.5%) should work
            with patch('builtins.print'):
                result = get_percent_input("Commission", default=0.001, max_percent=1)
                assert abs(result - 0.005) < 0.00001
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_commission_bug_regression(self, mock_print, mock_input):
        """REGRESSION TEST: 0.22 should be interpreted as 0.22% not 22%
        
        This test ensures the original bug is fixed:
        - User inputs 0.22 for a commission
        - Should be interpreted as 0.22% (0.0022 in decimal)
        - NOT as 22% (0.22 in decimal)
        """
        mock_input.return_value = '0.22'
        result = get_percent_input("Fund Commission", default=0.001, max_percent=1)
        
        # The correct interpretation: 0.22 < 1, so divide by 100 → 0.0022
        assert abs(result - 0.0022) < 0.00001, \
            f"0.22 input should be 0.0022 (0.22%), not 0.22 (22%)"
        
        # Make sure it's not the buggy result
        assert abs(result - 0.22) > 0.001, \
            f"0.22 should NOT be interpreted as 22%"


class TestCommissionWarnings:
    """Test that high commissions trigger appropriate warnings."""
    
    def test_commission_0_22_triggers_warning(self):
        """Test: 0.22% commission should trigger warning"""
        # This would need access to the show_summary function
        # to properly test warning generation
        pass


class TestWorkflowIntegration:
    """Test complete workflow scenarios."""
    
    def test_user_rejects_parameters_can_edit_commission(self):
        """Test: User can edit commission after rejecting parameters"""
        # This is an integration test that would mock the entire workflow
        pass
    
    def test_user_can_navigate_menu(self):
        """Test: User can navigate parameter editing menu"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

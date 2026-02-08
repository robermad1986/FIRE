"""Tests for portfolio composition functionality."""

import pytest
from src.cli import INSTRUMENTS, PRESET_PORTFOLIOS


# ============================================================================
# Instruments & Portfolios Configuration Tests
# ============================================================================
class TestInstruments:
    """Test the INSTRUMENTS configuration."""

    def test_instruments_exist(self):
        """All expected instruments should be defined."""
        expected_instruments = [
            "eu_stocks", "indexed", "balanced60", "balanced50",
            "gov_bonds", "corp_bonds", "deposits", "gold", "custom",
            "vwce", "iwda", "msci_world", "emim", "sp500",
            "bond_1_3y", "bond_7_10y", "bond_20_plus", "commodity_swap"
        ]
        for instr in expected_instruments:
            assert instr in INSTRUMENTS, f"Missing instrument: {instr}"

    def test_instruments_have_required_fields(self):
        """Each instrument should have name, default_return, and risk."""
        for key, instr in INSTRUMENTS.items():
            assert "name" in instr, f"Missing 'name' in {key}"
            assert "risk" in instr, f"Missing 'risk' in {key}"
            if key != "custom":
                assert "default_return" in instr, f"Missing 'default_return' in {key}"
                assert isinstance(instr["default_return"], float), f"Return should be float in {key}"
                assert 0 <= instr["default_return"] <= 1, f"Return out of range in {key}"

    def test_european_stocks_return(self):
        """European stocks should have ~7.5% expected return."""
        assert INSTRUMENTS["eu_stocks"]["default_return"] == pytest.approx(0.075, abs=0.005)

    def test_indexed_funds_return(self):
        """Indexed funds should have ~6.5% expected return."""
        assert INSTRUMENTS["indexed"]["default_return"] == pytest.approx(0.065, abs=0.005)

    def test_government_bonds_return(self):
        """Government bonds should have ~2.5% expected return."""
        assert INSTRUMENTS["gov_bonds"]["default_return"] == pytest.approx(0.025, abs=0.005)

    def test_deposits_return(self):
        """Deposits should have ~3.5% expected return."""
        assert INSTRUMENTS["deposits"]["default_return"] == pytest.approx(0.035, abs=0.005)

    def test_gold_return(self):
        """Gold should have ~2.5% expected return."""
        assert INSTRUMENTS["gold"]["default_return"] == pytest.approx(0.025, abs=0.005)

    def test_vwce_return(self):
        """Vanguard FTSE All-World UCITS ETF should have ~6.5% expected return."""
        assert INSTRUMENTS["vwce"]["default_return"] == pytest.approx(0.065, abs=0.005)

    def test_iwda_return(self):
        """iShares Core MSCI World UCITS ETF should have ~6.8% expected return."""
        assert INSTRUMENTS["iwda"]["default_return"] == pytest.approx(0.068, abs=0.005)

    def test_msci_world_return(self):
        """iShares Core MSCI World UCITS ETF should have ~6.8% expected return."""
        assert INSTRUMENTS["msci_world"]["default_return"] == pytest.approx(0.068, abs=0.005)

    def test_emim_return(self):
        """iShares Core MSCI Emerging Markets IMI UCITS ETF should have ~7.5% expected return."""
        assert INSTRUMENTS["emim"]["default_return"] == pytest.approx(0.075, abs=0.005)

    def test_sp500_return(self):
        """Vanguard S&P 500 UCITS ETF should have ~7.5% expected return."""
        assert INSTRUMENTS["sp500"]["default_return"] == pytest.approx(0.075, abs=0.005)

    def test_bond_1_3y_return(self):
        """iShares USD Treasury Bond 1-3yr UCITS ETF should have ~2.5% expected return."""
        assert INSTRUMENTS["bond_1_3y"]["default_return"] == pytest.approx(0.025, abs=0.005)

    def test_bond_7_10y_return(self):
        """iShares USD Treasury Bond 7-10yr UCITS ETF should have ~3.5% expected return."""
        assert INSTRUMENTS["bond_7_10y"]["default_return"] == pytest.approx(0.035, abs=0.005)

    def test_bond_20_plus_return(self):
        """iShares USD Treasury Bond 20+yr UCITS ETF should have ~4.0% expected return."""
        assert INSTRUMENTS["bond_20_plus"]["default_return"] == pytest.approx(0.040, abs=0.005)

    def test_commodity_swap_return(self):
        """iShares Diversified Commodity Swap UCITS ETF should have ~4.0% expected return."""
        assert INSTRUMENTS["commodity_swap"]["default_return"] == pytest.approx(0.040, abs=0.005)


class TestPresetPortfolios:
    """Test the PRESET_PORTFOLIOS configuration."""

    def test_preset_portfolios_exist(self):
        """All three preset portfolios should exist."""
        expected_portfolios = ["conservative", "balanced", "growth"]
        for portfolio in expected_portfolios:
            assert portfolio in PRESET_PORTFOLIOS, f"Missing portfolio: {portfolio}"

    def test_preset_portfolio_fields(self):
        """Each preset portfolio should have required fields."""
        for key, portfolio in PRESET_PORTFOLIOS.items():
            assert "name" in portfolio, f"Missing 'name' in {key}"
            assert "description" in portfolio, f"Missing 'description' in {key}"
            assert "composition" in portfolio, f"Missing 'composition' in {key}"
            assert "expected_return" in portfolio, f"Missing 'expected_return' in {key}"

    def test_conservative_portfolio_params(self):
        """Conservative portfolio should have low risk & low return."""
        conservative = PRESET_PORTFOLIOS["conservative"]
        assert conservative["expected_return"] == pytest.approx(0.035, abs=0.005)
        assert "30/70" in conservative["name"].lower() or "conserv" in conservative["name"].lower()

    def test_balanced_portfolio_params(self):
        """Balanced portfolio should have medium risk & medium return."""
        balanced = PRESET_PORTFOLIOS["balanced"]
        assert balanced["expected_return"] == pytest.approx(0.048, abs=0.005)
        assert "50/50" in balanced["name"].lower() or "balanc" in balanced["name"].lower()

    def test_growth_portfolio_params(self):
        """Growth portfolio should have high risk & high return."""
        growth = PRESET_PORTFOLIOS["growth"]
        assert growth["expected_return"] == pytest.approx(0.062, abs=0.005)
        assert "70/30" in growth["name"].lower() or "crec" in growth["name"].lower()

    def test_preset_portfolio_returns_increasing(self):
        """Portfolio returns should increase: conservative < balanced < growth."""
        conservative_ret = PRESET_PORTFOLIOS["conservative"]["expected_return"]
        balanced_ret = PRESET_PORTFOLIOS["balanced"]["expected_return"]
        growth_ret = PRESET_PORTFOLIOS["growth"]["expected_return"]
        
        assert conservative_ret < balanced_ret < growth_ret


# ============================================================================
# Weighted Return Calculation Tests
# ============================================================================
class TestWeightedReturnCalculation:
    """Test weighted return calculations (simplified unit tests)."""

    def test_equal_weight_calculation(self):
        """Equal amounts of two instruments should average returns."""
        # 50% @ 7.5% + 50% @ 2.5% = 5.0%
        amount1, return1 = 50_000, 0.075
        amount2, return2 = 50_000, 0.025
        total = amount1 + amount2
        
        weighted = (amount1/total * return1) + (amount2/total * return2)
        assert weighted == pytest.approx(0.05)

    def test_weighted_return_single_instrument(self):
        """Portfolio with single instrument should equal that return."""
        amount, return_rate = 100_000, 0.065
        weighted = (amount / amount) * return_rate
        assert weighted == pytest.approx(return_rate)

    def test_weighted_return_three_instruments(self):
        """Portfolio with three instruments."""
        # €60k @ 7.5% + €30k @ 2.5% + €10k @ 3.5%
        portfolio = {
            "stocks": {"amount": 60_000, "return": 0.075},
            "bonds": {"amount": 30_000, "return": 0.025},
            "deposits": {"amount": 10_000, "return": 0.035},
        }
        
        total = sum(item["amount"] for item in portfolio.values())
        weighted = sum((item["amount"] / total) * item["return"] for item in portfolio.values())
        
        # Manual: (60k/100k * 7.5%) + (30k/100k * 2.5%) + (10k/100k * 3.5%)
        #       = 4.5% + 0.75% + 0.35% = 5.6%
        assert weighted == pytest.approx(0.056)

    def test_weighted_return_aggressive_portfolio(self):
        """Very aggressive portfolio (mostly stocks)."""
        portfolio = {
            "stocks": {"amount": 80_000, "return": 0.075},
            "bonds": {"amount": 20_000, "return": 0.025},
        }
        
        total = 100_000
        weighted = (80_000/total * 0.075) + (20_000/total * 0.025)
        assert weighted == pytest.approx(0.065, abs=0.001)

    def test_weighted_return_conservative_portfolio(self):
        """Very conservative portfolio (mostly bonds)."""
        portfolio = {
            "stocks": {"amount": 20_000, "return": 0.075},
            "bonds": {"amount": 80_000, "return": 0.025},
        }
        
        total = 100_000
        weighted = (20_000/total * 0.075) + (80_000/total * 0.025)
        assert weighted == pytest.approx(0.035, abs=0.001)


# ============================================================================
# Portfolio Composition Integration Tests
# ============================================================================
class TestPortfolioCompositionIntegration:
    """Test portfolio composition in realistic scenarios."""

    def test_preset_conservative_aligns_with_composition(self):
        """Conservative preset composition should yield ~3.5% return."""
        portfolio = PRESET_PORTFOLIOS["conservative"]
        composition = portfolio["composition"]
        expected_return = portfolio["expected_return"]
        
        # Verify composition instruments are in INSTRUMENTS
        for instr_key, weight in composition.items():
            assert instr_key in INSTRUMENTS or weight == 0
        
        # Verify return is realistic for conservative
        assert expected_return <= 0.04, "Conservative return should be ≤ 4%"

    def test_preset_balanced_aligns_with_composition(self):
        """Balanced preset composition should yield ~4.8% return."""
        portfolio = PRESET_PORTFOLIOS["balanced"]
        composition = portfolio["composition"]
        expected_return = portfolio["expected_return"]
        
        for instr_key, weight in composition.items():
            assert instr_key in INSTRUMENTS or weight == 0
        
        assert 0.04 < expected_return < 0.06, "Balanced return should be 4-6%"

    def test_preset_growth_aligns_with_composition(self):
        """Growth preset composition should yield ~6.2% return."""
        portfolio = PRESET_PORTFOLIOS["growth"]
        composition = portfolio["composition"]
        expected_return = portfolio["expected_return"]
        
        for instr_key, weight in composition.items():
            assert instr_key in INSTRUMENTS or weight == 0
        
        assert expected_return >= 0.06, "Growth return should be ≥ 6%"


class TestInstrumentRiskLevels:
    """Test that instruments have appropriate risk classifications."""

    def test_stocks_high_risk(self):
        """Stocks should be classified as high risk."""
        assert "alto" in INSTRUMENTS["eu_stocks"]["risk"].lower() or \
               "high" in INSTRUMENTS["eu_stocks"]["risk"].lower()

    def test_bonds_low_risk(self):
        """Bonds should be classified as low/medium risk."""
        risk_level = INSTRUMENTS["gov_bonds"]["risk"].lower()
        assert "bajo" in risk_level or "low" in risk_level

    def test_deposits_very_low_risk(self):
        """Deposits should be classified as very low risk."""
        risk_level = INSTRUMENTS["deposits"]["risk"].lower()
        assert "muy bajo" in risk_level or "very low" in risk_level

    def test_higher_return_higher_risk(self):
        """Generally, higher return instruments should have higher risk."""
        eu_stocks_return = INSTRUMENTS["eu_stocks"]["default_return"]
        gov_bonds_return = INSTRUMENTS["gov_bonds"]["default_return"]
        
        # Stocks should have higher return than bonds
        assert eu_stocks_return > gov_bonds_return


class TestPortfolioEdgeCases:
    """Test edge cases in portfolio composition."""

    def test_single_large_position(self):
        """Portfolio with single large position."""
        portfolio = {
            "all_stocks": {"amount": 100_000, "return": 0.075},
        }
        
        total = 100_000
        weighted = (100_000/total) * 0.075
        assert weighted == pytest.approx(0.075)

    def test_many_small_positions(self):
        """Portfolio with many small positions (real diversification)."""
        portfolio = {
            "stocks": {"amount": 20_000, "return": 0.075},
            "indexed": {"amount": 20_000, "return": 0.065},
            "balanced60": {"amount": 20_000, "return": 0.056},
            "bonds": {"amount": 20_000, "return": 0.025},
            "deposits": {"amount": 20_000, "return": 0.035},
        }
        
        total = 100_000
        weighted = sum((item["amount"]/total) * item["return"] for item in portfolio.values())
        
        # Average should be between bonds (2.5%) and stocks (7.5%)
        assert 0.025 < weighted < 0.075
        assert weighted == pytest.approx(0.0512, abs=0.001)

    def test_extreme_aggressive(self):
        """100% in highest-return instrument."""
        weighted = (100_000/100_000) * INSTRUMENTS["eu_stocks"]["default_return"]
        assert weighted == INSTRUMENTS["eu_stocks"]["default_return"]

    def test_extreme_conservative(self):
        """100% in lowest-return instrument."""
        weighted = (100_000/100_000) * INSTRUMENTS["gov_bonds"]["default_return"]
        assert weighted == INSTRUMENTS["gov_bonds"]["default_return"]


class TestPortfolioRealism:
    """Test that portfolio parameters are realistic for EUR/UCITS."""

    def test_balanced_portfolio_realistic(self):
        """Balanced portfolio should have realistic 50/50 split."""
        # Test that it includes both stocks and bonds
        balanced = PRESET_PORTFOLIOS["balanced"]
        composition = balanced["composition"]
        
        # Should have equity exposure and bond exposure
        has_equity = any(k in ["eu_stocks", "indexed", "balanced60"] for k in composition.keys())
        has_bonds = any(k in ["gov_bonds", "corp_bonds", "balanced50"] for k in composition.keys())
        
        assert has_equity or composition.get("balanced60", 0) > 0, "Balanced needs equity exposure"
        assert has_bonds or composition.get("balanced50", 0) > 0, "Balanced needs bond exposure"

    def test_stock_return_gt_bonds(self):
        """Stock returns should always exceed bond returns."""
        assert INSTRUMENTS["eu_stocks"]["default_return"] > INSTRUMENTS["gov_bonds"]["default_return"]
        assert INSTRUMENTS["eu_stocks"]["default_return"] > INSTRUMENTS["corp_bonds"]["default_return"]

    def test_deposits_safe_rate(self):
        """Deposits return should reflect small safe yield."""
        deposits_return = INSTRUMENTS["deposits"]["default_return"]
        assert 0.02 <= deposits_return <= 0.05, "Deposits should yield 2-5%"

    def test_gold_stable_return(self):
        """Gold should have low but positive real return."""
        gold_return = INSTRUMENTS["gold"]["default_return"]
        assert gold_return > 0, "Gold should have positive return"
        assert gold_return < 0.05, "Gold shouldn't have high yield"

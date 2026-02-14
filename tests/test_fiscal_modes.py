"""Tests for fiscal mode drag helper."""

from src.fiscal_modes import (
    FISCAL_MODE_ES_TAXPACK,
    FISCAL_MODE_INTL_BASIC,
    get_effective_fiscal_drag,
)


def test_es_taxpack_drag_keeps_existing_behavior():
    drag = get_effective_fiscal_drag(
        regimen_fiscal="España - Fondos de Inversión",
        include_optimization=False,
        fiscal_mode=FISCAL_MODE_ES_TAXPACK,
    )
    assert drag == 0.003


def test_es_taxpack_optimization_reduces_drag():
    base = get_effective_fiscal_drag(
        regimen_fiscal="España - Fondos de Inversión",
        include_optimization=False,
        fiscal_mode=FISCAL_MODE_ES_TAXPACK,
    )
    opt = get_effective_fiscal_drag(
        regimen_fiscal="España - Fondos de Inversión",
        include_optimization=True,
        fiscal_mode=FISCAL_MODE_ES_TAXPACK,
    )
    assert opt < base


def test_intl_basic_drag_uses_manual_rates():
    drag = get_effective_fiscal_drag(
        regimen_fiscal="Otro",
        include_optimization=False,
        fiscal_mode=FISCAL_MODE_INTL_BASIC,
        intl_tax_rates={"gains": 0.2, "dividends": 0.2, "interest": 0.2, "wealth": 0.01},
    )
    # 7% assumed taxable return base * 20% weighted rate + 1% wealth = 2.4% drag.
    assert abs(drag - 0.024) < 1e-9

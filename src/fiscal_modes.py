"""Helpers for fiscal mode behavior in web/CLI orchestration."""

from typing import Dict, Optional


FISCAL_MODE_ES_TAXPACK = "ES_TAXPACK"
FISCAL_MODE_INTL_BASIC = "INTL_BASIC"
INTL_BASIC_ASSUMED_TAXABLE_RETURN_BASE = 0.07


def get_effective_fiscal_drag(
    regimen_fiscal: str,
    include_optimization: bool = False,
    fiscal_mode: str = FISCAL_MODE_ES_TAXPACK,
    intl_tax_rates: Optional[Dict[str, float]] = None,
) -> float:
    """Approximate annual return drag from taxes/frictions.

    - ES_TAXPACK: maintains current behavior by fiscal regime.
    - INTL_BASIC: uses manual effective rates as an approximation.
    """
    if fiscal_mode == FISCAL_MODE_INTL_BASIC:
        rates = intl_tax_rates or {}
        gains = max(0.0, min(1.0, float(rates.get("gains", 0.10))))
        dividends = max(0.0, min(1.0, float(rates.get("dividends", 0.15))))
        interest = max(0.0, min(1.0, float(rates.get("interest", 0.20))))
        wealth = max(0.0, min(1.0, float(rates.get("wealth", 0.00))))

        weighted_effective_tax_rate = (0.55 * gains) + (0.25 * dividends) + (0.20 * interest)
        # Apply tax rate to an assumed annual taxable return base (7%), then add wealth tax drag.
        tax_drag_from_returns = INTL_BASIC_ASSUMED_TAXABLE_RETURN_BASE * weighted_effective_tax_rate
        return max(0.0, tax_drag_from_returns + wealth)

    base_drag = {
        "España - Fondos de Inversión": 0.003,
        "España - Cartera Directa": 0.012,
        "Otro": 0.008,
    }.get(regimen_fiscal, 0.008)

    if include_optimization and regimen_fiscal == "España - Fondos de Inversión":
        base_drag = max(0.0, base_drag - 0.0015)

    return base_drag

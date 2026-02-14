"""
FIRE Web Application - Financial Independence Calculator
=========================================================

IMPROVED EXECUTIVE PROMPT IMPLEMENTATION
Incorporates refinements to address:
  1. Explicit dependency interfaces from src/calculator.py
  2. Streamlit session state management (cache vs session_state separation)
  3. Detailed sensitivity matrix specification (5x5, color-coded)
  4. PDF export with comprehensive structure
  5. Complete input validation ruleset
  6. Color scheme + multiversion support (future)
  7. Edge case tax treatment

Architecture:
  - Presentation Layer: Streamlit UI (this module)
  - Orchestration Layer: Calculation pipeline with caching
  - Domain Layer: src/calculator.py (FIRE mathematics, black-box)
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Tuple, List, Optional, Any
import inspect
from datetime import datetime
import warnings
import json
import re

# Black-box import from domain layer
from src.calculator import (
    target_fire,
    calculate_net_worth,
)
from src.tax_engine import (
    load_tax_pack,
    list_available_taxpack_years,
    get_region_options,
    calculate_general_tax_with_details,
    calculate_savings_tax_with_details,
    calculate_wealth_taxes_with_details,
    validate_tax_pack_metadata,
)
from src.simulation_models import (
    monte_carlo_normal,
    monte_carlo_bootstrap,
    backtest_rolling_windows,
    load_historical_annual_returns,
    load_historical_annual_series,
)
from src.real_estate_model import compute_effective_housing_and_rental_flows
from src.retirement_models import (
    calculate_effective_public_pension_annual,
    estimate_retirement_tax_context as estimate_retirement_tax_context_core,
    estimate_auto_taxable_withdrawal_ratio as estimate_auto_taxable_withdrawal_ratio_core,
    build_decumulation_table_two_stage_schedule as build_decumulation_table_two_stage_schedule_core,
)
from src.profile_io import serialize_profile, deserialize_profile
from src.fiscal_modes import (
    FISCAL_MODE_ES_TAXPACK,
    FISCAL_MODE_INTL_BASIC,
    get_effective_fiscal_drag,
)

warnings.filterwarnings("ignore")

# =====================================================================
# CONFIGURATION & CONSTANTS
# =====================================================================

PAGE_CONFIG = {
    "page_title": "Calculadora FIRE | Calculadora de Independencia Financiera",
    "page_icon": "📈",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

COLOR_SCHEME = {
    "primary": "#1f77b4",      # Blue
    "success": "#2ecc71",       # Green
    "warning": "#f39c12",       # Orange
    "danger": "#e74c3c",        # Red
    "neutral": "#95a5a6",       # Gray
    "background": "#f8f9fa",
}

WEB_PROFILES = {
    "Personalizado": None,
    "Lean FIRE": {"gastos_anuales": 25_000, "rentabilidad_esperada": 0.06, "inflacion": 0.02, "safe_withdrawal_rate": 0.04},
    "Fat FIRE": {"gastos_anuales": 75_000, "rentabilidad_esperada": 0.07, "inflacion": 0.02, "safe_withdrawal_rate": 0.04},
    "Coast FIRE": {"gastos_anuales": 40_000, "rentabilidad_esperada": 0.065, "inflacion": 0.02, "safe_withdrawal_rate": 0.04},
    "Barista FIRE": {"gastos_anuales": 50_000, "rentabilidad_esperada": 0.055, "inflacion": 0.02, "safe_withdrawal_rate": 0.04},
    "UCITS Tax Efficient": {"gastos_anuales": 45_000, "rentabilidad_esperada": 0.06, "inflacion": 0.02, "safe_withdrawal_rate": 0.04},
    "Spain FIT": {"gastos_anuales": 40_000, "rentabilidad_esperada": 0.065, "inflacion": 0.02, "safe_withdrawal_rate": 0.04},
}

# =====================================================================
# 1. PAGE SETUP & INITIALIZATION
# =====================================================================

st.set_page_config(**PAGE_CONFIG)

# Custom CSS for improved styling
st.markdown("""
<style>
    /* Main background */
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    
    /* KPI styling */
    .kpi-success { border-left-color: #2ecc71 !important; }
    .kpi-warning { border-left-color: #f39c12 !important; }
    .kpi-danger { border-left-color: #e74c3c !important; }
    
    /* Form labels */
    label {
        font-weight: 600;
        color: #2c3e50;
    }

    @media (prefers-color-scheme: dark) {
        .stMetric {
            background-color: #1f2430 !important;
            border-left-color: #4da3ff !important;
            color: #e6edf3 !important;
        }
        [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
            color: #e6edf3 !important;
        }
    }

    @media (max-width: 768px) {
        .stMetric {
            padding: 10px !important;
            border-left-width: 3px !important;
            border-radius: 10px !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.9rem !important;
            line-height: 1.2rem !important;
        }
    }

    .ab-compare-shell {
        border: 1px solid rgba(31, 119, 180, 0.25);
        border-radius: 12px;
        padding: 14px;
        margin-top: 6px;
        background: rgba(31, 119, 180, 0.03);
    }
    .ab-compare-title {
        font-weight: 700;
        margin-bottom: 8px;
    }
    .ab-compare-caption {
        color: #556070;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    .ab-compare-insight {
        border-radius: 10px;
        padding: 10px 12px;
        margin-top: 8px;
        background: rgba(46, 204, 113, 0.12);
        border: 1px solid rgba(46, 204, 113, 0.35);
    }
    .ab-compare-insight.warn {
        background: rgba(243, 156, 18, 0.12);
        border: 1px solid rgba(243, 156, 18, 0.35);
    }
    .ab-compare-insight.danger {
        background: rgba(231, 76, 60, 0.12);
        border: 1px solid rgba(231, 76, 60, 0.35);
    }

    @media (prefers-color-scheme: dark) {
        .ab-compare-shell {
            background: rgba(77, 163, 255, 0.09);
            border-color: rgba(77, 163, 255, 0.38);
        }
        .ab-compare-caption {
            color: #c1ccd7;
        }
        .ab-compare-insight {
            color: #dbe6ee;
            background: rgba(46, 204, 113, 0.18);
            border-color: rgba(46, 204, 113, 0.45);
        }
        .ab-compare-insight.warn {
            background: rgba(243, 156, 18, 0.18);
            border-color: rgba(243, 156, 18, 0.45);
        }
        .ab-compare-insight.danger {
            background: rgba(231, 76, 60, 0.18);
            border-color: rgba(231, 76, 60, 0.45);
        }
    }

    @media (max-width: 768px) {
        .ab-compare-shell {
            padding: 10px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "initial_load" not in st.session_state:
    st.session_state.initial_load = True
    st.session_state.cached_results = None


def render_plotly_chart(fig, key: Optional[str] = None) -> None:
    """Render Plotly chart with Streamlit-version-safe width handling."""
    plotly_sig = inspect.signature(st.plotly_chart)
    if "width" in plotly_sig.parameters:
        st.plotly_chart(fig, width="stretch", config={"responsive": True}, key=key)
    else:
        st.plotly_chart(fig, use_container_width=True, config={"responsive": True}, key=key)

# =====================================================================
# 2. VALIDATION & ERROR HANDLING
# =====================================================================

class ValidationError(Exception):
    """Custom validation error with user-friendly messages"""
    pass


# =====================================================================
# DYNAMIC INSPIRATIONAL TEXT GENERATION
# =====================================================================

def generate_fire_readiness_message(
    years_to_fire: Optional[int],
    years_horizon: int,
) -> Tuple[str, str]:
    """
    Generate inspirational message based on FIRE timeline readiness.
    
    Returns: (emoji, message)
    """
    if years_to_fire is None:
        return "🧱", (
            "Con los parámetros actuales, la mediana de escenarios no alcanza FIRE "
            f"en tu horizonte ({years_horizon} años). No significa imposible, pero sí "
            "que necesitas ajustar aportaciones, gasto objetivo o plazo."
        )

    diff = years_to_fire - years_horizon
    
    if years_to_fire <= 5:
        return "🚀", (
            "Estás en la recta final. Con los parámetros actuales, FIRE "
            "aparece en un plazo corto."
        )
    elif years_to_fire <= 10:
        return "🌟", (
            "Escenario favorable: podrías alcanzar FIRE en menos de 10 años "
            "si mantienes el plan actual."
        )
    elif years_to_fire <= 15:
        return "⚡", (
            "Tu objetivo FIRE está dentro de un horizonte razonable "
            "(alrededor de 15 años)."
        )
    elif years_to_fire <= 20:
        return "📈", (
            "Buen progreso. El objetivo es alcanzable con constancia en ahorro "
            "y revisiones periódicas."
        )
    elif years_to_fire <= 25:
        return "🎯", (
            "El plan es exigente pero viable. Mejoras moderadas en ahorro o "
            "rentabilidad pueden reducir varios años."
        )
    elif years_to_fire <= 30:
        return "🔥", (
            "El horizonte es largo (cerca de 30 años). El efecto del interés "
            "compuesto sigue siendo una ventaja importante."
        )
    else:
        return "💪", (
            "Con los supuestos actuales el plazo es alto. Conviene revisar "
            "aportaciones, gasto objetivo y horizonte."
        )


def generate_success_probability_message(success_rate: float) -> Tuple[str, str]:
    """
    Generate message based on Monte Carlo success probability.
    
    Returns: (emoji, message)
    """
    if success_rate >= 95:
        return "✅", (
            "Probabilidad muy alta. El plan es robusto frente a variaciones "
            "de mercado en este modelo."
        )
    elif success_rate >= 85:
        return "👍", (
            "Probabilidad alta. El plan tiene un margen razonable de seguridad."
        )
    elif success_rate >= 75:
        return "⚖️", (
            "Probabilidad aceptable. Pequeños ajustes pueden mejorar la solidez "
            "del plan."
        )
    elif success_rate >= 60:
        return "⚠️", (
            "Riesgo moderado. Conviene revisar supuestos y plantear un margen "
            "de seguridad adicional."
        )
    else:
        return "🔴", (
            "Riesgo alto. El plan depende de escenarios optimistas; se recomienda "
            "revisar ahorro, gasto objetivo o plazo."
        )


def generate_savings_velocity_message(monthly_contribution: float, annual_spending: float) -> Tuple[str, str]:
    """
    Generate message about savings rate and velocity.
    
    Returns: (emoji, message)
    """
    annual_savings = monthly_contribution * 12
    
    if annual_savings == 0:
        return "📉", (
            "Sin aportaciones mensuales, dependerás 100% del crecimiento del capital inicial. "
            "Incluso pequeñas aportaciones (€100/mes) aceleraran tu FIRE significativamente."
        )
    elif annual_savings <= annual_spending * 0.1:
        return "🐢", (
            "Ritmo lento: Tu ahorro anual es <10% del gasto. El crecimiento será gradual. "
            "Aumentar aportaciones a €500-1k/mes cambiaría dramáticamente tu timeline."
        )
    elif annual_savings <= annual_spending * 0.3:
        return "🚴", (
            "Ritmo moderado: Ahorras 10-30% de tu gasto anual. Buen balance entre vivir hoy "
            "y preparar el futuro. Sigue así."
        )
    elif annual_savings <= annual_spending * 0.6:
        return "🚗", (
            "Ritmo acelerado: ahorras entre el 30% y el 60% del gasto objetivo. "
            "Es un nivel sólido para acortar plazos."
        )
    else:
        return "🏎️", (
            "Ritmo muy alto: ahorras más de lo que gastas. En general, este patrón "
            "acelera de forma notable el objetivo FIRE."
        )


def generate_horizon_comparison_message(
    years_to_fire: Optional[int],
    years_horizon: int,
) -> str:
    """
    Generate contextual message comparing FIRE timeline to user's horizon.
    """
    if years_to_fire is None:
        return (
            f"🧭 Con el escenario base, FIRE no se alcanza en {years_horizon} años. "
            "Prioriza cambios de alto impacto: subir ahorro mensual, reducir gasto FIRE "
            "objetivo, o extender horizonte."
        )

    diff = years_to_fire - years_horizon
    
    if diff <= -5:
        return (
            f"Vas por delante del plan: FIRE llegaría {abs(diff)} años antes "
            f"de la fecha objetivo."
        )
    elif diff < 0:
        return (
            f"Escenario adelantado: FIRE llegaría {abs(diff)} años antes "
            f"de tu objetivo."
        )
    elif diff == 0:
        return (
            "Tu objetivo FIRE coincide con la fecha objetivo marcada."
        )
    elif diff <= 2:
        return (
            f"📅 Muy cercano: Alcanzarás FIRE solo {diff} años después de tu objetivo. "
            f"Pequeños ajustes pueden mover la aguja: aumentar ahorros {diff*5}% o reducir gastos un 2-3%."
        )
    elif diff <= 5:
        return (
            f"🤔 Brecha moderada: {diff} años de diferencia con tu objetivo inicial. "
            f"Revisa si puedes: (1) aumentar contribuciones, (2) mejorar retorno esperado, "
            f"o (3) ajustar expectativas de gasto en jubilación."
        )
    else:
        return (
            f"💭 Brecha significativa: {diff} años más allá de tu objetivo inicial. "
            f"Tu plan requiere revisión. Considera: extender horizonte, aumentar ahorros drásticamente, "
            f"o reducir gastos de jubilación esperados."
        )


def generate_market_scenario_message(base_return: float, volatility: float) -> str:
    """
    Generate message about market assumptions and risk.
    """
    if volatility >= 0.20:
        return (
            f"Volatilidad alta ({volatility*100:.0f}% anual). Es esperable ver "
            f"oscilaciones amplias en años negativos."
        )
    elif volatility >= 0.15:
        return (
            f"Volatilidad moderada-alta ({volatility*100:.0f}%). Puede ofrecer "
            f"crecimiento a largo plazo, con años de caídas relevantes."
        )
    elif volatility >= 0.10:
        return (
            f"Volatilidad moderada ({volatility*100:.0f}%). Compromiso razonable "
            f"entre crecimiento y estabilidad."
        )
    else:
        return (
            f"Volatilidad baja ({volatility*100:.0f}%). Perfil más estable, aunque "
            f"con potencial de crecimiento menor."
        )


def validate_inputs(params: Dict) -> Tuple[bool, List[str]]:
    """
    Validate all input parameters against defined rules.
    Returns (is_valid, error_messages)
    """
    errors = []
    warnings = []

    # Age consistency check
    if params["edad_actual"] >= params["edad_objetivo"]:
        errors.append("❌ Edad objetivo debe ser mayor que edad actual")

    # Patrimonio vs gastos sanity check
    annual_burn = params["gastos_anuales"]
    if params["patrimonio_inicial"] > 0:
        burn_ratio = annual_burn / params["patrimonio_inicial"]
        if burn_ratio > 0.5:
            warnings.append(
                f"⚠️  Gastos anuales (€{annual_burn:,.0f}) representan {burn_ratio*100:.1f}% "
                f"de patrimonio actual. Objetivo FIRE podría no ser alcanzable."
            )

    # Initial wealth too low for sustainable FIRE
    years_horizon = params["edad_objetivo"] - params["edad_actual"]
    swr = params["safe_withdrawal_rate"]
    required_portfolio = annual_burn / swr
    if (
        params["aportacion_mensual"] == 0
        and params["patrimonio_inicial"] < required_portfolio * 0.3
    ):
        warnings.append(
            f"⚠️  Sin aportaciones mensuales, alcanzar portafolio FIRE "
            f"(€{required_portfolio:,.0f}) en {years_horizon} años requiere "
            f"rentabilidad anual >{(required_portfolio/max(params['patrimonio_inicial'], 1))**(1/years_horizon) - 1:.1%}, "
            f"superior a expectativas mostradas."
        )

    # Contribution sustainability check
    max_monthly = 50_000
    if params["aportacion_mensual"] > max_monthly:
        errors.append(f"❌ Aportación mensual máxima: €{max_monthly:,.0f}")

    pension_start_age = params.get("edad_inicio_pension_publica", params.get("edad_pension_oficial", 67))
    if params.get("two_stage_retirement_model") and pension_start_age < params["edad_objetivo"]:
        warnings.append(
            "⚠️  Edad de inicio de pensión menor que edad objetivo FIRE. El tramo pre-pensión quedará en 0 años."
        )

    return len(errors) == 0, errors + warnings


def render_plain_language_overview() -> None:
    """Show an easy-to-understand explanation of what the app does."""
    st.subheader("🧭 ¿Qué hace esta calculadora?")
    st.markdown(
        "Esta calculadora convierte tus decisiones de hoy en una historia financiera plausible para los "
        "próximos años. Primero toma tu punto de partida (patrimonio, aportaciones, edad y gasto esperado), "
        "después proyecta miles de trayectorias de mercado con inflación y fiscalidad, y finalmente te muestra "
        "qué tan probable es alcanzar tu objetivo FIRE y en qué plazos podrías hacerlo."
    )
    with st.expander("Ejemplo rápido (lenguaje simple)", expanded=False):
        st.write(
            "Si indicas que tienes €100.000 y ahorras €1.000/mes, el simulador prueba muchos "
            "escenarios de mercado. Luego te dice, por ejemplo, en cuántos años podrías llegar "
            "a tu objetivo y con qué probabilidad."
        )


def render_active_context_summary(params: Dict) -> None:
    """Render a unified narrative block for active simulation context."""
    base_name = (
        "capital invertible ampliado"
        if params.get("usar_capital_invertible_ampliado")
        else "cartera líquida"
    )
    base_explanation = (
        "cartera líquida + inmuebles invertibles netos - otras deudas"
        if params.get("usar_capital_invertible_ampliado")
        else "solo cartera líquida"
    )
    fiscal_focus = "jubilación" if params.get("fiscal_priority") == "Jubilación" else "acumulación"
    fiscal_sentence = (
        "El objetivo FIRE se ajusta para aproximar impuestos durante la retirada de capital."
        if fiscal_focus == "jubilación"
        else "La simulación prioriza la fiscalidad durante los años previos a FIRE."
    )
    renta_efectiva = params.get("renta_neta_alquiler_anual_efectiva", 0.0)
    renta_bruta_base = params.get("renta_bruta_alquiler_anual_efectiva", 0.0)
    cuota_hipotecas_mensual = params.get("cuota_total_hipotecas_mensual_efectiva", 0.0)
    ahorro_vivienda_efectivo = params.get("ahorro_vivienda_habitual_anual_efectivo", 0.0)
    renta_sentence = ""
    if renta_efectiva > 0:
        renta_sentence = f" También se está considerando una renta por alquiler de **€{renta_efectiva:,.0f}/año**."
        if abs(renta_bruta_base - renta_efectiva) > 1:
            renta_sentence += (
                f" (Bruta declarada: €{renta_bruta_base:,.0f}/año; ajustada por vacancia/gastos/fiscalidad simple)."
            )
    vivienda_sentence = ""
    if ahorro_vivienda_efectivo > 0:
        vivienda_sentence = (
            f" Además, se descuenta un ahorro anual por vivienda habitual de **€{ahorro_vivienda_efectivo:,.0f}** "
            "al calcular el gasto que debe cubrir la cartera."
        )
    hipoteca_sentence = ""
    if cuota_hipotecas_mensual > 0:
        hipoteca_sentence = (
            f" Las cuotas hipotecarias activas restan **€{cuota_hipotecas_mensual:,.0f}/mes** "
            "a la capacidad de ahorro durante la fase de acumulación."
        )

    st.markdown(
        "### 📘 Contexto del escenario activo\n"
        f"En esta ejecución, la simulación arranca desde **{base_name}** "
        f"(base usada: **€{params.get('patrimonio_base_simulacion', params['patrimonio_inicial']):,.0f}**, "
        f"{base_explanation}; la vivienda habitual se mantiene fuera de esta base). "
        f"Además, el enfoque fiscal está orientado a **{fiscal_focus}**: "
        f"{fiscal_sentence}{renta_sentence}{vivienda_sentence}{hipoteca_sentence}"
    )


def render_simple_result_summary(simulation_results: Dict, params: Dict) -> None:
    """Show a plain-language summary for non-professional users."""
    fire_target = get_display_fire_target(simulation_results, params)
    years_horizon = params["edad_objetivo"] - params["edad_actual"]
    years_to_fire = find_years_to_fire(simulation_results["real_percentile_50"], fire_target)
    success_rate = simulation_results["success_rate_final"]

    if years_to_fire is None:
        timeline_text = f"No se alcanza FIRE en el horizonte elegido ({years_horizon} años)."
    else:
        timeline_text = f"El escenario central llega a FIRE en aproximadamente {years_to_fire} años."
    renta_line = ""
    renta_efectiva = params.get("renta_neta_alquiler_anual_efectiva", 0.0)
    renta_bruta_base = params.get("renta_bruta_alquiler_anual_efectiva", 0.0)
    cuota_hipotecas_mensual = params.get("cuota_total_hipotecas_mensual_efectiva", 0.0)
    cuota_post_fire_mensual = params.get("cuota_post_fire_hipotecas_mensual_efectiva", 0.0)
    if renta_efectiva > 0:
        renta_line = (
            f"- Renta por alquiler considerada en cálculo: **€{renta_efectiva:,.0f}/año**.\n"
        )
        if abs(renta_bruta_base - renta_efectiva) > 1:
            renta_line += (
                f"- Renta bruta declarada: **€{renta_bruta_base:,.0f}/año** "
                "(ajustada por vacancia/gastos/fiscalidad simple).\n"
            )
    vivienda_line = ""
    ahorro_vivienda_efectivo = params.get("ahorro_vivienda_habitual_anual_efectivo", 0.0)
    if ahorro_vivienda_efectivo > 0:
        vivienda_line = (
            f"- Ahorro anual por vivienda habitual considerado: **€{ahorro_vivienda_efectivo:,.0f}/año**.\n"
        )
    hipoteca_line = ""
    if cuota_hipotecas_mensual > 0:
        hipoteca_line += (
            f"- Cuotas hipotecarias pre-FIRE descontadas del ahorro: **€{cuota_hipotecas_mensual:,.0f}/mes**.\n"
        )
    if cuota_post_fire_mensual > 0:
        hipoteca_line += (
            f"- Cuotas hipotecarias que seguirían vivas en FIRE: **€{cuota_post_fire_mensual:,.0f}/mes** "
            "(sumadas al gasto de cartera).\n"
        )

    st.info(
        "🗣️ **Resumen en lenguaje simple**\n\n"
        f"- Capital inicial usado en simulación: **€{params.get('patrimonio_base_simulacion', params['patrimonio_inicial']):,.0f}**.\n"
        f"{renta_line}"
        f"{vivienda_line}"
        f"{hipoteca_line}"
        f"- Tu objetivo de cartera es **€{fire_target:,.0f}**.\n"
        f"- {timeline_text}\n"
        f"- Probabilidad estimada de éxito: **{success_rate:.0f}%**.\n\n"
        "Si esto no encaja con tu objetivo, normalmente las palancas más efectivas son: "
        "subir ahorro mensual, bajar gasto objetivo o ampliar horizonte."
    )


def render_final_narrative_summary(simulation_results: Dict, params: Dict) -> None:
    """Render long-form final narrative with actionable guidance."""
    years_horizon = params["edad_objetivo"] - params["edad_actual"]
    fire_target = get_display_fire_target(simulation_results, params)
    years_to_fire = find_years_to_fire(simulation_results["real_percentile_50"], fire_target)
    success_rate = float(simulation_results.get("success_rate_final", 0.0))
    final_real = float(simulation_results["real_percentile_50"][-1])
    gap = final_real - fire_target
    savings_monthly = float(params.get("aportacion_mensual_efectiva", params.get("aportacion_mensual", 0.0)))
    fiscal_mode = params.get("fiscal_mode", FISCAL_MODE_ES_TAXPACK)

    if years_to_fire is None:
        stage = "bajo"
        state_line = (
            f"Con los parámetros actuales, el escenario central no alcanza FIRE en el horizonte de {years_horizon} años. "
            f"La probabilidad estimada de éxito es {success_rate:.0f}% y la brecha final esperada ronda €{abs(gap):,.0f} en euros de hoy."
        )
    elif success_rate >= 90:
        stage = "alto"
        state_line = (
            f"Tu plan se ve sólido: el escenario central llega a FIRE en {years_to_fire} años "
            f"y la probabilidad de éxito se sitúa en {success_rate:.0f}%."
        )
    else:
        stage = "intermedio"
        state_line = (
            f"Tu plan es alcanzable en el escenario central ({years_to_fire} años), "
            f"pero con sensibilidad relevante: probabilidad de éxito {success_rate:.0f}%."
        )

    explain_line = (
        f"El resultado se explica por tres palancas principales: gasto objetivo (€{params['gastos_anuales']:,.0f}/año), "
        f"ahorro efectivo (≈€{savings_monthly:,.0f}/mes) y rentabilidad real esperada "
        f"({(((1 + params['rentabilidad_esperada']) / (1 + params['inflacion'])) - 1)*100:.2f}% anual). "
        f"Además, el cálculo fiscal activo es {'español con Tax Pack' if fiscal_mode == FISCAL_MODE_ES_TAXPACK else 'internacional básico (tasas efectivas)'}."
    )

    risk_line = (
        "El principal riesgo está en la combinación de inflación alta y rentabilidad baja durante varios años seguidos. "
        "Si ese escenario se materializa, el tiempo a FIRE puede desplazarse de forma significativa."
    )

    if stage == "alto":
        plan_line = (
            "Plan recomendado: en los próximos 90 días, define un rebalanceo automático y política de retirada; "
            "en 12 meses, valida que tu gasto real sigue alineado con el objetivo; y después revisa trimestralmente "
            "la matriz de sensibilidad y ajusta solo si cambian ingresos, gasto o horizonte."
        )
    elif stage == "intermedio":
        plan_line = (
            "Plan recomendado: en 90 días, identifica 1-2 mejoras de ahorro recurrente y valida costes fiscales; "
            "en 12 meses, incrementa aportación o reduce gasto objetivo para ganar margen; "
            "y a partir de ahí revisa trimestralmente la probabilidad de éxito con disciplina."
        )
    else:
        plan_line = (
            "Plan recomendado: en 90 días, prioriza aumentar ahorro y recortar gasto objetivo con impacto alto; "
            "en 12 meses, recalibra horizonte o estrategia de ingresos complementarios; "
            "y mantén revisión trimestral para comprobar progreso contra una meta intermedia anual."
        )

    st.markdown("### 🧱 Resumen final de tu plan FIRE")
    st.write(state_line)
    st.write(explain_line)
    st.write(risk_line)
    st.write(plan_line)
    st.markdown(
        "1. Descarga tu proyección (`CSV/JSON`) para seguimiento anual.\n"
        "2. Revisa sensibilidad e hipótesis fiscales al menos una vez por trimestre.\n"
        "3. Ajusta aportación, gasto objetivo u horizonte solo con cambios reales de contexto."
    )


def build_ab_summary(simulation_results: Dict, params: Dict) -> Dict[str, Any]:
    """Build a compact, comparable snapshot for A/B comparison."""
    fire_target = float(get_display_fire_target(simulation_results, params))
    years_horizon = int(params["edad_objetivo"] - params["edad_actual"])
    years_to_fire = find_years_to_fire(simulation_results["real_percentile_50"], fire_target)
    return {
        "model": "Monte Carlo (Normal)",
        "years_horizon": years_horizon,
        "years_to_fire": years_to_fire,
        "success_rate_final": float(simulation_results.get("success_rate_final", 0.0)),
        "final_real_p50": float(simulation_results["real_percentile_50"][-1]),
        "final_nominal_p50": float(simulation_results["percentile_50"][-1]),
        "fire_target": fire_target,
    }


def render_ab_comparator(current_results: Dict, params: Dict) -> None:
    """Render A/B comparator: baseline scenario A vs current scenario B."""
    st.markdown("### 🆚 Comparador A/B (escenario guardado vs actual)")
    st.markdown(
        "<div class='ab-compare-shell'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='ab-compare-title'>Compara rápidamente tu escenario actual (B) contra una línea base guardada (A).</div>",
        unsafe_allow_html=True,
    )

    controls_col1, controls_col2 = st.columns(2)
    with controls_col1:
        if st.button("Guardar escenario actual como A", key="ab_save_baseline", width="stretch"):
            st.session_state["ab_baseline_params"] = serialize_profile(params)
            st.session_state["ab_baseline_summary"] = build_ab_summary(current_results, params)
            st.session_state["ab_baseline_created_at"] = datetime.now().isoformat(timespec="seconds")
            st.session_state["ab_baseline_model"] = "Monte Carlo (Normal)"
            st.success("Escenario A guardado para comparación.")
    with controls_col2:
        if st.button("Limpiar comparación", key="ab_clear_baseline", width="stretch"):
            st.session_state.pop("ab_baseline_params", None)
            st.session_state.pop("ab_baseline_summary", None)
            st.session_state.pop("ab_baseline_created_at", None)
            st.session_state.pop("ab_baseline_model", None)
            st.info("Comparación A/B eliminada.")

    baseline_summary = st.session_state.get("ab_baseline_summary")
    if not baseline_summary:
        st.info("Aún no hay escenario A. Guarda uno para activar la comparación.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    current_summary = build_ab_summary(current_results, params)
    created_at = st.session_state.get("ab_baseline_created_at", "n/d")
    st.markdown(
        f"<div class='ab-compare-caption'>A guardado: {created_at} | Modelo fijo: Monte Carlo (Normal)</div>",
        unsafe_allow_html=True,
    )

    baseline_years = baseline_summary.get("years_to_fire")
    current_years = current_summary.get("years_to_fire")
    baseline_horizon = int(baseline_summary.get("years_horizon", current_summary["years_horizon"]))
    current_horizon = int(current_summary["years_horizon"])

    def _format_years(value: Optional[int], horizon: int) -> str:
        return f"{value} años" if value is not None else f"No alcanzable (> {horizon} años)"

    if baseline_years is not None and current_years is not None:
        delta_years = current_years - baseline_years
        years_delta_text = f"{delta_years:+d} años vs A"
        years_delta_color = "inverse"
    elif baseline_years is None and current_years is not None:
        years_delta_text = "Ahora sí alcanzable"
        years_delta_color = "normal"
    elif baseline_years is not None and current_years is None:
        years_delta_text = "Ahora no alcanzable"
        years_delta_color = "off"
    else:
        years_delta_text = "Sin cambio (no alcanzable)"
        years_delta_color = "off"

    success_delta = float(current_summary["success_rate_final"]) - float(baseline_summary.get("success_rate_final", 0.0))
    real_delta = float(current_summary["final_real_p50"]) - float(baseline_summary.get("final_real_p50", 0.0))
    target_delta = float(current_summary["fire_target"]) - float(baseline_summary.get("fire_target", 0.0))

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "⏱️ Años hasta FIRE (B)",
            _format_years(current_years, current_horizon),
            delta=years_delta_text,
            delta_color=years_delta_color,
        )
    with m2:
        st.metric(
            "📈 Éxito final (B)",
            f"{current_summary['success_rate_final']:.0f}%",
            delta=f"{success_delta:+.1f} pp vs A",
            delta_color="normal",
        )
    with m3:
        st.metric(
            "💰 P50 poder adquisitivo (B)",
            f"€{current_summary['final_real_p50']:,.0f}",
            delta=f"{real_delta:+,.0f} € vs A",
            delta_color="normal",
        )
    with m4:
        st.metric(
            "🎯 Objetivo FIRE (B, € hoy)",
            f"€{current_summary['fire_target']:,.0f}",
            delta=f"{target_delta:+,.0f} € vs A",
            delta_color="inverse",
        )

    score = 0
    if baseline_years is None and current_years is not None:
        score += 2
    elif baseline_years is not None and current_years is None:
        score -= 2
    elif baseline_years is not None and current_years is not None:
        if current_years < baseline_years:
            score += 1
        elif current_years > baseline_years:
            score -= 1

    if success_delta >= 2.0:
        score += 1
    elif success_delta <= -2.0:
        score -= 1

    if real_delta >= 10_000:
        score += 1
    elif real_delta <= -10_000:
        score -= 1

    if score >= 2:
        insight_cls = ""
        insight_text = "Lectura rápida: B mejora de forma clara frente a A en robustez y/o velocidad hacia FIRE."
    elif score <= -2:
        insight_cls = "danger"
        insight_text = "Lectura rápida: B empeora frente a A. Revisa sobre todo ahorro, gasto objetivo y horizonte."
    else:
        insight_cls = "warn"
        insight_text = "Lectura rápida: resultado mixto entre A y B. Hay cambios, pero no una mejora neta contundente."

    st.markdown(
        f"<div class='ab-compare-insight {insight_cls}'>{insight_text}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def estimate_retirement_tax_context(
    net_spending: float,
    safe_withdrawal_rate: float,
    taxable_withdrawal_ratio: float,
    tax_pack: Optional[Dict],
    region: Optional[str],
) -> Dict[str, float]:
    """Compatibility wrapper around core retirement tax model."""
    return estimate_retirement_tax_context_core(
        net_spending=net_spending,
        safe_withdrawal_rate=safe_withdrawal_rate,
        taxable_withdrawal_ratio=taxable_withdrawal_ratio,
        tax_pack=tax_pack,
        region=region,
    )


def estimate_retirement_tax_context_intl_basic(
    net_spending: float,
    safe_withdrawal_rate: float,
    taxable_withdrawal_ratio: float,
    intl_tax_rates: Dict[str, float],
) -> Dict[str, float]:
    """Approximate retirement-tax context for non-Spain basic mode."""
    base_target = net_spending / safe_withdrawal_rate
    ratio = min(1.0, max(0.0, taxable_withdrawal_ratio))
    savings_rate = (
        max(0.0, min(1.0, float(intl_tax_rates.get("gains", 0.10)))) * 0.55
        + max(0.0, min(1.0, float(intl_tax_rates.get("dividends", 0.15)))) * 0.25
        + max(0.0, min(1.0, float(intl_tax_rates.get("interest", 0.20)))) * 0.20
    )
    wealth_rate = max(0.0, min(1.0, float(intl_tax_rates.get("wealth", 0.0))))

    portfolio_target = base_target
    annual_savings_tax = 0.0
    annual_wealth_tax = 0.0
    gross_withdrawal = net_spending
    converged = False
    iterations = 0

    for outer_idx in range(1, 31):
        iterations = outer_idx
        annual_wealth_tax = portfolio_target * wealth_rate
        gross_candidate = net_spending + annual_wealth_tax
        for _ in range(30):
            annual_savings_tax_new = max(0.0, gross_candidate * ratio) * savings_rate
            updated = net_spending + annual_wealth_tax + annual_savings_tax_new
            if abs(updated - gross_candidate) <= 0.01:
                annual_savings_tax = annual_savings_tax_new
                gross_candidate = updated
                break
            annual_savings_tax = annual_savings_tax_new
            gross_candidate = updated
        new_target = gross_candidate / safe_withdrawal_rate
        if abs(new_target - portfolio_target) <= 1.0:
            portfolio_target = new_target
            gross_withdrawal = gross_candidate
            converged = True
            break
        portfolio_target = new_target
        gross_withdrawal = gross_candidate

    return {
        "base_target": base_target,
        "gross_withdrawal_required": gross_withdrawal,
        "annual_savings_tax_retirement": annual_savings_tax,
        "annual_wealth_tax_retirement": annual_wealth_tax,
        "total_annual_tax_retirement": annual_savings_tax + annual_wealth_tax,
        "target_portfolio_gross": portfolio_target,
        "converged": converged,
        "iterations": iterations,
    }


def estimate_auto_taxable_withdrawal_ratio(
    initial_wealth: float,
    monthly_contribution: float,
    years: int,
    expected_return: float,
    contribution_growth_rate: float = 0.0,
) -> float:
    """Compatibility wrapper around core taxable-withdrawal estimator."""
    return estimate_auto_taxable_withdrawal_ratio_core(
        initial_wealth=initial_wealth,
        monthly_contribution=monthly_contribution,
        years=years,
        expected_return=expected_return,
        contribution_growth_rate=contribution_growth_rate,
    )


def get_display_fire_target(simulation_results: Dict, params: Dict) -> float:
    """Use a single FIRE target source for UI consistency."""
    if params.get("fiscal_priority") == "Jubilación":
        ctx = params.get("retirement_tax_context")
        if ctx and ctx.get("target_portfolio_gross") is not None:
            return float(ctx["target_portfolio_gross"])
    return float(
        simulation_results.get(
            "fire_target_real",
            params["gastos_anuales"] / params["safe_withdrawal_rate"],
        )
    )


def render_retirement_tax_focus_summary(params: Dict) -> None:
    """Explain retirement-tax-focused target adjustments."""
    ctx = params.get("retirement_tax_context")
    if not ctx or params.get("fiscal_priority") != "Jubilación":
        return

    st.subheader("🎯 Objetivo fiscal en jubilación")
    st.caption(
        "Este bloque prioriza impuestos durante la jubilación (retiros), no la acumulación previa."
    )
    net_spending_for_portfolio = params.get("gasto_anual_neto_cartera", params["gastos_anuales"])
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gasto neto deseado", f"€{net_spending_for_portfolio:,.0f}")
    col2.metric("Retirada bruta estimada", f"€{ctx['gross_withdrawal_required']:,.0f}")
    col3.metric("Impuestos anuales estimados", f"€{ctx['total_annual_tax_retirement']:,.0f}")
    col4.metric("Objetivo FIRE ajustado", f"€{ctx['target_portfolio_gross']:,.0f}")
    st.caption(
        f"Supuesto clave: {params.get('taxable_withdrawal_ratio_effective', params.get('taxable_withdrawal_ratio', 0.4))*100:.0f}% "
        "de la retirada anual tributa "
        "como base del ahorro."
    )
    if params.get("taxable_withdrawal_ratio_mode") == "Automático (estimado)":
        st.caption(
            "Ese porcentaje se estima automáticamente con aportaciones y crecimiento proyectado."
        )
    st.caption(
        "Referencia de fórmula: objetivo base = gasto neto / SWR. Al subir SWR, ese objetivo base baja; "
        "el ajuste fiscal puede suavizar esa caída, pero no invertirla en condiciones normales."
    )
    if params.get("renta_neta_alquiler_anual_efectiva", 0) > 0:
        st.caption(
            f"Ingreso alquiler considerado: €{params['renta_neta_alquiler_anual_efectiva']:,.0f}/año."
        )
    if params.get("ahorro_vivienda_habitual_anual_efectivo", 0) > 0:
        st.caption(
            f"Ahorro anual por vivienda habitual considerado: €{params['ahorro_vivienda_habitual_anual_efectivo']:,.0f}/año."
        )


def build_decumulation_table(
    starting_portfolio: float,
    annual_withdrawal_base: float,
    years_in_retirement: int,
    expected_return: float,
    inflation_rate: float,
    tax_rate_on_gains: float,
) -> pd.DataFrame:
    """Build a year-by-year decumulation table for retirement."""
    rows: List[Dict[str, float]] = []
    portfolio = float(max(0.0, starting_portfolio))
    inflation_factor = 1.0

    for year in range(1, years_in_retirement + 1):
        capital_inicial = portfolio
        retirada = annual_withdrawal_base * inflation_factor
        growth_gross = capital_inicial * expected_return
        tax_growth = max(0.0, growth_gross) * max(0.0, tax_rate_on_gains)
        growth_net = growth_gross - tax_growth
        capital_final = max(0.0, capital_inicial + growth_net - retirada)

        rows.append(
            {
                "Año jubilación": year,
                "Capital inicial (€)": capital_inicial,
                "Retirada anual (€)": retirada,
                "Crecimiento neto (€)": growth_net,
                "Capital final (€)": capital_final,
                "Capital agotado": capital_final <= 0,
            }
        )

        portfolio = capital_final
        inflation_factor *= (1 + inflation_rate)

    return pd.DataFrame(rows)


def build_decumulation_table_two_stage(
    starting_portfolio: float,
    annual_withdrawal_stage1: float,
    annual_withdrawal_stage2: float,
    stage1_years: int,
    years_in_retirement: int,
    expected_return: float,
    inflation_rate: float,
    tax_rate_on_gains: float,
) -> pd.DataFrame:
    """Build decumulation table with two retirement stages.

    Stage 1: pre-pension withdrawals (typically higher).
    Stage 2: post-pension net withdrawals from portfolio (typically lower).
    """
    rows: List[Dict[str, float]] = []
    portfolio = float(max(0.0, starting_portfolio))
    inflation_factor = 1.0

    for year in range(1, years_in_retirement + 1):
        tramo = "Pre-pensión" if year <= stage1_years else "Post-pensión"
        retirada_base = annual_withdrawal_stage1 if year <= stage1_years else annual_withdrawal_stage2
        capital_inicial = portfolio
        retirada = retirada_base * inflation_factor
        growth_gross = capital_inicial * expected_return
        tax_growth = max(0.0, growth_gross) * max(0.0, tax_rate_on_gains)
        growth_net = growth_gross - tax_growth
        capital_final = max(0.0, capital_inicial + growth_net - retirada)

        rows.append(
            {
                "Año jubilación": year,
                "Tramo": tramo,
                "Capital inicial (€)": capital_inicial,
                "Retirada anual (€)": retirada,
                "Crecimiento neto (€)": growth_net,
                "Capital final (€)": capital_final,
                "Capital agotado": capital_final <= 0,
            }
        )

        portfolio = capital_final
        inflation_factor *= (1 + inflation_rate)

    return pd.DataFrame(rows)


def build_decumulation_table_two_stage_schedule(
    starting_portfolio: float,
    fire_age: int,
    years_in_retirement: int,
    annual_spending_base: float,
    pension_public_start_age: int,
    pension_public_net_annual: float,
    plan_private_start_age: int,
    plan_private_duration_years: int,
    plan_private_net_annual: float,
    other_income_post_pension_annual: float,
    pre_pension_extra_cost_annual: float,
    expected_return: float,
    inflation_rate: float,
    tax_rate_on_gains: float,
) -> pd.DataFrame:
    """Compatibility wrapper around core two-stage schedule model."""
    return build_decumulation_table_two_stage_schedule_core(
        starting_portfolio=starting_portfolio,
        fire_age=fire_age,
        years_in_retirement=years_in_retirement,
        annual_spending_base=annual_spending_base,
        pension_public_start_age=pension_public_start_age,
        pension_public_net_annual=pension_public_net_annual,
        plan_private_start_age=plan_private_start_age,
        plan_private_duration_years=plan_private_duration_years,
        plan_private_net_annual=plan_private_net_annual,
        other_income_post_pension_annual=other_income_post_pension_annual,
        pre_pension_extra_cost_annual=pre_pension_extra_cost_annual,
        expected_return=expected_return,
        inflation_rate=inflation_rate,
        tax_rate_on_gains=tax_rate_on_gains,
    )


def render_decumulation_box(simulation_results: Dict, params: Dict) -> None:
    """Render retirement capital-spending table."""
    st.subheader("🪙 Gasto de capital en jubilación")
    st.caption(
        "Proyección anual de cómo evoluciona el capital tras retirarte "
        "(escenario base, aproximación simplificada)."
    )

    default_years = 30
    years_in_retirement = st.slider(
        "Años de jubilación a proyectar",
        min_value=10,
        max_value=45,
        value=default_years,
        step=1,
        help="Horizonte de retirada para la tabla de decumulación.",
    )

    percentile_series = {
        "P5": "percentile_5",
        "P25": "percentile_25",
        "P50": "percentile_50",
        "P75": "percentile_75",
        "P95": "percentile_95",
    }
    starting_portfolios = {
        label: float(simulation_results[key][-1]) for label, key in percentile_series.items()
    }
    annual_withdrawal_base = float(params.get("annual_spending_for_target", params["gastos_anuales"]))
    tax_rate_hint = 0.19 if params["regimen_fiscal"] in ("España - Fondos de Inversión", "España - Cartera Directa") else 0.15

    # Use scenario-specific annual return from path-level market returns (robust vs contributions).
    default_ret = float(params["rentabilidad_neta_simulacion"])
    percentile_labels = ["P5", "P25", "P50", "P75", "P95"]
    raw_return_map = simulation_results.get("path_return_percentiles")
    if not isinstance(raw_return_map, dict):
        raw_return_map = {k: default_ret for k in percentile_labels}

    raw_returns = [raw_return_map[label] for label in percentile_labels]
    # Enforce coherence: favorable percentiles cannot have lower expected return than adverse ones.
    coherent_returns: List[float] = []
    current_floor = -1.0
    for r in raw_returns:
        current_floor = max(current_floor, r)
        coherent_returns.append(float(min(0.60, max(-0.60, current_floor))))
    scenario_expected_return = {
        label: coherent_returns[idx] for idx, label in enumerate(percentile_labels)
    }
    two_stage_enabled = params.get("two_stage_retirement_model", False)
    stage1_years = 0
    annual_withdrawal_stage1 = annual_withdrawal_base
    annual_withdrawal_stage2 = annual_withdrawal_base
    pension_public_start_age = int(params.get("edad_inicio_pension_publica", params.get("edad_pension_oficial", 67)))
    plan_private_start_age = int(params.get("edad_inicio_plan_privado", pension_public_start_age))
    plan_private_duration_years = int(params.get("duracion_plan_privado_anos", 0))
    plan_private_net_annual = float(params.get("plan_pensiones_privado_neto_anual", 0.0))
    pension_public_net_annual = float(params.get("pension_publica_neta_anual_efectiva", 0.0))
    other_income_post = float(params.get("otras_rentas_post_jubilacion_netas", 0.0))
    if two_stage_enabled:
        fire_age = params["edad_objetivo"]
        pension_age = pension_public_start_age
        stage1_years = max(0, pension_age - fire_age)
        annual_withdrawal_stage1 = max(
            0.0,
            annual_withdrawal_base + params.get("coste_pre_pension_anual", 0.0),
        )
        annual_withdrawal_stage2 = max(
            0.0,
            annual_withdrawal_base - params.get("pension_neta_anual", 0.0),
        )

    dec_tables: Dict[str, pd.DataFrame] = {}
    for label, start_portfolio in starting_portfolios.items():
        expected_return_scenario = scenario_expected_return.get(label, default_ret)
        if two_stage_enabled:
            dec_tables[label] = build_decumulation_table_two_stage_schedule(
                starting_portfolio=start_portfolio,
                fire_age=params["edad_objetivo"],
                years_in_retirement=years_in_retirement,
                annual_spending_base=annual_withdrawal_base,
                pension_public_start_age=pension_public_start_age,
                pension_public_net_annual=pension_public_net_annual,
                plan_private_start_age=plan_private_start_age,
                plan_private_duration_years=plan_private_duration_years,
                plan_private_net_annual=plan_private_net_annual,
                other_income_post_pension_annual=other_income_post,
                pre_pension_extra_cost_annual=float(params.get("coste_pre_pension_anual", 0.0)),
                expected_return=expected_return_scenario,
                inflation_rate=params["inflacion"],
                tax_rate_on_gains=tax_rate_hint,
            )
        else:
            dec_tables[label] = build_decumulation_table(
                starting_portfolio=start_portfolio,
                annual_withdrawal_base=annual_withdrawal_base,
                years_in_retirement=years_in_retirement,
                expected_return=expected_return_scenario,
                inflation_rate=params["inflacion"],
                tax_rate_on_gains=tax_rate_hint,
            )

    depletion_texts: Dict[str, str] = {}
    for label, dec_df in dec_tables.items():
        depletion_df = dec_df[dec_df["Capital agotado"]]
        depletion_texts[label] = (
            f"Año {int(depletion_df.iloc[0]['Año jubilación'])}"
            if not depletion_df.empty
            else "No se agota"
        )

    start_cols = st.columns(5)
    for col, label in zip(start_cols, percentile_series.keys()):
        col.metric(f"Capital inicio ({label})", f"€{starting_portfolios[label]:,.0f}")

    col_e, col_f = st.columns(2)
    retirada_inicial = float(dec_tables["P50"].iloc[0]["Retirada anual (€)"]) if not dec_tables["P50"].empty else 0.0
    col_e.metric("Retirada anual inicial", f"€{retirada_inicial:,.0f}")
    col_f.metric(
        "Diferencia capital inicial (P95 - P5)",
        f"€{(starting_portfolios['P95'] - starting_portfolios['P5']):,.0f}",
    )

    depletion_cols = st.columns(5)
    for col, label in zip(depletion_cols, percentile_series.keys()):
        col.metric(f"Agotamiento {label}", depletion_texts[label])

    tab_labels = [
        "Escenario muy adverso (P5)",
        "Escenario conservador (P25)",
        "Escenario base (P50)",
        "Escenario favorable (P75)",
        "Escenario muy favorable (P95)",
    ]
    tabs = st.tabs(tab_labels)
    for tab, label in zip(tabs, percentile_series.keys()):
        with tab:
            implied_return = float(scenario_expected_return.get(label, params["rentabilidad_neta_simulacion"]))
            st.metric(
                "📈 Retorno anual implícito usado",
                f"{implied_return*100:.2f}%",
                delta="Aplicado a este escenario",
                delta_color="off",
            )

            dec_display_df = dec_tables[label].copy()
            if {
                "Capital inicial (€)",
                "Crecimiento neto (€)",
                "Retirada anual (€)",
                "Capital final (€)",
            }.issubset(dec_display_df.columns):
                dec_display_df["Chequeo flujo (€)"] = (
                    dec_display_df["Capital inicial (€)"]
                    + dec_display_df["Crecimiento neto (€)"]
                    - dec_display_df["Retirada anual (€)"]
                    - dec_display_df["Capital final (€)"]
                )

            base_order = [
                "Año jubilación",
                "Edad",
                "Tramo",
                "Capital inicial (€)",
                "Ingreso pensión pública (€)",
                "Ingreso plan privado (€)",
                "Otras rentas (€)",
                "Coste extra pre-pensión (€)",
                "Retirada anual (€)",
                "Crecimiento neto (€)",
                "Capital final (€)",
                "Chequeo flujo (€)",
                "Capital agotado",
            ]
            ordered_cols = [c for c in base_order if c in dec_display_df.columns]
            dec_display_df = dec_display_df[ordered_cols]

            format_map = {
                "Capital inicial (€)": "€{:,.0f}",
                "Retirada anual (€)": "€{:,.0f}",
                "Crecimiento neto (€)": "€{:,.0f}",
                "Capital final (€)": "€{:,.0f}",
                "Chequeo flujo (€)": "€{:,.2f}",
            }
            for optional_col in (
                "Ingreso pensión pública (€)",
                "Ingreso plan privado (€)",
                "Otras rentas (€)",
                "Coste extra pre-pensión (€)",
            ):
                if optional_col in dec_display_df.columns:
                    format_map[optional_col] = "€{:,.0f}"
            st.dataframe(
                dec_display_df.style.format(format_map),
                width="stretch",
                hide_index=True,
            )
            if "Chequeo flujo (€)" in dec_display_df.columns:
                max_abs_check = float(dec_display_df["Chequeo flujo (€)"].abs().max())
                if max_abs_check > 0.01:
                    st.warning(
                        f"Se detectó descuadre contable máximo de €{max_abs_check:,.2f} en esta tabla."
                    )
                else:
                    st.caption("Chequeo de flujo OK: columnas de capital/retiro/cuadre son coherentes.")

    with st.expander("Supuestos del cuadro de gasto de capital", expanded=False):
        cagr_text = (
            f"P5 {scenario_expected_return['P5']*100:.2f}% · "
            f"P25 {scenario_expected_return['P25']*100:.2f}% · "
            f"P50 {scenario_expected_return['P50']*100:.2f}% · "
            f"P75 {scenario_expected_return['P75']*100:.2f}% · "
            f"P95 {scenario_expected_return['P95']*100:.2f}%"
        )
        if two_stage_enabled:
            st.write(
                "- Capital inicial: percentiles 5, 25, 50, 75 y 95 al final del horizonte de acumulación.\n"
                f"- Tramo pre-pensión: {stage1_years} años (hasta edad {pension_public_start_age}).\n"
                f"- Pensión pública neta: €{pension_public_net_annual:,.0f}/año desde {pension_public_start_age}.\n"
                f"- Plan privado neto: €{plan_private_net_annual:,.0f}/año desde {plan_private_start_age} "
                f"durante {plan_private_duration_years} años.\n"
                f"- Otras rentas post-pensión: €{other_income_post:,.0f}/año.\n"
                "- Ambos tramos se actualizan por inflación año a año.\n"
                f"- Retorno anual usado por escenario (CAGR implícito de acumulación): {cagr_text}.\n"
                f"- Impuesto orientativo sobre crecimiento: {tax_rate_hint*100:.1f}%.\n"
                "- Es una aproximación para planificación; no sustituye un plan de retiro personalizado."
            )
        else:
            st.write(
                "- Capital inicial: percentiles 5, 25, 50, 75 y 95 al final del horizonte de acumulación.\n"
                f"- Retirada base anual: €{annual_withdrawal_base:,.0f} (se actualiza por inflación).\n"
                f"- Retorno anual usado por escenario (CAGR implícito de acumulación): {cagr_text}.\n"
                f"- Impuesto orientativo sobre crecimiento: {tax_rate_hint*100:.1f}%.\n"
                "- Es una aproximación para planificación; no sustituye un plan de retiro personalizado."
            )


# =====================================================================
# 3. MONTE CARLO SIMULATION ENGINE
# =====================================================================

def monte_carlo_simulation(
    initial_wealth: float,
    monthly_contribution: float,
    years: int,
    mean_return: float,
    volatility: float,
    inflation_rate: float,
    annual_spending: float = 0,
    contribution_growth_rate: float = 0.0,
    num_simulations: int = 10_000,
    seed: int = 42,
    tax_pack: Optional[Dict] = None,
    region: Optional[str] = None,
    safe_withdrawal_rate: float = 0.04,
    model_type: str = "normal",
    historical_strategy: str = "sp500_us_total_return",
) -> Dict:
    """
    Run Monte Carlo simulation with geometric Brownian motion.
    
    Parameters
    ----------
    initial_wealth: Starting portfolio (EUR)
    monthly_contribution: Monthly savings (EUR)
    years: Projection period
    mean_return: Expected annual return (decimal)
    volatility: Annual volatility (decimal)
    inflation_rate: Annual inflation (decimal)
    annual_spending: Annual FIRE spending threshold (EUR)
    num_simulations: Number of paths (default 10,000)
    
    Returns
    -------
    Dictionary with simulation results including percentiles, success rate, etc.
    """
    if model_type == "bootstrap":
        historical = load_historical_annual_returns(strategy=historical_strategy)
        result = monte_carlo_bootstrap(
            initial_wealth=initial_wealth,
            monthly_contribution=monthly_contribution,
            years=years,
            inflation_rate=inflation_rate,
            annual_spending=annual_spending,
            safe_withdrawal_rate=safe_withdrawal_rate,
            contribution_growth_rate=contribution_growth_rate,
            historical_returns=historical,
            num_simulations=num_simulations,
            seed=seed,
            tax_pack=tax_pack,
            region=region,
        )
        result["model_name"] = "Monte Carlo (Bootstrap histórico)"
        return result

    if model_type == "backtest":
        historical_years, historical_returns, historical_months = load_historical_annual_series(
            strategy=historical_strategy
        )
        result = backtest_rolling_windows(
            initial_wealth=initial_wealth,
            monthly_contribution=monthly_contribution,
            years=years,
            inflation_rate=inflation_rate,
            annual_spending=annual_spending,
            safe_withdrawal_rate=safe_withdrawal_rate,
            contribution_growth_rate=contribution_growth_rate,
            historical_returns=historical_returns,
            historical_years=historical_years,
            historical_months_observed=historical_months,
            tax_pack=tax_pack,
            region=region,
        )
        result["model_name"] = "Backtesting histórico (ventanas móviles)"
        return result

    result = monte_carlo_normal(
        initial_wealth=initial_wealth,
        monthly_contribution=monthly_contribution,
        years=years,
        mean_return=mean_return,
        volatility=volatility,
        inflation_rate=inflation_rate,
        annual_spending=annual_spending,
        safe_withdrawal_rate=safe_withdrawal_rate,
        contribution_growth_rate=contribution_growth_rate,
        num_simulations=num_simulations,
        seed=seed,
        tax_pack=tax_pack,
        region=region,
    )
    result["model_name"] = "Monte Carlo (Normal)"
    return result


def get_fiscal_return_adjustment(
    regimen_fiscal: str,
    include_optimización: bool,
    fiscal_mode: str = FISCAL_MODE_ES_TAXPACK,
    intl_tax_rates: Optional[Dict[str, float]] = None,
) -> float:
    """
    Approximate annual return drag from taxes/friction by regime.
    This ensures fiscal selector changes simulation outcomes.
    """
    return get_effective_fiscal_drag(
        regimen_fiscal=regimen_fiscal,
        include_optimization=include_optimización,
        fiscal_mode=fiscal_mode,
        intl_tax_rates=intl_tax_rates,
    )


def find_years_to_fire(median_real_path: np.ndarray, fire_target: float) -> Optional[int]:
    """Return first year reaching FIRE target in real terms, or None if not reached."""
    for year, value in enumerate(median_real_path):
        if value >= fire_target:
            return year
    return None


# =====================================================================
# 4. CACHING LAYER - Separate cache vs session state
# =====================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def run_cached_simulation(
    params_key: str,
    initial_wealth: float,
    monthly_contribution: float,
    years: int,
    mean_return: float,
    volatility: float,
    inflation_rate: float,
    annual_spending: float,
    safe_withdrawal_rate: float,
    contribution_growth_rate: float,
    model_type: str,
    historical_strategy: str,
    tax_pack: Optional[Dict] = None,
    region: Optional[str] = None,
) -> Dict:
    """
    Cached Monte Carlo simulation. Cache key invalidates if params change.
    TTL: 1 hour
    """
    return monte_carlo_simulation(
        initial_wealth=initial_wealth,
        monthly_contribution=monthly_contribution,
        years=years,
        mean_return=mean_return,
        volatility=volatility,
        inflation_rate=inflation_rate,
        annual_spending=annual_spending,
        safe_withdrawal_rate=safe_withdrawal_rate,
        contribution_growth_rate=contribution_growth_rate,
        model_type=model_type,
        historical_strategy=historical_strategy,
        num_simulations=10_000,
        tax_pack=tax_pack,
        region=region,
    )


# =====================================================================
# 5. SIDEBAR - INPUT COLLECTION & PARAMETER PANEL
# =====================================================================

def render_sidebar() -> Dict:
    """
    Render sidebar with investor profile, market assumptions, & fiscal config.
    Returns validated parameter dictionary.
    """
    st.sidebar.markdown("## ⚙️ Panel de Control")
    st.sidebar.divider()

    loaded_profile_config = st.session_state.get("loaded_profile_config", {})
    loaded_profile_warnings = st.session_state.get("loaded_profile_warnings", [])

    def apply_loaded_profile_to_widget_state(config: Dict[str, Any]) -> None:
        """Map profile config keys to widget state keys so controls reflect loaded JSON."""
        key_map = {
            "modo_guiado": "modo_guiado_key",
            "setup_mode": "setup_mode_key",
            "profile_name": "profile_name_key",
            "apply_profile_defaults": "apply_profile_defaults_key",
            "gastos_anuales": "gastos_anuales_key",
            "safe_withdrawal_rate": "safe_withdrawal_rate_key",
            "edad_actual": "edad_actual_key",
            "edad_objetivo": "edad_objetivo_key",
            "vivienda_habitual_valor": "vivienda_habitual_valor_key",
            "vivienda_habitual_hipoteca": "vivienda_habitual_hipoteca_key",
            "incluir_cuota_vivienda_en_simulacion": "incluir_cuota_vivienda_en_simulacion_key",
            "aplicar_ajuste_vivienda_habitual": "aplicar_ajuste_vivienda_habitual_key",
            "ahorro_vivienda_habitual_anual": "ahorro_vivienda_habitual_anual_key",
            "inmuebles_invertibles_valor": "inmuebles_invertibles_valor_key",
            "inmuebles_invertibles_hipoteca": "inmuebles_invertibles_hipoteca_key",
            "incluir_cuota_inmuebles_en_simulacion": "incluir_cuota_inmuebles_en_simulacion_key",
            "otras_deudas": "otras_deudas_key",
            "usar_capital_invertible_ampliado": "usar_capital_invertible_ampliado_key",
            "renta_bruta_alquiler_anual": "renta_bruta_alquiler_anual_key",
            "usar_modelo_avanzado_alquiler": "usar_modelo_avanzado_alquiler_key",
            "alquiler_costes_vacancia_pct": "alquiler_costes_vacancia_pct_key",
            "alquiler_irpf_efectivo_pct": "alquiler_irpf_efectivo_pct_key",
            "incluir_rentas_alquiler_en_simulacion": "incluir_rentas_alquiler_en_simulacion_key",
            "include_pension_in_simulation": "include_pension_in_simulation_key",
            "two_stage_retirement_model": "two_stage_retirement_model_key",
            "edad_pension_oficial": "edad_pension_oficial_key",
            "edad_inicio_pension_publica": "edad_inicio_pension_publica_key",
            "bonificacion_demora_pct": "bonificacion_demora_pct_key",
            "pension_publica_neta_anual": "pension_publica_neta_anual_key",
            "edad_inicio_plan_privado": "edad_inicio_plan_privado_key",
            "duracion_plan_privado_anos": "duracion_plan_privado_anos_key",
            "plan_pensiones_privado_neto_anual": "plan_pensiones_privado_neto_anual_key",
            "otras_rentas_post_jubilacion_netas": "otras_rentas_post_jubilacion_netas_key",
            "coste_pre_pension_anual": "coste_pre_pension_anual_key",
            "rentabilidad_esperada": "rentabilidad_esperada_key",
            "volatilidad": "volatilidad_key",
            "inflacion": "inflacion_key",
            "inflacionar_aportacion": "inflacionar_aportacion_key",
            "fiscal_priority": "fiscal_priority_key",
            "regimen_fiscal": "regimen_fiscal_key",
            "include_optimización": "include_optimizacion_key",
            "taxable_withdrawal_ratio_mode": "taxable_withdrawal_ratio_mode_key",
            "taxable_withdrawal_ratio": "taxable_withdrawal_ratio_key",
            "tax_year": "tax_year_key",
            "region": "region_key",
        }
        for cfg_key, widget_key in key_map.items():
            if cfg_key in config:
                value = config[cfg_key]
                if cfg_key == "safe_withdrawal_rate":
                    value = float(value) * 100.0
                elif cfg_key in ("rentabilidad_esperada", "volatilidad", "inflacion"):
                    value = float(value) * 100.0
                elif cfg_key == "bonificacion_demora_pct":
                    value = float(value) * 100.0
                elif cfg_key == "taxable_withdrawal_ratio":
                    value = float(value) * 100.0
                st.session_state[widget_key] = value

        if "fiscal_mode" in config:
            st.session_state["fiscal_mode_label_key"] = (
                "Internacional básico"
                if config["fiscal_mode"] == FISCAL_MODE_INTL_BASIC
                else "España (Tax Pack)"
            )
        if "intl_tax_rates" in config and isinstance(config["intl_tax_rates"], dict):
            rates = config["intl_tax_rates"]
            st.session_state["intl_tax_gains_key"] = float(rates.get("gains", 0.10)) * 100.0
            st.session_state["intl_tax_dividends_key"] = float(rates.get("dividends", 0.15)) * 100.0
            st.session_state["intl_tax_interest_key"] = float(rates.get("interest", 0.20)) * 100.0
            st.session_state["intl_tax_wealth_key"] = float(rates.get("wealth", 0.00)) * 100.0

        if "patrimonio_inicial" in config:
            st.session_state["patrimonio_exact_mode"] = True
            st.session_state["patrimonio_exact_value"] = int(float(config["patrimonio_inicial"]))
        if "aportacion_mensual" in config:
            st.session_state["aportacion_exact_mode"] = True
            st.session_state["aportacion_exact_value"] = int(float(config["aportacion_mensual"]))
        if "cuota_hipoteca_vivienda_mensual" in config:
            st.session_state["primary_mortgage_payment_exact_mode"] = True
            st.session_state["primary_mortgage_payment_exact_value"] = int(float(config["cuota_hipoteca_vivienda_mensual"]))
        if "meses_hipoteca_vivienda_restantes_exact_mode" in config:
            st.session_state["primary_mortgage_months_exact_mode"] = bool(config["meses_hipoteca_vivienda_restantes_exact_mode"])
        if "meses_hipoteca_vivienda_restantes" in config:
            st.session_state["primary_mortgage_months_exact_value"] = int(float(config["meses_hipoteca_vivienda_restantes"]))
        if "cuota_hipoteca_inmuebles_mensual" in config:
            st.session_state["investment_mortgage_payment_exact_mode"] = True
            st.session_state["investment_mortgage_payment_exact_value"] = int(float(config["cuota_hipoteca_inmuebles_mensual"]))
        if "meses_hipoteca_inmuebles_restantes_exact_mode" in config:
            st.session_state["investment_mortgage_months_exact_mode"] = bool(config["meses_hipoteca_inmuebles_restantes_exact_mode"])
        if "meses_hipoteca_inmuebles_restantes" in config:
            st.session_state["investment_mortgage_months_exact_value"] = int(float(config["meses_hipoteca_inmuebles_restantes"]))

    with st.sidebar.expander("💾 Perfil (cargar JSON)", expanded=False):
        profile_file = st.file_uploader(
            "Cargar perfil FIRE (.json)",
            type=["json"],
            key="profile_json_uploader",
        )
        col_apply_profile, col_clear_profile = st.columns(2)
        with col_apply_profile:
            if st.button("Aplicar perfil", key="apply_profile_button", width="stretch"):
                if profile_file is not None:
                    try:
                        payload = json.loads(profile_file.read().decode("utf-8"))
                        safe_cfg, warnings_profile = deserialize_profile(payload)
                        st.session_state["loaded_profile_config"] = safe_cfg
                        st.session_state["loaded_profile_warnings"] = warnings_profile
                        apply_loaded_profile_to_widget_state(safe_cfg)
                        st.success("Perfil cargado. Se aplicará en esta ejecución.")
                        loaded_profile_config = safe_cfg
                        loaded_profile_warnings = warnings_profile
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo cargar el perfil: {e}")
                else:
                    st.warning("Selecciona un archivo JSON antes de aplicar.")
        with col_clear_profile:
            if st.button("Limpiar perfil", key="clear_profile_button", width="stretch"):
                st.session_state.pop("loaded_profile_config", None)
                st.session_state.pop("loaded_profile_warnings", None)
                loaded_profile_config = {}
                loaded_profile_warnings = []
                st.info("Perfil cargado eliminado.")

        if loaded_profile_config:
            st.caption("Perfil cargado activo: se aplicará sobre los controles actuales.")
        if loaded_profile_warnings:
            st.warning(" | ".join(loaded_profile_warnings))
        st.caption("Carga perfil aquí. Para exportar/guardar usa el bloque `📥 Exportar Resultados`.")

    # STEP 1: Experience and setup mode
    st.sidebar.markdown("### 1) Configuración inicial")
    modo_guiado = st.sidebar.checkbox(
        "Modo guiado (explicaciones simples)",
        value=True,
        key="modo_guiado_key",
        help="Muestra ayudas adicionales para usuarios no técnicos.",
    )
    setup_mode = st.sidebar.radio(
        "¿Cómo quieres configurar?",
        options=["Perfil FIRE", "Personalizado"],
        key="setup_mode_key",
        help="Perfil FIRE aplica una plantilla inicial; Personalizado deja todo manual.",
    )

    profile_name = "Personalizado"
    apply_profile_defaults = False
    profile_defaults = {
        "gastos_anuales": 30_000,
        "rentabilidad_esperada": 0.07,
        "inflacion": 0.025,
        "safe_withdrawal_rate": 0.04,
    }
    if setup_mode == "Perfil FIRE":
        profile_name = st.sidebar.selectbox(
            "Perfil FIRE",
            options=[p for p in WEB_PROFILES.keys() if p != "Personalizado"],
            key="profile_name_key",
            help="Plantilla con valores sugeridos para gastos, retorno, inflación y SWR.",
        )
        apply_profile_defaults = st.sidebar.checkbox(
            "Bloquear parámetros del perfil",
            value=True,
            key="apply_profile_defaults_key",
            help="Si está activo, esos parámetros quedan en modo solo lectura.",
        )
        profile_defaults = WEB_PROFILES[profile_name] or profile_defaults

    if modo_guiado:
        st.sidebar.caption(
            "Consejo: empieza con valores aproximados y cambia una variable cada vez."
        )

    lock_profile_fields = setup_mode == "Perfil FIRE" and apply_profile_defaults

    st.sidebar.divider()

    # STEP 2: FIRE target
    st.sidebar.markdown("### 2) Objetivo FIRE")
    gastos_anuales = st.sidebar.number_input(
        "Gastos anuales en jubilación (€)",
        min_value=1_000,
        max_value=1_000_000,
        value=int(profile_defaults["gastos_anuales"]),
        step=1_000,
        key="gastos_anuales_key",
        disabled=lock_profile_fields,
        help="Se interpreta en euros de hoy. El modelo ajusta por inflación para años futuros.",
    )
    safe_withdrawal_rate = st.sidebar.slider(
        "SWR / TRS (%)",
        min_value=2.0,
        max_value=6.0,
        value=float(profile_defaults["safe_withdrawal_rate"] * 100),
        step=0.1,
        key="safe_withdrawal_rate_key",
        disabled=lock_profile_fields,
        help="Tasa de retirada segura usada para calcular objetivo FIRE.",
    ) / 100

    if lock_profile_fields:
        st.sidebar.info(
            f"Perfil activo: {profile_name}. "
            "Estos parámetros están bloqueados. Desmarca 'Bloquear parámetros del perfil' para editarlos."
        )
    if modo_guiado:
        objetivo_cartera = gastos_anuales / safe_withdrawal_rate if safe_withdrawal_rate > 0 else 0
        st.sidebar.info(
            "📌 Objetivo de cartera = Gastos anuales / SWR.\n"
            f"Con tus datos: €{gastos_anuales:,.0f} / {safe_withdrawal_rate*100:.1f}% = €{objetivo_cartera:,.0f}."
        )

    st.sidebar.divider()

    def select_currency_with_exact_input(
        label: str,
        options: List[int],
        default_value: int,
        exact_label: str,
        exact_input_label: str,
        max_exact: int,
        step_exact: int,
        help_text: Optional[str] = None,
        key_prefix: Optional[str] = None,
    ) -> float:
        """Render currency slider with optional exact input override."""
        state_key = key_prefix or re.sub(r"[^a-z0-9_]+", "_", exact_input_label.lower())
        use_exact = st.sidebar.checkbox(
            exact_label,
            value=bool(st.session_state.get(f"{state_key}_exact_mode", False)),
            key=f"{state_key}_exact_mode",
            help="Permite fijar un importe exacto sin saltos de la barra.",
        )
        if use_exact:
            selected_value = st.sidebar.number_input(
                exact_input_label,
                min_value=0,
                max_value=max_exact,
                value=int(st.session_state.get(f"{state_key}_exact_value", default_value)),
                step=step_exact,
                key=f"{state_key}_exact_value",
            )
        else:
            selected_value = st.sidebar.select_slider(
                label,
                options=options,
                value=int(st.session_state.get(f"{state_key}_slider_value", default_value)),
                format_func=lambda x: f"€{x:,.0f}",
                help=help_text,
                key=f"{state_key}_slider_value",
            )
        return float(selected_value)

    def select_int_with_exact_input(
        label: str,
        options: List[int],
        default_value: int,
        exact_checkbox_label: str,
        exact_input_label: str,
        max_exact: int,
        key_prefix: str,
    ) -> Tuple[int, bool]:
        """Render integer select slider with optional exact input override."""
        use_exact = st.checkbox(
            exact_checkbox_label,
            value=bool(st.session_state.get(f"{key_prefix}_exact_mode", False)),
            key=f"{key_prefix}_exact_mode",
            help="Permite fijar un valor exacto sin los saltos de la barra.",
        )
        if use_exact:
            exact_value = int(
                st.number_input(
                    exact_input_label,
                    min_value=0,
                    max_value=max_exact,
                    value=int(st.session_state.get(f"{key_prefix}_exact_value", default_value)),
                    step=1,
                    key=f"{key_prefix}_exact_value",
                )
            )
            return exact_value, True
        selected = int(
            st.select_slider(
                label,
                options=options,
                value=int(st.session_state.get(f"{key_prefix}_slider_value", default_value)),
                key=f"{key_prefix}_slider_value",
            )
        )
        return selected, False

    # STEP 3: Current situation and horizon
    st.sidebar.markdown("### 3) Situación actual")
    patrimonio_min_nonzero = 1_000
    patrimonio_max = 2_000_000
    patrimonio_default = 150_000
    patrimonio_steps = 120
    patrimonio_scale = np.geomspace(patrimonio_min_nonzero, patrimonio_max, patrimonio_steps)
    patrimonio_options = [0]
    for v in patrimonio_scale:
        rounded = int(round(float(v) / 1_000) * 1_000)
        if rounded > patrimonio_options[-1]:
            patrimonio_options.append(rounded)
    if patrimonio_options[-1] != patrimonio_max:
        patrimonio_options.append(patrimonio_max)

    default_idx = min(
        range(len(patrimonio_options)),
        key=lambda i: abs(patrimonio_options[i] - patrimonio_default),
    )
    patrimonio_default_value = patrimonio_options[default_idx]

    patrimonio_inicial = select_currency_with_exact_input(
        label="Patrimonio actual (€)",
        options=patrimonio_options,
        default_value=patrimonio_default_value,
        exact_label="Introducir patrimonio exacto",
        exact_input_label="Patrimonio actual exacto (€)",
        max_exact=20_000_000,
        step_exact=1_000,
        help_text=(
            "Escala exponencial: más precisión en importes bajos y "
            "más recorrido en importes altos."
        ),
        key_prefix="patrimonio",
    )

    aportacion_min_nonzero = 100
    aportacion_max = 50_000
    aportacion_default = 1_000
    aportacion_steps = 110
    aportacion_scale = np.geomspace(aportacion_min_nonzero, aportacion_max, aportacion_steps)
    aportacion_options = [0]
    for v in aportacion_scale:
        rounded = int(round(float(v) / 50) * 50)
        if rounded > aportacion_options[-1]:
            aportacion_options.append(rounded)
    if aportacion_options[-1] != aportacion_max:
        aportacion_options.append(aportacion_max)

    aportacion_default_idx = min(
        range(len(aportacion_options)),
        key=lambda i: abs(aportacion_options[i] - aportacion_default),
    )
    aportacion_default_value = aportacion_options[aportacion_default_idx]

    aportacion_mensual = select_currency_with_exact_input(
        label="Aportación mensual (€)",
        options=aportacion_options,
        default_value=aportacion_default_value,
        exact_label="Introducir aportación exacta",
        exact_input_label="Aportación mensual exacta (€)",
        max_exact=200_000,
        step_exact=50,
        help_text=(
            "Escala exponencial de €0 a €50.000: más precisión en importes bajos "
            "y mejor recorrido en importes altos."
        ),
        key_prefix="aportacion",
    )

    edad_actual = st.sidebar.slider(
        "Edad actual",
        min_value=18,
        max_value=100,
        value=35,
        step=1,
        key="edad_actual_key",
    )
    edad_objetivo = st.sidebar.slider(
        "Edad objetivo FIRE",
        min_value=18,
        max_value=100,
        value=50,
        step=1,
        key="edad_objetivo_key",
    )

    if modo_guiado:
        st.sidebar.caption(
            "Patrimonio = lo que ya tienes invertido. Aportación = lo que añades cada mes."
        )

    cuota_min_nonzero = 50
    cuota_max = 15_000
    cuota_steps = 120
    cuota_scale = np.geomspace(cuota_min_nonzero, cuota_max, cuota_steps)
    cuota_options = [0]
    for v in cuota_scale:
        rounded = int(round(float(v) / 25) * 25)
        if rounded > cuota_options[-1]:
            cuota_options.append(rounded)
    if cuota_options[-1] != cuota_max:
        cuota_options.append(cuota_max)

    months_options = list(range(0, 601))

    with st.sidebar.expander("🏠 Patrimonio inmobiliario y deudas (opcional)", expanded=False):
        vivienda_habitual_valor = st.number_input(
            "Valor vivienda principal (€)",
            min_value=0,
            max_value=10_000_000,
            value=0,
            step=10_000,
            key="vivienda_habitual_valor_key",
        )
        vivienda_habitual_hipoteca = st.number_input(
            "Hipoteca vivienda principal (€)",
            min_value=0,
            max_value=10_000_000,
            value=0,
            step=10_000,
            key="vivienda_habitual_hipoteca_key",
        )
        incluir_cuota_vivienda_en_simulacion = st.checkbox(
            "Incluir cuota de hipoteca de vivienda principal en simulación",
            value=True,
            key="incluir_cuota_vivienda_en_simulacion_key",
            disabled=vivienda_habitual_hipoteca <= 0,
            help="Resta esta cuota de tu capacidad de ahorro antes de FIRE y, si sigue pendiente en FIRE, la suma al gasto anual.",
        )
        cuota_hipoteca_vivienda_mensual = 0.0
        meses_hipoteca_vivienda_restantes = 0
        meses_hipoteca_vivienda_restantes_exact_mode = False
        if vivienda_habitual_hipoteca > 0:
            cuota_hipoteca_vivienda_mensual = select_currency_with_exact_input(
                "Cuota mensual hipoteca vivienda principal (€)",
                options=cuota_options,
                default_value=800 if 800 in cuota_options else cuota_options[min(len(cuota_options) - 1, 10)],
                exact_label="Introducir cuota exacta vivienda",
                exact_input_label="Cuota exacta hipoteca vivienda (€)",
                max_exact=50_000,
                step_exact=25,
                help_text="Importe total mensual de la cuota actual de hipoteca.",
                key_prefix="primary_mortgage_payment",
            )
            meses_hipoteca_vivienda_restantes, meses_hipoteca_vivienda_restantes_exact_mode = select_int_with_exact_input(
                label="Meses restantes hipoteca vivienda principal",
                options=months_options,
                default_value=240,
                exact_checkbox_label="Introducir meses exactos vivienda",
                exact_input_label="Meses exactos hipoteca vivienda principal",
                max_exact=600,
                key_prefix="primary_mortgage_months",
            )
        aplicar_ajuste_vivienda_habitual = st.checkbox(
            "Ajustar gasto de jubilación por vivienda habitual pagada",
            value=False,
            key="aplicar_ajuste_vivienda_habitual_key",
            disabled=vivienda_habitual_valor <= 0,
            help="Si ya tienes vivienda habitual, parte del gasto de jubilación puede reducirse (alquiler/hipoteca).",
        )
        ahorro_vivienda_habitual_anual = st.number_input(
            "Ahorro anual estimado por vivienda habitual (€)",
            min_value=0,
            max_value=200_000,
            value=0,
            step=500,
            key="ahorro_vivienda_habitual_anual_key",
            disabled=not aplicar_ajuste_vivienda_habitual,
            help="Cuánto gasto anual dejarías de necesitar cubrir con la cartera por tener vivienda habitual.",
        )
        inmuebles_invertibles_valor = st.number_input(
            "Valor inmuebles invertibles (€)",
            min_value=0,
            max_value=10_000_000,
            value=0,
            step=10_000,
            key="inmuebles_invertibles_valor_key",
        )
        inmuebles_invertibles_hipoteca = st.number_input(
            "Hipoteca inmuebles invertibles (€)",
            min_value=0,
            max_value=10_000_000,
            value=0,
            step=10_000,
            key="inmuebles_invertibles_hipoteca_key",
        )
        incluir_cuota_inmuebles_en_simulacion = st.checkbox(
            "Incluir cuota de hipoteca de inmuebles invertibles en simulación",
            value=True,
            key="incluir_cuota_inmuebles_en_simulacion_key",
            disabled=inmuebles_invertibles_hipoteca <= 0,
            help="Aplica el mismo criterio de flujos: resta ahorro pre-FIRE y puede sumar gasto si sigue viva tras FIRE.",
        )
        cuota_hipoteca_inmuebles_mensual = 0.0
        meses_hipoteca_inmuebles_restantes = 0
        meses_hipoteca_inmuebles_restantes_exact_mode = False
        if inmuebles_invertibles_hipoteca > 0:
            cuota_hipoteca_inmuebles_mensual = select_currency_with_exact_input(
                "Cuota mensual hipoteca inmuebles invertibles (€)",
                options=cuota_options,
                default_value=600 if 600 in cuota_options else cuota_options[min(len(cuota_options) - 1, 9)],
                exact_label="Introducir cuota exacta inmuebles invertibles",
                exact_input_label="Cuota exacta hipoteca inmuebles invertibles (€)",
                max_exact=50_000,
                step_exact=25,
                help_text="Cuota mensual agregada de hipotecas en inmuebles alquilables/invertibles.",
                key_prefix="investment_mortgage_payment",
            )
            meses_hipoteca_inmuebles_restantes, meses_hipoteca_inmuebles_restantes_exact_mode = select_int_with_exact_input(
                label="Meses restantes hipoteca inmuebles invertibles",
                options=months_options,
                default_value=240,
                exact_checkbox_label="Introducir meses exactos inmuebles invertibles",
                exact_input_label="Meses exactos hipoteca inmuebles invertibles",
                max_exact=600,
                key_prefix="investment_mortgage_months",
            )
        otras_deudas = st.number_input(
            "Otras deudas (€)",
            min_value=0,
            max_value=10_000_000,
            value=0,
            step=5_000,
            key="otras_deudas_key",
        )
        usar_capital_invertible_ampliado = st.checkbox(
            "Usar capital invertible ampliado como base de simulación",
            value=False,
            key="usar_capital_invertible_ampliado_key",
            help="Usa cartera líquida + equity de inmuebles invertibles - otras deudas. No incluye vivienda habitual.",
        )
        renta_bruta_alquiler_anual = st.number_input(
            "Renta bruta anual por alquileres (€)",
            min_value=0,
            max_value=2_000_000,
            value=0,
            step=1_000,
            key="renta_bruta_alquiler_anual_key",
            help="Ingresos brutos anuales por alquiler de inmuebles.",
        )
        usar_modelo_avanzado_alquiler = st.checkbox(
            "Modelo avanzado de alquiler (vacancia/gastos/fiscalidad simple)",
            value=False,
            key="usar_modelo_avanzado_alquiler_key",
            disabled=renta_bruta_alquiler_anual <= 0,
            help="Convierte renta bruta en neta restando vacancia, gastos e IRPF efectivo aproximado.",
        )
        alquiler_costes_vacancia_pct = 0.0
        alquiler_irpf_efectivo_pct = 0.0
        if usar_modelo_avanzado_alquiler:
            alquiler_costes_vacancia_pct = st.slider(
                "Costes + vacancia sobre renta bruta (%)",
                min_value=0.0,
                max_value=60.0,
                value=20.0,
                step=0.5,
                key="alquiler_costes_vacancia_pct_key",
            )
            alquiler_irpf_efectivo_pct = st.slider(
                "IRPF efectivo sobre rendimiento neto (%)",
                min_value=0.0,
                max_value=50.0,
                value=15.0,
                step=0.5,
                key="alquiler_irpf_efectivo_pct_key",
                help="Aproximación fiscal anual para no sobreestimar la renta disponible.",
            )
        incluir_rentas_alquiler_en_simulacion = st.checkbox(
            "Incluir rentas de alquiler en simulación",
            value=True,
            key="incluir_rentas_alquiler_en_simulacion_key",
            help="Suma la renta al ahorro anual y reduce el gasto que debe cubrir la cartera en FIRE (aproximación neta si activas modelo avanzado).",
        )
        if usar_modelo_avanzado_alquiler:
            st.caption(
                "Modelo avanzado activo: renta neta = renta bruta × (1 - costes/vacancia) × (1 - IRPF efectivo)."
            )
        else:
            st.caption(
                "Modo simple: se usa renta bruta como aproximación. No modela gastos deducibles, vacancia ni IRPF inmobiliario."
            )

    with st.sidebar.expander("🧓 Pensión y retiro en 2 tramos (opcional)", expanded=False):
        include_pension_in_simulation = st.checkbox(
            "Incluir planes/pensión en simulación",
            value=False,
            help="Si está desactivado, la simulación no tendrá en cuenta pensión ni planes.",
        )
        two_stage_retirement_model = st.checkbox(
            "Activar tramo pre-pensión y tramo post-pensión",
            value=False,
            disabled=not include_pension_in_simulation,
            help=(
                "Permite modelar una etapa desde FIRE hasta la edad de pensión con retirada más alta "
                "y otra etapa posterior con menor retirada de cartera por efecto de la pensión."
            ),
        )
        edad_pension_oficial = st.slider(
            "Edad legal de pensión (referencia)",
            min_value=50,
            max_value=100,
            value=67,
            step=1,
            disabled=not include_pension_in_simulation,
        )
        edad_inicio_pension_publica = st.slider(
            "Edad de inicio de pensión pública",
            min_value=50,
            max_value=100,
            value=67,
            step=1,
            disabled=not include_pension_in_simulation,
            help="Permite retrasar la pensión pública respecto a la edad legal.",
        )
        bonificacion_demora_pct = st.slider(
            "Ajuste anual por anticipo/demora de pensión pública (%)",
            min_value=0.0,
            max_value=8.0,
            value=4.0,
            step=0.5,
            disabled=not include_pension_in_simulation,
            help=(
                "Se aplica por cada año de diferencia entre edad legal e inicio real. "
                "Si inicias antes, el ajuste total será negativo; si inicias después, positivo."
            ),
        ) / 100.0
        pension_publica_neta_anual = st.number_input(
            "Pensión pública neta anual esperada (€ de hoy)",
            min_value=0,
            max_value=200_000,
            value=0,
            step=1_000,
            disabled=not include_pension_in_simulation,
        )
        years_delta = edad_inicio_pension_publica - edad_pension_oficial
        pension_publica_neta_anual_efectiva = calculate_effective_public_pension_annual(
            pension_publica_neta_anual=pension_publica_neta_anual,
            edad_pension_oficial=edad_pension_oficial,
            edad_inicio_pension_publica=edad_inicio_pension_publica,
            ajuste_anual_pct=bonificacion_demora_pct,
        )
        if include_pension_in_simulation and years_delta > 0:
            st.caption(
                f"Pensión pública ajustada por demora ({years_delta} años): €{pension_publica_neta_anual_efectiva:,.0f}/año."
            )
        elif include_pension_in_simulation and years_delta < 0:
            st.caption(
                f"Pensión pública ajustada por anticipo ({abs(years_delta)} años): €{pension_publica_neta_anual_efectiva:,.0f}/año."
            )
        elif include_pension_in_simulation:
            st.caption(
                f"Pensión pública usada en simulación: €{pension_publica_neta_anual_efectiva:,.0f}/año."
            )

        edad_inicio_plan_privado = st.slider(
            "Edad de inicio del plan privado",
            min_value=50,
            max_value=100,
            value=63,
            step=1,
            disabled=not include_pension_in_simulation,
            help="Permite rescatar plan privado antes o después de la pensión pública.",
        )
        duracion_plan_privado_anos = st.slider(
            "Duración del plan privado (años)",
            min_value=0,
            max_value=40,
            value=0,
            step=1,
            disabled=not include_pension_in_simulation,
            help="Años durante los que se cobra el plan privado (0 = no se cobra).",
        )
        plan_pensiones_privado_neto_anual = st.number_input(
            "Plan de pensiones privado neto anual (€ de hoy)",
            min_value=0,
            max_value=200_000,
            value=0,
            step=1_000,
            disabled=not include_pension_in_simulation,
        )
        otras_rentas_post_jubilacion_netas = st.number_input(
            "Otras rentas netas post-jubilación (€ de hoy)",
            min_value=0,
            max_value=200_000,
            value=0,
            step=500,
            disabled=not include_pension_in_simulation,
            help="Ingresos recurrentes netos esperados que reduzcan la retirada de cartera.",
        )
        pension_neta_anual = (
            pension_publica_neta_anual_efectiva
            + plan_pensiones_privado_neto_anual
            + otras_rentas_post_jubilacion_netas
        )
        pension_neta_anual = pension_neta_anual if include_pension_in_simulation else 0.0

        coste_pre_pension_anual = st.number_input(
            "Coste anual extra antes de pensión pública (€ de hoy)",
            min_value=0,
            max_value=200_000,
            value=0,
            step=500,
            disabled=not include_pension_in_simulation or not two_stage_retirement_model,
            help=(
                "No está ligado al rescate del plan privado. "
                "Aplica solo al tramo previo al inicio de la pensión pública."
            ),
        )
        if include_pension_in_simulation:
            st.caption(
                f"Ingreso neto total considerado post-jubilación: €{pension_neta_anual:,.0f}/año."
            )
        if two_stage_retirement_model and include_pension_in_simulation:
            st.caption(
                "En decumulación, tramo 1 = FIRE→pensión; tramo 2 = post-pensión. "
                "La pensión reduce la retirada que debe cubrir la cartera."
            )
        two_stage_retirement_model = bool(include_pension_in_simulation and two_stage_retirement_model)
        if not include_pension_in_simulation:
            pension_neta_anual = 0.0
            coste_pre_pension_anual = 0.0

    st.sidebar.divider()

    # STEP 4: Market assumptions
    st.sidebar.markdown("### 4) Mercado")
    rentabilidad_esperada = st.sidebar.slider(
        "Rentabilidad esperada anual (%)",
        min_value=-10.0,
        max_value=25.0,
        value=float(profile_defaults["rentabilidad_esperada"] * 100),
        step=0.5,
        disabled=lock_profile_fields,
        help="Rendimiento esperado del portafolio (histórico promedio: 7%)",
    ) / 100

    volatilidad = st.sidebar.slider(
        "Volatilidad estimada (%)",
        min_value=5.0,
        max_value=25.0,
        value=15.0,
        step=1.0,
        help="Desviación estándar de retornos (riesgo de mercado)",
    ) / 100

    inflacion = st.sidebar.slider(
        "Inflación anual (%)",
        min_value=-5.0,
        max_value=20.0,
        value=float(profile_defaults["inflacion"] * 100),
        step=0.5,
        disabled=lock_profile_fields,
        help="Inflación esperada para ajustar poder adquisitivo",
    ) / 100
    inflacionar_aportacion = st.sidebar.checkbox(
        "Actualizar aportación mensual con inflación",
        value=False,
        help="Si se activa, tu aportación sube cada año al ritmo de la inflación.",
    )
    contribution_growth_rate = inflacion if inflacionar_aportacion else 0.0
    if modo_guiado:
        st.sidebar.caption(
            "Por defecto la aportación es fija en euros nominales. Activa esta opción para mantener poder de compra."
        )

    st.sidebar.divider()

    # STEP 5: Fiscal configuration
    st.sidebar.markdown("### 5) Fiscalidad")
    fiscal_mode_label = st.sidebar.selectbox(
        "Modo fiscal",
        options=["España (Tax Pack)", "Internacional básico"],
        index=0,
        help=(
            "España (Tax Pack): fiscalidad regional española detallada. "
            "Internacional básico: aproximación con tasas efectivas manuales."
        ),
    )
    fiscal_mode = (
        FISCAL_MODE_ES_TAXPACK
        if fiscal_mode_label == "España (Tax Pack)"
        else FISCAL_MODE_INTL_BASIC
    )

    fiscal_priority = st.sidebar.selectbox(
        "Prioridad fiscal del cálculo",
        options=[
            "Jubilación",
            "Acumulación",
        ],
        index=0,
        help="Jubilación: prioriza impuestos al retirar. Acumulación: prioriza impuestos antes de FIRE.",
    )
    intl_tax_rates: Dict[str, float] = {
        "gains": 0.10,
        "dividends": 0.15,
        "interest": 0.20,
        "wealth": 0.00,
    }
    if fiscal_mode == FISCAL_MODE_ES_TAXPACK:
        regimen_fiscal = st.sidebar.selectbox(
            "Régimen fiscal",
            options=[
                "España - Fondos de Inversión",
                "España - Cartera Directa",
                "Otro",
            ],
            help="Aplicar tratamiento fiscal específico",
        )

        # Tax optimization context for Spanish users
        if regimen_fiscal == "España - Fondos de Inversión":
            st.sidebar.info(
                "⚖️ **Ventaja FIRE en España:** La Ley de Diferimiento permite traspasos exentos entre fondos "
                "sin tributación, diferiendo impuestos hasta el reembolso final. Esta calculadora usa una "
                "aproximación de impacto fiscal para comparar escenarios. No sustituye asesoría fiscal profesional."
            )

        include_optimización = st.sidebar.checkbox(
            "Incluir optimización de traspasos entre fondos",
            value=False,
            help="Estrategia de harvest-loss para optimizar impuestos",
        )
    else:
        regimen_fiscal = "Otro"
        include_optimización = False
        st.sidebar.info(
            "🌍 Modo internacional básico: aproximación para acumulación con tasas efectivas manuales."
        )
        intl_tax_rates["gains"] = st.sidebar.slider(
            "Impuesto efectivo plusvalías (%)",
            min_value=0.0,
            max_value=60.0,
            value=10.0,
            step=0.5,
        ) / 100.0
        intl_tax_rates["dividends"] = st.sidebar.slider(
            "Impuesto efectivo dividendos (%)",
            min_value=0.0,
            max_value=60.0,
            value=15.0,
            step=0.5,
        ) / 100.0
        intl_tax_rates["interest"] = st.sidebar.slider(
            "Impuesto efectivo intereses (%)",
            min_value=0.0,
            max_value=60.0,
            value=20.0,
            step=0.5,
        ) / 100.0
        intl_tax_rates["wealth"] = st.sidebar.slider(
            "Impuesto anual efectivo sobre patrimonio (%)",
            min_value=0.0,
            max_value=5.0,
            value=0.0,
            step=0.1,
        ) / 100.0

    taxable_withdrawal_ratio_mode = st.sidebar.selectbox(
        "Cálculo de parte retirada que tributa",
        options=["Automático (estimado)", "Manual"],
        index=0,
        help=(
            "Automático: se estima con aportaciones + crecimiento proyectado. "
            "Manual: tú defines el porcentaje."
        ),
    )
    taxable_withdrawal_ratio = 0.40
    if taxable_withdrawal_ratio_mode == "Manual":
        taxable_withdrawal_ratio = st.sidebar.slider(
            "Parte de retirada que tributa en jubilación (%)",
            min_value=0,
            max_value=100,
            value=40,
            step=5,
            help=(
                "Estimación de qué parte de tu retirada anual genera base del ahorro imponible. "
                "Depende de cuánto de la retirada sean plusvalías/intereses frente a principal aportado."
            ),
        ) / 100
        if modo_guiado:
            st.sidebar.caption(
                "Guía rápida: ratio imponible ≈ plusvalías latentes / valor total de la cartera. "
                "Ejemplo: cartera €500k con €200k de plusvalías -> 40% imponible (aprox)."
            )
    elif modo_guiado:
        st.sidebar.caption(
            "Modo automático activo: estimaremos ese porcentaje con tus aportaciones y rentabilidad esperada."
        )

    tax_year = None
    region = None
    tax_pack_meta = None
    tax_pack_meta_errors: List[str] = []
    if fiscal_mode == FISCAL_MODE_ES_TAXPACK and regimen_fiscal in ("España - Fondos de Inversión", "España - Cartera Directa"):
        available_years = list_available_taxpack_years("es")
        if available_years:
            tax_year = st.sidebar.selectbox(
                "Año fiscal (Tax Pack)",
                options=available_years,
                index=len(available_years) - 1,
                help="Conjunto de reglas fiscales versionadas por año.",
            )
            try:
                tax_pack = load_tax_pack(int(tax_year), "es")
                tax_pack_meta = tax_pack.get("meta", {})
                tax_pack_meta_errors = validate_tax_pack_metadata(tax_pack)
                region_options = get_region_options(tax_pack)
                region_labels = [label for _, label in region_options]
                label_to_key = {label: key for key, label in region_options}
                selected_label = st.sidebar.selectbox(
                    "Comunidad / territorio",
                    options=region_labels,
                    index=region_labels.index("Madrid") if "Madrid" in region_labels else 0,
                    help="Se usa para IRPF del ahorro y Patrimonio/ISGF regionales.",
                )
                region = label_to_key[selected_label]
                if tax_pack_meta:
                    st.sidebar.caption(
                        f"Tax Pack {tax_pack_meta.get('country', 'ES')} "
                        f"{tax_pack_meta.get('year', tax_year)} · v{tax_pack_meta.get('version', 'n/a')}"
                    )
                    if tax_pack_meta_errors:
                        st.sidebar.warning("Meta Tax Pack incompleta: " + "; ".join(tax_pack_meta_errors))
            except Exception as e:
                st.sidebar.warning(f"No se pudo cargar Tax Pack {tax_year}: {e}")

    # Compile parameters
    real_estate_value_total = vivienda_habitual_valor + inmuebles_invertibles_valor
    real_estate_mortgage_total = vivienda_habitual_hipoteca + inmuebles_invertibles_hipoteca
    net_worth_data = calculate_net_worth(
        liquid_portfolio=patrimonio_inicial,
        real_estate_value=real_estate_value_total,
        real_estate_mortgage=real_estate_mortgage_total,
        other_liabilities=otras_deudas,
    )
    equity_inmuebles_invertibles = max(0.0, inmuebles_invertibles_valor - inmuebles_invertibles_hipoteca)
    capital_invertible_ampliado = max(0.0, patrimonio_inicial + equity_inmuebles_invertibles - otras_deudas)
    patrimonio_base_simulacion = (
        capital_invertible_ampliado
        if usar_capital_invertible_ampliado
        else patrimonio_inicial
    )

    params = {
        "setup_mode": setup_mode,
        "lock_profile_fields": lock_profile_fields,
        "profile_name": profile_name,
        "apply_profile_defaults": apply_profile_defaults,
        "patrimonio_inicial": patrimonio_inicial,
        "aportacion_mensual": aportacion_mensual,
        "edad_actual": edad_actual,
        "edad_objetivo": edad_objetivo,
        "rentabilidad_esperada": rentabilidad_esperada,
        "volatilidad": volatilidad,
        "inflacion": inflacion,
        "inflacionar_aportacion": inflacionar_aportacion,
        "contribution_growth_rate": contribution_growth_rate,
        "gastos_anuales": gastos_anuales,
        "safe_withdrawal_rate": safe_withdrawal_rate,
        "fiscal_priority": fiscal_priority,
        "fiscal_mode": fiscal_mode,
        "taxable_withdrawal_ratio_mode": taxable_withdrawal_ratio_mode,
        "taxable_withdrawal_ratio": taxable_withdrawal_ratio,
        "regimen_fiscal": regimen_fiscal,
        "include_optimización": include_optimización,
        "intl_tax_rates": intl_tax_rates,
        "simulation_model": "Monte Carlo (Normal)",
        "tax_year": tax_year,
        "region": region,
        "tax_pack_meta": tax_pack_meta,
        "tax_pack_meta_errors": tax_pack_meta_errors,
        "modo_guiado": modo_guiado,
        "vivienda_habitual_valor": vivienda_habitual_valor,
        "vivienda_habitual_hipoteca": vivienda_habitual_hipoteca,
        "incluir_cuota_vivienda_en_simulacion": incluir_cuota_vivienda_en_simulacion,
        "cuota_hipoteca_vivienda_mensual": cuota_hipoteca_vivienda_mensual,
        "meses_hipoteca_vivienda_restantes": meses_hipoteca_vivienda_restantes,
        "meses_hipoteca_vivienda_restantes_exact_mode": meses_hipoteca_vivienda_restantes_exact_mode,
        "aplicar_ajuste_vivienda_habitual": aplicar_ajuste_vivienda_habitual,
        "ahorro_vivienda_habitual_anual": ahorro_vivienda_habitual_anual,
        "inmuebles_invertibles_valor": inmuebles_invertibles_valor,
        "inmuebles_invertibles_hipoteca": inmuebles_invertibles_hipoteca,
        "incluir_cuota_inmuebles_en_simulacion": incluir_cuota_inmuebles_en_simulacion,
        "cuota_hipoteca_inmuebles_mensual": cuota_hipoteca_inmuebles_mensual,
        "meses_hipoteca_inmuebles_restantes": meses_hipoteca_inmuebles_restantes,
        "meses_hipoteca_inmuebles_restantes_exact_mode": meses_hipoteca_inmuebles_restantes_exact_mode,
        # Compatibilidad con nombres anteriores
        "vivienda_principal_valor": vivienda_habitual_valor,
        "vivienda_principal_hipoteca": vivienda_habitual_hipoteca,
        "otros_inmuebles_valor": inmuebles_invertibles_valor,
        "otros_inmuebles_hipoteca": inmuebles_invertibles_hipoteca,
        "otras_deudas": otras_deudas,
        "real_estate_value_total": real_estate_value_total,
        "real_estate_mortgage_total": real_estate_mortgage_total,
        "equity_inmuebles_invertibles": equity_inmuebles_invertibles,
        "capital_invertible_ampliado": capital_invertible_ampliado,
        "usar_capital_invertible_ampliado": usar_capital_invertible_ampliado,
        "renta_bruta_alquiler_anual": renta_bruta_alquiler_anual,
        "usar_modelo_avanzado_alquiler": usar_modelo_avanzado_alquiler,
        "alquiler_costes_vacancia_pct": alquiler_costes_vacancia_pct,
        "alquiler_irpf_efectivo_pct": alquiler_irpf_efectivo_pct,
        "incluir_rentas_alquiler_en_simulacion": incluir_rentas_alquiler_en_simulacion,
        "include_pension_in_simulation": include_pension_in_simulation,
        "two_stage_retirement_model": two_stage_retirement_model,
        "edad_pension_oficial": edad_pension_oficial,
        "edad_inicio_pension_publica": edad_inicio_pension_publica,
        "bonificacion_demora_pct": bonificacion_demora_pct,
        "pension_neta_anual": pension_neta_anual,
        "pension_publica_neta_anual": pension_publica_neta_anual,
        "pension_publica_neta_anual_efectiva": pension_publica_neta_anual_efectiva,
        "edad_inicio_plan_privado": edad_inicio_plan_privado,
        "duracion_plan_privado_anos": duracion_plan_privado_anos,
        "plan_pensiones_privado_neto_anual": plan_pensiones_privado_neto_anual,
        "otras_rentas_post_jubilacion_netas": otras_rentas_post_jubilacion_netas,
        "coste_pre_pension_anual": coste_pre_pension_anual,
        # Compatibilidad con lógica previa
        "usar_patrimonio_neto_en_simulacion": usar_capital_invertible_ampliado,
        "net_worth_data": net_worth_data,
        "patrimonio_base_simulacion": patrimonio_base_simulacion,
    }

    # Profile JSON now preloads widget state only; it must not overwrite manual edits each rerun.
    params["profile_loaded"] = bool(loaded_profile_config)
    params["profile_loaded_warnings"] = loaded_profile_warnings if loaded_profile_config else []

    return params


# =====================================================================
# 6. DASHBOARD - KPIs
# =====================================================================

def render_kpis(simulation_results: Dict, params: Dict) -> None:
    """
    Render top-level KPI metrics in 4-column layout with color coding.
    """
    fire_target = get_display_fire_target(simulation_results, params)
    years_horizon = params["edad_objetivo"] - params["edad_actual"]

    # Determine years to FIRE from real-value median path (today's euros).
    years_to_fire = find_years_to_fire(simulation_results["real_percentile_50"], fire_target)

    success_rate = simulation_results["success_rate_final"]
    
    if success_rate >= 90:
        success_status = "success"
        success_emoji = "🟢"
    elif success_rate >= 75:
        success_status = "warning"
        success_emoji = "🟡"
    else:
        success_status = "danger"
        success_emoji = "🔴"

    active_model = simulation_results.get("model_name", params.get("simulation_model", "n/d"))
    final_nominal = simulation_results["percentile_50"][-1]
    final_real = simulation_results["real_percentile_50"][-1]
    brecha_vs_objetivo = final_real - fire_target
    inflation_factor_horizon = (1 + params["inflacion"]) ** years_horizon
    st.markdown(f"**Método en esta pestaña:** {active_model}")
    with st.expander("Qué hace cada método y cuándo usarlo", expanded=False):
        st.write(
            "- **Monte Carlo (Normal):** genera miles de años posibles con retornos gaussianos. "
            "Útil como referencia rápida y estable.\n"
            "- **Monte Carlo (Bootstrap histórico):** remezcla años reales del histórico. "
            "Útil para evitar depender solo del supuesto normal.\n"
            "- **Backtesting histórico (ventanas móviles):** recorre periodos reales consecutivos "
            "(por ejemplo, 20 años empezando en distintos años). Útil para ver sensibilidad a secuencia histórica.\n\n"
            "**Por qué comparar los tres:** si los resultados convergen, el plan suele ser más robusto; "
            "si divergen mucho, conviene usar supuestos más conservadores."
        )
    if params.get("modo_guiado", False):
        with st.expander("¿Cómo leer estos indicadores?", expanded=False):
            help_lines = (
                "- **Años hasta FIRE**: cuándo llegarías al objetivo en el escenario central.\n"
                "- **Capital al final (P50, euros de hoy)**: poder adquisitivo estimado al final del horizonte, comparado con dinero actual.\n"
                "- **Probabilidad de éxito**: porcentaje de escenarios que sí alcanzan FIRE.\n"
                "- **Rentabilidad real**: crecimiento descontando inflación.\n"
                "- **Objetivo FIRE y alcanzable/no alcanzable**: se evalúan en euros de hoy (valor real).\n"
                "- **Conversión real/nominal**: `real = nominal / (1 + inflación)^años`.\n"
                f"- **Horizonte aplicado en estas tarjetas**: {years_horizon} años.\n"
                f"- **Patrimonio nominal final (P50)**: €{final_nominal:,.0f} (euros futuros).\n"
                f"- **Factor de inflación acumulada**: x{inflation_factor_horizon:.2f} "
                f"(€1 hoy ≈ €{inflation_factor_horizon:.2f} al final).\n"
                f"- **Brecha vs objetivo FIRE (euros de hoy)**: {brecha_vs_objetivo:+,.0f} €."
            )
            nw = params.get("net_worth_data", {})
            if nw:
                help_lines += (
                    "\n"
                    f"- **Base de simulación**: €{params.get('patrimonio_base_simulacion', params['patrimonio_inicial']):,.0f} "
                    f"({'capital invertible ampliado' if params.get('usar_capital_invertible_ampliado') else 'cartera líquida'}).\n"
                    f"- **Patrimonio neto total**: €{nw.get('net_worth', 0):,.0f} "
                    f"(equity inmuebles invertibles: €{params.get('equity_inmuebles_invertibles', 0):,.0f})."
                )
            st.write(help_lines)

    # Layout: 4 columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if years_to_fire is None:
            st.metric(
                label="⏱️ Años hasta FIRE",
                value="No alcanzable",
                delta=f"> {years_horizon} años con escenario base",
                delta_color="off",
            )
        else:
            st.metric(
                label="⏱️ Años hasta FIRE",
                value=years_to_fire,
                delta=f"{years_to_fire - years_horizon:+d} años vs objetivo",
                delta_color="inverse",
            )

    with col2:
        st.metric(
            label="💰 Poder adquisitivo final (P50, € de hoy)",
            value=f"€{final_real:,.0f}",
            delta=f"{brecha_vs_objetivo:+,.0f} € vs objetivo FIRE",
            delta_color="normal",
        )

    with col3:
        st.metric(
            label="📈 Probabilidad de Éxito",
            value=f"{success_rate:.0f}%",
            delta="Percentil 95 no agota capital" if success_rate >= 90 else "Riesgo moderado/alto",
            delta_color="normal" if success_rate >= 90 else "off",
        )

    with col4:
        real_return = (
            ((1 + params["rentabilidad_esperada"]) / (1 + params["inflacion"])) - 1
        ) * 100
        st.metric(
            label="📊 Rentabilidad Real Anual",
            value=f"{real_return:.2f}%",
            delta=f"Ajustado por inflación {params['inflacion']*100:.1f}%",
        )

    col5, col6 = st.columns(2)
    with col5:
        st.metric(
            label="🧾 Patrimonio nominal final (P50)",
            value=f"€{final_nominal:,.0f}",
            delta="Euros futuros al final del horizonte",
            delta_color="off",
        )
    with col6:
        st.metric(
            label="🛒 Factor de inflación acumulada",
            value=f"x{inflation_factor_horizon:.2f}",
            delta=f"€1 hoy ≈ €{inflation_factor_horizon:.2f} al final",
            delta_color="off",
        )

    # Unified narrative insight block
    st.divider()
    emoji_readiness, msg_readiness = generate_fire_readiness_message(years_to_fire, years_horizon)
    _emoji_success, msg_success = generate_success_probability_message(success_rate)
    _emoji_velocity, msg_velocity = generate_savings_velocity_message(
        params["aportacion_mensual"],
        params["gastos_anuales"],
    )
    msg_comparison = generate_horizon_comparison_message(years_to_fire, years_horizon)

    st.markdown(
        "### 🧠 Lectura guiada del escenario\n"
        f"{emoji_readiness} {msg_readiness} {msg_success} {msg_velocity} {msg_comparison}"
    )


def render_tax_trace(params: Dict, tax_pack: Optional[Dict]) -> None:
    """Render auditable tax trace for selected region/year."""
    if params.get("fiscal_mode", FISCAL_MODE_ES_TAXPACK) == FISCAL_MODE_INTL_BASIC:
        if params.get("fiscal_priority") == "Jubilación" and params.get("retirement_tax_context"):
            ctx = params["retirement_tax_context"]
            st.subheader("🧾 Resumen Fiscal Internacional (aproximación anual)")
            st.caption(
                "Estimación simplificada con tasas efectivas manuales para ahorradores con residencia fiscal fuera de España."
            )
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Retirada bruta", f"€{ctx['gross_withdrawal_required']:,.0f}")
            col_b.metric("Impuesto ahorro estimado", f"€{ctx['annual_savings_tax_retirement']:,.0f}")
            col_c.metric("Impuesto patrimonio estimado", f"€{ctx['annual_wealth_tax_retirement']:,.0f}")
            col_d.metric("Total fiscal anual", f"€{ctx['total_annual_tax_retirement']:,.0f}")
        else:
            st.subheader("🧾 Fiscalidad internacional (aproximación)")
            st.caption(
                "En modo internacional básico se aplica un drag fiscal efectivo sobre rentabilidad. "
                "No se calculan tramos IRPF/Patrimonio por CCAA."
            )
        return

    if not tax_pack or not params.get("region"):
        return

    if params.get("fiscal_priority") == "Jubilación" and params.get("retirement_tax_context"):
        ctx = params["retirement_tax_context"]
        gross_withdrawal = ctx["gross_withdrawal_required"]
        taxable_base = gross_withdrawal * params.get(
            "taxable_withdrawal_ratio_effective",
            params.get("taxable_withdrawal_ratio", 0.4),
        )
        savings_detail = calculate_savings_tax_with_details(taxable_base, tax_pack, params["region"])
        wealth_detail = calculate_wealth_taxes_with_details(ctx["target_portfolio_gross"], tax_pack, params["region"])

        st.subheader("🧾 Resumen Fiscal en Jubilación (estimación anual)")
        st.caption("Estimación sobre retirada anual y cartera objetivo durante la jubilación.")
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Retirada bruta", f"€{gross_withdrawal:,.0f}")
        col_b.metric("IRPF ahorro retiro", f"€{ctx['annual_savings_tax_retirement']:,.0f}")
        col_c.metric("Patrimonio + ISGF", f"€{ctx['annual_wealth_tax_retirement']:,.0f}")
        col_d.metric("Total fiscal retiro", f"€{ctx['total_annual_tax_retirement']:,.0f}")

        with st.expander("Ver detalle técnico (jubilación)", expanded=False):
            st.write(
                f"Base imponible estimada de retirada: €{taxable_base:,.0f} "
                f"({params.get('taxable_withdrawal_ratio_effective', params.get('taxable_withdrawal_ratio', 0.4))*100:.0f}% de la retirada)."
            )
            st.write(
                f"Objetivo FIRE bruto estimado: €{ctx['target_portfolio_gross']:,.0f} "
                f"(vs objetivo base €{ctx['base_target']:,.0f})."
            )
            if savings_detail["lines"]:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Tramo": line["step"],
                                "Hasta": line["upper"] if line["upper"] is not None else "∞",
                                "Tipo": f"{line['rate']*100:.2f}%",
                                "Base": line["taxable_in_bracket"],
                                "Cuota": line["quota"],
                            }
                            for line in savings_detail["lines"]
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )
            st.write(
                f"IP neta estimada: €{wealth_detail['ip_tax']:,.0f} | "
                f"ISGF neto estimado: €{wealth_detail['isgf_tax_net']:,.0f}."
            )

        with st.expander("Ver detalle anual por tramos (bases separadas)", expanded=False):
            net_spending_base = float(params.get("gasto_anual_neto_cartera", params["gastos_anuales"]))
            taxable_ratio = float(
                params.get(
                    "taxable_withdrawal_ratio_effective",
                    params.get("taxable_withdrawal_ratio", 0.4),
                )
            )
            use_two_stage = bool(
                params.get("two_stage_retirement_model", False)
                and params.get("include_pension_in_simulation", False)
            )
            fire_age = int(params.get("edad_objetivo", 0))
            pension_start_age = int(
                params.get("edad_inicio_pension_publica", params.get("edad_pension_oficial", 67))
            )
            private_start_age = int(params.get("edad_inicio_plan_privado", pension_start_age))
            private_duration = int(params.get("duracion_plan_privado_anos", 0))
            private_end_age = private_start_age + private_duration - 1

            def income_general_for_age(age: int) -> float:
                if not params.get("include_pension_in_simulation", False):
                    return 0.0
                income_public = (
                    float(params.get("pension_publica_neta_anual_efectiva", 0.0))
                    if age >= pension_start_age
                    else 0.0
                )
                income_private = (
                    float(params.get("plan_pensiones_privado_neto_anual", 0.0))
                    if private_duration > 0 and private_start_age <= age <= private_end_age
                    else 0.0
                )
                income_other = (
                    float(params.get("otras_rentas_post_jubilacion_netas", 0.0))
                    if age >= pension_start_age
                    else 0.0
                )
                return income_public + income_private + income_other

            stage_rows: List[Dict[str, Any]] = []
            if use_two_stage:
                pre_extra = float(params.get("coste_pre_pension_anual", 0.0))
                pre_general_income = income_general_for_age(fire_age)
                post_general_income = income_general_for_age(max(fire_age, pension_start_age))
                stage_inputs = [
                    (
                        "Pre-pensión",
                        max(0.0, net_spending_base + pre_extra - pre_general_income),
                        pre_general_income,
                    ),
                    (
                        "Post-pensión",
                        max(0.0, net_spending_base - post_general_income),
                        post_general_income,
                    ),
                ]
            else:
                single_general_income = income_general_for_age(fire_age)
                stage_inputs = [
                    (
                        "Retiro (único tramo)",
                        max(0.0, net_spending_base - single_general_income),
                        single_general_income,
                    )
                ]

            for stage_name, net_from_portfolio, base_general in stage_inputs:
                taxable_base_stage = max(0.0, net_from_portfolio * taxable_ratio)
                general_stage = calculate_general_tax_with_details(
                    base_general, tax_pack, params["region"]
                )
                savings_stage = calculate_savings_tax_with_details(
                    taxable_base_stage, tax_pack, params["region"]
                )
                wealth_stage = calculate_wealth_taxes_with_details(
                    ctx["target_portfolio_gross"], tax_pack, params["region"]
                )
                total_stage = (
                    general_stage["tax"]
                    + savings_stage["tax"]
                    + wealth_stage["total_wealth_tax"]
                )
                stage_rows.append(
                    {
                        "Tramo": stage_name,
                        "Gasto neto objetivo (€)": net_spending_base,
                        "Base general estimada (€)": base_general,
                        "Retirada neta desde cartera (€)": net_from_portfolio,
                        "Ratio imponible ahorro (%)": taxable_ratio * 100,
                        "Base ahorro estimada (€)": taxable_base_stage,
                        "IRPF base general estimado (€)": general_stage["tax"],
                        "IRPF ahorro estimado (€)": savings_stage["tax"],
                        "Patrimonio+ISGF estimado (€)": wealth_stage["total_wealth_tax"],
                        "Fiscal anual total estimada (€)": total_stage,
                    }
                )

            st.dataframe(
                pd.DataFrame(stage_rows).style.format(
                    {
                        "Gasto neto objetivo (€)": "€{:,.0f}",
                        "Base general estimada (€)": "€{:,.0f}",
                        "Retirada neta desde cartera (€)": "€{:,.0f}",
                        "Ratio imponible ahorro (%)": "{:.1f}%",
                        "Base ahorro estimada (€)": "€{:,.0f}",
                        "IRPF base general estimado (€)": "€{:,.0f}",
                        "IRPF ahorro estimado (€)": "€{:,.0f}",
                        "Patrimonio+ISGF estimado (€)": "€{:,.0f}",
                        "Fiscal anual total estimada (€)": "€{:,.0f}",
                    }
                ),
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "Base general (pensión y otras rentas) y base del ahorro (retirada tributable) se muestran separadas. "
                "En este bloque se estima IRPF base general + IRPF ahorro + Patrimonio/ISGF por tramo."
            )
        return

    st.subheader("🧾 Resumen Fiscal (estimación anual)")
    st.caption("Estimación orientativa para un año tipo con el Tax Pack y región seleccionados.")

    assumed_growth = max(0.0, params["patrimonio_inicial"] * params["rentabilidad_neta_simulacion"])
    assumed_wealth = params["patrimonio_inicial"] + params["aportacion_mensual"] * 12 + assumed_growth

    savings_detail = calculate_savings_tax_with_details(assumed_growth, tax_pack, params["region"])
    wealth_detail = calculate_wealth_taxes_with_details(assumed_wealth, tax_pack, params["region"])
    total_tax = savings_detail["tax"] + wealth_detail["total_wealth_tax"]

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Base ahorro", f"€{assumed_growth:,.0f}")
    col_b.metric("IRPF ahorro", f"€{savings_detail['tax']:,.0f}")
    col_c.metric("Patrimonio + ISGF", f"€{wealth_detail['total_wealth_tax']:,.0f}")
    col_d.metric("Total fiscal estimado", f"€{total_tax:,.0f}")

    st.markdown(
        f"- Región: **{savings_detail['region']}**  \n"
        f"- Sistema de ahorro aplicado: **{savings_detail['system']}**  \n"
        f"- Patrimonio estimado para cálculo: **€{assumed_wealth:,.0f}**"
    )

    with st.expander("Ver detalle técnico (tramos y bases)", expanded=False):
        left, right = st.columns(2)

        with left:
            st.markdown("**IRPF ahorro**")
            if savings_detail["lines"]:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Tramo": line["step"],
                                "Hasta": line["upper"] if line["upper"] is not None else "∞",
                                "Tipo": f"{line['rate']*100:.2f}%",
                                "Base": line["taxable_in_bracket"],
                                "Cuota": line["quota"],
                            }
                            for line in savings_detail["lines"]
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.write("Sin cuota para la base estimada.")

        with right:
            st.markdown("**Patrimonio + ISGF**")
            st.write(
                f"Base IP: €{wealth_detail['ip_base']:,.0f} | "
                f"Bonificación IP: {wealth_detail['ip_bonus_pct']*100:.1f}%"
            )
            st.write(
                f"IP neta: €{wealth_detail['ip_tax']:,.0f} | "
                f"ISGF neto: €{wealth_detail['isgf_tax_net']:,.0f}"
            )

# =====================================================================
# 7. VISUALIZATION - CHARTS & GRAPHS
# =====================================================================

def render_main_chart(simulation_results: Dict, params: Dict) -> None:
    """
    Primary chart: Portfolio evolution with uncertainty cone (percentiles 5-95).
    Uses Plotly for interactivity.
    """
    years = np.arange(len(simulation_results["percentile_50"]))
    fire_target = get_display_fire_target(simulation_results, params)
    
    fig = go.Figure()

    # Percentile band: 5-95 (main uncertainty cone)
    fig.add_trace(
        go.Scatter(
            x=years,
            y=simulation_results["percentile_95"],
            fill=None,
            mode="lines",
            line_color="rgba(0,0,0,0)",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=years,
            y=simulation_results["percentile_5"],
            fill="tonexty",
            mode="lines",
            line_color="rgba(0,0,0,0)",
            name="Percentiles 5-95",
            fillcolor="rgba(31, 119, 180, 0.15)",
            hoverinfo="skip",
        )
    )

    # Percentile band: 25-75
    fig.add_trace(
        go.Scatter(
            x=years,
            y=simulation_results["percentile_75"],
            fill=None,
            mode="lines",
            line_color="rgba(0,0,0,0)",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=years,
            y=simulation_results["percentile_25"],
            fill="tonexty",
            mode="lines",
            line_color="rgba(0,0,0,0)",
            name="Percentiles 25-75",
            fillcolor="rgba(31, 119, 180, 0.30)",
            hoverinfo="skip",
        )
    )

    # Median (P50) line
    fig.add_trace(
        go.Scatter(
            x=years,
            y=simulation_results["percentile_50"],
            mode="lines",
            name="Mediana (P50)",
            line=dict(color="rgb(31, 119, 180)", width=3),
            hovertemplate="<b>Año %{x}</b><br>Portafolio: €%{y:,.0f}<extra></extra>",
        )
    )

    # Inflation-adjusted FIRE target in nominal euros (for chart consistency).
    target_path_nominal = np.array(
        [fire_target * ((1 + params["inflacion"]) ** y) for y in years]
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=target_path_nominal,
            mode="lines",
            name="Objetivo FIRE (nominal, ajustado inflación)",
            line=dict(color="rgb(46, 204, 113)", dash="dash", width=2),
            hovertemplate="<b>Año %{x}</b><br>Objetivo FIRE: €%{y:,.0f}<extra></extra>",
        )
    )

    model_name = simulation_results.get("model_name", "")
    is_backtest = "backtesting" in model_name.lower()
    if is_backtest:
        worst_path = simulation_results.get("worst_path_nominal")
        best_path = simulation_results.get("best_path_nominal")
        if worst_path is not None and len(worst_path) == len(years):
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=worst_path,
                    mode="lines",
                    name="Ventana crítica (peor histórica)",
                    line=dict(color="rgba(231, 76, 60, 0.9)", width=2, dash="dot"),
                    hovertemplate="<b>Año %{x}</b><br>Peor ventana: €%{y:,.0f}<extra></extra>",
                )
            )
        if best_path is not None and len(best_path) == len(years):
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=best_path,
                    mode="lines",
                    name="Ventana favorable (mejor histórica)",
                    line=dict(color="rgba(46, 204, 113, 0.9)", width=2, dash="dot"),
                    hovertemplate="<b>Año %{x}</b><br>Mejor ventana: €%{y:,.0f}<extra></extra>",
                )
            )

    fig.update_layout(
        title=f"<b>Evolución del Portafolio - {simulation_results.get('model_name', 'Simulación')}</b>",
        xaxis_title="Años desde hoy",
        yaxis_title="Valor del Portafolio (€, nominal)",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        yaxis=dict(tickformat=",.0f"),
    )

    if is_backtest and simulation_results.get("backtest_diagnostics"):
        d = simulation_results["backtest_diagnostics"]
        worst_span = (
            f"{d['worst_window_start_year']}-{d['worst_window_end_year']}"
            if d.get("worst_window_start_year") is not None and d.get("worst_window_end_year") is not None
            else "n/d"
        )
        best_span = (
            f"{d['best_window_start_year']}-{d['best_window_end_year']}"
            if d.get("best_window_start_year") is not None and d.get("best_window_end_year") is not None
            else "n/d"
        )
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.99,
            align="left",
            showarrow=False,
            bordercolor="rgba(52, 73, 94, 0.35)",
            borderwidth=1,
            bgcolor="rgba(255, 255, 255, 0.8)",
            text=(
                f"<b>Backtesting crítico</b><br>"
                f"Peor ventana: {worst_span} → €{float(d.get('worst_final_real', 0.0)):,.0f} reales<br>"
                f"Mejor ventana: {best_span} → €{float(d.get('best_final_real', 0.0)):,.0f} reales"
            ),
        )

    model_key = (
        simulation_results.get("model_name", params.get("simulation_model", "model"))
        .lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
    )
    render_plotly_chart(fig, key=f"main_chart_{model_key}")

    if is_backtest and simulation_results.get("backtest_diagnostics"):
        d = simulation_results["backtest_diagnostics"]
        windows_count = int(d.get("windows_count", 0))
        data_start = d.get("data_start_year")
        data_end = d.get("data_end_year")
        months_min = d.get("min_months_observed")
        months_avg = d.get("avg_months_observed")
        st.caption(
            "Indicadores de fidelidad del backtesting: "
            f"ventanas evaluadas={windows_count}, "
            f"histórico={data_start}-{data_end}, "
            f"calidad de cobertura mensual min/prom={months_min if months_min is not None else 'n/d'}/{(f'{months_avg:.1f}' if months_avg is not None else 'n/d')}."
        )
        st.caption(
            "Lectura de puntos críticos: la línea roja muestra una secuencia histórica adversa (riesgo de secuencia en acumulación/FIRE) "
            "y la verde una secuencia favorable. La diferencia entre ambas acota la sensibilidad histórica del plan."
        )

        worst_real = float(d.get("worst_final_real", 0.0))
        best_real = float(d.get("best_final_real", 0.0))
        seq_spread_real = best_real - worst_real
        worst_path_real = simulation_results.get("worst_path_real")
        best_path_real = simulation_results.get("best_path_real")
        worst_years_to_fire = (
            find_years_to_fire(np.array(worst_path_real, dtype=float), fire_target)
            if worst_path_real is not None
            else None
        )
        best_years_to_fire = (
            find_years_to_fire(np.array(best_path_real, dtype=float), fire_target)
            if best_path_real is not None
            else None
        )
        if worst_years_to_fire is not None and best_years_to_fire is not None:
            timeline_gap_text = f"{(worst_years_to_fire - best_years_to_fire):+d} años (crítica vs favorable)"
        elif worst_years_to_fire is None and best_years_to_fire is not None:
            timeline_gap_text = "Crítica: no alcanza FIRE"
        elif worst_years_to_fire is not None and best_years_to_fire is None:
            timeline_gap_text = "Favorable: no alcanza FIRE"
        else:
            timeline_gap_text = "Ninguna ventana alcanza FIRE"

        seq_col1, seq_col2, seq_col3 = st.columns(3)
        seq_col1.metric(
            "🧨 Riesgo de secuencia (brecha final real)",
            f"€{seq_spread_real:,.0f}",
            delta="Mejor ventana - peor ventana",
            delta_color="off",
        )
        seq_col2.metric(
            "⏱️ FIRE en ventana crítica",
            f"{worst_years_to_fire} años" if worst_years_to_fire is not None else "No alcanzable",
        )
        seq_col3.metric(
            "⚡ FIRE en ventana favorable",
            f"{best_years_to_fire} años" if best_years_to_fire is not None else "No alcanzable",
            delta=timeline_gap_text,
            delta_color="off",
        )
    if params.get("modo_guiado", False):
        st.caption(
            "Lectura rápida: línea azul = escenario central. Banda ancha = incertidumbre. "
            "Línea verde discontinua = objetivo FIRE."
        )
    
    # Dynamic chart insights
    with st.expander("💡 Entender tu Cono de Incertidumbre", expanded=False):
        msg_volatility = generate_market_scenario_message(
            params["rentabilidad_esperada"], 
            params["volatilidad"]
        )
        st.info(msg_volatility)


def render_success_distribution_chart(simulation_results: Dict, params: Dict) -> None:
    """
    Secondary chart: Year-by-year probability of reaching FIRE target.
    """
    years = np.arange(len(simulation_results["yearly_success"]))
    success_rate = simulation_results["yearly_success"]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=years,
            y=success_rate,
            name="% Simulaciones que alcanzan FIRE",
            marker=dict(
                color=success_rate,
                colorscale="RdYlGn",
                showscale=True,
                colorbar=dict(title="% Éxito"),
            ),
            hovertemplate="<b>Año %{x}</b><br>Éxito: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Probabilidad Acumulada de Alcanzar FIRE por Año</b>",
        xaxis_title="Años desde hoy",
        yaxis_title="Porcentaje de simulaciones (%)",
        template="plotly_white",
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=False,
    )

    model_key = (
        simulation_results.get("model_name", params.get("simulation_model", "model"))
        .lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
    )
    render_plotly_chart(fig, key=f"success_chart_{model_key}")
    if params.get("modo_guiado", False):
        st.caption(
            "Cada barra muestra la probabilidad acumulada de haber alcanzado FIRE en ese año."
        )
    
    # Dynamic success distribution insights
    success_final = simulation_results["success_rate_final"]
    if success_final >= 90:
        st.success(
            f"🎯 **Probabilidad alta:** {success_final:.0f}% de escenarios alcanzan FIRE."
        )
    elif success_final >= 75:
        st.info(
            f"✅ **Probabilidad aceptable:** {success_final:.0f}% de escenarios alcanzan FIRE."
        )
    elif success_final >= 60:
        st.warning(
            f"⚠️ **Riesgo moderado:** {success_final:.0f}% de escenarios alcanzan FIRE."
        )
    else:
        st.error(
            f"🔴 **Riesgo alto:** {success_final:.0f}% de escenarios alcanzan FIRE."
        )


# =====================================================================
# 8. SENSITIVITY ANALYSIS - 5x5 MATRIX
# =====================================================================

def render_sensitivity_analysis(params: Dict) -> None:
    """
    5x5 matrix: Returns vs Inflation scenarios.
    Shows impact on years to FIRE with color coding.
    
    Improvements:
    - Explicit matrix dimensions (5x5)
    - Green/Orange/Red color bands
    - Shows actual years calculation
    """
    st.subheader("🎯 Análisis de Sensibilidad - Matriz de Escenarios")
    st.caption(
        "Impacto en años hasta FIRE cuando rentabilidad/inflación varían respecto a valores base"
    )
    if params.get("modo_guiado", False):
        st.info(
            "Esta matriz es avanzada. Si estás empezando, úsala solo para comparar si tu plan "
            "cambia mucho cuando el mercado va mejor o peor."
        )

    base_return = params.get("rentabilidad_neta_simulacion", params["rentabilidad_esperada"]) * 100
    base_inflation = params["inflacion"] * 100
    fire_target = params.get("fire_target_effective", params["gastos_anuales"] / params["safe_withdrawal_rate"])
    years_horizon = params["edad_objetivo"] - params["edad_actual"]

    # Define matrix parameters
    return_offsets = [-2, -1, 0, 1, 2]  # % points
    inflation_offsets = [-2, -1, 0, 1, 2]  # % points

    sensitivity_matrix = np.zeros((len(inflation_offsets), len(return_offsets)))
    reachability_matrix = np.zeros((len(inflation_offsets), len(return_offsets)), dtype=bool)

    for i, inf_offset in enumerate(inflation_offsets):
        for j, ret_offset in enumerate(return_offsets):
            test_return = (base_return + ret_offset) / 100
            test_inflation = (base_inflation + inf_offset) / 100

            # Quick projection
            portfolio = params["patrimonio_inicial"]
            years_to_target = None

            for year in range(1, years_horizon + 1):
                portfolio = (
                    portfolio * (1 + test_return)
                    + params["aportacion_mensual"] * 12
                )
                real_portfolio = portfolio / ((1 + test_inflation) ** year)
                if real_portfolio >= fire_target:
                    years_to_target = year
                    break

            reachability_matrix[i, j] = years_to_target is not None
            sensitivity_matrix[i, j] = (
                years_to_target if years_to_target else years_horizon
            )

    # Create DataFrame for display
    df_sensitivity = pd.DataFrame(
        sensitivity_matrix,
        index=[f"{inf:+.1f}%" for inf in inflation_offsets],
        columns=[f"{ret:+.1f}%" for ret in return_offsets],
    )

    # Render as heatmap with improved color scaling (Z-score normalization for better contrast)
    # Normalize matrix to [0, 1] for better color sensitivity
    z_min = sensitivity_matrix.min()
    z_max = sensitivity_matrix.max()
    z_normalized = (sensitivity_matrix - z_min) / (z_max - z_min) if z_max > z_min else sensitivity_matrix
    
    fig = go.Figure(
        data=go.Heatmap(
            z=sensitivity_matrix,
            x=[f"Renta {ret:+.0f}pp" for ret in return_offsets],
            y=[f"Inflación {inf:+.0f}pp" for inf in inflation_offsets],
            colorscale=[
                [0, "rgb(46, 204, 113)"],  # Green
                [0.5, "rgb(243, 156, 18)"],  # Orange
                [1, "rgb(231, 76, 60)"],  # Red
            ],
            zmin=z_min,
            zmax=z_max,
            text=np.round(sensitivity_matrix, 1),  # Display with 1 decimal for more granularity
            texttemplate="%{text} años",
            textfont={"size": 10},
            colorbar=dict(title="Años a FIRE"),
        )
    )

    fig.update_layout(
        title="<b>Matriz de Sensibilidad: Impacto en Timeline FIRE</b>",
        height=400,
        xaxis_title="Rentabilidad esperada",
        yaxis_title="Inflación esperada",
    )

    render_plotly_chart(fig, key="sensitivity_matrix_chart")

    # Dynamic sensitivity insights  
    sensitivity_col1, sensitivity_col2 = st.columns(2)
    
    with sensitivity_col1:
        min_years = sensitivity_matrix.min()
        max_years = sensitivity_matrix.max()
        range_years = max_years - min_years
        total_scenarios = sensitivity_matrix.size
        reached_scenarios = int(reachability_matrix.sum())
        center_i = inflation_offsets.index(0)
        center_j = return_offsets.index(0)
        base_reachable = bool(reachability_matrix[center_i, center_j])
        
        with st.expander("📊 Interpretación de resultados", expanded=False):
            st.write(
                f"**Rango observado:** {min_years:.0f} a {max_years:.0f} años (~{range_years:.0f} años de variación)"
            )
            st.write(
                f"**Escenarios alcanzables en la matriz:** {reached_scenarios}/{total_scenarios}"
            )
            st.write(
                "**Verde (<15 años):** Escenario optimista - Alcanzable en corto plazo"
            )
            st.write(
                "**Naranja (15-25 años):** Escenario realista - Horizonte moderado"
            )
            st.write(
                "**Rojo (>25 años):** Escenario conservador - Horizonte desafiante"
            )
    
    with sensitivity_col2:
        # Dynamic message about sensitivity
        if reached_scenarios == 0:
            st.error(
                "🔴 **No alcanzable en la matriz de sensibilidad.** Ninguno de los escenarios "
                "de rentabilidad/inflación llega a FIRE en el horizonte actual."
            )
        elif not base_reachable:
            st.warning(
                f"⚠️ **Escenario base no alcanzable.** Aunque {reached_scenarios}/{total_scenarios} "
                "escenarios alternativos sí llegan, tu configuración base no alcanza FIRE."
            )
        elif reached_scenarios < total_scenarios:
            st.info(
                f"📌 **Alcanzable solo en parte de escenarios.** {reached_scenarios}/{total_scenarios} "
                "combinaciones de rentabilidad/inflación alcanzan FIRE en horizonte."
            )
        elif range_years < 10:
            st.success(
                f"✅ **Tu plan es robusto.** Variaciones de rentabilidad/inflación solo mueven "
                f"el timeline en {range_years:.1f} años. Eres resiliente a cambios de mercado."
            )
        elif range_years < 20:
            st.info(
                f"⚡ **Sensibilidad moderada.** Tu timeline puede variar {range_years:.1f} años "
                f"según condiciones. Monitorea mercados pero no entres en pánico."
            )
        else:
            st.warning(
                f"⚠️ **Alta sensibilidad.** Tu plan varía {range_years:.1f} años según escenarios. "
                f"Considera aumentar ahorros para menos dependencia de mercados optimistas."
            )


# =====================================================================
# 9. ACCUMULATION + EXPORT FUNCTIONALITY
# =====================================================================

def render_accumulation_box(simulation_results: Dict, params: Dict) -> None:
    """Render accumulation table and summary cards (pre-FIRE phase)."""
    st.subheader("📈 Acumulación de capital (antes de FIRE)")
    st.caption("Evolución anual durante la fase de acumulación en escenarios P5/P25/P50/P75/P95.")

    total_points = len(simulation_results["percentile_50"])
    if total_points <= 1:
        st.info("No hay horizonte suficiente para mostrar acumulación anual.")
        return

    # Show year 0 as initial state; table starts at year 1 to align with yearly contribution flow.
    initial_nominal = float(simulation_results["percentile_50"][0])
    initial_real = float(simulation_results["real_percentile_50"][0])
    st.caption(
        f"Año 0 (inicio): P50 nominal €{initial_nominal:,.0f} | P50 real €{initial_real:,.0f}."
    )

    years = np.arange(1, total_points)
    ages = params["edad_actual"] + years
    g = float(params.get("contribution_growth_rate", 0.0))
    annual_contrib = np.array(
        [
            float(params.get("aportacion_mensual_efectiva", params["aportacion_mensual"])) * 12 * ((1 + g) ** (y - 1))
            for y in years
        ]
    )
    cumulative_contrib = np.cumsum(annual_contrib)

    accumulation_df = pd.DataFrame(
        {
            "Año": years,
            "Edad": ages,
            "Aportación anual efectiva (€)": annual_contrib,
            "Aportación acumulada (€)": cumulative_contrib,
            "P5 nominal (€)": simulation_results["percentile_5"][1:],
            "P25 nominal (€)": simulation_results["percentile_25"][1:],
            "P50 nominal (€)": simulation_results["percentile_50"][1:],
            "P75 nominal (€)": simulation_results["percentile_75"][1:],
            "P95 nominal (€)": simulation_results["percentile_95"][1:],
            "P5 real (€ hoy)": simulation_results["real_percentile_5"][1:],
            "P25 real (€ hoy)": simulation_results["real_percentile_25"][1:],
            "P50 real (€ hoy)": simulation_results["real_percentile_50"][1:],
            "P75 real (€ hoy)": simulation_results["real_percentile_75"][1:],
            "P95 real (€ hoy)": simulation_results["real_percentile_95"][1:],
        }
    )
    st.dataframe(
        accumulation_df.style.format(
            {
                "Aportación anual efectiva (€)": "€{:,.0f}",
                "Aportación acumulada (€)": "€{:,.0f}",
                "P5 nominal (€)": "€{:,.0f}",
                "P25 nominal (€)": "€{:,.0f}",
                "P50 nominal (€)": "€{:,.0f}",
                "P75 nominal (€)": "€{:,.0f}",
                "P95 nominal (€)": "€{:,.0f}",
                "P5 real (€ hoy)": "€{:,.0f}",
                "P25 real (€ hoy)": "€{:,.0f}",
                "P50 real (€ hoy)": "€{:,.0f}",
                "P75 real (€ hoy)": "€{:,.0f}",
                "P95 real (€ hoy)": "€{:,.0f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )

    fire_target = get_display_fire_target(simulation_results, params)
    years_to_fire_by_percentile = {
        "P5": find_years_to_fire(simulation_results["real_percentile_5"], fire_target),
        "P25": find_years_to_fire(simulation_results["real_percentile_25"], fire_target),
        "P50": find_years_to_fire(simulation_results["real_percentile_50"], fire_target),
        "P75": find_years_to_fire(simulation_results["real_percentile_75"], fire_target),
        "P95": find_years_to_fire(simulation_results["real_percentile_95"], fire_target),
    }

    summary_cols = st.columns(5)
    for col, label in zip(summary_cols, ["P5", "P25", "P50", "P75", "P95"]):
        years_value = years_to_fire_by_percentile[label]
        delta_label = f"{years_value} años hasta FIRE" if years_value is not None else "No alcanza FIRE"
        col.metric(
            f"{label} capital final",
            f"€{float(accumulation_df[f'{label} nominal (€)'].iloc[-1]):,.0f}",
            delta=delta_label,
            delta_color="normal" if years_value is not None else "off",
        )

    st.caption(
        f"Aportación acumulada total en horizonte: €{annual_contrib.sum():,.0f}. "
        "Años a FIRE se evalúan en euros reales (poder adquisitivo de hoy)."
    )


def render_export_options(simulation_results: Dict, params: Dict) -> None:
    """
    Export CSV/JSON and browser print-to-PDF.
    """
    st.subheader("📥 Exportar Resultados")

    col1, col2, col3 = st.columns(3)

    with col1:
        # CSV Export
        years = np.arange(len(simulation_results["percentile_50"]))
        fire_target = get_display_fire_target(simulation_results, params)

        export_data = pd.DataFrame(
            {
                "Año": years,
                "Modelo": simulation_results.get("model_name", params.get("simulation_model", "n/d")),
                "SWR": params["safe_withdrawal_rate"],
                "P5 (€)": simulation_results["percentile_5"].astype(int),
                "P25 (€)": simulation_results["percentile_25"].astype(int),
                "P50 - Mediana (€)": simulation_results["percentile_50"].astype(int),
                "P75 (€)": simulation_results["percentile_75"].astype(int),
                "P95 (€)": simulation_results["percentile_95"].astype(int),
                "% Éxito Acumulado": simulation_results["yearly_success"],
                "Objetivo FIRE (€)": int(fire_target),
            }
        )

        csv_buffer = export_data.to_csv(index=False).encode()
        st.download_button(
            label="📊 Descargar CSV (Serie Completa)",
            data=csv_buffer,
            file_name=f"fire_projection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch",
        )

    with col2:
        profile_payload = serialize_profile(params)
        st.download_button(
            label="💾 Descargar perfil (JSON)",
            data=json.dumps(profile_payload, ensure_ascii=False, indent=2),
            file_name=f"fire_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width="stretch",
        )
        scenario_payload = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "model": simulation_results.get("model_name", params.get("simulation_model", "n/d")),
                "fiscal_mode": params.get("fiscal_mode", FISCAL_MODE_ES_TAXPACK),
            },
            "params": serialize_profile(params),
            "summary": {
                "success_rate_final": float(simulation_results.get("success_rate_final", 0.0)),
                "final_median_nominal": float(simulation_results.get("final_median", 0.0)),
                "final_median_real": float(simulation_results.get("final_median_real", 0.0)),
                "fire_target_display": float(fire_target),
            },
        }
        st.download_button(
            label="🧩 Descargar JSON (escenario)",
            data=json.dumps(scenario_payload, ensure_ascii=False, indent=2),
            file_name=f"fire_scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width="stretch",
        )

    with col3:
        if "print_nonce" not in st.session_state:
            st.session_state["print_nonce"] = 0
        if "print_nonce_rendered" not in st.session_state:
            st.session_state["print_nonce_rendered"] = -1
        if st.button(
            "🖨️ Imprimir / Guardar PDF",
            key="print_page_button",
            width="stretch",
            help="Abre el diálogo nativo del navegador para imprimir o guardar como PDF.",
        ):
            st.session_state["print_nonce"] += 1
        if st.session_state["print_nonce"] != st.session_state["print_nonce_rendered"]:
            nonce = st.session_state["print_nonce"]
            if nonce > 0:
                components.html(
                    f"<div id='print-trigger-{nonce}'></div><script>setTimeout(() => window.print(), 0);</script>",
                    height=0,
                )
                st.session_state["print_nonce_rendered"] = nonce
        st.caption("Usa la impresora PDF del navegador para generar el informe en un clic.")

    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 14px;'>"
        "<p>❤️ <strong>¿Te ha sido útil esta herramienta?</strong></p>"
        "<p>Esta calculadora es gratuita, sin publicidad, y siempre lo será. "
        "Si deseas apoyar el desarrollo y mantener la fiscalidad española actualizada, "
        "<a href='https://buymeacoffee.com/pishu' target='_blank' style='color: #FF6B6B; font-weight: bold;'>"
        "invítame a un café ☕</a></p>"
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================================
# 10. MAIN APP ORCHESTRATION
# =====================================================================

def main():
    """Main application flow"""

    if "sidebar_visible" not in st.session_state:
        st.session_state["sidebar_visible"] = True

    top_left, _top_right = st.columns([1, 5])
    with top_left:
        toggle_label = "Ocultar panel" if st.session_state["sidebar_visible"] else "Mostrar panel"
        if st.button(toggle_label, key="toggle_sidebar_visibility", width="stretch"):
            st.session_state["sidebar_visible"] = not st.session_state["sidebar_visible"]

    if not st.session_state["sidebar_visible"]:
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] {display: none !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )

    # Header
    st.title("📈 Calculadora FIRE - Calculadora de Independencia Financiera")
    st.markdown(
        "Simulador FIRE con escenarios de mercado, inflación y fiscalidad española (en versión aproximada)."
    )

    # Privacy banner
    st.info(
        "🔒 **Privacidad:** Los cálculos se ejecutan en el servidor del despliegue actual (local o cloud). "
        "Si ejecutas en local, los datos permanecen en tu equipo."
    )
    st.warning(
        "🚧 **Limitaciones importantes (actual):**\n\n"
        "• Simulador educativo: no sustituye asesoría fiscal/legal.\n"
        "• Fiscalidad regional basada en Tax Pack versionado (actualmente ES-2026 en este repo).\n"
        "• SWR configurable: se aplica en objetivo FIRE (TRS).\n"
        "• Monte Carlo y fiscalidad: modelo anual simplificado."
    )
    render_plain_language_overview()

    # 1. RENDER SIDEBAR (Input Collection)
    params = render_sidebar()
    ahorro_vivienda_anual = (
        params.get("ahorro_vivienda_habitual_anual", 0.0)
        if params.get("aplicar_ajuste_vivienda_habitual", False)
        else 0.0
    )
    housing_flows = compute_effective_housing_and_rental_flows(
        base_monthly_contribution=params["aportacion_mensual"],
        annual_spending=params["gastos_anuales"],
        age_current=params["edad_actual"],
        age_target=params["edad_objetivo"],
        rental_annual_gross=params.get("renta_bruta_alquiler_anual", 0.0),
        include_rental_in_simulation=params.get("incluir_rentas_alquiler_en_simulacion", True),
        use_advanced_rental_model=params.get("usar_modelo_avanzado_alquiler", False),
        rental_costs_vacancy_pct=params.get("alquiler_costes_vacancia_pct", 0.0),
        rental_effective_irpf_pct=params.get("alquiler_irpf_efectivo_pct", 0.0),
        annual_primary_home_savings=ahorro_vivienda_anual,
        include_primary_mortgage_payment=params.get("incluir_cuota_vivienda_en_simulacion", False),
        primary_mortgage_monthly_payment=params.get("cuota_hipoteca_vivienda_mensual", 0.0),
        primary_mortgage_months_remaining=params.get("meses_hipoteca_vivienda_restantes", 0),
        include_investment_mortgage_payment=params.get("incluir_cuota_inmuebles_en_simulacion", False),
        investment_mortgage_monthly_payment=params.get("cuota_hipoteca_inmuebles_mensual", 0.0),
        investment_mortgage_months_remaining=params.get("meses_hipoteca_inmuebles_restantes", 0),
    )

    params["renta_bruta_alquiler_anual_efectiva"] = housing_flows["rental_gross_effective"]
    params["renta_neta_alquiler_anual_efectiva"] = housing_flows["rental_net_effective"]
    params["cuota_total_hipotecas_mensual_efectiva"] = housing_flows["mortgages_monthly_total"]
    params["cuota_post_fire_hipotecas_mensual_efectiva"] = housing_flows["mortgages_monthly_post_fire"]
    params["months_after_fire_vivienda"] = housing_flows["months_after_fire_primary"]
    params["months_after_fire_inmuebles"] = housing_flows["months_after_fire_investment"]
    params["ahorro_vivienda_habitual_anual_efectivo"] = ahorro_vivienda_anual
    params["aportacion_mensual_efectiva"] = housing_flows["monthly_contribution_effective"]
    params["gasto_anual_neto_cartera"] = housing_flows["annual_spending_effective"]

    render_active_context_summary(params)
    tax_drag = get_fiscal_return_adjustment(
        params["regimen_fiscal"],
        params["include_optimización"],
        params.get("fiscal_mode", FISCAL_MODE_ES_TAXPACK),
        params.get("intl_tax_rates"),
    )
    mean_return_for_sim = params["rentabilidad_esperada"] - tax_drag
    params["rentabilidad_neta_simulacion"] = mean_return_for_sim
    years_horizon = params["edad_objetivo"] - params["edad_actual"]
    if params.get("taxable_withdrawal_ratio_mode") == "Automático (estimado)":
        taxable_ratio_effective = estimate_auto_taxable_withdrawal_ratio(
            initial_wealth=params.get("patrimonio_base_simulacion", params["patrimonio_inicial"]),
            monthly_contribution=params.get("aportacion_mensual_efectiva", params["aportacion_mensual"]),
            years=years_horizon,
            expected_return=mean_return_for_sim,
            contribution_growth_rate=params.get("contribution_growth_rate", 0.0),
        )
    else:
        taxable_ratio_effective = params.get("taxable_withdrawal_ratio", 0.4)
    params["taxable_withdrawal_ratio_effective"] = taxable_ratio_effective

    # 2. VALIDATE INPUTS
    is_valid, validation_messages = validate_inputs(params)

    if not is_valid or validation_messages:
        st.divider()
        st.warning(
            "⚠️ **Validación de Entrada**\n\n" + "\n".join(validation_messages)
        )

        if not is_valid:
            st.stop()

    # 3. CALCULATE SIMULATIONS (ALL MODELS FOR COMPARISON)
    st.divider()
    st.subheader("🧪 Comparación de métodos")
    if params.get("modo_guiado"):
        st.caption("Compara los tres enfoques en pestañas. El detalle inferior usa el modelo base (Normal).")
    strategy_options = [
        "100% renta variable (histórica S&P 500 EE. UU., 1871+)",
        "70% renta variable / 30% renta fija (sintética)",
        "50% renta variable / 50% renta fija (sintética)",
        "30% renta variable / 70% renta fija (sintética)",
        "15% renta variable / 85% renta fija (sintética)",
    ]
    strategy_map = {
        "100% renta variable (histórica S&P 500 EE. UU., 1871+)": "sp500_us_total_return",
        "70% renta variable / 30% renta fija (sintética)": "portfolio_70_30_synthetic",
        "50% renta variable / 50% renta fija (sintética)": "portfolio_50_50_synthetic",
        "30% renta variable / 70% renta fija (sintética)": "portfolio_30_70_synthetic",
        "15% renta variable / 85% renta fija (sintética)": "portfolio_15_85_synthetic",
    }
    default_strategy_label = strategy_options[0]
    if "bootstrap_historical_strategy_label" not in st.session_state:
        st.session_state["bootstrap_historical_strategy_label"] = default_strategy_label
    if "backtest_historical_strategy_label" not in st.session_state:
        st.session_state["backtest_historical_strategy_label"] = default_strategy_label

    with st.spinner("🔄 Ejecutando simulaciones (Normal, Bootstrap y Backtesting)..."):
        model_map = {
            "Monte Carlo (Normal)": "normal",
            "Monte Carlo (Bootstrap histórico)": "bootstrap",
            "Backtesting histórico (ventanas móviles)": "backtest",
        }

        tax_pack_for_run = None
        if (
            params.get("fiscal_mode", FISCAL_MODE_ES_TAXPACK) == FISCAL_MODE_ES_TAXPACK
            and params.get("tax_year") is not None
            and params.get("region")
        ):
            try:
                tax_pack_for_run = load_tax_pack(int(params["tax_year"]), "es")
            except Exception:
                tax_pack_for_run = None

        if params.get("fiscal_priority") == "Jubilación":
            if params.get("fiscal_mode", FISCAL_MODE_ES_TAXPACK) == FISCAL_MODE_INTL_BASIC:
                retirement_ctx = estimate_retirement_tax_context_intl_basic(
                    net_spending=params.get("gasto_anual_neto_cartera", params["gastos_anuales"]),
                    safe_withdrawal_rate=params["safe_withdrawal_rate"],
                    taxable_withdrawal_ratio=params.get("taxable_withdrawal_ratio_effective", 0.4),
                    intl_tax_rates=params.get("intl_tax_rates", {}),
                )
            else:
                retirement_ctx = estimate_retirement_tax_context(
                    net_spending=params.get("gasto_anual_neto_cartera", params["gastos_anuales"]),
                    safe_withdrawal_rate=params["safe_withdrawal_rate"],
                    taxable_withdrawal_ratio=params.get("taxable_withdrawal_ratio_effective", 0.4),
                    tax_pack=tax_pack_for_run,
                    region=params.get("region"),
                )
            params["retirement_tax_context"] = retirement_ctx
            annual_spending_for_target = retirement_ctx["gross_withdrawal_required"]
            params["fire_target_effective"] = retirement_ctx["target_portfolio_gross"]
            tax_pack_accumulation = None
        else:
            params["retirement_tax_context"] = None
            annual_spending_for_target = params.get("gasto_anual_neto_cartera", params["gastos_anuales"])
            params["fire_target_effective"] = annual_spending_for_target / params["safe_withdrawal_rate"]
            tax_pack_accumulation = tax_pack_for_run

        params["annual_spending_for_target"] = annual_spending_for_target

        simulation_results_by_model: Dict[str, Dict] = {}
        for model_label, model_type in model_map.items():
            if model_type == "bootstrap":
                historical_strategy_label = st.session_state["bootstrap_historical_strategy_label"]
            elif model_type == "backtest":
                historical_strategy_label = st.session_state["backtest_historical_strategy_label"]
            else:
                historical_strategy_label = default_strategy_label
            historical_strategy = strategy_map[historical_strategy_label]

            params_key = (
                f"{params['patrimonio_inicial']}_{params.get('patrimonio_base_simulacion')}_{params['aportacion_mensual']}_"
                f"{params.get('aportacion_mensual_efectiva')}_{params.get('renta_neta_alquiler_anual_efectiva')}_"
                f"{params.get('cuota_total_hipotecas_mensual_efectiva')}_{params.get('cuota_post_fire_hipotecas_mensual_efectiva')}_"
                f"{params.get('ahorro_vivienda_habitual_anual_efectivo')}_"
                f"{params['rentabilidad_esperada']}_{params['volatilidad']}_{params['inflacion']}_"
                f"{params.get('contribution_growth_rate')}_"
                f"{params['gastos_anuales']}_{params.get('gasto_anual_neto_cartera')}_{params['regimen_fiscal']}_{params['include_optimización']}_"
                f"{params.get('fiscal_mode')}_{params.get('intl_tax_rates')}_"
                f"{params['safe_withdrawal_rate']}_{params.get('fiscal_priority')}_{params.get('taxable_withdrawal_ratio_effective')}_"
                f"{model_type}_{historical_strategy}_{params.get('tax_year')}_{params.get('region')}"
            )
            simulation_results_by_model[model_label] = run_cached_simulation(
                params_key=params_key,
                initial_wealth=params.get("patrimonio_base_simulacion", params["patrimonio_inicial"]),
                monthly_contribution=params.get("aportacion_mensual_efectiva", params["aportacion_mensual"]),
                years=params["edad_objetivo"] - params["edad_actual"],
                mean_return=mean_return_for_sim,
                volatility=params["volatilidad"],
                inflation_rate=params["inflacion"],
                annual_spending=annual_spending_for_target,
                safe_withdrawal_rate=params["safe_withdrawal_rate"],
                contribution_growth_rate=params.get("contribution_growth_rate", 0.0),
                model_type=model_type,
                historical_strategy=historical_strategy,
                tax_pack=tax_pack_accumulation,
                region=params.get("region"),
            )
            simulation_results_by_model[model_label]["historical_strategy_label"] = historical_strategy_label
            simulation_results_by_model[model_label]["historical_strategy"] = historical_strategy

    tab_labels = list(simulation_results_by_model.keys())
    tabs = st.tabs(tab_labels)
    for tab, label in zip(tabs, tab_labels):
        with tab:
            if label in ("Monte Carlo (Bootstrap histórico)", "Backtesting histórico (ventanas móviles)"):
                state_key = (
                    "bootstrap_historical_strategy_label"
                    if label == "Monte Carlo (Bootstrap histórico)"
                    else "backtest_historical_strategy_label"
                )
                chosen_label = st.selectbox(
                    "Estrategia histórica",
                    options=strategy_options,
                    index=strategy_options.index(st.session_state[state_key])
                    if st.session_state[state_key] in strategy_options
                    else 0,
                    key=f"strategy_select_{state_key}",
                    help="Solo aplica a Bootstrap y Backtesting.",
                )
                st.session_state[state_key] = chosen_label
                chosen_strategy = strategy_map[chosen_label]
                if simulation_results_by_model[label].get("historical_strategy") != chosen_strategy:
                    model_type = "bootstrap" if label == "Monte Carlo (Bootstrap histórico)" else "backtest"
                    params_key = (
                        f"{params['patrimonio_inicial']}_{params.get('patrimonio_base_simulacion')}_{params['aportacion_mensual']}_"
                        f"{params.get('aportacion_mensual_efectiva')}_{params.get('renta_neta_alquiler_anual_efectiva')}_"
                        f"{params.get('cuota_total_hipotecas_mensual_efectiva')}_{params.get('cuota_post_fire_hipotecas_mensual_efectiva')}_"
                        f"{params.get('ahorro_vivienda_habitual_anual_efectivo')}_"
                        f"{params['rentabilidad_esperada']}_{params['volatilidad']}_{params['inflacion']}_"
                        f"{params.get('contribution_growth_rate')}_"
                        f"{params['gastos_anuales']}_{params.get('gasto_anual_neto_cartera')}_{params['regimen_fiscal']}_{params['include_optimización']}_"
                        f"{params.get('fiscal_mode')}_{params.get('intl_tax_rates')}_"
                        f"{params['safe_withdrawal_rate']}_{params.get('fiscal_priority')}_{params.get('taxable_withdrawal_ratio_effective')}_"
                        f"{model_type}_{chosen_strategy}_{params.get('tax_year')}_{params.get('region')}"
                    )
                    simulation_results_by_model[label] = run_cached_simulation(
                        params_key=params_key,
                        initial_wealth=params.get("patrimonio_base_simulacion", params["patrimonio_inicial"]),
                        monthly_contribution=params.get("aportacion_mensual_efectiva", params["aportacion_mensual"]),
                        years=params["edad_objetivo"] - params["edad_actual"],
                        mean_return=mean_return_for_sim,
                        volatility=params["volatilidad"],
                        inflation_rate=params["inflacion"],
                        annual_spending=annual_spending_for_target,
                        safe_withdrawal_rate=params["safe_withdrawal_rate"],
                        contribution_growth_rate=params.get("contribution_growth_rate", 0.0),
                        model_type=model_type,
                        historical_strategy=chosen_strategy,
                        tax_pack=tax_pack_accumulation,
                        region=params.get("region"),
                    )
                    simulation_results_by_model[label]["historical_strategy_label"] = chosen_label
                    simulation_results_by_model[label]["historical_strategy"] = chosen_strategy

                with st.expander("Histórico vs sintético: qué significa", expanded=False):
                    st.markdown(
                        "- **Histórico (100% renta variable):** usa retorno anual observado de S&P 500 total return (EE. UU.) desde 1871.\n"
                        "- **Sintético (carteras mixtas):** combina cada año histórico de renta variable con renta fija sintética al 3% anual.\n"
                        "- **Fórmula de composición:** `retorno_cartera = w_rv * retorno_rv_histórico + w_rf * 0.03`.\n"
                        "- En años con menos de 12 observaciones mensuales, el retorno anual se anualiza de forma aproximada.\n"
                        "- **Fidelidad del backtesting:** es alta para estudiar secuencia de mercado histórica anual, "
                        "pero no replica fricción real completa (comisiones, deslizamientos, ejecución intra-año, divisa, "
                        "impuestos exactos por activo). Usa los indicadores de ventana crítica para acotar riesgo."
                    )
            params["simulation_model"] = label
            params["historical_strategy_label"] = simulation_results_by_model[label].get("historical_strategy_label")
            params["historical_strategy"] = simulation_results_by_model[label].get("historical_strategy")
            render_kpis(simulation_results_by_model[label], params)
            render_simple_result_summary(simulation_results_by_model[label], params)
            render_main_chart(simulation_results_by_model[label], params)
            render_success_distribution_chart(simulation_results_by_model[label], params)

    # Base model for downstream sections (export/sensitivity/final banner)
    simulation_results = simulation_results_by_model["Monte Carlo (Normal)"]
    params["simulation_model"] = "Monte Carlo (Normal)"

    # 4. RENDER TAX TRACE AND RETIREMENT-TAX SUMMARY
    st.divider()
    render_retirement_tax_focus_summary(params)
    render_tax_trace(params, tax_pack_for_run)

    st.divider()

    # 5. RENDER SENSITIVITY ANALYSIS
    render_sensitivity_analysis(params)

    st.divider()

    # 6. RENDER ACCUMULATION BOX
    render_accumulation_box(simulation_results, params)

    st.divider()

    # 7. RENDER RETIREMENT DECUMULATION BOX
    render_decumulation_box(simulation_results, params)

    st.divider()

    # 8. RENDER EXPORT (BASE MODEL)
    render_export_options(simulation_results, params)

    st.divider()
    
    # 9. FINAL NARRATIVE SUMMARY
    render_final_narrative_summary(simulation_results, params)

    st.divider()

    # 10. A/B COMPARATOR (BASE MODEL)
    render_ab_comparator(simulation_results, params)

    # Footer
    st.divider()
    st.markdown(
        """
    ---
    **Aviso:** Este simulador ofrece proyecciones educativas basadas en supuestos.
    No constituye asesoramiento financiero, fiscal ni legal.
    
    **Documentación técnica:** Ver `README.md` y comentarios en `app.py` para detalles arquitectónicos.
    """
    )


if __name__ == "__main__":
    main()

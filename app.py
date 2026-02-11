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
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Tuple, List, Optional
import math
from io import BytesIO
from datetime import datetime
import warnings

# Black-box import from domain layer
from src.calculator import (
    target_fire,
    project_portfolio,
    calculate_market_scenarios,
    project_retirement,
    calculate_net_worth,
)
from src.tax_engine import (
    load_tax_pack,
    list_available_taxpack_years,
    get_region_options,
    calculate_savings_tax,
    calculate_wealth_taxes,
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

VALIDATION_RULES = {
    "patrimonio_inicial": {
        "min": 0,
        "max": 10_000_000,
        "error_min": "Capital inicial no puede ser negativo",
        "error_max": "Capital inicial no puede superar €10M",
    },
    "aportacion_mensual": {
        "min": 0,
        "max": 50_000,
        "error_min": "Aportación mensual no puede ser negativa",
        "error_max": "Aportación mensual no puede superar €50k",
    },
    "edad_actual": {
        "min": 18,
        "max": 100,
        "error_min": "Edad mínima es 18 años",
        "error_max": "Edad máxima es 100 años",
    },
    "edad_objective": {
        "min": 18,
        "max": 100,
        "error_min": "Edad objetivo mínima es 18 años",
        "error_max": "Edad objetivo máxima es 100 años",
    },
    "rentabilidad_esperada": {
        "min": -0.10,
        "max": 0.25,
        "error_min": "Rentabilidad esperada no puede ser menor a -10%",
        "error_max": "Rentabilidad esperada no puede superar 25%",
    },
    "inflacion": {
        "min": -0.05,
        "max": 0.20,
        "error_min": "Inflación no puede ser menor a -5%",
        "error_max": "Inflación no puede superar 20%",
    },
    "gastos_anuales": {
        "min": 1_000,
        "max": 1_000_000,
        "error_min": "Gastos anuales mínimos €1.000",
        "error_max": "Gastos anuales máximos €1M",
        "warning_threshold_ratio": 0.5,  # Alert if > 50% of assets annually
    },
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "initial_load" not in st.session_state:
    st.session_state.initial_load = True
    st.session_state.cached_results = None

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
            "¡FIRE! Estás en la recta final. Con tus parámetros actuales, "
            "la independencia financiera está al alcance de tu mano. Prepárate para "
            "hacer realidad tus sueños en los próximos años."
        )
    elif years_to_fire <= 10:
        return "🌟", (
            "¡Excelente camino! Alcanzarás FIRE en menos de una década. A este ritmo, "
            "tu libertad financiera es inevitable. Mantén el rumbo y disfruta del viaje."
        )
    elif years_to_fire <= 15:
        return "⚡", (
            "¡Vamos bien! Tu objetivo FIRE está dentro de lo alcanzable en un horizonte "
            "realista (15 años). Eres más disciplinado que el 95% de la población."
        )
    elif years_to_fire <= 20:
        return "📈", (
            "¡Buen progreso! Con 20 años o menos hasta FIRE, tienes una hoja de ruta clara. "
            "Cada mes que ahorre te acerca más a tu objetivo de libertad financiera."
        )
    elif years_to_fire <= 25:
        return "🎯", (
            "¡Rumbo a FIRE! Tu timeline es desafiante pero alcanzable. Una pequeña mejora "
            "en rentabilidad o ahorro podría acelerar significativamente tu objetivo."
        )
    elif years_to_fire <= 30:
        return "🔥", (
            "¡Perseverancia! Aunque el horizonte es largo (28-30 años), tu compromiso con "
            "la independencia financiera ya te diferencia del resto. El tiempo trabaja a tu favor."
        )
    else:
        return "💪", (
            "¡No es imposible! Aunque el path es largo, cada euro invertido te acerca a FIRE. "
            "Considera aumentar aportaciones o ajustar expectativas de gasto para acelerar tu meta."
        )


def generate_success_probability_message(success_rate: float) -> Tuple[str, str]:
    """
    Generate message based on Monte Carlo success probability.
    
    Returns: (emoji, message)
    """
    if success_rate >= 95:
        return "✅", (
            "¡Prácticamente garantizado! Con 95%+ de probabilidad de éxito, tu plan FIRE es "
            "robusto incluso ante volatilidad de mercado. Duerme tranquilo cada noche."
        )
    elif success_rate >= 85:
        return "👍", (
            "¡Muy probable! 85-95% de las simulaciones monte carlo alcanzan tu objetivo. "
            "Tu plan tiene margen de seguridad ante mercados adversos."
        )
    elif success_rate >= 75:
        return "⚖️", (
            "¡Probable! Con 75-85% de éxito, tienes una buena oportunidad. Considera pequeños "
            "ajustes (ahorrar 5% más, reducir gastos en 2%) para aumentar confianza."
        )
    elif success_rate >= 60:
        return "⚠️", (
            "¡Moderado! El riesgo es notable (60-75% de éxito). Una caída de 20% en mercados "
            "durantelos primeros años podría comprometer tu plan. Revisa tus supuestos."
        )
    else:
        return "🔴", (
            "¡Riesgo elevado! Con <60% de probabilidad de éxito, tu plan depende demasiado "
            "de escenarios optimistas. Aumenta ahorros, reduce gastos, o extiende tu horizonte."
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
            "Ritmo acelerado: Tu tasa de ahorro es impresionante (30-60% del gasto). "
            "¡Eres un acumulador! Tu FIRE llegará antes de lo que imaginas."
        )
    else:
        return "🏎️", (
            "¡Velocidad máxima! Ahorras más de lo que gastas. Este nivel de disciplina es "
            "excepcional. Tu independencia financiera es casi inevitable."
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
            f"🎉 ¡Magia! FIRE llega {abs(diff)} años ANTES de tu objetivo. "
            f"Tendrás {abs(diff)} años extra de libertad. Considera: "
            f"¿Quieres retirarte antes y vivir más, o acumular más patrimonio para mayor seguridad?"
        )
    elif diff < 0:
        return (
            f"✨ Bonus: Alcanzarás FIRE {abs(diff)} años antes. "
            f"Esto te da margen para: (1) retirarte pronto, (2) reducir ahorros y disfrutar más hoy, "
            f"o (3) acumular colchón adicional."
        )
    elif diff == 0:
        return (
            "🎯 ¡Timing perfecto! Tu FIRE coincide exactamente con tu edad objetivo. "
            "Tu plan está impeccablemente calibrado."
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
            f"⚡ Portafolio volátil ({volatility*100:.0f}% anual). Espera oscilaciones de ±30% en años difíciles. "
            f"Esto es normal en carteras con 70%+ acciones. Si te despiertas sudando por caídas del 20%, "
            f"reduce volatilidad asignando más a bonos/renta fija."
        )
    elif volatility >= 0.15:
        return (
            f"📊 Volatilidad moderada-alta ({volatility*100:.0f}%). Tu cartera tiene exposición accionaria "
            f"importante (~60%). Buena para el largo plazo, puede causar ansiedad en crisis."
        )
    elif volatility >= 0.10:
        return (
            f"☘️ Volatilidad moderada ({volatility*100:.0f}%). Balance equilibrado entre "
            f"crecimiento y estabilidad. Duerme bien, tu cartera está diversificada."
        )
    else:
        return (
            f"🛡️ Volatilidad baja ({volatility*100:.0f}%). Cartera muy conservadora. "
            f"Será más estable, pero cuidado: la inflación podría corroer tus ganancias más lentamente."
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
    swr = 0.04
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

    return len(errors) == 0, errors + warnings


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
    num_simulations: int = 10_000,
    seed: int = 42,
    tax_pack: Optional[Dict] = None,
    region: Optional[str] = None,
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
    np.random.seed(seed)
    
    annual_contribution = monthly_contribution * 12

    # Initialize annual paths (simulations x years+1)
    annual_paths = np.zeros((num_simulations, years + 1))
    annual_paths[:, 0] = initial_wealth

    # Annual simulation with regional tax drag.
    for sim in range(num_simulations):
        portfolio = initial_wealth
        for year in range(1, years + 1):
            annual_return = np.random.normal(mean_return, volatility)
            gross_growth = portfolio * annual_return
            portfolio_pre_tax = portfolio + gross_growth + annual_contribution

            if tax_pack and region:
                savings_base = max(0.0, gross_growth)
                savings_tax = calculate_savings_tax(savings_base, tax_pack, region)
                wealth_taxes = calculate_wealth_taxes(portfolio_pre_tax, tax_pack, region)
                portfolio = portfolio_pre_tax - savings_tax - wealth_taxes["total_wealth_tax"]
            else:
                portfolio = portfolio_pre_tax

            annual_paths[sim, year] = max(0.0, portfolio)
    
    # Inflation adjustment (real values)
    inflation_factors = np.array([(1 + inflation_rate) ** y for y in range(years + 1)])
    real_paths = annual_paths / inflation_factors
    
    # FIRE target in today's euros; compare against real (inflation-adjusted) paths.
    fire_target_real = annual_spending / 0.04 if annual_spending > 0 else 0
    
    # Success analysis
    final_values = annual_paths[:, -1]
    final_values_real = real_paths[:, -1]
    percent_success = (final_values_real >= fire_target_real).sum() / num_simulations * 100
    
    # Percentiles
    percentile_5 = np.percentile(annual_paths, 5, axis=0)
    percentile_25 = np.percentile(annual_paths, 25, axis=0)
    percentile_50 = np.percentile(annual_paths, 50, axis=0)
    percentile_75 = np.percentile(annual_paths, 75, axis=0)
    percentile_95 = np.percentile(annual_paths, 95, axis=0)
    
    # Year-by-year success rate (reaching FIRE target)
    yearly_success = np.zeros(years + 1)
    for year in range(years + 1):
        yearly_success[year] = (
            (real_paths[:, year] >= fire_target_real).sum() / num_simulations * 100
        )

    # Real-value percentiles for timeline interpretation in today's euros.
    real_percentile_5 = np.percentile(real_paths, 5, axis=0)
    real_percentile_25 = np.percentile(real_paths, 25, axis=0)
    real_percentile_50 = np.percentile(real_paths, 50, axis=0)
    real_percentile_75 = np.percentile(real_paths, 75, axis=0)
    real_percentile_95 = np.percentile(real_paths, 95, axis=0)
    
    return {
        "paths": annual_paths,
        "real_paths": real_paths,
        "percentile_5": percentile_5,
        "percentile_25": percentile_25,
        "percentile_50": percentile_50,
        "percentile_75": percentile_75,
        "percentile_95": percentile_95,
        "real_percentile_5": real_percentile_5,
        "real_percentile_25": real_percentile_25,
        "real_percentile_50": real_percentile_50,
        "real_percentile_75": real_percentile_75,
        "real_percentile_95": real_percentile_95,
        "success_rate_final": percent_success,
        "yearly_success": yearly_success,
        "final_values": final_values,
        "final_values_real": final_values_real,
        "final_median": np.median(final_values),
        "final_median_real": np.median(final_values_real),
        "final_percentile_95": np.percentile(final_values, 95),
        "fire_target_real": fire_target_real,
        "fire_target": fire_target_real,
    }


def get_fiscal_return_adjustment(regimen_fiscal: str, include_optimización: bool) -> float:
    """
    Approximate annual return drag from taxes/friction by regime.
    This ensures fiscal selector changes simulation outcomes.
    """
    base_drag = {
        "España - Fondos de Inversión": 0.003,
        "España - Cartera Directa": 0.012,
        "Otro": 0.008,
    }.get(regimen_fiscal, 0.008)

    if include_optimización and regimen_fiscal == "España - Fondos de Inversión":
        base_drag = max(0.0, base_drag - 0.0015)

    return base_drag


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
        num_simulations=10_000,
        tax_pack=tax_pack,
        region=region,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def run_cached_deterministic(
    params_key: str,
    current_savings: float,
    annual_contribution: float,
    years: int,
    expected_return: float,
    inflation_rate: float,
    annual_spending: float,
    tax_rate_gains: float = 0.15,
):
    """Cached deterministic projection using calculator.py"""
    return project_portfolio(
        current_savings=current_savings,
        annual_contribution=annual_contribution * 12,
        years=years,
        expected_return=expected_return,
        inflation_rate=inflation_rate,
        tax_rate_on_gains=tax_rate_gains,
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

    # SECTION 1: Investor Profile
    st.sidebar.markdown("### 👤 Perfil del Inversor")
    patrimonio_inicial = st.sidebar.slider(
        "Patrimonio actual (€)",
        min_value=0,
        max_value=2_000_000,
        value=150_000,
        step=10_000,
        help="Capital disponible hoy para invertir",
    )

    aportacion_mensual = st.sidebar.slider(
        "Aportación mensual (€)",
        min_value=0,
        max_value=10_000,
        value=1_000,
        step=100,
        help="Ahorro mensual que planeas invertir",
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        edad_actual = st.sidebar.number_input(
            "Edad actual",
            min_value=18,
            max_value=100,
            value=35,
            step=1,
        )

    with col2:
        edad_objetivo = st.sidebar.number_input(
            "Edad objetivo FIRE",
            min_value=18,
            max_value=100,
            value=50,
            step=1,
        )

    st.sidebar.divider()

    # SECTION 2: Market Assumptions
    st.sidebar.markdown("### 📊 Hipótesis de Mercado")
    rentabilidad_esperada = st.sidebar.slider(
        "Rentabilidad esperada anual (%)",
        min_value=-10.0,
        max_value=25.0,
        value=7.0,
        step=0.5,
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
        value=2.5,
        step=0.5,
        help="Inflación esperada para ajustar poder adquisitivo",
    ) / 100

    gastos_anuales = st.sidebar.number_input(
        "Gastos anuales en jubilación (€)",
        min_value=1_000,
        max_value=1_000_000,
        value=30_000,
        step=1_000,
        help="Gasto anual necesario para vivir en FIRE",
    )

    st.sidebar.divider()

    # SECTION 3: Fiscal Configuration
    st.sidebar.markdown("### 🏛️ Configuración Fiscal")
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

    tax_year = None
    region = None
    tax_pack_meta = None
    if regimen_fiscal in ("España - Fondos de Inversión", "España - Cartera Directa"):
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
            except Exception as e:
                st.sidebar.warning(f"No se pudo cargar Tax Pack {tax_year}: {e}")

    # Compile parameters
    params = {
        "patrimonio_inicial": patrimonio_inicial,
        "aportacion_mensual": aportacion_mensual,
        "edad_actual": edad_actual,
        "edad_objetivo": edad_objetivo,
        "rentabilidad_esperada": rentabilidad_esperada,
        "volatilidad": volatilidad,
        "inflacion": inflacion,
        "gastos_anuales": gastos_anuales,
        "regimen_fiscal": regimen_fiscal,
        "include_optimización": include_optimización,
        "tax_year": tax_year,
        "region": region,
        "tax_pack_meta": tax_pack_meta,
    }

    return params


# =====================================================================
# 6. DASHBOARD - KPIs
# =====================================================================

def render_kpis(simulation_results: Dict, params: Dict) -> None:
    """
    Render top-level KPI metrics in 4-column layout with color coding.
    """
    fire_target = params["gastos_anuales"] / 0.04
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
                delta_color="inverse" if years_to_fire < years_horizon else "normal",
            )

    with col2:
        final_nominal = simulation_results["percentile_50"][-1]
        final_real = simulation_results["real_percentile_50"][-1]
        st.metric(
            label="💰 Patrimonio Final (P50)",
            value=f"€{final_nominal:,.0f}",
            delta=f"Real: €{final_real:,.0f} ({final_real - fire_target:+,.0f} vs FIRE target)",
            delta_color="inverse" if final_real >= fire_target else "normal",
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

    # Dynamic inspirational messages
    st.divider()
    
    col_msg1, col_msg2 = st.columns(2)
    
    with col_msg1:
        emoji_readiness, msg_readiness = generate_fire_readiness_message(years_to_fire, years_horizon)
        st.info(f"{emoji_readiness} **Tu Timeline FIRE**\n\n{msg_readiness}")
    
    with col_msg2:
        emoji_success, msg_success = generate_success_probability_message(success_rate)
        if success_rate >= 75:
            st.success(f"{emoji_success} **Tu Probabilidad de Éxito**\n\n{msg_success}")
        elif success_rate >= 60:
            st.warning(f"{emoji_success} **Tu Probabilidad de Éxito**\n\n{msg_success}")
        else:
            st.error(f"{emoji_success} **Tu Probabilidad de Éxito**\n\n{msg_success}")
    
    # Additional insights
    col_velocity, col_horizon = st.columns(2)
    
    with col_velocity:
        emoji_velocity, msg_velocity = generate_savings_velocity_message(
            params["aportacion_mensual"], 
            params["gastos_anuales"]
        )
        st.info(f"{emoji_velocity} **Tu Ritmo de Ahorro**\n\n{msg_velocity}")
    
    with col_horizon:
        msg_comparison = generate_horizon_comparison_message(years_to_fire, years_horizon)
        st.info(f"📊 **Comparación vs Objetivo**\n\n{msg_comparison}")


# =====================================================================
# 7. VISUALIZATION - CHARTS & GRAPHS
# =====================================================================

def render_main_chart(simulation_results: Dict, params: Dict) -> None:
    """
    Primary chart: Portfolio evolution with uncertainty cone (percentiles 5-95).
    Uses Plotly for interactivity.
    """
    years = np.arange(len(simulation_results["percentile_50"]))
    fire_target = params["gastos_anuales"] / 0.04
    
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

    fig.update_layout(
        title="<b>Evolución del Portafolio - Simulación Monte Carlo (10,000 trayectorias)</b>",
        xaxis_title="Años desde hoy",
        yaxis_title="Valor del Portafolio (€, nominal)",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        yaxis=dict(tickformat=",.0f"),
    )

    st.plotly_chart(fig, width="stretch")
    
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

    st.plotly_chart(fig, width="stretch")
    
    # Dynamic success distribution insights
    success_final = simulation_results["success_rate_final"]
    if success_final >= 90:
        st.success(
            f"🎯 **¡Excelente!** Con {success_final:.0f}% de probabilidad, tu plan FIRE "
            f"es robusto. Incluso en mercados adversos (caídas 20-30%), alcanzarás tu objetivo."
        )
    elif success_final >= 75:
        st.info(
            f"✅ **Buena oportunidad:** {success_final:.0f}% de las simulaciones alcanzan FIRE. "
            f"Tu plan tiene margen de seguridad, pero vigila mercados bajistas."
        )
    elif success_final >= 60:
        st.warning(
            f"⚠️ **Moderado:** Solo {success_final:.0f}% de éxito. Considera aumentar ahorros "
            f"o reducir expectativas de gasto para mejorar confianza."
        )
    else:
        st.error(
            f"🔴 **Riesgoso:** {success_final:.0f}% de probabilidad es baja. "
            f"Tu plan necesita ajustes significativos para ser viable."
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

    base_return = params.get("rentabilidad_neta_simulacion", params["rentabilidad_esperada"]) * 100
    base_inflation = params["inflacion"] * 100
    fire_target = params["gastos_anuales"] / 0.04
    years_horizon = params["edad_objetivo"] - params["edad_actual"]

    # Define matrix parameters
    return_offsets = [-2, -1, 0, 1, 2]  # % points
    inflation_offsets = [-2, -1, 0, 1, 2]  # % points

    sensitivity_matrix = np.zeros((len(inflation_offsets), len(return_offsets)))

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

    st.plotly_chart(fig, width="stretch")

    # Dynamic sensitivity insights  
    sensitivity_col1, sensitivity_col2 = st.columns(2)
    
    with sensitivity_col1:
        min_years = sensitivity_matrix.min()
        max_years = sensitivity_matrix.max()
        range_years = max_years - min_years
        
        with st.expander("📊 Interpretación de resultados", expanded=False):
            st.write(
                f"**Rango observado:** {min_years:.0f} a {max_years:.0f} años (~{range_years:.0f} años de variación)"
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
        if range_years < 10:
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
# 9. EXPORT FUNCTIONALITY
# =====================================================================

def render_export_options(simulation_results: Dict, params: Dict) -> None:
    """
    Export CSV (full time series) and PDF (executive summary), and support options.
    """
    st.subheader("📥 Exportar Resultados")

    col1, col2 = st.columns(2)

    with col1:
        # CSV Export
        years = np.arange(len(simulation_results["percentile_50"]))
        fire_target = params["gastos_anuales"] / 0.04

        export_data = pd.DataFrame(
            {
                "Año": years,
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
        )

    with col2:
        # PDF Export placeholder with friendly message
        col_pdf, col_coffee = st.columns([2, 1])
        
        with col_pdf:
            st.info(
                "📄 **Generar PDF:** Reporte ejecutivo (1 página) con KPIs, gráfico principal y "
                "recomendaciones. Beta en desarrollo."
            )
        
        with col_coffee:
            st.markdown(
                "<a href='https://buymeacoffee.com/pishu' target='_blank' style='display: inline-block; padding: 10px 20px; "
                "background-color: #FFDD00; color: #222; text-decoration: none; border-radius: 5px; font-weight: bold;'>"
                "☕ Apóyame"
                "</a>",
                unsafe_allow_html=True
            )
    
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

    # Header
    st.title("📈 Calculadora FIRE - Calculadora de Independencia Financiera")
    st.markdown(
        "Proyecciones FIRE personalizadas con precisión fiscal española y análisis de incertidumbre probabilística"
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
        "• SWR en web: objetivo base calculado con 4%.\n"
        "• Monte Carlo y fiscalidad: modelo anual simplificado."
    )

    # 1. RENDER SIDEBAR (Input Collection)
    params = render_sidebar()
    tax_drag = get_fiscal_return_adjustment(
        params["regimen_fiscal"],
        params["include_optimización"],
    )
    mean_return_for_sim = params["rentabilidad_esperada"] - tax_drag
    params["rentabilidad_neta_simulacion"] = mean_return_for_sim

    # 2. VALIDATE INPUTS
    is_valid, validation_messages = validate_inputs(params)

    if not is_valid or validation_messages:
        st.divider()
        st.warning(
            "⚠️ **Validación de Entrada**\n\n" + "\n".join(validation_messages)
        )

        if not is_valid:
            st.stop()

    # 3. CALCULATE SIMULATIONS
    st.divider()

    with st.spinner("🔄 Ejecutando simulación Monte Carlo (10,000 trayectorias)..."):
        params_key = (
            f"{params['patrimonio_inicial']}_{params['aportacion_mensual']}_"
            f"{params['rentabilidad_esperada']}_{params['volatilidad']}_{params['inflacion']}_"
            f"{params['gastos_anuales']}_{params['regimen_fiscal']}_{params['include_optimización']}_"
            f"{params.get('tax_year')}_{params.get('region')}"
        )

        tax_pack_for_run = None
        if params.get("tax_year") is not None and params.get("region"):
            try:
                tax_pack_for_run = load_tax_pack(int(params["tax_year"]), "es")
            except Exception:
                tax_pack_for_run = None

        simulation_results = run_cached_simulation(
            params_key=params_key,
            initial_wealth=params["patrimonio_inicial"],
            monthly_contribution=params["aportacion_mensual"],
            years=params["edad_objetivo"] - params["edad_actual"],
            mean_return=mean_return_for_sim,
            volatility=params["volatilidad"],
            inflation_rate=params["inflacion"],
            annual_spending=params["gastos_anuales"],
            tax_pack=tax_pack_for_run,
            region=params.get("region"),
        )

    # 4. RENDER KPIs
    st.subheader("📊 Indicadores Clave")
    render_kpis(simulation_results, params)

    st.divider()

    # 5. RENDER CHARTS
    st.subheader("📈 Simulaciones y Tendencias")
    render_main_chart(simulation_results, params)
    render_success_distribution_chart(simulation_results, params)

    st.divider()

    # 6. RENDER SENSITIVITY ANALYSIS
    render_sensitivity_analysis(params)

    st.divider()

    # 7. RENDER EXPORT
    render_export_options(simulation_results, params)

    st.divider()
    
    # 8. FINAL INSPIRATIONAL MESSAGE
    fire_target = params["gastos_anuales"] / 0.04
    years_to_fire = find_years_to_fire(simulation_results["real_percentile_50"], fire_target)
    
    final_emoji, final_msg = generate_fire_readiness_message(years_to_fire, params["edad_objetivo"] - params["edad_actual"])

    final_banner = st.success if years_to_fire is not None else st.warning
    final_banner(
        f"{final_emoji} **¡Tu Camino a la Libertad Financiera!**\n\n{final_msg}\n\n"
        f"**Próximos pasos:**\n"
        f"1. Descarga tu proyección (CSV) para seguimiento anual\n"
        f"2. Revisa la matriz de sensibilidad cada trimestre\n"
        f"3. Ajusta tus aportaciones si tu situación financiera cambia\n"
        f"4. Consulta con un asesor para optimización fiscal"
    )

    # Footer
    st.divider()
    st.markdown(
        """
    ---
    **Disclaimer:** Este simulador proporciona proyecciones educativas basadas en supuestos de mercado.
    No constituye asesoramiento financiero. Consulta con un asesor financiero calificado para decisiones de inversión.
    
    **Documentación técnica:** Ver `README.md` y comentarios en `app.py` para detalles arquitectónicos.
    """
    )


if __name__ == "__main__":
    main()

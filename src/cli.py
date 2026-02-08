"""Interactive CLI for the FIRE calculator (EUR/UCITS).

Provides a friendly, didactic interface for users to input their financial
situation and explore multiple FIRE scenarios with motivational feedback.
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, Optional
import sys
from pathlib import Path
import random  # For Monte Carlo simulations

# Add project root to sys.path to allow imports from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calculator import target_fire, coast_fire_condition, project_portfolio, calculate_gross_target, calculate_savings_rate, project_retirement, calculate_market_scenarios, calculate_net_worth


# ============================================================================
# DIDACTIC MESSAGES AND PROFILES
# ============================================================================

WELCOME_MESSAGE = """
╔════════════════════════════════════════════════════════════════════════════╗
║                   🎯 CALCULADORA FIRE PARA INVERSORES EUR 🎯               ║
║                                                                            ║
║  Bienvenido a tu viaje hacia la Independencia Financiera (FIRE).          ║
║  Esta herramienta te ayudará a calcular cuándo podrás retirarte,          ║
║  según tus metas de gasto, ahorro y expectativas de rendimiento.          ║
║                                                                            ║
║  FIRE variantes soportadas:                                               ║
║  • Lean FIRE (€20k-€30k/año): vida modesta pero libre                     ║
║  • Fat FIRE (€60k-€100k/año): jubilación confortable                      ║
║  • Coast FIRE (€40k/año): acumula ahora, deja crecer sin aportes          ║
║  • Barista FIRE (€50k/año): €15k trabajo part-time + €35k portfolio       ║
║  • UCITS Tax Efficient (€45k/año): optimizado inversiones UCITS           ║
║                                                                            ║
║  Todas optimizadas para fiscalidad EUR/UCITS.                             ║
║  💡 Presiona 0 en el menú principal para salir.                           ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

PROFILES = {
    "lean": {
        "name": "Lean FIRE",
        "description": "Gasto €20k-€30k/año: vida modesta pero independiente",
        "defaults": {
            "annual_spending": 25_000,
            "safe_withdrawal_rate": 0.04,
            "expected_return": 0.06,
            "inflation_rate": 0.02,
            "tax_rate_on_gains": 0.15,
            "tax_rate_on_dividends": 0.30,
            "tax_rate_on_interest": 0.45,
            "fund_fees": 0.001,
        },
    },
    "fat": {
        "name": "Fat FIRE",
        "description": "Gasto €60k-€100k/año: retiro confortable y sin restricciones",
        "defaults": {
            "annual_spending": 75_000,
            "safe_withdrawal_rate": 0.04,
            "expected_return": 0.07,
            "inflation_rate": 0.02,
            "tax_rate_on_gains": 0.15,
            "tax_rate_on_dividends": 0.30,
            "tax_rate_on_interest": 0.45,
            "fund_fees": 0.0012,
        },
    },
    "coast": {
        "name": "Coast FIRE",
        "description": "Gasto €40k/año: acumula ahora, deja crecer sin aportes después",
        "defaults": {
            "annual_spending": 40_000,
            "safe_withdrawal_rate": 0.04,
            "expected_return": 0.065,
            "inflation_rate": 0.02,
            "tax_rate_on_gains": 0.15,
            "tax_rate_on_dividends": 0.30,
            "tax_rate_on_interest": 0.45,
            "fund_fees": 0.001,
        },
    },
    "barista": {
        "name": "Barista FIRE",
        "description": "Gasto €50k/año: €15k trabajo part-time + €35k portfolio (4% SWR)",
        "defaults": {
            "annual_spending": 50_000,
            "safe_withdrawal_rate": 0.04,
            "expected_return": 0.055,
            "inflation_rate": 0.02,
            "tax_rate_on_gains": 0.15,
            "tax_rate_on_dividends": 0.30,
            "tax_rate_on_interest": 0.45,
            "fund_fees": 0.001,
        },
    },
    "ucits": {
        "name": "UCITS Tax Efficient",
        "description": "Gasto €45k/año: optimizado para UCITS y cuentas múltiples",
        "defaults": {
            "annual_spending": 45_000,
            "safe_withdrawal_rate": 0.04,
            "expected_return": 0.06,
            "inflation_rate": 0.02,
            "tax_rate_on_gains": 0.15,
            "tax_rate_on_dividends": 0.15,  # Lower thanks to UCITS efficiency
            "tax_rate_on_interest": 0.45,
            "fund_fees": 0.0015,
        },
    },
}

MOTIVATIONAL_MESSAGES = {
    "early": "¡Ya estás muy cerca! 🚀 Con tu ritmo actual, estarás en FIRE en menos de 5 años.",
    "medium": "¡Vamos bien! 💪 Estás en buen camino. Mantén el fokus y estarás libre en ~10 años.",
    "long": "Es un viaje hermoso. 🌱 La libertad financiera requiere paciencia, pero cada aporte cuenta.",
    "very_long": "Cada paso cuenta. 📈 Aunque tarde más, recuerda que estás construyendo tu futuro.",
    "already": "¡FELICIDADES! 🎉 ¡Ya has alcanzado tu objetivo FIRE! Es tiempo de disfrutar.",
    "high_progress": "¡Impresionante progreso! 💎 Ya has acumulado más del 75% de tu meta.",
    "mid_progress": "¡Buen progreso! 👍 Ya tienes más del 50% de tu objetivo.",
}


# ============================================================================
# INPUT FUNCTIONS
# ============================================================================

def clear_screen():
    """Clear terminal screen."""
    import os
    os.system("clear" if os.name == "posix" else "cls")


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def get_profile_choice() -> str:
    """Let user choose a FIRE profile or go custom."""
    print_section("Elige tu Perfil FIRE")
    print("Perfiles predefinidos (puedes ajustarlos después):\n")
    
    for i, (key, profile) in enumerate(PROFILES.items(), 1):
        print(f"  {i}) {profile['name'].ljust(20)} — {profile['description']}")
    
    print(f"\n  {len(PROFILES) + 1}) Entrada personalizada (Custom)")
    print(f"  {len(PROFILES) + 2}) Ver ejemplo JSON (para usar con API)")
    print(f"  0) Salir")

    while True:
        try:
            choice = int(input(f"\nElige (0-{len(PROFILES) + 2}): ").strip())
            if 0 <= choice <= len(PROFILES) + 2:
                profiles_list = list(PROFILES.keys())
                if choice == 0:
                    return "exit"
                elif choice <= len(PROFILES):
                    return profiles_list[choice - 1]
                elif choice == len(PROFILES) + 1:
                    return "custom"
                else:
                    return "show_json"
            else:
                print(f"❌ Por favor, elige un número entre 0 y {len(PROFILES) + 2}.")
        except ValueError:
            print("❌ Entrada inválida. Introduce un número.")


def get_float_input(
    prompt: str,
    default: Optional[float] = None,
    min_val: float = 0,
    max_val: Optional[float] = None,
    help_text: str = "",
) -> float:
    """Get validated float input from user."""
    while True:
        try:
            default_str = f" [default: €{default:,.0f}]" if default else ""
            full_prompt = f"{prompt}{default_str}: "
            print(f"   💡 Nota: usa puntos (30000.50) o comas (30000,50) para decimales.")
            
            user_input = input(full_prompt).strip()
            
            if not user_input:
                if default is not None:
                    return default
                else:
                    print("❌ Este campo es obligatorio.")
                    if help_text:
                        print(f"   Consejo: {help_text}")
                    continue
            
            value = float(user_input.replace("€", "").replace(",", ""))
            
            if value < min_val:
                print(f"❌ El valor debe ser ≥ {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"❌ El valor debe ser ≤ {max_val}.")
                continue
            
            return value
        except ValueError:
            print("❌ Introduce un número válido (ej. 30000 o 30.000).")
            if help_text:
                print(f"   Consejo: {help_text}")


def get_int_input(prompt: str, default: int, min_val: int = 0, max_val: int = None) -> int:
    """Get validated integer input from user."""
    while True:
        try:
            user_input = input(f"{prompt} [default: {default}]: ").strip()
            
            if not user_input:
                return default
            
            value = int(user_input)
            if value < min_val:
                print(f"❌ El valor debe ser ≥ {min_val}.")
                continue
            
            if max_val is not None and value > max_val:
                print(f"❌ El valor debe ser ≤ {max_val}.")
                continue
            
            return value
        except ValueError:
            print("❌ Introduce un número entero válido.")


def get_percent_input(prompt: str, default: float, max_percent: float = 100) -> float:
    """Get percentage input from user.
    
    Args:
        prompt: Question to ask
        default: Default value in decimal (0.0022 for 0.22%)
        max_percent: Maximum allowed percentage (1 for commissions, 100 for taxes)
    
    Returns:
        Value in decimal format (0.0022 for 0.22%)
    
    Logic:
        - User input "0.22" with max_percent=1 → 0.0022 (0.22%)
        - User input "5" with max_percent=100 → 0.05 (5%)
        - User input "0.05" with max_percent=100 → 0.05 (5%)
        - Auto-handles % symbol removal
    """
    while True:
        user_input = input(f"{prompt} [default: {default*100:.3f}%]: ").strip()
        
        if not user_input:
            return default
        
        try:
            # Remove % symbol if present
            user_input = user_input.replace("%", "").strip()
            value = float(user_input)
            
            # Core logic: if value > what it would be in decimal form,
            # assume user meant percentage notation (e.g., "22" for 22% or "0.22" for 0.22%)
            max_decimal = max_percent / 100
            
            if value > max_decimal:
                value = value / 100
            
            # Validate: value must be in range [0, max_percent/100]
            if not (0 <= value <= max_decimal):
                print(f"❌ El valor debe estar entre 0% y {max_percent}%.")
                continue
            
            return value
            
        except ValueError:
            print(f"❌ Introduce un porcentaje válido (ej. 0.22 para {default*100:.2f}%).")


# ============================================================================
# PARAMETER CONTEXT DISPLAY FUNCTIONS
# ============================================================================

def show_spending_context() -> None:
    """Show explanation for annual spending parameter."""
    print("""
┌──────────────────────────────────────────────────────────────┐
│ 💰 GASTO ANUAL DESEADO EN JUBILACIÓN                        │
├──────────────────────────────────────────────────────────────┤
│ ¿Cuánto necesitas gastar cada año una vez jubilado?        │
│                                                              │
│ Ejemplos reales (familias europeas):                       │
│  • €25,000: Lifestyle modesto (Lean FIRE)                  │
│  • €40,000-€50,000: Confortable, sin restricciones       │
│  • €60,000-€75,000: Con viajes y ocio (Fat FIRE)         │
│  • €100,000+: Muy holgado                                  │
│                                                              │
│ ✓ Incluye: vivienda, comida, salud, seguros, ocio        │
│ ✗ Excluye: depreciación de bienes, ahorros adicionales   │
│                                                              │
│ 💡 Tip: Sé realista. Este número define todo.            │
└──────────────────────────────────────────────────────────────┘
""")

def show_swr_context() -> None:
    """Show explanation for Safe Withdrawal Rate."""
    print("""
┌──────────────────────────────────────────────────────────────┐
│ 📊 TASA DE RETIRADA SEGURA (SWR / TRS)                      │
├──────────────────────────────────────────────────────────────┤
│ % del portfolio que puedes retirar cada año sin arruinarte  │
│ en 30 años (95% de probabilidad de éxito histórico)        │
│                                                              │
│ Estándares reconocidos:                                     │
│  • 3.0%: MÁS SEGURO (Trinity Study 1998)                   │
│  • 3.5%: Recomendado (margen de seguridad)                 │
│  • 4.0%: CLÁSICO (funciona en 95% escenarios)             │
│  • 4.5%+: ARRIESGADO (requiere ingresos adicionales)      │
│                                                              │
│ Fórmula: Portfolio necesario = Gasto anual / SWR           │
│ Ejemplo: €40,000/año ÷ 4% = €1,000,000 necesarios       │
│                                                              │
│ 💡 Consejo: Usa 4% si eres conservador/a,                │
│             3.5% si tu riesgo psicológico es bajo          │
└──────────────────────────────────────────────────────────────┘
""")

def show_return_context() -> None:
    """Show explanation for expected return."""
    print("""
┌──────────────────────────────────────────────────────────────┐
│ 📈 RETORNO ESPERADO ANUAL (% - ANTES DE IMPUESTOS)         │
├──────────────────────────────────────────────────────────────┤
│ ¿Cuál es tu objetivo de rentabilidad anual?                │
│ (Depende de tu asignación: % acciones vs. % bonos)        │
│                                                              │
│ Rentabilidad histórica REAL (ajustada inflación):         │
│  • 2-3%: Bonos, depósitos (muy seguro)                     │
│  • 5-6%: Cartera equilibrada 50/50 acciones-bonos        │
│  • 7-8%: Cartera agresiva 80/20 (histórico EUR)          │
│  • 9-10%: 100% acciones (esperanza, muy volátil)         │
│                                                              │
│ 💡 Recomendación FIRE: usa 5-6% (realista, documentado)  │
│    Evita soñar con 9-10% a menos que sean joven/agresivo  │
│    Recuerda: comisiones de fondos (~0.2%) se restan aquí  │
└──────────────────────────────────────────────────────────────┘
""")

def show_inflation_context() -> None:
    """Show explanation for inflation rate."""
    print("""
┌──────────────────────────────────────────────────────────────┐
│ 🎯 INFLACIÓN ESPERADA ANUAL (%)                            │
├──────────────────────────────────────────────────────────────┤
│ A qué ritmo esperas que suban de los precios cada año      │
│                                                              │
│ Contexto histórico y actual:                              │
│  • 2.0-2.5%: Target Banco Central Europa (normal)         │
│  • 2.5-3.5%: Inflación moderada (actual, 2024-2026)      │
│  • 5%+: Inflación alta (preocupante, requiere revisión)   │
│                                                              │
│ Impacto en FIRE:                                           │
│  • €40,000 hoy con 2%: necesitarás €59,548 en 20 años   │
│  • €40,000 hoy con 3%: necesitarás €64,500 en 20 años   │
│                                                              │
│ 💡 Tip: Para planificación larga (30+ años) usa 2.0%     │
│         (convergencia a target ECB)                        │
└──────────────────────────────────────────────────────────────┘
""")

def show_taxes_context() -> None:
    """Show explanation for taxes (gains, dividends, interest)."""
    print("""
┌──────────────────────────────────────────────────────────────┐
│ 🏛️  IMPUESTOS SOBRE RETORNOS (%)                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ PLUSVALÍAS (venta de inversiones con ganancia):           │
│  • 15%: España (si >1 año)                                 │
│  • 19-25%: Alemania, Francia (variable)                    │
│                                                              │
│ Estrategia: Fondos UCITS ACUMULATIVOS differem impuestos   │
│            hasta que vendas (defer 30+ años = genial)     │
│                                                              │
│ DIVIDENDOS (ingresos anuales):                            │
│  • 19-30%: Retención típica EU                             │
│  • Reducido con fondos acumulativos (no reparten)         │
│                                                              │
│ INTERESES (depósitos, bonos):                             │
│  • 19-20%: Retención estándar                              │
│  • Menos importante en FIRE (usas acciones)               │
│                                                              │
│ 💡 Consejo: Usa fondos acumulativos, espera >1 año        │
│             para vender (minimiza impuestos)              │
└──────────────────────────────────────────────────────────────┘
""")

def show_fees_context() -> None:
    """Show explanation for fund fees."""
    print("""
┌──────────────────────────────────────────────────────────────┐
│ 💸 COMISIONES ANUALES DE FONDOS UCITS (TER - %)            │
├──────────────────────────────────────────────────────────────┤
│ % anual que cobran por gestión, custodia, administración    │
│ (esto se suma al cálculo y reduce tu rentabilidad neta)    │
│                                                              │
│ Comisiones reales en mercado (2024):                      │
│  • 0.05-0.15%: iShares, Vanguard (EXCELENTE - ⭐)         │
│  • 0.20-0.35%: Fondos indexados medianos (bueno)          │
│  • 0.50-1.00%: Gestores activos (caro, raramente útil)   │
│  • 1.50%+: Fondos antiguos (EVITA)                        │
│                                                              │
│ IMPACTO EN FUTUROS (cartera €400,000 a 30 años):        │
│  • 0.10%: riqueza final€400,000 × 1.055^30 = €3.3M     │
│  • 0.30%: riqueza final €400,000 × 1.035^30 = €3.2M     │
│  • 1.00%: riqueza final €400,000 × 0.925^30 = €2.9M     │
│    ↳ Diferencia: €340,000 menos por 0.90% más en fees!  │
│                                                              │
│ 💡 RECOMENDACIÓN: Usa 0.10-0.20% (ETFs indexados)       │
│    Ahorraré €100k-€300k en 30 años                       │
└──────────────────────────────────────────────────────────────┘
""")


def collect_real_estate_and_liabilities(config: Dict[str, Any]) -> Dict[str, Any]:
    """Collect real estate and liability information from user."""
    print("\n" + "=" * 80)
    print("🏠 INFORMACIÓN INMOBILIARIA Y DEUDAS")
    print("=" * 80)
    print("""
Esta sección recopila info sobre inmuebles, hipotecas y créditos.
Datos precisos aquí son CRUCIALES para un análisis FIRE realista.
""")
    
    # Primary Residence Value
    print("\n" + "─" * 80)
    print("1️⃣  VIVIENDA PRINCIPAL (donde vives actualmente)")
    print("─" * 80)
    print("""
Valor de mercado actual de tu casa/piso:
  • Estima realista según mercado local (no precio de compra)
  • Busca comparables en Idealista/Fotocasa  
  • Deja en €0 si la usarás siempre (no FIRE con venta)
""")
    
    config['primary_residence_value'] = get_float_input(
        "Valor de tu vivienda principal (€)",
        default=config.get('primary_residence_value', 0),
        min_val=0
    )
    
    # Primary Residence Mortgage
    if config['primary_residence_value'] > 0:
        print("""
Hipoteca pendiente (lo que aún debes):
  • Coloca €0 si ya la pagaste o es tuya sin deuda
  • Equity = Valor - Hipoteca pendiente
  • Estrategia FIRE: paga antes de retirarte (sin estrés)
""")
        config['primary_residence_mortgage'] = get_float_input(
            "Hipoteca pendiente en vivienda principal (€)",
            default=config.get('primary_residence_mortgage', 0),
            min_val=0
        )
        
        # Mortgage details if there's a balance
        if config['primary_residence_mortgage'] > 0:
            print("""
Detalles de la hipoteca (si quieres calcular impacto de pago anticipado):
""")
            config['primary_mortgage_interest_rate'] = get_percent_input(
                "Tasa de interés anual (%)",
                default=config.get('primary_mortgage_interest_rate', 0.03),
                max_percent=15
            )
            
            config['primary_mortgage_years_remaining'] = get_int_input(
                "Años pendientes de amortización",
                default=config.get('primary_mortgage_years_remaining', 20),
                min_val=0,
                max_val=40
            )
            
            config['primary_mortgage_months_remaining'] = get_int_input(
                "Meses adicionales (0-11)",
                default=config.get('primary_mortgage_months_remaining', 0),
                min_val=0,
                max_val=11
            )
        else:
            config['primary_mortgage_interest_rate'] = 0
            config['primary_mortgage_years_remaining'] = 0
            config['primary_mortgage_months_remaining'] = 0
        
        # Ask about rental income from primary residence
        rent_primary = input("""
¿Alquilas tu vivienda principal? (típicamente NO, pero a veces sí)
  • Coloca 's' si sí, 'n' si no: """).strip().lower()
        
        if rent_primary == 's':
            config['primary_residence_annual_rent'] = get_float_input(
                "Alquiler anual de vivienda principal (€/año)",
                default=config.get('primary_residence_annual_rent', 0),
                min_val=0
            )
        else:
            config['primary_residence_annual_rent'] = 0
    else:
        config['primary_residence_mortgage'] = 0
        config['primary_residence_annual_rent'] = 0
        config['primary_mortgage_interest_rate'] = 0
        config['primary_mortgage_years_remaining'] = 0
        config['primary_mortgage_months_remaining'] = 0
    
    # Other Real Estate
    print("\n" + "─" * 80)
    print("2️⃣  OTROS INMUEBLES (segundas casas, inversión, etc.)")
    print("─" * 80)
    print("""
¿Tienes otra propiedad? ¿Terreno? ¿Apartamento vacacional?
  • Incluir si: genera renta, planeas venderla, es parte de FIRE
  • Excluir si: es hobby, cuesta más mantener, no es liquidable
  • Coloca valor de mercado actual
""")
    
    config['other_real_estate_value'] = get_float_input(
        "Valor de otros inmuebles (€)",
        default=config.get('other_real_estate_value', 0),
        min_val=0
    )
    
    if config['other_real_estate_value'] > 0:
        config['other_real_estate_mortgage'] = get_float_input(
            "Hipoteca/deuda en otros inmuebles (€)",
            default=config.get('other_real_estate_mortgage', 0),
            min_val=0
        )
        
        # Mortgage details if there's a balance
        if config['other_real_estate_mortgage'] > 0:
            print("""
Detalles de hipoteca/deuda en otros inmuebles:
""")
            config['other_mortgage_interest_rate'] = get_percent_input(
                "Tasa de interés anual (%)",
                default=config.get('other_mortgage_interest_rate', 0.03),
                max_percent=15
            )
            
            config['other_mortgage_years_remaining'] = get_int_input(
                "Años pendientes de amortización",
                default=config.get('other_mortgage_years_remaining', 20),
                min_val=0,
                max_val=40
            )
            
            config['other_mortgage_months_remaining'] = get_int_input(
                "Meses adicionales (0-11)",
                default=config.get('other_mortgage_months_remaining', 0),
                min_val=0,
                max_val=11
            )
        
        # Ask about rental income from other properties
        rent_other = input("""
¿Generan alquiler estos otros inmuebles?
  • Apartamiento de inversión, casa vacacional, etc.
  • Coloca 's' si sí, 'n' si no: """).strip().lower()
        
        if rent_other == 's':
            config['other_real_estate_annual_rent'] = get_float_input(
                "Alquiler anual total de otros inmuebles (€/año)",
                default=config.get('other_real_estate_annual_rent', 0),
                min_val=0
            )
        else:
            config['other_real_estate_annual_rent'] = 0
    else:
        config['other_real_estate_mortgage'] = 0
        config['other_real_estate_annual_rent'] = 0
        config['other_mortgage_interest_rate'] = 0
        config['other_mortgage_years_remaining'] = 0
        config['other_mortgage_months_remaining'] = 0
    
    # Other Liabilities
    print("\n" + "─" * 80)
    print("3️⃣  OTRAS DEUDAS (préstamos personales, tarjetas, etc.)")
    print("─" * 80)
    print("""
¿Debes dinero sin hipoteca? (créditos, tarjetas de crédito, etc.)

⚠️  IMPORTANTE PARA FIRE:
   PAGA TODO ANTES DE RETIRARTE
   Sin ingresos, deudas con interés = problema

  • Coloca deuda TOTAL pendiente (suma todo)
  • Excluye hipotecas (ya están en sección anterior)
  • Calcula: años hasta estar libre de deudas < años hasta FIRE?
""")
    
    config['other_liabilities'] = get_float_input(
        "Total de otras deudas (€)",
        default=config.get('other_liabilities', 0),
        min_val=0
    )
    
    # Calculate and display net worth basics
    gross_real_estate = (config.get('primary_residence_value', 0) + 
                         config.get('other_real_estate_value', 0))
    total_real_estate_debt = (config.get('primary_residence_mortgage', 0) +
                              config.get('other_real_estate_mortgage', 0))
    real_estate_equity = gross_real_estate - total_real_estate_debt
    other_liabilities = config.get('other_liabilities', 0)
    
    # Calculate total rental income
    total_annual_rent = (config.get('primary_residence_annual_rent', 0) + 
                         config.get('other_real_estate_annual_rent', 0))
    
    current_savings = config.get('current_savings', 0)
    
    total_liquid_assets = current_savings
    total_liabilities = total_real_estate_debt + other_liabilities
    net_worth = total_liquid_assets + real_estate_equity - total_liabilities
    
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE PATRIMONIO (NET WORTH)")
    print("=" * 80)
    print(f"""
Activos líquidos (inversiones):        €{current_savings:>15,.0f}
Inmuebles (valor bruto):                €{gross_real_estate:>15,.0f}
  - Hipotecas relacionadas:            €{total_real_estate_debt:>15,.0f}
  - Equity en inmuebles:                €{real_estate_equity:>15,.0f}

Otras deudas (préstamos, tarjetas):   €{other_liabilities:>15,.0f}

─────────────────────────────────────────────────────────────
PATRIMONIO NETO (Net Worth):           €{net_worth:>15,.0f}

💰 INGRESOS POR ALQUILER (anual):      €{total_annual_rent:>15,.0f}
""")
    
    # Add rental income to config for later use in projections
    config['annual_rental_income'] = total_annual_rent
    
    if net_worth < 0:
        print("""
⚠️  ALERTA: Tu patrimonio neto es NEGATIVO.
   Esto significa debes más de lo que posees.
   Recomendación: Enfócate en pagar deudas antes de FIRE.
""")
    elif net_worth < current_savings:
        print(f"""
ℹ️  Tienes deudas. Equity real = €{net_worth:,.0f}
   Tu portfolio de inversiones (€{current_savings:,.0f}) es
   {(current_savings/net_worth*100):.1f}% de tu patrimonio neto.
""")
    
    return config


def show_dividend_tax_context(profile_key: str) -> None:
    """Show explanation for how dividends are taxed in each profile."""
    if profile_key == "ucits":
        print("""
┌──────────────────────────────────────────────────────────────┐
│ 💰 CÓMO FUNCIONAN LOS DIVIDENDOS EN ESTE PERFIL             │
├──────────────────────────────────────────────────────────────┤
│ TU ESTRATEGIA: FONDOS UCITS ACUMULATIVOS (sin distribuir)  │
│              ✅ NO hay retención fiscal anual                │
│              ✅ Impuesto solo al vender (30+ años)          │
│                                                              │
│ VENTAJA (30 años @ 7%):  100€ → 761€ vs 650€ con impuesto  │
│                                                              │
│ Fondos UCITS Acumulativos recomendados:                     │
│  • VWCE (Vanguard All-World) - 0.22% TER                   │
│  • IWDA (iShares Core World) - 0.20% TER                   │
│                                                              │
│ ✅ Tu cartera target ES 5-8% MÁS BAJA (menos capital)      │
└──────────────────────────────────────────────────────────────┘
""")
    else:
        profile = PROFILES[profile_key]
        defaults = profile["defaults"]
        div_tax = defaults['tax_rate_on_dividends']
        example_div_gross = 900
        example_div_net = example_div_gross * (1 - div_tax)
        example_div_tax = example_div_gross * div_tax
        print(f"""
┌──────────────────────────────────────────────────────────────┐
│ 💰 CÓMO FUNCIONAN LOS DIVIDENDOS EN ESTE PERFIL             │
├──────────────────────────────────────────────────────────────┤
│ TU ESTRATEGIA: FONDOS/ACCIONES QUE DISTRIBUYEN DIVIDENDOS   │
│              ⚠️  Hay retención fiscal anual ({div_tax*100:.0f}%)        │
│              ⚠️  Solo reinviertes neto (menos eficiente)    │
│                                                              │
│ EJEMPLO: Cartera €100.000 @ 6% bruto = €6.000              │
│  • Dividendos brutos (15%): €{example_div_gross:,.0f}                              │
│  • Impuesto retenido ({div_tax*100:.0f}%): €{example_div_tax:,.0f}                     │
│  • Reinvertible neto: €{example_div_net:,.0f}   ← Pérdidas €{example_div_tax:,.0f}/año │
│                                                              │
│ A LARGO PLAZO: Tu cartera target es 5-8% MÁS ALTA          │
│                Pueden ser 2-3 años extra hasta FIRE          │
│                                                              │
│ CÓMO MEJORAR:                                               │
│  1️⃣  Cambia a fondos UCITS ACUMULATIVOS (Acc)              │
│  2️⃣  Ajusta % impuesto si tu broker retiene diferente      │
│                                                              │
│ 📌 Este modelo asume dividendos BRUTOS. Sé realista.       │
└──────────────────────────────────────────────────────────────┘
""")


def show_defaults(profile_key: str) -> None:
    
    profile = PROFILES[profile_key]
    defaults = profile["defaults"]
    
    print(f"\n🎯  {profile['name']}")
    print("━" * 80)
    print("Valores por defecto (presiona ENTER para aceptarlos sin cambios):\n")
    print(f"  • Gasto anual deseado          : €{defaults['annual_spending']:>10,}")
    print(f"  • Tasa de Retirada Segura (TRS): {defaults['safe_withdrawal_rate']*100:>10.1f}%")
    print(f"  • Retorno esperado             : {defaults['expected_return']*100:>10.1f}%")
    print(f"  • Inflación esperada           : {defaults['inflation_rate']*100:>10.1f}%")
    print(f"  • Impuesto sobre plusvalías    : {defaults['tax_rate_on_gains']*100:>10.1f}%")
    print(f"  • Impuesto sobre dividendos    : {defaults['tax_rate_on_dividends']*100:>10.1f}%")
    print(f"  • Impuesto sobre intereses     : {defaults['tax_rate_on_interest']*100:>10.1f}%")
    print(f"  • Comisión de fondos UCITS     : {defaults['fund_fees']*100:>10.3f}%")
    print("━" * 80)
    
    # Show dividend tax treatment specific to this profile
    show_dividend_tax_context(profile_key)


def ask_with_default(prompt: str, default_value: float, unit: str = "", is_percentage: bool = False, max_pct: float = 100) -> float:
    """Ask for input with a default value; pressing ENTER accepts the default.
    
    Args:
        prompt: Question to ask user
        default_value: Value to use if user presses ENTER (in decimal for percentages)
        unit: "€" for currency
        is_percentage: True if input should be treated as a percentage
        max_pct: Maximum allowed percentage (e.g., 1 for commissions, 100 for taxes)
    """
    while True:
        if is_percentage:
            suffix = f" [defecto {default_value*100:.1f}%]"
        elif unit:
            suffix = f" [defecto €{default_value:,.0f}]"
        else:
            suffix = f" [defecto {default_value}]"
        
        resp = input(f"{prompt}{suffix}: ").strip()
        
        if not resp:
            return default_value
        
        try:
            # Remove common characters
            cleaned = resp.replace("€", "").replace(",", ".").replace("%", "").strip()
            value = float(cleaned)
            
            if is_percentage:
                # User input logic for percentages
                # If value is greater than what it would be in decimal form,
                # assume user entered a percentage (e.g., 22 for 22%, or 0.22 for 0.22%)
                max_decimal = max_pct / 100
                
                if value > max_decimal:
                    # User entered a percentage notation - divide by 100
                    value = value / 100
                
                # Validate range (in decimal form)
                if not (0 <= value <= max_decimal):
                    print(f"❌ El porcentaje debe estar entre 0% y {max_pct}%.")
                    continue
            else:
                # Basic validation for non-percentages
                if value < 0:
                    print("❌ El valor debe ser no-negativo.")
                    continue
            
            return value
        except ValueError:
            print("❌ Introduce un número válido.")
            continue


# ============================================================================
# PORTFOLIO COMPOSITION FUNCTIONS
# ============================================================================

INSTRUMENTS = {
    "eu_stocks": {"name": "Acciones Europeas", "default_return": 0.075, "risk": "Alto"},
    "indexed": {"name": "Fondos Indexados (MSCI Europe)", "default_return": 0.065, "risk": "Medio-Alto"},
    "balanced60": {"name": "Fondos Balanceados (60/40)", "default_return": 0.056, "risk": "Medio"},
    "balanced50": {"name": "Fondos Balanceados (50/50)", "default_return": 0.045, "risk": "Medio-Bajo"},
    "gov_bonds": {"name": "Bonos Gobierno (España)", "default_return": 0.025, "risk": "Bajo"},
    "corp_bonds": {"name": "Bonos Corporativos", "default_return": 0.035, "risk": "Medio"},
    "deposits": {"name": "Depósitos a Plazo (1-3 años)", "default_return": 0.035, "risk": "Muy Bajo"},
    "gold": {"name": "Oro (ETF)", "default_return": 0.025, "risk": "Bajo"},
    "custom": {"name": "Instrumento personalizado", "default_return": None, "risk": "Variable"},
    # Additional popular ETFs and instruments
    "vwce": {"name": "Vanguard FTSE All-World UCITS ETF (USD) Accumulating", "default_return": 0.065, "risk": "Medio-Alto"},
    "iwda": {"name": "iShares Core MSCI World UCITS ETF USD (Acc)", "default_return": 0.068, "risk": "Medio-Alto"},
    "msci_world": {"name": "iShares Core MSCI World UCITS ETF USD (Acc)", "default_return": 0.068, "risk": "Medio-Alto"},
    "emim": {"name": "iShares Core MSCI Emerging Markets IMI UCITS ETF (Acc)", "default_return": 0.075, "risk": "Alto"},
    "sp500": {"name": "Vanguard S&P 500 UCITS ETF (USD) Distributing", "default_return": 0.075, "risk": "Alto"},
    "bond_1_3y": {"name": "iShares USD Treasury Bond 1-3yr UCITS ETF (Acc)", "default_return": 0.025, "risk": "Bajo"},
    "bond_7_10y": {"name": "iShares USD Treasury Bond 7-10yr UCITS ETF (Acc)", "default_return": 0.035, "risk": "Medio"},
    "bond_20_plus": {"name": "iShares USD Treasury Bond 20+yr UCITS ETF USD (Acc)", "default_return": 0.040, "risk": "Medio"},
    "commodity_swap": {"name": "iShares Diversified Commodity Swap UCITS ETF", "default_return": 0.040, "risk": "Medio"},
}

PRESET_PORTFOLIOS = {
    "conservative": {
        "name": "Cartera Conservadora (30/70)",
        "description": "30% acciones, 70% bonos/depósitos. Bajo riesgo.",
        "composition": {"balanced50": 0.5, "gov_bonds": 0.3, "deposits": 0.2},
        "expected_return": 0.035,
    },
    "balanced": {
        "name": "Cartera Balanceada (50/50)",
        "description": "50% acciones, 50% bonos. Equilibrio riesgo-rendimiento.",
        "composition": {"balanced60": 0.7, "gov_bonds": 0.3},
        "expected_return": 0.048,
    },
    "growth": {
        "name": "Cartera Crecimiento (70/30)",
        "description": "70% acciones, 30% bonos. Mayor potencial, más riesgo.",
        "composition": {"eu_stocks": 0.4, "indexed": 0.3, "gov_bonds": 0.3},
        "expected_return": 0.062,
    },
}


def get_portfolio_composition() -> tuple[float, Dict[str, Any]]:
    """Get user's portfolio composition and calculate weighted return.
    
    Returns:
        (weighted_return, portfolio_dict)
    """
    print("""
💳 PARÁMETRO 3: TASA DE INTERESES (Interest Tax)
────────────────────────────────────────────────────────────────────────────
Qué es: El % de impuesto sobre INTERESES: cuentas de ahorro, depósitos a plazo,
        bonos, etc. Es la tasa más alta porque los intereses son ingresos
        regulares (no como ganancias de capital).
        
Ejemplo: Tienes 50,000 € en depósitos con 2% de interés anual:
         • Intereses brutos = 50,000 € × 0.02 = 1,000 €
         • Impuesto (45%) = 1,000 € × 0.45 = 450 €
         • Intereses netos = 1,000 € - 450 € = 550 € (55% neto)

Por qué importa: Los depósitos seguros generan poco rendimiento, pero
                 luego los impuestos lo reducen más aún.
                 No es eficiente confiar en intereses para FIRE.

⚠️  VARÍA MUCHO POR PAÍS EUROPEO:
   España: 19% (retención) / 45% (con IRPF, clase media)
   Bélgica: 15-37% (depende del tipo de depósito)
   Francia: 30% (retención única)
   Italia: 26% (fijo)
   Portugal: 0% (si están en depósitos según 38/88/CEE)
   Países Bajos: 32% (sobre ganancia subyacente)
   Polonia: 19% (fijo)
   Alemania: 26% (Kapitalertragssteuer)
   Irlanda: 33% (impuesto de retención)

Nota: Muchos países europeos ofrecen exenciones en planes de pensiones.
      Algunos depósitos están parcialmente exentos si son a largo plazo.
""")
    
    tax_rate_on_interest = get_percent_input(
        "  Tasa de intereses [%] [defecto 45.0%]",
        default=0.45,
    )
    print(f"  ✅ Intereses: {tax_rate_on_interest*100:.1f}%\n")
    
    print("""
� PARÁMETRO 4: COMISIÓN DE FONDOS UCITS (Fund Management Fee)
────────────────────────────────────────────────────────────────────────────
Qué es: Lo que el fondo te COBRA cada año simplemente por gestionar
        tu dinero. Se expresa como % del patrimonio que gestiona.
        NO es un impuesto; es lo que cobra el gestor del fondo.
        
Ejemplo: Inviertes en un ETF con comisión 0.1% sobre 100,000 €:
         • Comisión anual = 100,000 € × 0.001 = 100 €
         • Después de 30 años (con crecimiento): ≈ 15,000 € perdidos
         • Mismo ETF con 0.5%? Pierdes ≈ 75,000 € en 30 años.

Por qué importa: Las comisiones actúan como un "impuesto invisible".
                 A mayor comisión → menor rendimiento neto → más capital necesario.
                 Con el tiempo, incluso 0.1% de diferencia suma mucho.

Valores típicos:
  • 0.03-0.10% = ETF de bajo costo (recomendado para FIRE)
  • 0.20-0.50% = Fondos activos normales
  • 0.75-1.5% = Fondos con asesoría personalizada
  • 1.5%+ = Evita (destroza retornos a largo plazo)
""")
    
    # Tax explanations by country - context for user
    print("\n💡 NOTA SOBRE IMPUESTOS (varía por país):\n")
    print("\n💡 NOTA SOBRE IMPUESTOS (varía por país):\n")
    print("   • Plusvalías: Impuesto al vender (España 19-27%, algunos países 0%)")
    print("   • Dividendos: Retención en origen (España 19-21%, EU: 10-42%)")
    print("   • Intereses: Sobre depósitos y bonos (España 19-45%, algunos 0%)")
    print("   → Consulta con asesor fiscal local para valores exactos\n")
    
    fund_fees = get_percent_input(
        "  Comisión de fondos UCITS (ej: 0.22 para 0.22%, 5 para 5%)",
        default=0.001,
        max_percent=1,  # Comisiones typically < 1%
    )
    print(f"  ✅ Comisión fondos: {fund_fees*100:.3f}%")
    print(f"     (Típico: 0.03-0.10% para ETF bajo costo)\n")
    
    print("""
SECCIÓN 5: HORIZONTE TEMPORAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 AÑOS DE PROYECCIÓN: ¿Cuántos años deseas ver en la tabla de crecimiento?
   • 20-25 años = Típico para gente que quiere FIRE en 15-20 años.
   • 40+ años = Si eres joven y quieres proyección a largo plazo.
   Recomendación: 25-30 años para ver el impacto de impuestos a largo plazo.
""")
    
    years_horizon = get_int_input(
        "¿Cuántos años deseas proyectar? - Horizonte temporal",
        default=25,
        min_val=1,
        max_val=70,
    )
    print(f"✅ Horizonte temporal: {years_horizon} años")
    print("\n" + "="*80)
    
    print("""
SECCIÓN 6: PATRIMONIO Y PASIVOS (Opcional)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 PATRIMONIO INMOBILIARIO: ¿Posees bienes raíces?
   Incluye: casa principal, propiedades de alquiler, terrenos, garajes, etc.
   Estima el valor actual de mercado (qué precio tendrían si los vendieras HOY).
   💡 Tip: Consulta Zoopla/Idealista o tasación profesional para estimar.
""")
    
    real_estate_value = get_float_input(
        "Valor estimado de patrimonio inmobiliario (€) [0 si no aplica]",
        default=0,
        min_val=0,
    )
    print(f"✅ Patrimonio inmobiliario: €{real_estate_value:,.0f}")
    
    if real_estate_value > 0:
        print("""
📌 HIPOTECA PENDIENTE: ¿Tienes deuda pendiente en bienes raíces?
""")
        real_estate_mortgage = get_float_input(
            "  Hipoteca pendiente (€)",
            default=0,
            min_val=0,
        )
        print(f"  ✅ Hipoteca: €{real_estate_mortgage:,.0f}")
    else:
        real_estate_mortgage = 0
    
    print("""
📌 OTROS PASIVOS: ¿Tienes otras deudas (préstamos, tarjetas, etc.)?
""")
    
    other_liabilities = get_float_input(
        "Otros pasivos/deudas (€)",
        default=0,
        min_val=0,
    )
    print(f"✅ Otros pasivos: €{other_liabilities:,.0f}")
    
    print("""
SECCIÓN 7: ESCENARIOS DE MERCADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 ¿Deseas ver proyecciones bajo diferentes escenarios de mercado?
   Pesimista: -30% retorno (mercado a la baja)
   Base: Tus expectativas actuales
   Optimista: +30% retorno (mercado fuerte)
""")
    
    include_scenarios = input("¿Ver escenarios de mercado? (s/n) [defecto: s]: ").strip().lower()
    include_scenarios = include_scenarios != "n" if include_scenarios else True
    
    print("\n" + "="*80)
    
    return {
        "age": age,
        "annual_spending": annual_spending,
        "safe_withdrawal_rate": safe_withdrawal_rate,
        "current_savings": current_savings,
        "annual_contribution": annual_contribution,
        "expected_return": expected_return,
        "inflation_rate": inflation_rate,
        "tax_rate_on_gains": tax_rate_on_gains,
        "tax_rate_on_dividends": tax_rate_on_dividends,
        "tax_rate_on_interest": tax_rate_on_interest,
        "fund_fees": fund_fees,
        "years_horizon": years_horizon,
        "withholding_tax": 0.15,
        "social_security_contributions": 0.0,
        "portfolio_info": portfolio_info,
        "real_estate_value": real_estate_value,
        "real_estate_mortgage": real_estate_mortgage,
        "other_liabilities": other_liabilities,
        "include_scenarios": include_scenarios,
    }


# ============================================================================
# RESULT DISPLAY FUNCTIONS
# ============================================================================

def show_summary(config: Dict[str, Any]):
    """Show configuration summary before running calculations."""
    print_section("Resumen de tu Perfil FIRE")
    
    from src.calculator import calculate_net_worth
    
    print("OBJETIVOS:")
    print(f"  • Gasto anual deseado: €{config['annual_spending']:,.0f}")
    print(f"  • Tasa de Retirada Segura (TRS): {config['safe_withdrawal_rate']*100:.1f}%")
    
    # Calculate both net and gross targets
    net_target = target_fire(config['annual_spending'], config['safe_withdrawal_rate'])
    gross_target = calculate_gross_target(
        config['annual_spending'],
        config['safe_withdrawal_rate'],
        config['tax_rate_on_gains']
    )
    
    print(f"  → Cartera objetivo neta: €{net_target:,.0f}")
    print(f"  → Cartera objetivo bruta (con impuestos): €{gross_target:,.0f}")
    print(f"  • Edad: {config['age']} años")
    
    print("\nSITUACIÓN PATRIMONIAL:")
    print(f"  • Ahorros invertidos: €{config['current_savings']:,.0f}")
    
    if config.get('real_estate_value', 0) > 0 or config.get('real_estate_mortgage', 0) > 0 or config.get('other_liabilities', 0) > 0:
        nw = calculate_net_worth(
            config['current_savings'],
            config.get('real_estate_value', 0),
            config.get('real_estate_mortgage', 0),
            config.get('other_liabilities', 0),
        )
        print(f"  • Patrimonio inmobiliario: €{nw['real_estate_value']:,.0f}")
        print(f"  • Hipoteca: €{nw['real_estate_mortgage']:,.0f}")
        print(f"  • Patrimonio neto inmobiliario: €{nw['real_estate_equity']:,.0f}")
        print(f"  • Otros pasivos: €{nw['total_liabilities'] - nw['real_estate_mortgage']:,.0f}")
        print(f"  → Patrimonio neto total: €{nw['net_worth']:,.0f}")
    
    print("\nAHORRO:")
    annual_rent = config.get('annual_rental_income', 0)
    print(f"  • Aportación anual (ahorro personal): €{config['annual_contribution']:,.0f}")
    if annual_rent > 0:
        print(f"  • Ingresos por alquiler (anual):      €{annual_rent:,.0f}")
        total_contribution_effective = config['annual_contribution'] + annual_rent
        print(f"  → TOTAL APORTE EFECTIVO:              €{total_contribution_effective:,.0f}")
    progress = (config['current_savings'] / gross_target) * 100 if gross_target > 0 else 0
    print(f"  → Progreso hacia objetivo: {progress:.1f}%")
    
    print("\nEXPECTATIVAS:")
    print(f"  • Retorno esperado: {config['expected_return']*100:.1f}%")
    print(f"  • Inflación esperada: {config['inflation_rate']*100:.1f}%")
    print(f"  • Retorno real (neto de inflación): {(config['expected_return'] - config['inflation_rate'])*100:.1f}%")
    
    print("\nFISCALIDAD & COMISIONES:")
    print(f"  • Impuesto sobre plusvalías: {config['tax_rate_on_gains']*100:.1f}%")
    print(f"  • Impuesto sobre dividendos: {config['tax_rate_on_dividends']*100:.1f}%")
    print(f"  • Impuesto sobre intereses: {config['tax_rate_on_interest']*100:.1f}%")
    print(f"  • Comisión de fondos: {config['fund_fees']*100:.3f}%")
    
    # Validations and warnings
    print("\n" + "="*80)
    warnings = []
    
    if config['fund_fees'] > 0.02:
        warnings.append(f"⚠️  COMISIÓN MUY ALTA ({config['fund_fees']*100:.2f}%)")
        warnings.append("   Típico: 0.03-0.10% (ETF bajo costo)")
        warnings.append("   → Considera cambiar a fondos más baratos (destruye retornos)")
    
    if config['current_savings'] == 0 and config['annual_contribution'] < 10_000:
        warnings.append(f"⚠️  AHORROS = €0 CON BAJO APORTE (€{config['annual_contribution']:,.0f}/año)")
        warnings.append("   → FIRE tomará mucho tiempo (30-50+ años)")
        warnings.append("   → Considera aumentar tu aporte anual (negociar salario, reducir gastos)")
    
    if config['tax_rate_on_gains'] + config['tax_rate_on_dividends'] + config['tax_rate_on_interest'] > 1.0:
        avg_tax = (config['tax_rate_on_gains'] + config['tax_rate_on_dividends'] + config['tax_rate_on_interest']) / 3
        warnings.append(f"⚠️  IMPUESTOS ALGO ALTOS (promedio {avg_tax*100:.1f}%)")
        warnings.append("   → Revisa si aplicas en un país con mejores tasas")
        warnings.append("   → O considera planes de pensiones (exención fiscal)")
    
    if config['expected_return'] - config['inflation_rate'] < 0.02:
        real_return = config['expected_return'] - config['inflation_rate']
        warnings.append(f"⚠️  RETORNO REAL BAJO ({real_return*100:.1f}% = retorno - inflación)")
        warnings.append("   → Retorno bruto 6% - inflación 2% = solo 4% real")
        warnings.append("   → Considera aumentar exposición a renta variable")
    
    if warnings:
        print("\n" + "⚠️  ALERTAS DETECTADAS:\n")
        for warning in warnings:
            print(f"{warning}")
        print("\n" + "="*80)
    
    confirm = input("\n¿Continuar con estos parámetros? (s/n): ").strip().lower()
    return confirm == "s"


def interactive_edit_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Allow user to edit parameters interactively one by one.
    
    Returns modified config or None if user wants to exit.
    """
    while True:
        print("\n" + "="*80)
        print("EDICIÓN DE PARÁMETROS - Elige qué deseas cambiar:\n")
        
        options = [
            ("Gasto anual deseado", "annual_spending", "€"),
            ("Tasa de Retirada Segura (TRS)", "safe_withdrawal_rate", "%"),
            ("Retorno esperado", "expected_return", "%"),
            ("Inflación esperada", "inflation_rate", "%"),
            ("Impuesto sobre plusvalías", "tax_rate_on_gains", "%"),
            ("Impuesto sobre dividendos", "tax_rate_on_dividends", "%"),
            ("Impuesto sobre intereses", "tax_rate_on_interest", "%"),
            ("Comisión de fondos UCITS", "fund_fees", "%"),
            ("Ahorros actuales", "current_savings", "€"),
            ("Aporte anual", "annual_contribution", "€"),
        ]
        
        for i, (display, key, unit) in enumerate(options, 1):
            if unit == "€":
                print(f"  {i}. {display.ljust(40)}: €{config[key]:,.0f}")
            else:
                print(f"  {i}. {display.ljust(40)}: {config[key]*100:.2f}%")
        
        print(f"  {len(options) + 1}. Ver resumen actualizado")
        print(f"  0. Salir sin cambios")
        
        while True:
            try:
                choice = int(input("\nElige opción (0-{0}): ".format(len(options) + 1)).strip())
                if 0 <= choice <= len(options) + 1:
                    break
                print("❌ Opción inválida.")
            except ValueError:
                print("❌ Introduce un número válido.")
        
        if choice == 0:
            return None  # Exit
        elif choice == len(options) + 1:
            return config  # Return to summary view
        else:
            # Edit selected parameter
            display, key, unit = options[choice - 1]
            default_value = config[key]
            
            try:
                if unit == "€":
                    config[key] = ask_with_default(f"\n{display}", default_value, unit="€")
                else:  # Percentage
                    max_pct = 1 if key == "fund_fees" else 100
                    config[key] = get_percent_input(f"  {display}", default_value, max_percent=max_pct)
                
                print(f"✅ Actualizado: {display}")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Show updated summary
            if show_summary(config):
                return config
            # If user rejected again, loop to edit more


def calculate_years_to_fire(config: Dict[str, Any]) -> Optional[int]:
    """Calculate years to reach FIRE target (using gross target with taxes)."""
    # Use net target (what user needs in portfolio after withdrawals)
    target = target_fire(config['annual_spending'], config['safe_withdrawal_rate'])
    current = config.get('current_savings', 0)

    if current >= target:
        return 0

    # Use effective contribution (include rental income)
    annual_contrib = config.get('annual_contribution', 0)
    annual_rent = config.get('annual_rental_income', 0)
    annual_contrib_effective = annual_contrib + annual_rent

    if annual_contrib_effective <= 0 and config.get('expected_return', 0) <= 0:
        return None

    # Project forward up to a sensible cap and find first year meeting target
    max_search_years = max(50, config.get('years_horizon', 25) * 4)
    from src.calculator import project_portfolio

    proj = project_portfolio(
        current_savings=current,
        annual_contribution=annual_contrib_effective,
        years=max_search_years,
        expected_return=config.get('expected_return', 0.06),
        inflation_rate=config.get('inflation_rate', 0.02),
        tax_rate_on_gains=0,  # align with UCITS accumulative projection
        tax_rate_on_dividends=0,
        tax_rate_on_interest=0,
        fund_fees=config.get('fund_fees', 0.001),
    )

    for y in range(1, max_search_years + 1):
        if proj.get(y) and proj[y]['nominal_portfolio'] >= target:
            return y

    return None


def calculate_years_for_target(config: Dict[str, Any], target_portfolio: float) -> Optional[int]:
    """Calculate years to reach a specific portfolio target."""
    current = config.get('current_savings', 0)

    if current >= target_portfolio:
        return 0

    # Use effective contribution (include rental income)
    annual_contrib = config.get('annual_contribution', 0)
    annual_rent = config.get('annual_rental_income', 0)
    annual_contrib_effective = annual_contrib + annual_rent

    if annual_contrib_effective <= 0 and config.get('expected_return', 0) <= 0:
        return None

    # Project forward and find first year meeting target
    max_search_years = max(50, config.get('years_horizon', 25) * 4)
    from src.calculator import project_portfolio

    proj = project_portfolio(
        current_savings=current,
        annual_contribution=annual_contrib_effective,
        years=max_search_years,
        expected_return=config.get('expected_return', 0.06),
        inflation_rate=config.get('inflation_rate', 0.02),
        tax_rate_on_gains=0,
        tax_rate_on_dividends=0,
        tax_rate_on_interest=0,
        fund_fees=config.get('fund_fees', 0.001),
    )

    for y in range(1, max_search_years + 1):
        if proj.get(y) and proj[y]['nominal_portfolio'] >= target_portfolio:
            return y

    return None


def get_motivational_message(config: Dict[str, Any], years_to_fire: Optional[int]) -> str:
    """Generate personalized motivational message."""
    target = target_fire(config['annual_spending'], config['safe_withdrawal_rate'])
    progress = (config['current_savings'] / target) * 100
    
    if config['current_savings'] >= target:
        return MOTIVATIONAL_MESSAGES["already"]
    elif progress > 75:
        return MOTIVATIONAL_MESSAGES["high_progress"]
    elif progress > 50:
        return MOTIVATIONAL_MESSAGES["mid_progress"]
    elif years_to_fire and years_to_fire < 5:
        return MOTIVATIONAL_MESSAGES["early"]
    elif years_to_fire and years_to_fire < 10:
        return MOTIVATIONAL_MESSAGES["medium"]
    elif years_to_fire and years_to_fire < 20:
        return MOTIVATIONAL_MESSAGES["long"]
    else:
        return MOTIVATIONAL_MESSAGES["very_long"]


# ============================================================================
# MONTE CARLO & KPI FUNCTIONS FOR ADVANCED REPORTING
# ============================================================================

def simulate_monte_carlo(config: Dict[str, Any], simulations: int = 1000) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation to estimate probability of success.
    
    Assumes returns are normally distributed with mean = expected_return,
    std dev = about 15% (typical market volatility).
    """
    random.seed(42)  # For reproducibility
    
    target = target_fire(config['annual_spending'], config['safe_withdrawal_rate'])
    current = config['current_savings']
    annual_contrib = config['annual_contribution']
    years_to_simulate = config.get('years_horizon', 25)
    mean_return = config['expected_return']
    inflation = config['inflation_rate']
    
    # Asset volatility (standard deviation of returns)
    # Conservative estimate: 15% annually
    volatility = 0.15
    
    success_count = 0
    final_values = []
    
    for _ in range(simulations):
        portfolio = current
        
        for year in range(years_to_simulate):
            # Random annual return from normal distribution
            annual_return = random.gauss(mean_return, volatility)
            
            # Growth + contribution
            portfolio = portfolio * (1 + annual_return) + annual_contrib
            
            # Adjust contribution for inflation
            adjusted_contrib = annual_contrib * ((1 + inflation) ** (year + 1))
        
        final_values.append(portfolio)
        
        # Check if portfolio reached target
        if portfolio >= target:
            success_count += 1
    
    success_rate = (success_count / simulations) * 100
    
    # Calculate percentiles
    final_values_sorted = sorted(final_values)
    percentile_10 = final_values_sorted[int(len(final_values) * 0.10)]
    percentile_50 = final_values_sorted[int(len(final_values) * 0.50)]
    percentile_90 = final_values_sorted[int(len(final_values) * 0.90)]
    
    return {
        'success_rate': success_rate,
        'percentile_10': percentile_10,    # Pessimistic scenario
        'percentile_50': percentile_50,    # Median scenario
        'percentile_90': percentile_90,    # Optimistic scenario
        'target': target,
        'mean_final': sum(final_values) / len(final_values),
    }


def print_recommendations(config: Dict[str, Any], kpis: Dict[str, Any]) -> None:
    """Print tailored recommendations based on user's FIRE stage."""
    progress = kpis.get('progress_pct', 0)
    years_to_fire = kpis.get('years_to_fire', None)
    debt_ratio = kpis.get('debt_to_fire_ratio', 0)
    savings_rate = kpis.get('savings_rate', 0)

    print("\n" + "╔" + "═" * 76 + "╗")
    print("║                         🧭 RECOMENDACIONES PRÁCTICAS                        ║")
    print("╚" + "═" * 76 + "╝\n")

    if progress >= 100 or kpis.get('fire_number', 0) <= kpis.get('net_worth', 0):
        # Already FIRE
        print("🔒 Estado: Ya alcanzaste tu objetivo FIRE o lo tienes cubierto.")
        print("  - Mantén una estrategia de retirada conservadora (SWR ajustada).")
        print("  - Optimiza fiscalidad antes de vender: planifica ventas e impuestos.")
        print("  - Revisa seguros, testamento y planificación patrimonial.")
        print("  - Considera un plan de decumulation: bonos + retiro escalonado.")
        return

    if progress < 25:
        print("🚀 Etapa: Inicial (Early stage)")
        print("  - Aumenta tu tasa de ahorro: objetivo 20-50% del ingreso si es posible.")
        print("  - Reduce gastos discrecionales y automatiza ahorros.")
        print("  - Prioriza pagar deudas de alto interés (tarjeta, préstamos personales).")
        print("  - Controla comisiones: usa ETFs de bajo coste (0.05%-0.20%).")
        print("  - Crea fondo de emergencia (3-6 meses) antes de asumir riesgos mayores.")
        print("  - Si tienes alquileres: guarda 20-30% de ingresos para capex y vacancias.")
    elif progress < 75:
        print("⚖️ Etapa: Intermedia (Mid stage)")
        print("  - Diversifica cartera (acciones globales + bonos según horizonte).")
        print("  - Considera estrategia fiscal: UCITS acumulativos, cuenta de pensión si existe.")
        print("  - Reduce deuda de forma estratégica: prioriza deuda caro vs barato.")
        print("  - Optimiza ingresos por alquiler: revisión de contratos, selección de inquilinos.")
        print("  - Aumenta ahorro incremental: bonificaciones salariales, freelancing.")
    else:
        print("🎯 Etapa: Avanzada (Late stage)")
        print("  - Empieza a des-risk: baja porcentaje de acciones según tolerancia.")
        print("  - Planifica retirada: orden de ventas, impuestos y secuencia de retiros.")
        print("  - Protege capital: seguros, planificación sanitaria y legal.")
        print("  - Simula distintos SWR (3.0%-4.5%) y prepara buffers para años malos.")

    # Cross-cutting advice
    print("\nConsejos transversales:")
    print("  - Mantén comisiones bajas y reinvierte ingresos de alquiler si tu objetivo es crecimiento.")
    print("  - Revisa tu asignación de activos cada 1-3 años o tras eventos importantes.")
    if debt_ratio > 0.2:
        print("  - Atención: tu ratio Deuda/FIRE es alto. Prioriza reducir deuda antes de retirarte.")
    if savings_rate < 0.10:
        print("  - Considera aumentar ahorro (actual <10%). Busca medir gastos y optimizar.")
    print("")


def calculate_kpis(config: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate and return Key Performance Indicators for FIRE plan."""
    target = target_fire(config['annual_spending'], config['safe_withdrawal_rate'])
    current = config['current_savings']
    annual_contrib = config['annual_contribution']
    annual_rental_income = config.get('annual_rental_income', 0)
    annual_contrib_effective = annual_contrib + annual_rental_income  # Include rental income
    annual_spending = config['annual_spending']
    expected_return = config['expected_return']
    inflation = config['inflation_rate']
    
    # 1. FIRE Number: capital needed
    fire_number = target
    
    # 2. Burning rate: annual expenses as % of portfolio
    burning_rate = annual_spending / current if current > 0 else float('inf')
    
    # 3. Years to FIRE (simplified) - using effective contribution
    if annual_contrib_effective <= 0:
        years_to_fire_est = float('inf')
    else:
        # Rough estimate using annuity formula
        # FV = PV(1+r)^n + PMT * [((1+r)^n - 1) / r]
        # Simplified: if no returns, years = (target - current) / contrib
        net_contrib_needed = target - current
        if net_contrib_needed <= 0:
            years_to_fire_est = 0
        else:
            # With returns factored in roughly
            years_to_fire_est = math.log((target - current * (1 + expected_return)) / annual_contrib_effective + 1) / math.log(1 + expected_return) if expected_return > 0 else net_contrib_needed / annual_contrib_effective
            years_to_fire_est = max(0, years_to_fire_est)
    
    # 4. Savings rate: annual contribution as % of assumed income
    # We don't know actual income, so estimate from spending + effective contribution
    estimated_income = annual_spending + annual_contrib_effective
    savings_rate = annual_contrib_effective / estimated_income if estimated_income > 0 else 0
    
    # 5. Progress: current as % of target
    progress = (current / target) * 100 if target > 0 else 0
    
    # 5b. Years until desired retirement age
    current_age = config.get('age', 30)
    desired_retirement_age = config.get('desired_retirement_age', 65)
    years_until_retirement = max(0, desired_retirement_age - current_age)
    
    # 6. Equity value (liquid assets only)
    equity_liquid = current
    
    # 7. Real estate equity
    primary_re = config.get('primary_residence_value', 0)
    primary_mort = config.get('primary_residence_mortgage', 0)
    other_re = config.get('other_real_estate_value', 0)
    other_mort = config.get('other_real_estate_mortgage', 0)
    
    real_estate_equity = (primary_re - primary_mort) + (other_re - other_mort)
    
    # 8. Total net worth
    other_liab = config.get('other_liabilities', 0)
    net_worth = equity_liquid + real_estate_equity - other_liab
    
    # 9. Debt-to-FIRE ratio
    total_debt = primary_mort + other_mort + other_liab
    debt_to_fire_ratio = total_debt / fire_number if fire_number > 0 else 0
    
    # Use the more accurate simulation-based years_to_fire if available
    try:
        years_to_fire_sim = calculate_years_to_fire(config)
    except Exception:
        years_to_fire_sim = years_to_fire_est

    return {
        'fire_number': fire_number,
        'burning_rate': burning_rate,
        'years_to_fire': years_to_fire_sim,
        'savings_rate': savings_rate,
        'progress_pct': progress,
        'equity_liquid': equity_liquid,
        'real_estate_equity': real_estate_equity,
        'net_worth': net_worth,
        'total_debt': total_debt,
        'debt_to_fire_ratio': debt_to_fire_ratio,
        'years_until_retirement': years_until_retirement,
    }


def show_results(config: Dict[str, Any]):
    """Display comprehensive results and analysis."""
    print_section("🎯 RESULTADOS DE TU ANÁLISIS FIRE")
    
    target = target_fire(config['annual_spending'], config['safe_withdrawal_rate'])
    years_to_fire = calculate_years_to_fire(config)
    progress = (config['current_savings'] / target) * 100
    
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                          🎯 OBJETIVO PRINCIPAL                             ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"\n  Portfolio necesario: €{target:,.0f}")
    print(f"  Tienes actualmente: €{config['current_savings']:,.0f}")
    print(f"  Te falta: €{max(0, target - config['current_savings']):,.0f}")
    print(f"  Progreso: {progress:.1f}% {'✓' if progress >= 100 else ''}\n")
    
    # KPI SUMMARY
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                    📈 INDICADORES CLAVE (KPIs)                             ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝\n")
    
    kpis = calculate_kpis(config)
    
    print(f"  🎯 FIRE Number (Objetivo):              €{kpis['fire_number']:>15,.0f}")
    print(f"  💰 Patrimonio Neto (Net Worth):         €{kpis['net_worth']:>15,.0f}")
    print(f"  📊 Equity Líquido (inversiones):        €{kpis['equity_liquid']:>15,.0f}")
    print(f"  🏠 Equity Inmobiliario (neto deudas):  €{kpis['real_estate_equity']:>15,.0f}")
    print(f"  💳 Deuda Total Pendiente:               €{kpis['total_debt']:>15,.0f}")
    print(f"\n  🔥 Burning Rate (anual):                {kpis['burning_rate']:>19.1%}")
    print(f"  💾 Savings Rate (anual):                {kpis['savings_rate']:>19.1%}")
    print(f"  📈 Progreso hacia FIRE:                 {kpis['progress_pct']:>19.1f}%")
    
    # Recommendations based on KPIs
    print_recommendations(config, kpis)
    
    if kpis['years_to_fire'] != float('inf'):
        print(f"  ⏰ Años hasta FIRE (estimado):          {kpis['years_to_fire']:>19.1f}")
    else:
        print(f"  ⏰ Años hasta FIRE (estimado):          {'∞ (sin aporte)':>19}")
    
    # Show retirement age vs FIRE target
    years_until_retirement = kpis.get('years_until_retirement', 0)
    years_to_fire_est = kpis['years_to_fire']
    
    if years_to_fire_est != float('inf') and years_until_retirement > 0:
        if years_to_fire_est <= years_until_retirement:
            gap = years_until_retirement - years_to_fire_est
            if gap == 0:
                print(f"  ⏱️  Alcanzarás FIRE justo en tu edad de retiro deseada")
            else:
                print(f"  ✅ Alcanzarás FIRE {gap:.1f} años antes de tu edad deseada ({int(config['desired_retirement_age'])}a)")
        else:
            gap = years_to_fire_est - years_until_retirement
            print(f"  ⚠️  FIRE {gap:.1f} años después de tu edad de retiro deseada ({int(config['desired_retirement_age'])}a)")
    
    print(f"  ⚠️  Deuda/FIRE Ratio:                    {kpis['debt_to_fire_ratio']:>19.1%}")
    
    if kpis['debt_to_fire_ratio'] > 0:
        print("\n  💡 Nota: Recomendación FIRE típica es pagar todas las deudas")
        print("           antes de retirarte para máxima tranquilidad.\n")
    else:
        print("\n  ✅ ¡Excelente! Ninguna deuda vinculada a tu FIRE number.\n")
    
    # MONTE CARLO ANALYSIS
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║              🎲 ANÁLISIS DE MONTECARLO (Probabilidad de Éxito)            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝\n")
    
    print("  Simulando 1,000 escenarios con retornos variable ({:.1f}% ± 15% volatividad)".format(config['expected_return']*100))
    print("  Horizonte: {} años | Objetivo: €{:,.0f}\n".format(config.get('years_horizon', 25), target))
    
    mc_results = simulate_monte_carlo(config, simulations=1000)
    
    print(f"  ✅ PROBABILIDAD DE ÉXITO:                {mc_results['success_rate']:>14.1f}%")
    print(f"     (Probabilidad de alcanzar €{target:,.0f} en {config.get('years_horizon', 25)} años)\n")
    
    print(f"  📊 ESCENARIOS PROYECTADOS EN {config.get('years_horizon', 25)} AÑOS:")
    print(f"     Pesimista (10º percentil):         €{mc_results['percentile_10']:>15,.0f}  ({(mc_results['percentile_10']/target)*100:>5.1f}% del objetivo)")
    print(f"     Mediano (50º percentil):           €{mc_results['percentile_50']:>15,.0f}  ({(mc_results['percentile_50']/target)*100:>5.1f}% del objetivo)")
    print(f"     Optimista (90º percentil):         €{mc_results['percentile_90']:>15,.0f}  ({(mc_results['percentile_90']/target)*100:>5.1f}% del objetivo)")
    print(f"     Promedio:                          €{mc_results['mean_final']:>15,.0f}  ({(mc_results['mean_final']/target)*100:>5.1f}% del objetivo)\n")
    
    # Interpretation
    if mc_results['success_rate'] >= 95:
        print("     Veredicto: 🟢 EXCELENTE - Muy alta probabilidad de éxito\n")
    elif mc_results['success_rate'] >= 85:
        print("     Veredicto: 🟢 BUENO - Alta probabilidad de éxito\n")
    elif mc_results['success_rate'] >= 75:
        print("     Veredicto: 🟡 ACEPTABLE - Probabilidad adecuada (margen estrecho)\n")
    else:
        print("     Veredicto: 🔴 RIESGO - Probabilidad baja (necesitas más capital/contribución)\n")
    
    if years_to_fire is not None:
        print("╔════════════════════════════════════════════════════════════════════════════╗")
        print("║                     ⏰ AÑOS HASTA INDEPENDENCIA FINANCIERA                 ║")
        print("╚════════════════════════════════════════════════════════════════════════════╝")
        
        if years_to_fire == 0:
            print("\n  🎉 ¡YA LO LOGRASTE! ¡Felicidades! 🎉\n")
        else:
            current_age = config.get('age', 30)
            retire_age = current_age + years_to_fire
            print(f"\n  Años hasta FIRE: {years_to_fire} años")
            print(f"  (Edad actual: {current_age}a → Podrías retirarte a los {retire_age}a)\n")
    
    # Motivational message
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                    💫 MENSAJE INSPIRADOR PERSONALIZADO                     ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    motivational = get_motivational_message(config, years_to_fire)
    print(f"\n  {motivational}\n")
    
    # Projection table - Use full horizon
    years_horizon = config.get('years_horizon', 25)
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print(f"║              📊 PROYECCIÓN DE CARTERA ({years_horizon} AÑOS)                         ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝\n")
    
    # Calculate effective annual contribution (salary savings + rental income)
    annual_contribution_effective = (config['annual_contribution'] + 
                                    config.get('annual_rental_income', 0))
    
    print(f"  Contribución anual efectiva: €{annual_contribution_effective:,.0f}")
    print(f"  (€{config['annual_contribution']:,.0f} ahorros + €{config.get('annual_rental_income', 0):,.0f} alquiler)\n")
    
    # For UCITS accumulative funds: no annual taxes until realization
    # Calculate projection without annual tax drag
    proj = project_portfolio(
        current_savings=config['current_savings'],
        annual_contribution=annual_contribution_effective,
        years=years_horizon,
        expected_return=config['expected_return'],
        inflation_rate=config['inflation_rate'],
        tax_rate_on_gains=0,  # UCITS acumulativo: no tax until sold
        tax_rate_on_dividends=0,  # Acumulativo reinvierte sin impuestos
        tax_rate_on_interest=0,  # Idem
        fund_fees=config['fund_fees'],
    )
    
    print(f"{'Año':<6} {'Nominal (€)':<18} {'Real (€)':<18} {'Progreso':<12}")
    print("-" * 54)
    
    # Display all years, but show every year for <=10 years, every 2-3 years for larger horizons
    display_every = 1 if years_horizon <= 10 else (2 if years_horizon <= 20 else 3)
    
    for year in sorted(proj.keys()):
        if year % display_every == 0 or year == 1 or year == years_horizon:  # Always show year 1, final, and selected intervals
            nominal = proj[year]['nominal_portfolio']
            real = proj[year]['real_portfolio']
            pct = (nominal / target) * 100
            # Bar fills up to 100% only; show real % as number
            capped_pct = max(0.0, min(100.0, pct))
            blocks = int(capped_pct / 5)
            blocks = min(20, max(0, blocks))
            bar = "█" * blocks + "░" * (20 - blocks)
            print(f"{year:<6} €{nominal:>12,.0f}  €{real:>12,.0f}  [{bar}] {pct:>6.1f}%")
    
    print("\n  📌 Nota sobre impuestos:")
    print("     • Estos cálculos asumen UCITS ACUMULATIVO (sin distribución de dividendos)")
    print("     • Los impuestos sobre plusvalías se pagan SOLO cuando vendes (diferimiento fiscal)")
    print("     • Una vez alcances tu objetivo FIRE, pagarás impuestos al realizar la ganancia")
    print("     • 'Real' está ajustado por inflación; muestra poder de compra actual.\n")
    
    # Coast FIRE scenario
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                   🌴 COAST FIRE: ¿PODRÍAS DEJAR DE AHORRAR?               ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝\n")
    
    coast_possible = coast_fire_condition(
        current_savings=config['current_savings'],
        annual_contribution=0,  # Ya no contribuyes
        years_to_target=15,
        expected_return=config['expected_return'],
        target_portfolio=target,
    )
    
    if coast_possible:
        print(f"  ✅ SÍ PUEDES hacer Coast FIRE en 15 años.")
        print(f"     Tu capital de €{config['current_savings']:,.0f} crecerá hasta €{target:,.0f}")
        print(f"     sin nuevas aportaciones (solo con rendimiento del {config['expected_return']*100:.1f}% anual).\n")
    else:
        print(f"  📊 Coast FIRE aún no disponible (necesitarías más capital inicial).")
        if years_to_fire and years_to_fire != float('inf'):
            print(f"  ✅ PERO: Con tus aportaciones, lo lograrás en apenas {years_to_fire} años.")
            print(f"     Cuando llegues, ya no necesitarás trabajar (¡Free Money Forever!)\n")
        else:
            print(f"  Mantén tus aportaciones consistentes - ¡cada euro suma!\n")
    
    # ========== LEAN FIRE, FAT FIRE, BARISTA scenarios ==========
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║           📊 OTROS ESCENARIOS: ¿CUÁNDO PODRÍAS RETIRARTE?                 ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝\n")
    
    # Calculate different FIRE scenarios
    annual_spending = config.get('annual_spending', 0)
    annual_contrib = config.get('annual_contribution', 0)
    annual_rent = config.get('annual_rental_income', 0)
    annual_contrib_total = annual_contrib + annual_rent  # Total effective contribution
    swr = config.get('safe_withdrawal_rate', 0.04)
    
    # LEAN FIRE: 75% of spending (same contributions)
    spending_lean = annual_spending * 0.75
    target_lean = target_fire(spending_lean, swr)
    years_lean = calculate_years_for_target(config, target_lean)
    
    # NORMAL FIRE: 100% (already calculated as 'target')
    
    # FAT FIRE: 150% of spending (same contributions)
    spending_fat = annual_spending * 1.5
    target_fat = target_fire(spending_fat, swr)
    years_fat = calculate_years_for_target(config, target_fat)
    
    # BARISTA FIRE: Only 50% of salary contributions + keep all rental income
    barista_config = config.copy()
    barista_config['annual_contribution'] = annual_contrib * 0.5
    # annual_rental_income stays the same
    years_barista = calculate_years_to_fire(barista_config)
    barista_contrib_total = (annual_contrib * 0.5) + annual_rent
    
    # Display scenarios
    progress_target = (config['current_savings'] / target) * 100
    
    scenarios = [
        ("🥗 LEAN FIRE (75% gastos)", spending_lean, target_lean, years_lean, annual_contrib_total, progress_target * 0.75),
        ("💰 NORMAL FIRE (100% gastos)", annual_spending, target, years_to_fire, annual_contrib_total, progress_target),
        ("🍽️  FAT FIRE (150% gastos)", spending_fat, target_fat, years_fat, annual_contrib_total, progress_target * 1.5),
    ]
    
    for label, spending, target_amount, years, contrib_used, progress in scenarios:
        pct = min(100, progress)
        bar_width = 25
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        if years and years != float('inf'):
            print(f"  {label}")
            print(f"    Gasto: €{spending:,.0f} | Objetivo: €{target_amount:,.0f}")
            print(f"    Aportaciones: €{contrib_used:,.0f}/año | Progreso: {pct:.0f}% [{bar}]")
            print(f"    ✅ En {years} años (retiro a los {config.get('age', 30) + years}a)\n")
        else:
            print(f"  {label}")
            print(f"    Gasto: €{spending:,.0f} | Objetivo: €{target_amount:,.0f}")
            print(f"    Aportaciones: €{contrib_used:,.0f}/año | Progreso: {pct:.0f}% [{bar}]")
            print(f"    ⏰ Tiempo indeterminado sin contribuciones suficientes\n")
    
    # BARISTA FIRE explanation - different model
    print(f"  💼 BARISTA FIRE (Semi-retiro con ingresos pasivos)")
    if years_barista and years_barista != float('inf'):
        print(f"    Gasto: €{annual_spending:,.0f} (igual que NORMAL)")
        print(f"    Aportaciones: €{barista_contrib_total:,.0f}/año")
        print(f"      • Salario (50%): €{annual_contrib * 0.5:,.0f}/año (trabajo part-time)")
        print(f"      • Alquileres: €{annual_rent:,.0f}/año (pasivo, sin cambios)")
        print(f"    ✅ Alcanzas FIRE en {years_barista} años\n")
    else:
        print(f"    Gasto: €{annual_spending:,.0f}")
        print(f"    Con menor aportación laboral, se extiende el plazo significativamente.\n")
    
    # Summary table with all 4 scenarios
    print("  📋 TABLA COMPARATIVA DE ESCENARIOS:")
    print("  ┌──────────────────┬─────────┬──────────────┬──────────────┬─────┬─────────┐")
    print("  │ Escenario        │ Gasto   │ Objetivo     │ Aportaciones │ Años │ Retiro  │")
    print("  ├──────────────────┼─────────┼──────────────┼──────────────┼─────┼─────────┤")
    
    for scenario_label, spending, target_amt, scenario_years, scenario_contrib, _ in scenarios:
        display_label = scenario_label.split("(")[0].strip()[:15]
        scenario_age = (config.get('age', 30) + scenario_years) if scenario_years and scenario_years != float('inf') else "∞"
        scenario_years_display = f"{scenario_years}a" if scenario_years and scenario_years != float('inf') else "∞"
        print(f"  │ {display_label:<16} │ €{spending:>5,.0f}  │ €{target_amt:>10,.0f}  │ €{scenario_contrib:>10,.0f}  │ {scenario_years_display:>4} │ {scenario_age:>6}a │")
    
    # Add Barista to table
    scenario_age_barista = (config.get('age', 30) + years_barista) if years_barista and years_barista != float('inf') else "∞"
    scenario_years_barista = f"{years_barista}a" if years_barista and years_barista != float('inf') else "∞"
    print(f"  │ {'BARISTA FIRE':<16} │ €{annual_spending:>5,.0f}  │ €{target:>10,.0f}  │ €{barista_contrib_total:>10,.0f}  │ {scenario_years_barista:>4} │ {scenario_age_barista:>6}a │")
    
    print("  └──────────────────┴─────────┴──────────────┴──────────────┴─────┴─────────┘\n")
    print("  📌 NOTAS:")
    print(f"     • LEAN, NORMAL, FAT: Usan la misma aportación total (€{annual_contrib_total:,.0f}/año)")
    print(f"     • BARISTA: Reducen aportación laboral a €{annual_contrib * 0.5:,.0f} + mantienen alquileres")
    print(f"     • Todos asumen SWR del {swr*100:.1f}% para calcular el objetivo de cartera\n")


def show_json_example():
    """Display JSON example for API usage."""
    print_section("Ejemplo JSON para API/Automatización")
    
    example = {
        "annual_spending": 40_000,
        "safe_withdrawal_rate": 0.04,
        "current_savings": 500_000,
        "annual_contribution": 15_000,
        "expected_return": 0.065,
        "inflation_rate": 0.02,
        "tax_rate_on_gains": 0.15,
        "tax_rate_on_dividends": 0.30,
        "tax_rate_on_interest": 0.45,
        "fund_fees": 0.001,
        "withholding_tax": 0.15,
        "social_security_contributions": 0.0,
        "years_horizon": 25,
    }
    
    print(json.dumps(example, indent=2))
    print("\nGuarda esto en un archivo JSON y úsalo con src/calculator.py")


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    """Main CLI entry point."""
    clear_screen()
    print(WELCOME_MESSAGE)
    
    while True:
        choice = get_profile_choice()
        
        if choice == "exit":
            print("\n" + "=" * 80)
            print("  ¡Gracias por usar la Calculadora FIRE! 🚀")
            print("  Recuerda: la consistencia y la paciencia son tus mayores aliados.")
            print("=" * 80 + "\n")
            break
        elif choice == "show_json":
            show_json_example()
            input("\nPresiona ENTER para continuar...")
            clear_screen()
            print(WELCOME_MESSAGE)
            continue
        elif choice == "custom":
            config = input_custom_profile()
        else:
            # Use profile defaults with clear presentation
            profile_config = PROFILES[choice]["defaults"].copy()
            
            print_section(f"Perfil: {PROFILES[choice]['name']}")
            print(PROFILES[choice]['description'])
            
            # Show defaults prominently
            show_defaults(choice)
            
            customize = input("\n¿Deseas personalizar alguno de estos valores? (s/n) [defecto: n]: ").strip().lower()
            
            if customize == "s":
                # Allow customization with detailed explanations
                print("\n📝  PERSONALIZACIÓN DETALLADA\n")
                print("Presiona ENTER para mantener valor por defecto. Ahora verás explicaciones para cada parámetro.\n")
                
                config = profile_config.copy()
                
                # 1. Annual Spending
                print("─" * 80)
                show_spending_context()
                config['annual_spending'] = ask_with_default(
                    "Gasto anual deseado (€)",
                    profile_config['annual_spending'],
                    unit="€"
                )
                
                # 2. Safe Withdrawal Rate
                print("\n─" * 80)
                show_swr_context()
                config['safe_withdrawal_rate'] = ask_with_default(
                    "Tasa de Retirada Segura (TRS) [%]",
                    profile_config['safe_withdrawal_rate'],
                    is_percentage=True
                )
                
                # 3. Expected Return
                print("\n─" * 80)
                show_return_context()
                config['expected_return'] = ask_with_default(
                    "Retorno esperado anual [%]",
                    profile_config['expected_return'],
                    is_percentage=True
                )
                
                # 4. Inflation Rate
                print("\n─" * 80)
                show_inflation_context()
                config['inflation_rate'] = ask_with_default(
                    "Inflación esperada [%]",
                    profile_config['inflation_rate'],
                    is_percentage=True
                )
                
                # 5. Tax Rates
                print("\n─" * 80)
                show_taxes_context()
                config['tax_rate_on_gains'] = ask_with_default(
                    "Tasa de plusvalías [%]",
                    profile_config['tax_rate_on_gains'],
                    is_percentage=True
                )
                config['tax_rate_on_dividends'] = ask_with_default(
                    "Tasa de dividendos [%]",
                    profile_config['tax_rate_on_dividends'],
                    is_percentage=True
                )
                config['tax_rate_on_interest'] = ask_with_default(
                    "Tasa de intereses [%]",
                    profile_config['tax_rate_on_interest'],
                    is_percentage=True
                )
                
                # 6. Fund Fees
                print("\n─" * 80)
                show_fees_context()
                config['fund_fees'] = ask_with_default(
                    "Comisión de fondos UCITS [%]",
                    profile_config['fund_fees'],
                    is_percentage=True,
                    max_pct=1  # Commissions capped at 1%
                )
            else:
                # Use all defaults as-is
                config = profile_config.copy()
            
            # Always ask for projection horizon and current savings
            print("\n📊 Información adicional:\n")
            
            print("""
💰 AHORROS ACTUALES: ¿Cuánto dinero ya tienes invertido?
   • Incluye: fondos UCITS, acciones, bonos, depósitos de inversión.
   • NO incluye: efectivo en cuenta corriente, casa principal.
   • Usa €0 si aún no has started (inicio desde cero).""")
            
            config['current_savings'] = ask_with_default(
                "Ahorros actuales (€)",
                100_000,
                unit="€"
            )
            
            print("""
💰 APORTE ANUAL: ¿Cuánto ahorras cada año para FIRE?
   • Bruto = ingresos anuales - gastos necesarios.
   • Realista: típico 12,000-30,000 € para clase media europea.
   • Depende de tu salario e industria. Sé honesto/a.""")
            
            config['annual_contribution'] = ask_with_default(
                "Aporte anual (€)",
                12_000,
                unit="€"
            )
            
            print("""
📅 HORIZONTE TEMPORAL: ¿Cuántos años quieres ver en proyecciones?
   • 20-25 años = Standard (ves crecimiento + impacto de impuestos)
   • 40+ años = Si esperas trabajar muchos años más.""")
            
            config['years_horizon'] = get_int_input(
                "Años a proyectar",
                default=25,
                min_val=1,
                max_val=70,
            )
        
        # Add age if not already present
        if 'age' not in config:
            config['age'] = get_int_input(
                "Tu edad actual",
                default=30,
                min_val=18,
                max_val=120,
            )
        
        # Add desired retirement age
        if 'desired_retirement_age' not in config:
            config['desired_retirement_age'] = get_int_input(
                "Edad de retiro deseada",
                default=65,
                min_val=18,
                max_val=100,
            )
        
        # Collect real estate and liability information
        config = collect_real_estate_and_liabilities(config)
        
        # Set other defaults
        if 'include_scenarios' not in config:
            config['include_scenarios'] = True
        if 'withholding_tax' not in config:
            config['withholding_tax'] = 0.15
        if 'social_security_contributions' not in config:
            config['social_security_contributions'] = 0.0
        if 'portfolio_info' not in config:
            config['portfolio_info'] = {"method": "generic"}
        
        # Show summary and get confirmation
        if show_summary(config):
            show_results(config)
            
            again = input("\n¿Analizar otro escenario? (s/n): ").strip().lower()
            if again != "s":
                print("\n" + "=" * 80)
                print("  ¡Gracias por usar la Calculadora FIRE! 🚀")
                print("  Recuerda: la consistencia y la paciencia son tus mayores aliados.")
                print("=" * 80 + "\n")
                break
        else:
            # User rejected parameters - offer options for iter ative editing
            print("\n" + "="*80)
            print("OPCIONES:")
            print("  1. Editar parámetros individuales (vuelve al menú de edición)")
            print("  2. Volver al menú principal")
            print("  3. Salir")
            print("="*80)
            
            while True:
                choice = input("\nElige opción (1-3): ").strip()
                if choice in ["1", "2", "3"]:
                    break
                print("❌ Opción inválida (1-3).")
            
            if choice == "1":
                # Let user edit individual parameters with loop
                while True:
                    edited_config = interactive_edit_config(config)
                    if edited_config is None:
                        # User exited edit menu
                        break
                    
                    config = edited_config
                    # Show updated summary and loop
                    if show_summary(config):
                        # User accepted after edits
                        show_results(config)
                        again = input("\n¿Analizar otro escenario? (s/n): ").strip().lower()
                        if again != "s":
                            print("\n" + "=" * 80)
                            print("  ¡Gracias por usar la Calculadora FIRE! 🚀")
                            print("  Recuerda: la consistencia y la paciencia son tus mayores aliados.")
                            print("=" * 80 + "\n")
                            return
                        break  # Back to main profile menu
                    # else: User rejected again, loop continues in edit menu
            elif choice == "2":
                # Back to main menu
                clear_screen()
                print(WELCOME_MESSAGE)
                continue
            else:  # choice == "3"
                # Exit
                print("\n" + "=" * 80)
                print("  ¡Gracias por usar la Calculadora FIRE! 🚀")
                print("  Recuerda: la consistencia y la paciencia son tus mayores aliados.")
                print("=" * 80 + "\n")
                break


if __name__ == "__main__":
    main()

"""Enhanced input functions with contextual descriptions for FIRE parameters."""

from typing import Dict, Any, Optional

# ============================================================================
# PARAMETER DESCRIPTIONS AND CONTEXTS
# ============================================================================

PARAMETER_CONTEXTS = {
    'annual_spending': {
        'label': 'Gasto anual deseado en jubilación (€)',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ GASTO ANUAL DESEADO EN JUBILACIÓN                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Cuánto necesitas gastar cada año una vez jubilado?                     │
│                                                                          │
│ Ejemplos reales (familias europeas):                                    │
│  • €25,000: Lifestyle modesto, sin lujos (Lean FIRE)                    │
│  • €40,000: Cómodo, sin restricciones importantes                       │
│  • €60,000: Viajes, hobbies, vida normal (Fat FIRE)                     │
│  • €100,000+: Lujos, segundas residencias                               │
│                                                                          │
│ 💡 Tip: Incluye gastos fijos (vivienda, comida, salud, seguros)        │
│         + gastos variables (viajes, ocio, imprevistos)                 │
│                                                                          │
│ ⚠️  NO incluyas: depreciación de bienes (auto, etc.)                   │
│                 ahorros adicionales (ya estarás jubilado)              │
│                 impuestos sobre rendimientos (se restan automáticamente)│
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '€'
    },
    
    'safe_withdrawal_rate': {
        'label': 'Tasa de Retirada Segura (SWR) - TRS [%]',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ TASA DE RETIRADA SEGURA (SWR) - TASA DE RETIRO SEGURO                  │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Qué % de tu portfolio puedes retirar cada año sin arruinarte?         │
│ (Calculado con una probabilidad de éxito del ~95% en 30 años)          │
│                                                                          │
│ Estándares internacionales:                                             │
│  • 3.0%: MÁS SEGURO (casi nunca se agota el dinero)                    │
│  • 3.5%: Recomendado por Trinity Study (1998)                          │
│  • 4.0%: Clásico (funciona en 95% de los escenarios históricos)       │
│  • 4.5%+: MÁS ARRIESGADO (requiere disciplina o ingresos adicionales)  │
│                                                                          │
│ Fórmula: Portfolio necesario = Gasto anual / SWR                        │
│ Ejemplo: Si gastas €40,000 al 4% → necesitas €1,000,000               │
│                                                                          │
│ 💡 Tip: Usa 4% si eres conservador/a                                   │
│         Usa 3.5% si tienes baja tolerancia al riesgo                   │
│         Usa 4.5%+ si tienes ingresos flexibles (freelance, etc.)      │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '%'
    },
    
    'expected_return': {
        'label': 'Retorno anual esperado de tu cartera [%]',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ RETORNO ESPERADO DE TU CARTERA (% ANUAL)                               │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Cuál es tu objetivo de rentabilidad anual antes de impuestos?         │
│ (Esto depende de tu asignación de activos: acciones vs. bonos)         │
│                                                                          │
│ Retornos históricos reales (rentabilidad real, ajustada inflación):    │
│  • 2-3%: Bonos soberanos, depósitos bancarios (muy seguro)             │
│  • 5-6%: Cartera balance 50/50 acciones-bonos (recomendado)            │
│  • 7-8%: Cartera agresiva 80/20 acciones-bonos (histórico EUR)         │
│  • 9-10%: 100% acciones EU (esperanza, pero muy volátil)               │
│                                                                          │
│ 💡 Tip IMPORTANTE:                                                      │
│    • Para FIRE conservador: usa 5-6% (realista, basado en datos)      │
│    • Para bajo riesgo: usa 4-5% (más seguro)                          │
│    • Recuerda: incluir comisiones de fondos (~0.2% más)                │
│                                                                          │
│ Cartera ejemplo UCITS passive:                                         │
│  • 70% Acciones world (MSCI World): ~7% rendimiento                    │
│  • 30% Bonos soberanos: ~2% rendimiento                                │
│  • Ponderada: 0.7×7% + 0.3×2% = ~5.5% esperado                        │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '%'
    },
    
    'inflation_rate': {
        'label': 'Inflación esperada anual [%]',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ INFLACIÓN ESPERADA ANUAL (% ANUAL)                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿A qué ritmo esperas que suban los precios cada año?                   │
│ (Afecta el poder adquisitivo de tu dinero a largo plazo)               │
│                                                                          │
│ Contexto histórico:                                                     │
│  • 1-1.5%: Deflación o inflación muy baja (escenario raro)             │
│  • 2-2.5%: Target de Banco Central Europa (normal)                     │
│  • 3-4%: Inflación moderada (lo actual post-COVID, 2024)               │
│  • 5%+: Inflación alta (preocupa a centrales)                          │
│                                                                          │
│ 💡 Tip:                                                                 │
│    • Para 2024-2026: usa 2.0-2.5% (convergencia ECB)                  │
│    • Para planificación larga (30+ años): usa 2.0% (conservador)      │
│    • Si esperas inflación >3%: recalcula tu gasto deseado              │
│                                                                          │
│ Ejemplo: €40,000 hoy con 2% inflación anual:                          │
│    • Año 10: €48,740 (para mismo lifestyle)                            │
│    • Año 20: €59,548 (compra menos que antes)                          │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '%'
    },
    
    'tax_rate_on_gains': {
        'label': 'Tasa fiscal: Plusvalías de capital [%]',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ IMPUESTO SOBRE PLUSVALÍAS (Capital Gains Tax)                          │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Qué % pagas en impuestos cuando vendes inversiones con ganancia?      │
│ (p.ej. vender una acción que compré a €100 y vendo a €150)            │
│                                                                          │
│ Marcos tributarios típicos EU:                                          │
│  • 15%: España (holdings 1+ año), algunos países                        │
│  • 19-25%: Alemania, Francia (según tiempo de tenencia)                 │
│  • 21-27%: Italia (3 meses de espera para 50% exención)                │
│  • 0%: Algunos fondos UCITS con deferral en España (hasta 5 años)      │
│                                                                          │
│ 💡 Estrategia FIRE-friendly en EU:                                     │
│    • Usa fondos UCITS (acumulativos, no reparten): evita impuestos anuales│
│    • Mantén >1 año para impuestos reducidos (si aplica)                │
│    • Recolecta pérdidas para compensar ganancias (loss harvesting)     │
│                                                                          │
│ ⚠️  Consulta con asesor fiscal de tu país para tu situación           │
│    Este cálculo es aproximado.                                          │
│                                                                          │
│ Valores comúnes para FIRE:                                             │
│    • 15-20%: Escenario optimista (UCITS, tenencia larga)              │
│    • 25%: Escenario realista (plusvalías normales)                    │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '%'
    },
    
    'tax_rate_on_dividends': {
        'label': 'Tasa fiscal: Ingresos por dividendos [%]',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ IMPUESTO SOBRE DIVIDENDOS (Dividend Tax)                               │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Qué % pagas en impuestos por dividendos recibidos de acciones?        │
│ (Dinero en efectivo que recibes anualmente por poseer acciones)        │
│                                                                          │
│ Marcos tributarios típicos EU:                                          │
│  • 19%: España (dividendos, retención en origen)                        │
│  • 26-42%: Alemania (según progresividad + solidaridad)                 │
│  • 23-43%: Francia (progresivo, muy variable)                          │
│  • 25%: Italia (retenido en origen, bastante fijo)                     │
│                                                                          │
│ Estrategia FIRE en EU:                                                  │
│    • Prefiere fondos UCITS ACUMULATIVOS (no reparten, impuesto diferido)│
│    • Si usas fondos de reparto: aceptan impuestos anuales              │
│    • En jubilación: podrías estar exento si ingresos son bajos         │
│                                                                          │
│ Valores típicos para FIRE:                                             │
│    • 19-25%: Fondos acumulativos (impuestos solo al vender)            │
│    • 30-35%: Fondos de reparto (impuestos anuales)                     │
│    • 0%: En jubilación si vives de capital (escenario ideal)           │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '%'
    },
    
    'tax_rate_on_interest': {
        'label': 'Tasa fiscal: Ingresos por intereses [%]',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ IMPUESTO SOBRE INTERESES (Interest Tax)                                │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Qué % pagas en impuestos por intereses de depósitos/bonos?            │
│ (Dinero que ganas por dejar dinero en el banco o bonos)                │
│                                                                          │
│ Marcos tributarios típicos EU:                                          │
│  • 19%: España (retención en origen, bastante estándar)                 │
│  • 26-42%: Alemania (progresivo, muy variable)                          │
│  • 24-45%: Francia (depende de tipo de cuenta)                          │
│  • 20-27%: Italia (generalmente ~20% estándar)                         │
│                                                                          │
│ Contexto FIRE:                                                          │
│    • Menor importancia: En FIRE usas acciones/fondos, no depósitos     │
│    • Relevante SO si: mantienes cash buffer (3-6 meses gastos)        │
│    • ETF de bonos: impuestos similares a dividendos                   │
│                                                                          │
│ Valores típicos para FIRE:                                             │
│    • 19-20%: Baseline (retención estándar)                             │
│    • 30%: Si tienes muchos ahorros en depósitos (poco FIRE)           │
│    • Usado SO si 5-10% portfolio es capital seguro (bonos/depós)      │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '%'
    },
    
    'fund_fees': {
        'label': 'Comisiones de fondos UCITS [%]',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ COMISIONES ANUALES DE FONDOS UCITS (TER - Total Expense Ratio)        │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Cuánto te cobran anualmente como % de tu inversión?                   │
│ (Estos % van a gestión, custodia, administración - cada año!)          │
│                                                                          │
│ Comisiones reales en mercado (2024):                                   │
│  • 0.05-0.15%: iShares, Vanguard ETFs (excelente)                      │
│  • 0.20-0.35%: Fondos indexados medianos (bueno)                       │
│  • 0.50-1.00%: Gestores activos (caro, raramente justificado)         │
│  • 1.50%+: Fondos viejos o poco competitivos (evita)                   │
│                                                                          │
│ Impacto en FIRE (ejemplo 400k cartera):                                │
│  • 0.10% = €400/año | En 30 años: €34,000 menos de riqueza            │
│  • 0.30% = €1,200/año | En 30 años: €102,000 menos de riqueza         │
│  • 1.00% = €4,000/año | En 30 años: €340,000 MENOS de riqueza         │
│                                                                          │
│ 💡 Recomendación FIRE:                                                  │
│    ☆ Usa 0.10-0.20%: ETFs indexados pasivos (Vanguard, iShares)      │
│    • NO uses 0.50%+: Es un lujo que no puedes permitirte en FIRE      │
│                                                                          │
│ Entrada típica: 0.22% es moderado (un poco caro, educa el 0.10-0.15%) │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '%'
    },
}

REAL_ESTATE_CONTEXTS = {
    'primary_residence_value': {
        'label': 'Valor actual de tu vivienda principal (€)',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ VIVIENDA PRINCIPAL - VALOR ACTUAL                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Cuánto vale hoy tu casa/piso donde vives?                             │
│ (Estima realista según mercado local, no precio de compra)             │
│                                                                          │
│ Importancia en FIRE:                                                    │
│  ✓ INCLUIR: Si planeas venderla al jubilarte                           │
│  ✓ INCLUIR: Si calcularás hipoteca en tu gasto de retire              │
│  ✗ EXCLUIR: Si la mantendrás pagada para siempre                      │
│                                                                          │
│ 💡 Cómo estimar:                                                        │
│    • Busca similares en Idealista/Fotocasa (tu zona)                  │
│    • Ajusta por estado, ubicación exacta, año construcción             │
│    • Consulta catastro si tienes dudas                                 │
│                                                                          │
│ Dejar en €0 si:                                                         │
│    • Usarás vivienda de forma indefinida (no FIRE con venta)          │
│    • No es relevante para tus planes de jubilación                    │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '€'
    },
    
    'primary_residence_mortgage': {
        'label': 'Hipoteca pendiente en vivienda principal (€)',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ HIPOTECA PENDIENTE - VIVIENDA PRINCIPAL                                │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Cuánto debo aún del préstamo hipotecario?                             │
│ (Coloca €0 si ya la pagaste o es tuya sin deuda)                      │
│                                                                          │
│ Cálculo en FIRE:                                                        │
│  • Equity = Valor vivienda - Hipoteca pendiente                        │
│  • Ej: €400k casa - €200k hipoteca = €200k equity (patrimonio neto)   │
│                                                                          │
│ Estrategia en FIRE:                                                     │
│  ✓ Paga hipoteca ANTES de retirarte (sin deuda = sin estrés)          │
│  ✓ O liquida la casa y libera capital para inversiones                │
│  ✗ Evita vivir con hipoteca si tasa de retiro es <tasa hipoteca      │
│                                                                          │
│ Plazo típico:                                                          │
│    • 20-30 años: hipoteca estándar                                     │
│    • Calcula: años hasta vencimiento < años hasta FIRE?               │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '€'
    },
    
    'other_real_estate_value': {
        'label': 'Valor de otros inmuebles (segundas casas, inversión, etc.) (€)',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ OTROS INMUEBLES (Inversión, segunda residencia)                        │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Tienes otra propiedad? ¿Terreno? ¿Apartamento vacacional?             │
│ Coloca valor de mercado actual (no precio de compra)                   │
│                                                                          │
│ Incluir si:                                                             │
│  • Genera renta (alquiler)                                              │
│  • Planeas venderla durante FIRE                                        │
│  • Es parte de tu estrategia de jubilación                              │
│                                                                          │
│ Excluir si:                                                             │
│  • Solo es hobby/nostalgia                                              │
│  • Cuesta más mantener que lo que aporta                               │
│  • No está liquidable cuando la necesites                               │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '€'
    },
    
    'other_real_estate_mortgage': {
        'label': 'Hipoteca/deuda en otros inmuebles (€)',
        'description': """
┌─────────────────────────────────────────────────────────────────────────┐
│ DEUDA EN OTROS INMUEBLES                                               │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Tienes hipoteca u otro préstamo en eses otras propiedades?            │
│ Coloca el capital pendiente (no las cuotas mensuales)                  │
│                                                                          │
│ Impacto en FIRE:                                                        │
│  • Reduce tu equity bruto en esos inmuebles                            │
│  • Evalúa: ¿Te genera ingresos la propiedad?                          │
│  • Si deuda > capacidad de pago: problema en FIRE                      │
│                                                                          │
│ Acción recomendada:                                                     │
│  ✓ Pagar todo antes de jubilarse (opcional pero recomendado)          │
│  ✓ O vender propiedad + quitar deuda (liberarse)                      │
└─────────────────────────────────────────────────────────────────────────┘
""",
        'unit': '€'
    },
}

OTHER_LIABILITIES_CONTEXT = """
┌─────────────────────────────────────────────────────────────────────────┐
│ OTRAS DEUDAS (Personales, préstamos, tarjetas de crédito)              │
├─────────────────────────────────────────────────────────────────────────┤
│ ¿Debes dinero sin estar asociado a inmuebles?                          │
│ (Créditos personales, préstamos al consumo, deuda tarjeta, etc.)      │
│                                                                          │
│ Coloca la deuda TOTAL pendiente (suma todo)                            │
│                                                                          │
│ IMPORTANTE para FIRE:                                                   │
│  ⚠️  PAGA TODO ANTES DE RETIRARTE                                      │
│      Sin ingresos activos, las deudas con interés son un problema     │
│      Especialmente si tasa interés > retorno esperado del portfolio   │
│                                                                          │
│ Estrategia:                                                             │
│  1. Calcula: años hasta estar sin deudas                               │
│  2. Calcula: años hasta FIRE                                           │
│  3. Si (1) < (2): buen camino                                          │
│  4. Si (1) > (2): plan B necesario (ingresos adicionales, etc.)       │
│                                                                          │
│ No incluyas: hipotecas (ya están en sección inmobiliaria)             │
└─────────────────────────────────────────────────────────────────────────┘
"""

# ============================================================================
# ENHANCED INPUT FUNCTIONS
# ============================================================================

def show_parameter_context(param_key: str, section: str = 'basic') -> None:
    """Display detailed explanation before asking for parameter."""
    if section == 'basic' and param_key in PARAMETER_CONTEXTS:
        context = PARAMETER_CONTEXTS[param_key]
        print(context['description'])
    elif section == 'real_estate' and param_key in REAL_ESTATE_CONTEXTS:
        context = REAL_ESTATE_CONTEXTS[param_key]
        print(context['description'])
    elif section == 'other_liabilities':
        print(OTHER_LIABILITIES_CONTEXT)

def ask_with_context(
    param_key: str,
    default_value: float,
    section: str = 'basic',
    is_percentage: bool = False,
    max_pct: float = 100,
    unit: str = ""
) -> float:
    """Ask for parameter with full context explanation."""
    # Show context
    show_parameter_context(param_key, section)
    
    # Get label
    if section == 'basic':
        label = PARAMETER_CONTEXTS.get(param_key, {}).get('label', param_key)
        unit = PARAMETER_CONTEXTS.get(param_key, {}).get('unit', unit)
    elif section == 'real_estate':
        label = REAL_ESTATE_CONTEXTS.get(param_key, {}).get('label', param_key)
        unit = REAL_ESTATE_CONTEXTS.get(param_key, {}).get('unit', unit)
    else:
        label = param_key
    
    # Ask for input
    return ask_with_default(
        label,
        default_value,
        unit=unit,
        is_percentage=is_percentage,
        max_pct=max_pct if is_percentage else 100
    )

def collect_real_estate_and_liabilities(config: Dict[str, Any]) -> Dict[str, Any]:
    """Collect real estate and liability information from user."""
    print("\n" + "=" * 80)
    print("🏠 INFORMACIÓN INMOBILIARIA Y DEUDAS")
    print("=" * 80)
    print("""
Esta sección recopila información sobre propiedades e hipotecas.
Incluir datos precisos aquí es CRUCIAL para un análisis FIRE realista.
""")
    
    # Primary Residence
    print("\n" + "─" * 80)
    print("1️⃣  VIVIENDA PRINCIPAL (donde vives actualmente)")
    print("─" * 80)
    
    config['primary_residence_value'] = ask_with_context(
        'primary_residence_value',
        config.get('primary_residence_value', 0),
        section='real_estate',
        unit='€'
    )
    
    if config['primary_residence_value'] > 0:
        config['primary_residence_mortgage'] = ask_with_context(
            'primary_residence_mortgage',
            config.get('primary_residence_mortgage', 0),
            section='real_estate',
            unit='€'
        )
    else:
        config['primary_residence_mortgage'] = 0
    
    # Other Real Estate
    print("\n" + "─" * 80)
    print("2️⃣  OTROS INMUEBLES (segundas casas, inversión, etc.)")
    print("─" * 80)
    
    config['other_real_estate_value'] = ask_with_context(
        'other_real_estate_value',
        config.get('other_real_estate_value', 0),
        section='real_estate',
        unit='€'
    )
    
    if config['other_real_estate_value'] > 0:
        config['other_real_estate_mortgage'] = ask_with_context(
            'other_real_estate_mortgage',
            config.get('other_real_estate_mortgage', 0),
            section='real_estate',
            unit='€'
        )
    else:
        config['other_real_estate_mortgage'] = 0
    
    # Other Liabilities
    print("\n" + "─" * 80)
    print("3️⃣  OTRAS DEUDAS (préstamos personales, tarjetas, etc.)")
    print("─" * 80)
    
    show_parameter_context('other_liabilities', section='other_liabilities')
    
    config['other_liabilities'] = ask_with_default(
        "Total de otras deudas (€)",
        config.get('other_liabilities', 0),
        unit="€"
    )
    
    return config

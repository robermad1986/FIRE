# 🎯 FIRE Calculator EUR/UCITS — Professional-Grade Retirement Planning

> **Calculadora de Independencia Financiera (FIRE) optimizada para inversores europeos**
> 
> Calcula cuándo podrás retirarte con fondos UCITS, fiscalidad EUR, y análisis profesional.

**☕ Si esta herramienta te ayuda a planificar tu libertad financiera, considera [invitarme a un café](https://buymeacoffee.com/pishu) para apoyar el desarrollo.**

The source code is available on GitHub: [robermad1986/FIRE](https://github.com/robermad1986/FIRE).

🚀 **Live Demo**: [Fire Calculator (Streamlit)](https://fire-es.streamlit.app/)

---

## 📌 Tabla de Contenidos

- [Features](#-features-principales)
- [Quick Start](#-início-rápido)
- [FIRE Profiles](#-perfiles-fire-soportados)
- [How It Works](#-cómo-funciona)
- [Parameters](#-parámetros-configurables)
- [Examples](#-ejemplos)
- [Testing](#-testing)
- [Limitaciones Actuales](#-limitaciones-actuales-importantes)
- [Pendiente por Resolver](#-pendiente-por-resolver)
- [Backlog Reddit](#-backlog-reddit-priorizado)
- [Disclaimers](#-disclaimers)

---

## 🚀 Features Principales

### 6 Variantes de FIRE Preconfiguradas

| Perfil | Gasto Anual | Descripción |
|--------|-------------|------------|
| **Lean FIRE** | €20k-€30k | Vida modesta pero independiente |
| **Fat FIRE** | €60k-€100k | Jubilación confortable y sin restricciones |
| **Coast FIRE** | €40k | Acumula ahora, deja crecer sin aportes después |
| **Barista FIRE** | €50k | €15k código part-time + €35k portfolio |
| **UCITS Tax Efficient** | €45k | Optimizado para fondos UCITS acumulativos |
| **Spain FIT** | €40k | 🇪🇸 Fondos Indexados Traspasables españoles (0% retenida anual) |

### ✨ Funcionalidades Avanzadas

- **💰 Tax-Aware Targeting** — Calcula objetivo BRUTO considerando impuestos sobre plusvalías
- **📊 Proyecciones de 10+ años** — Visualiza crecimiento de tu portafolio
- **🎲 Monte Carlo Analysis** — 10,000 simulaciones → probabilidad de éxito realista
- **🧪 Comparación de Modelos** — Normal vs Bootstrap vs Backtesting con selector de estrategia histórica
- **🏠 Balance Completo** — Bienes raíces, hipotecas, deudas personales
- **📈 KPIs Profesionales** — FIRE Number, Net Worth, Burning Rate, Savings Rate
- **💵 Fiscalidad EUR/UCITS** — Impuestos sobre plusvalías, dividendos, intereses
- **🎯 Enfoque Fiscal Flexible** — Prioriza acumulación o jubilación en la estimación del objetivo FIRE
- **🧓 Retiro en 2 fases (simple por defecto)** — Define retirada neta pre-pensión y post-pensión sin obligar desglose de plan privado
- **🎓 Explicaciones Contextuales** — Cada parámetro con ejemplos y consejos
- **🌍 Soporte Multi-País** — Ajusta impuestos para tu país específico

Nota de consistencia reciente (web): la explicación del objetivo FIRE en el panel guiado se calcula en tiempo real con la fórmula
`Objetivo de cartera = Gastos anuales / SWR`, y el objetivo mostrado se unifica entre KPIs, gráfico principal y exportes.

Actualización reciente (web): ahora puedes incorporar **renta bruta anual por alquileres** y un **ajuste anual de gasto por vivienda habitual**
para estimar el gasto neto que debe cubrir la cartera en jubilación. Además, el bloque de decumulación muestra escenarios `P5/P25/P50/P75/P95`.
Actualización reciente (web): se añade bloque de **acumulación pre-FIRE**, persistencia de perfil por **JSON**, export **CSV+JSON** y modo fiscal
**Internacional básico** para acumulación fuera de España (aproximación).
También incluye toggle para ocultar/mostrar panel de control, mejoras de lectura en dark mode móvil y flujo de impresión PDF nativo del navegador.

### 🧪 Validación Exhaustiva

- ✅ **Test Suite Completa** — 30+ unit tests
- ✅ **Edge Cases** — Validación exhaustiva de inputs
- ✅ **Stress Testing** — Inputs aleatorios y casos extremos
- ✅ **100% Coverage** — Todas las funciones críticas probadas

---

## 🚧 Limitaciones Actuales Importantes

1. **No sustituye asesoría fiscal/legal**  
   Es un simulador educativo. No genera liquidaciones oficiales ni recomendaciones personalizadas vinculantes.

2. **Cobertura fiscal española dependiente de Tax Pack**  
   La web usa reglas versionadas por año (`Tax Pack`). Si la norma cambia, hay que actualizar el pack para mantener precisión.
   Validación técnica recomendada antes de cambios fiscales: `python3 scripts/validate_taxpack.py --year 2026 --country es`.

3. **Cobertura temporal actual del pack: 2026**  
   En el estado actual del repo, el pack integrado es `ES-2026`.

4. **SWR configurable en CLI y web**  
   El objetivo FIRE usa TRS/SWR configurable en ambas interfaces.

5. **Modelo de mercado en transición (más robusto, aún simplificado)**  
   La web soporta Monte Carlo normal, bootstrap histórico y backtesting por ventanas.  
   La serie histórica base es S&P 500 total return (EE. UU., 1871+) para el tramo de renta variable, con carteras sintéticas por composición:
   100/0, 70/30, 50/50, 30/70 y 15/85 (RV/RF).

6. **Impuestos modelados como aproximación anual**  
IRPF ahorro + Patrimonio + ISGF se aplican como drag anual sobre la simulación. No cubre toda la casuística personal (mínimos familiares, deducciones específicas, etc.).
En modo internacional básico se usan tasas efectivas manuales y no reglas fiscales detalladas país por país.

7. **Paridad funcional CLI/Web en progreso**  
   Se ha avanzado en paridad (SWR, modelos), pero hay diferencias de UX y profundidad en algunos flujos.

## 📍 Pendiente por Resolver

1. Validación legal profunda por CCAA con revisión externa (más allá del Tax Pack técnico).
2. Automatización completa de actualización anual de Tax Pack contra fuentes oficiales.
3. Backtesting de cartera personalizable multi-activo (no solo serie histórica de mercado general).
4. Export detallado de resultados de backtesting por ventana histórica.
5. Tests de paridad end-to-end CLI vs Web para escenarios canónicos.
6. Refactor de `app.py` y `src/cli.py` para reducir complejidad ciclomática.
7. Mejoras de UX no bloqueantes (inputs de alta precisión, ayudas contextuales más finas).
8. Observabilidad/logging estructurado para soporte y diagnóstico en producción.

## 🧭 Backlog Reddit Priorizado

El plan de ejecución basado en propuestas del post de Reddit está en:

- `BACKLOG_REDDIT.md`

Incluye tickets `P0/P1/P2`, criterios de aceptación y orden recomendado para implementación.

---

## ⚡ Inicio Rápido

### Requisitos

- Python 3.9+
- CLI (`src/cli.py`): sin dependencias externas (stdlib puro)
- Web (`app.py`): requiere dependencias de `requirements.txt` (Streamlit, Plotly, Pandas, NumPy)

### Instalación

```bash
git clone https://github.com/robermad1986/FIRE.git
cd FIRE
python3 src/cli.py
```

### Primer Uso

```
Elige tu Perfil FIRE
================================================================================

  1) Lean FIRE            — Gasto €20k-€30k/año: vida modesta pero independiente
  2) Fat FIRE             — Gasto €60k-€100k/año: retiro confortable y sin restricciones
  3) Coast FIRE           — Gasto €40k/año: acumula ahora, deja crecer sin aportes después
  4) Barista FIRE         — Gasto €50k/año: €15k trabajo part-time + €35k portfolio (4% SWR)
  5) UCITS Tax Efficient  — Gasto €45k/año: optimizado para UCITS y cuentas múltiples
  6) Spain FIT            — Gasto €40k/año: Fondos Indexados Traspasables españoles
  7) Entrada personalizada (Custom)
  8) Ver ejemplo JSON (para usar con API)
  0) Salir

Elige (0-8): 4
```

Luego personaliza los parámetros que desees (o acepta los defaults) y obtén tu análisis completo.

---

## 🎓 Perfiles FIRE Soportados

### 🥗 Lean FIRE (€20k-€30k anuales)

**Ideal para:** Personas minimalistas, sin dependientes, que priorizan libertad sobre confort.

```
Gasto anual esperado: €25,000
• Vivienda modesta (alquiler/hipoteca):  €800/mes
• Comida/Utilidades:                      €400/mes
• Transporte:                             €150/mes
• Ocio/Entretenimiento:                   €200/mes
• Reserva de emergencia:                  €450/mes
```

**Target (4% SWR):** €625,000

---

### 🍽️ Fat FIRE (€60k-€100k anuales)

**Ideal para:** Personas con familia, que quieren confort y flexibilidad de gastos.

```
Gasto anual esperado: €75,000
• Vivienda cómoda con margen:   €1,500/mes
• Comida/Restaurantes:          €600/mes
• Auto/Viajes:                  €800/mes
• Educación/Salud/Seguros:      €500/mes
• Lujos/Vacaciones:             €800/mes
• Otros:                        €500/mes
```

**Target (4% SWR):** €1,875,000

---

### 🌴 Coast FIRE (€40k anuales)

**Ideal para:** Personas que quieren trabajar menos (o nada) pero sin dejar de ahorrar estratégicamente.

**Estrategia:** Acumulas capital durante 10-15 años, luego dejas de contribuir y dejas que crezca por su cuenta.

```
Escenario típico:
• Años 1-10:  €20k/año contribución
• Años 11+:   €0 contribución (vives de trabajo part-time)
• Edad 60:    Portfolio ha crecido sin nuevas aportaciones
```

---

### 💼 Barista FIRE (€50k anuales)

**Ideal para:** Personas que quieren independencia pero están dispuestas a trabajar media jornada.

```
Ingresos esperados:
• Trabajo part-time:     €15,000/año (20-25 horas/semana)
• Portfolio (4% SWR):    €35,000/año (de €875,000 en cartera)
• Total disponible:      €50,000/año
```

**Ventajas:**
- Portfolio target MENOR (€875k vs €1,250k si fuera 100% pasivo)
- Seguridad psicológica (ingresos parte-time)
- Flexibilidad de horas

---

### 💎 UCITS Tax Efficient (€45k anuales)

**Ideal para:** Inversores europeos que quieren **máxima eficiencia fiscal con fondos UCITS acumulativos**.

**Diferencia clave:**

| Estrategia | Impuesto Dividendos | Tax Impact | Portfolio Target |
|-----------|-------------------|-----------|-----------------|
| Fondos distribuidores | 30% cada año | 5-8% más caro | €1,125,000 |
| **UCITS Acumulativos** | **0% (hasta vender)** | **Deferido 30+ años** | **€1,062,500** |

**Ganancia en 30 años:**
```
€100 en UCITS acumulativo  @ 7%  =  €761
vs.
€100 en fondo distribuidor @ 7%  =  €650   (€111 menos!)
```

---

### 🇪🇸 Spain FIT — Fondos Indexados Traspasables (€40k anuales)

**Ideal para:** Inversores en España que quieren **máxima eficiencia fiscal con liquidez local y comisiones ultra-bajas**.

**¿Por qué FITs?**

Los Fondos Indexados Traspasables son **extremadamente populares en comunidades FIRE españolas** (r/SpainFIRE, Forocoches) porque ofrecen:

| Ventaja | FIT | UCITS Acc | Fondo Distribuidor |
|---------|-----|-----------|-------------------|
| **Impuesto Anual** | 0% (acumulativos) | 0% | 30% (retenida) |
| **Impuesto al Vender** | 19% (plusvalías ES) | 15-19% | 0% (ya pagado) |
| **Comisión TER** | **0.03-0.05%** | 0.20-0.35% | 0.30-0.50% |
| **Traspasos (cambio broker)** | **0% (libre)** | Taxado | Taxado |
| **Liquidez** | Excelente (brokers ES) | Buena | Buena |

**Ganancia a 30 años (100€ @ 6.5% neto):**
```
FIT VWRT (Vanguard)    → €647  ✅ Comisión ultra-baja (0.04%)
UCITS Acumulativo      → €642     Comisión más alta (0.22%)
Distribuidor           → €560     Impuesto anual + comisión (5-8% menos)
```

**FITs Populares Recomendados:**

- **VWRT** (Vanguard World Index Traspasable) - 0.04% TER - World index
- **OMAM** (iShares Core MSCI World) - 0.03% TER - World index  
- **NWD** (NN World Equity Index Fund) - 0.06% TER - World index

**Ventajas Prácticas:**
- ✅ Puedes cambiar de broker **sin fiscalidad** (traspasos gratis)
- ✅ Ahorras €1-2k en 30 años vs UCITS (mejor comisión)
- ✅ Disponibles en **casi todos los brokers españoles** (Degiro, IB, Selfbank)
- ✅ Acumulativos: **reinversión automática** sin impuesto anual
- ✅ 19% plusvalías = **mismo que Spain personal cuenta corriente** (eficiencia fiscal local)

**Configuración en el Calculador:**
```python
annual_spending: €40k
tax_on_gains: 19%      # Plusvalías (España)
tax_on_dividends: 0%   # Acumulativos (sin retenida)
fund_fees: 0.0004      # 0.04% TER (similar VWRT Vanguard)
expected_return: 6.5%  # Después de comisión
```

---

## 📊 Cómo Funciona

### Flujo de la Aplicación

```
┌─────────────────────────────────────────────────┐
│ 1. Seleccionar Perfil FIRE (5 opciones)        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 2. Personalizar Parámetros (Opcional)          │
│    • Gasto anual                                 │
│    • Tasa de retirada segura (SWR)              │
│    • Retorno esperado                           │
│    • Inflación, impuestos, comisiones           │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 3. Datos Personales                             │
│    • Capital actual                              │
│    • Aportación anual                           │
│    • Edad actual & años horizonte                │
│    • Propiedades, deudas                        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 4. Análisis Completo                            │
│    ✓ FIRE Number (portafolio target)           │
│    ✓ Proyección a 10 años                       │
│    ✓ Monte Carlo (probabilidad de éxito)       │
│    ✓ KPIs profesionales                         │
│    ✓ Recomendaciones personalizadas             │
└─────────────────────────────────────────────────┘
```

### Ejemplo de Resultado

```
🎯 RESUMEN DE PERFIL - Barista FIRE
══════════════════════════════════════════════════════════════════════════════

📊 KEY PERFORMANCE INDICATORS:
  🎯 FIRE Number (Objetivo):           €     875,000
  💰 Patrimonio Neto (Net Worth):      €     100,000
  📊 Equity Líquido (inversiones):     €     100,000
  🏠 Equity Inmobiliario (neto):       €     320,000
  💳 Deuda Total Pendiente:            €     230,000

⏳ PROGRESO HACIA FIRE: [████████░░░░░░░░░░] 11.4%

⏰ CRONOLOGÍA:
  Años hasta FIRE: 9 años
  (Edad actual: 32a → Podrías retirarte a los 41a)
  ✅ Alcanzarás FIRE 19.0 años antes de tu edad deseada (60a)

💵 APORTACIONES ANUALES:
  • Ahorros de salario: €12,000
  • Ingresos por alquiler: €24,000
  • Total efectivo: €36,000
  • Tasa de ahorro: 64.3%

🎲 MONTE CARLO (10,000 simulaciones):
  ✅ PROBABILIDAD DE ÉXITO: 87.3%
  
  📊 ESCENARIOS EN 25 AÑOS:
     Pesimista (10%):  €750,000   (85% del objetivo)
     Mediano (50%):    €875,000   (100% del objetivo)
     Optimista (90%):  €1,050,000 (120% del objetivo)

🌴 COAST FIRE: Con deferimiento fiscal de UCITS, podrías dejar de aportar en 8 años.
```

---

## ⚙️ Parámetros Configurables

### Parámetros Principales

| Parámetro | Default Lean | Default Fat | Rango Típico | Impacto |
|-----------|-------------|-----------|------------|---------|
| **Gasto Anual** | €25,000 | €75,000 | €15k-€150k | 🔴 Crítico |
| **SWR (%)** | 4.0% | 4.0% | 3.0%-4.5% | 🔴 Crítico |
| **Retorno (%)** | 6.0% | 7.0% | 4.0%-8.0% | 🟠 Alto |
| **Inflación (%)** | 2.0% | 2.0% | 1.5%-3.0% | 🟠 Alto |
| **Impuesto Plusvalías (%)** | 15% | 15% | 10%-25% | 🟡 Medio |
| **Impuesto Dividendos (%)** | 30% | 30% | 0%-45% | 🟡 Medio |
| **Comisión Fondos (%)** | 0.100% | 0.120% | 0.03%-0.50% | 🟡 Medio |

### Impuestos Típicos por País (2024)

| País | Plusvalías | Dividendos | Intereses |
|------|-----------|-----------|----------|
| 🇪🇸 España | 15% | 19-24% | 19% |
| 🇩🇪 Alemania | 26% | 26% | 26% |
| 🇫🇷 Francia | 30% | 30% | 30% |
| 🇮🇹 Italia | 26% | 26% | 26% |
| 🇵🇹 Portugal | 10% | 10% | 10% |
| 🇧🇪 Bélgica | 15-33% | 15-33% | 15-37% |

---

## 💰 Fórmulas Utilizadas

### FIRE Number (Objetivo)

```math
FIRE\_Number = \frac{Annual\_Spending}{SWR}
```

**Ejemplo:**
```
€40,000 / 0.04 = €1,000,000 necesarios
```

### FIRE Target Bruto (Tax-Aware)

```math
Gross\_Target = \frac{Annual\_Spending}{SWR \times (1 - Tax\_Rate)}
```

**Ejemplo (con 15% impuesto sobre plusvalías):**
```
€40,000 / (0.04 × 0.85) = €1,176,471
```

### Crecimiento del Portfolio

```math
Portfolio_{n+1} = Portfolio_n \times (1 + Retorno - Fees) + Aportación
```

### Tasa de Ahorro

```math
Savings\_Rate = \frac{Income - Spending}{Income}
```

**Ejemplo:**
```
(€100,000 - €40,000) / €100,000 = 60%
```

---

## 📈 Tipos de Dividendos en eu Perfil

### 🎓 UCITS Acumulativos (vs. Distribuidores)

**Estrategia en tu Perfil UCITS Tax Efficient:**

| Aspecto | UCITS Acumulativo | Fondo Distribuidor |
|--------|-----------------|-------------------|
| **¿Reparten dividendos?** | ❌ No (reinvierten internamente) | ✅ Sí (cada año) |
| **Impuesto anual** | 0% (diferido hasta venta) | 30% (retención anual) |
| **Efecto compuesto** | Máximo (30+ años sin fricción) | Reducido (fricción fiscal anual) |
| **Ejemplos** | VWCE, IWDA, EMIM | S&P500 distribuidor |

**Impacto a 30 años (€100 @ 7% retorno):**
```
UCITS Acumulativo:  €761  ✅ Máximo crecimiento
Fondo Distribuidor: €650  ⚠️  €111 menos (15% menos!)
```

### Configuración por Perfil

- **Lean/Fat/Coast/Barista**: Asumen fondos distribuidores (30% impuesto anual)
- **UCITS Tax Efficient**: Asume acumulativos (0% impuesto anual, deferido)

**Puedes cambiar esto en personalización:**
- Si usas UCITS en Lean FIRE → baja "Impuesto dividendos" a 0%
- Si usas distribuidores en UCITS → sube a 30%

---

## 💻 Ejemplos de Uso

### Ejemplo 1: Lean FIRE Conservador

```python
# Default: €25,000/año @ 4% SWR = €625,000
# Con €500/mes ahorrados = 6 años hasta FIRE

Selecciona: 1) Lean FIRE
Personaliza: Acepta defaults o:
  • Gasto anual: €20,000 (más conservador)
  • Retorno: 5.5% (más realista)

Resultado: €500,000 target, ~5 años hasta FIRE
```

### Ejemplo 2: Fat FIRE con Matrimonio

```python
# Fat FIRE: dos personas, €75,000/año
# €3,000/mes ahorrados = ~20 años

Selecciona: 2) Fat FIRE
Personaliza:
  • Capital actual: €350,000 (ahorros juntos)
  • Aportación anual: €36,000 (€1,500/mes × 2)
  • Propiedades: €600,000 (casa + inversión)
  • Hipoteca: €200,000 (quedan 15 años)

Resultado: €1,875,000 target
  Equity neto: €400,000
  Años a FIRE: ~15 años
```

### Ejemplo 3: Barista FIRE con Real Estate

```python
# Barista: trabajo part-time + alquileres
# €12,000 salario + €24,000 renta = €36,000/año

Selecciona: 4) Barista FIRE
Personaliza:
  • Actual savings: €100,000
  • Annual contribution: €12,000 (solo salario)
  • Primary property: €300,000 / hipoteca €150,000
  • Other properties: €200,000 / hipoteca €80,000
  • Rental income: €24,000/año

Resultado:
  FIRE target: €875,000 (para €35k/año @ 4% SWR)
  Current equity: €220,000 (real estate)
  Years to FIRE: ~9 años
  Bonus: Portfolio protegido por ingresos de alquiler
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Tests específicos
pytest tests/test_calculator.py -v
pytest tests/test_cli_input.py -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html
```

### Estructura de Tests

```
tests/
├── test_calculator.py          # 30+ tests (funciones core)
├── test_cli_input.py           # Input validation
├── test_commission_fix.py       # Validación de parsing de %
└── test_monte_carlo.py         # Simulaciones
```

### Ejemplos de Tests

```python
# Test: FIRE Number básico
def test_target_fire():
    assert target_fire(40_000, 0.04) == 1_000_000

# Test: Commission parsing (30%, not 3000%)
def test_commission_parsing():
    val = get_percent_input("Fee%", 0.001, max_pct=1)
    assert val == 0.005  # 0.5%, not 500%

# Test: Monte Carlo probabilidad
def test_monte_carlo_success():
    results = simulate_monte_carlo(config, 1000)
    assert 0 <= results['success_rate'] <= 1.0
```

---

## ⚠️ Disclaimers y Advertencias

1. **Esta NO es asesoría financiera**
   - Consulta con un asesor fiscal/financiero certificado
   - Las simulaciones son estimaciones, no garantías

2. **Impuestos varían por país**
   - España: 15% plusvalías, 19-24% dividendos
   - Alemania, Francia, Italia: otros porcentajes
   - Adquiere asesoría local específica

3. **Volatilidad = Realidad**
   - Modelo usa 15% std dev (histórico)
   - Tus retornos pueden variar significativamente
   - Mont Carlo da probabilidad, no certeza

4. **UCITS es para Europa**
   - Si inviertes fuera UE, adáptalo a tu legislación
   - Fondos no-UCITS pueden tener fiscalidad diferente

5. **Cambios en la Ley**
   - Impuestos, normativa de UCITS pueden cambiar
   - Revisa legislación de tu país regularmente

---

## 🚀 Roadmap Futuro (Propuestas)

- 📄 Exportar PDF con reporte completo
- 💾 Base de datos para guardar múltiples escenarios
- 📡 API REST para integración
- 🌍 Impuestos localizados por país
- 📊 Gráficos interactivos (matplotlib/plotly)
- 🔍 Análisis de sensibilidad (¿qué pasa si X cambia?)
- 🎯 Inflación por categoría (comida, vivienda, ocio)

---

## 📁 Estructura del Proyecto

```
FIRE/
├── README.md                    # Este archivo
├── requirements.txt             # Dependencias (ninguna)
├── src/
│   ├── cli.py                   # Aplicación principal (interactiva)
│   ├── calculator.py            # Lógica de cálculo (core)
│   └── enhanced_input.py        # Funciones de input mejoradas
├── tests/
│   ├── test_calculator.py       # 30+ unit tests
│   ├── test_cli_input.py        # Tests de input
│   └── test_monte_carlo.py      # Tests de simulaciones
└── examples/
    └── scenario_*.py            # Ejemplos de uso
```

---

## 💡 Tips y Mejores Prácticas

### Para Principiantes
1. Elige tu perfil más cercano (Lean/Fat/Coast/Barista)
2. Solo personaliza "Gasto Anual" si es diferente
3. Deja otros parámetros con sus defaults
4. **Lee el "Probabilidad de Éxito"** en Monte Carlo
5. Repite con diferentes gastos para explorar escenarios

### Para Avanzados
1. Personaliza TODOS los parámetros según tu país
2. Ajusta impuestos específicos de tu fiscalidad
3. Testa múltiples veces (iterativamente)
4. Guarda screenshots de diferentes escenarios
5. Revisa análisis anual (la vida cambia)

### Parámetros Críticos

| Parámetro | Por qué importa | Cómo ajustarlo |
|-----------|-----------------|----------------|
| **Gasto anual** | Define TODO (cartera target, años, etc.) | Sé realista, no optimista |
| **Retorno esperado** | Afecta crecimiento del portfolio | 5-6% realista (no 9-10%) |
| **SWR** | Qué % puedes retirar anualmente | 4% clásico, 3.5% conservador |
| **Impuestos** | Reduce crecimiento significativamente | Consulta asesor fiscal de tu país |
| **Comisiones** | Pequeñas comisiones suman con tiempo | <0.20% si es posible (ETF pasivo) |

---

## 📞 Soporte y Contribuciones

### Reportar Bugs
1. Ejecuta `pytest tests/ -v` para confirmar
2. Abre un issue con pasos para reproducir
3. Incluye tu perfil, parámetros y salida esperada

### Mejoras Propuestas
- Sugerencias de nuevas características
- Mejoras de documentación
- Optimizaciones de código
- Soporte para nuevos países

### Contribuciones
Fork → Branch → Commit → Pull Request

### ☕ Apoyo al Desarrollo

Si esta calculadora te ha sido útil en tu viaje FIRE, considera apoyar su desarrollo
con una pequeña donación:

**[☕ Invítame a un Café](https://buymeacoffee.com/pishu)**

Tu apoyo ayuda a:
- Mantener la herramienta actualizada
- Agregar nuevas características
- Expandir soporte a más países
- Mejorar la documentación

---

## 📜 Licencia

MIT License — Libre para uso personal y comercial

---

## ✍️ Changelog

### v1.0.0 (8 Febrero 2026) — Release Inicial
- ✅ 5 perfiles FIRE preconfigurados
- ✅ Parámetros personalizables con contextos explicativos
- ✅ Datos inmobiliarios completos (net worth)
- ✅ Monte Carlo con 10,000 simulaciones
- ✅ KPIs profesionales (FIRE Number, Burning Rate, Savings Rate, etc.)
- ✅ Proyecciones a 10+ años
- ✅ Suite de testing completa (30+ tests)
- ✅ Coast FIRE y Barista FIRE scenarios
- ✅ Documentación unificada

### Futuras Versiones
- v1.1.0: Exportación PDF
- v1.2.0: Gráficos interactivos
- v2.0.0: Base de datos + API REST

---

**Última actualización:** 8 de febrero, 2026  
**Estado:** ✅ Producción — Listo para comunidad  
**Autor:** Community (FIRE Calculators)

---

*¿Listo para planificar tu libertad financiera? Ejecuta `python3 src/cli.py` ahora.* 🚀

**Si te ha gustado este proyecto, por favor considera:**
- ⭐ Dar una estrella en GitHub
- 🔀 Hacer un fork para contribuir
- ☕ [Apoyar el desarrollo](https://buymeacoffee.com/pishu)
- 📢 Compartir con otros inversores FIRE

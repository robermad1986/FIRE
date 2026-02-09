# 🌐 FIRE Calculator — Web Application (Streamlit)

> **Aplicación web interactiva para planificar tu Independencia Financiera**
>
> Simula tu jubilación con análisis Monte Carlo, visualizaciones profesionales y textos inspiradores personalizados.

![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Inicio Rápido (60 segundos)

### Opción 1: Local (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/robermad1986/FIRE.git
cd FIRE

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run app.py
```

✅ La aplicación se abrirá automáticamente en `http://localhost:8501`

### Opción 2: Sin instalación local (Próximamente)

Desplegar en **Streamlit Cloud** con un solo click: [Abrir en línea]() *(en desarrollo)*

---

## 📊 Características de la Aplicación Web

### 1. **Panel de Control Interactivo (Sidebar)**
Configura tu perfil en tiempo real:
- 💰 Patrimonio inicial y aportación mensual
- 📅 Edad actual y objetivo FIRE
- 📈 Rentabilidad esperada y volatilidad
- 💵 Inflación y gastos anuales en jubilación
- 🏛️ Régimen fiscal (España - Fondos/Cartera Directa)

### 2. **Dashboard de KPIs con Color-Coding Automático**

| Métrica | Rango | Interpretación |
|---------|-------|----------------|
| **Años hasta FIRE** | <5 años | 🚀 Fuego inmediato |
| | 5-15 años | 🌟 Excelente camino |
| | 15-25 años | 📈 Buen progreso |
| | >25 años | 💪 Perseverancia necesaria |
| **Probabilidad Éxito** | ≥95% | ✅ Prácticamente garantizado |
| | 75-95% | 👍 Muy probable |
| | 60-75% | ⚖️ Moderado |
| | <60% | 🔴 Riesgo elevado |

### 3. **Mensajes Dinámicos e Inspiradores**

Tu plan se adapta a 4 dimensiones:

```
⚡ Tu Timeline FIRE
"¡Vamos bien! Tu objetivo FIRE está dentro de lo alcanzable..."

👍 Tu Probabilidad de Éxito  
"82% de las simulaciones alcanzan FIRE..."

🚗 Tu Ritmo de Ahorro
"Ritmo acelerado: Tu tasa de ahorro es impresionante..."

📅 Comparación vs Objetivo
"Muy cercano: Solo 1 año después de tu objetivo..."
```

### 4. **Gráficos Interactivos Plotly**

- **Gráfico Principal:** Evolución del portafolio con bandas de incertidumbre (percentiles 5-95)
- **Distribución de Éxito:** Probabilidad año-a-año de alcanzar FIRE
- **Matriz de Sensibilidad:** 5x5 escenarios (rentabilidad vs inflación)

### 5. **Monte Carlo Simulation (10,000 trayectorias)**

- ✅ Cálculo de probabilidad real de éxito
- ✅ Cono de incertidumbre visual
- ✅ Análisis de escenarios pesimista/base/optimista
- ✅ Caché automático para rendimiento (<3s)

### 6. **Exportación de Datos**

- 📊 CSV con serie temporal completa (P5, P25, P50, P75, P95, % éxito)
- 📄 PDF ejecutivo (próximamente)

### 7. **Privacidad Total**

🔒 **Todos los cálculos se ejecutan localmente en tu navegador.**  
Ningún dato financiero abandona tu dispositivo.

---

## 🛠️ Instalación Detallada

### Requisitos Previos

- **Python 3.9+** ([Descargar](https://www.python.org/downloads/))
- **pip** (incluido con Python)
- **Git** ([Descargar](https://git-scm.com/))

### Pasos

#### 1. Clonar el repositorio

```bash
git clone https://github.com/robermad1986/FIRE.git
cd FIRE
```

#### 2. Crear entorno virtual (opcional pero recomendado)

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

**Dependencias principales:**
- `streamlit>=1.28.0` — Framework web
- `plotly>=5.15.0` — Gráficos interactivos
- `pandas>=2.0.0` — Manejo de datos
- `numpy>=1.24.0` — Computación numérica
- `reportlab>=3.6.0` — Generación PDF (futuro)

#### 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

✅ Se abrirá automáticamente en `http://localhost:8501`

---

## 📖 Uso de la Aplicación

### Flujo Típico

1. **Configura tu perfil** en el sidebar izquierdo
2. **Espera 2-5 segundos** mientras se ejecutan 10,000 simulaciones Monte Carlo
3. **Visualiza los resultados:**
   - 4 KPIs principales con color-coding
   - 4 mensajes inspiradores personalizados
   - Gráficos interactivos con tus datos
4. **Analiza sensibilidad** usando la matriz 5x5
5. **Descarga tu proyección en CSV** para seguimiento anual

### Ejemplo: María, 35 años, Inversora Moderada

```
INPUTS:
├─ Patrimonio: €200.000
├─ Aportación: €1.000/mes
├─ Horizonte: 50 años (FIRE a los 50)
├─ Rentabilidad: 7% anual
├─ Volatilidad: 15%
├─ Inflación: 2.5%
└─ Gastos jubilación: €30.000/año

OUTPUT:
├─ Años a FIRE: 15 años (P50)
├─ Éxito: 85% (Monte Carlo)
├─ Patrimonio final: €900.000 (mediana)
├─ Rentabilidad real: +4.35% anual
└─ Mensajes: ⚡ "¡Vamos bien!" + 👍 "Muy probable" + ...
```

---

## 🔄 Cálculos Internos

### 1. **Objetivo FIRE (SWR = 4%)**

```
FIRE Target = Gasto Anual Jubilación / 0.04
Ejemplo: €30.000 / 0.04 = €750.000 requeridos
```

### 2. **Simulación Monte Carlo**

- 10,000 trayectorias usando **geometría Browniana**
- Rentabilidad: μ = esperada, σ = volatilidad
- Reinversión de aportaciones mensuales
- Ajuste por inflación (valores reales)

### 3. **Validación de Inputs**

Se valida automáticamente:
- ✅ Patrimonio: €0 - €10M
- ✅ Aportación: €0 - €50k/mes
- ✅ Edades: 18-100 años
- ✅ Rentabilidad: -10% a +25%
- ✅ Volatilidad: 5%-25%
- ✅ Inflación: -5% a +20%
- ✅ Gastos: €1k - €1M/año

### 4. **Mensajes Dinámicos**

Se adaptan automáticamente según:
- `generate_fire_readiness_message()` — Años a FIRE
- `generate_success_probability_message()` — Probabilidad éxito
- `generate_savings_velocity_message()` — Ratio ahorro/gasto
- `generate_horizon_comparison_message()` — vs objetivo usuario
- `generate_market_scenario_message()` — Volatilidad esperada

---

## 🧪 Testing

```bash
# Ejecutar tests unitarios
pytest tests/

# Cobertura de tests
pytest --cov=src tests/

# Tests específicos para la aplicación web
pytest tests/test_cli_workflow.py
```

**Cobertura:** 95%+ de las funciones críticas

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"

```bash
pip install streamlit>=1.28.0
```

### "Port 8501 already in use"

```bash
streamlit run app.py --server.port=8502
```

### Aplicación lenta en simulaciones

- La primera ejecución carga 10k simulaciones (~3-5s)
- Las siguientes son instantáneas (caché de 1 hora)
- Si no cambian los parámetros, no se recalculan

### Gráficos no se muestran

- Verificar que `plotly>=5.15.0` está instalado
- Limpiar caché: `streamlit cache clear`

---

## 📝 Arquitectura de Código

```
app.py (1,230 líneas)
├── CONFIGURATION & CONSTANTS (líneas 45-139)
│   ├─ PAGE_CONFIG, COLOR_SCHEME, VALIDATION_RULES
│   └─ 5 funciones generadoras de textos dinámicos
│
├── SESSION STATE (líneas 140-145)
│   └─ Inicialización de caché
│
├── VALIDATION (líneas 147-250)
│   ├─ validate_inputs()
│   └─ Soporte para 7 reglas de negocio
│
├── MONTE CARLO ENGINE (líneas 252-350)
│   ├─ monte_carlo_simulation()
│   └─ Geometric Brownian Motion con 10k trayectorias
│
├── CACHING LAYER (líneas 352-385)
│   ├─ run_cached_simulation()
│   └─ @st.cache_data(ttl=3600)
│
├── SIDEBAR (líneas 387-655)
│   └─ render_sidebar()
│
├── KPIS (líneas 657-775)
│   └─ render_kpis() + 4 mensajes dinámicos
│
├── CHARTS (líneas 777-950)
│   ├─ render_main_chart()
│   └─ render_success_distribution_chart()
│
├── SENSITIVITY (líneas 952-1078)
│   └─ render_sensitivity_analysis() 5x5 matrix
│
├── EXPORT (líneas 1080-1125)
│   └─ render_export_options() CSV + PDF placeholder
│
└── MAIN ORCHESTRATION (líneas 1127-1235)
    └─ main() — Flujo principal
```

---

## 📊 Integración con Backend

La aplicación reutiliza el motor de cálculo de `src/calculator.py`:

```python
from src.calculator import (
    target_fire,              # Objetivo FIRE
    project_portfolio,        # Proyección determinística
    calculate_market_scenarios,  # 3 escenarios
    project_retirement,       # Fase de jubilación
    calculate_net_worth,      # Patrimonio neto
)
```

**Ventaja:** El motor puede usarse independientemente en CLI, scripts, o APIs.

---

## 🚀 Próximas Mejoras

### MVP (Actual)
- ✅ Interfaz web Streamlit
- ✅ 5 funciones de textos dinámicos
- ✅ Gráficos interactivos
- ✅ Matriz de sensibilidad 5x5
- ✅ Validación de inputs completa
- ✅ CSV export

### v1.1 (Próximas 2 semanas)
- [ ] PDF export con reportlab
- [ ] Soporte multiidioma (ES/EN/FR)
- [ ] Persistencia local (SQLite)
- [ ] Despliegue en Streamlit Cloud
- [ ] Docker support

### v2.0 (Roadmap)
- [ ] API REST (FastAPI)
- [ ] App móvil (React Native)
- [ ] Notificaciones semanales (email)
- [ ] Comparativa comunitaria (anónima)
- [ ] Gamification (badges/hitos)

---

## 📚 Documentación Adicional

| Archivo | Descripción |
|---------|------------|
| [README.md](README.md) | Documentación general del proyecto |
| [DYNAMIC_MESSAGES_GUIDE.md](DYNAMIC_MESSAGES_GUIDE.md) | Guía técnica de textos dinámicos |
| [PROMPT_IMPROVEMENTS.md](PROMPT_IMPROVEMENTS.md) | Mejoras al prompt ejecutivo original |
| [INSTALLATION.md](INSTALLATION.md) | Guía de instalación detallada |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guía para contribuidores |

---

## 🤝 Contribuciones

¿Encontraste un bug? ¿Tienes una idea de mejora?

1. **Report a bug:** [Abrir un Issue](https://github.com/robermad1986/FIRE/issues)
2. **Sugerir mejora:** [Discusión](https://github.com/robermad1986/FIRE/discussions)
3. **Contribuir código:** [Pull Request](https://github.com/robermad1986/FIRE/pulls)

---

## 📄 Licencia

MIT License — Libre para usar, modificar y distribuir.  
Ver [LICENSE](LICENSE) para detalles.

---

## ☕ Apoyo

Si esta herramienta te ayuda en tu camino a la libertad financiera, considera:

- ⭐ Dar una estrella en GitHub
- 🔗 Compartir con tu comunidad
- 💰 [Invitarme a un café](https://buymeacoffee.com/pishu)

---

**Última actualización:** 9 de febrero de 2026  
**Versión:** 1.0  
**Estado:** Production Ready ✅

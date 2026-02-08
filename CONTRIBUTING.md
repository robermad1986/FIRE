# Contributing to FIRE Calculator

¡Gracias por tu interés en contribuir a FIRE Calculator! Esta guía te ayudará a entender cómo colaborar efectivamente.

## 📋 Código de Conducta

- Sé respetuoso y constructivo en todas las discusiones
- Proporciona feedback útil sin atacar ideas personales
- Reconoce el trabajo de otros contribuidores

## 🐛 Reportar Bugs

1. **Verifica que no exista un issue similar** en la sección de Issues
2. **Ejecuta los tests** para confirmar el problema:
   ```bash
   pytest tests/ -v
   ```
3. **Abre un Issue** con:
   - Título descriptivo: `[BUG] Descripción clara`
   - Pasos para reproducir
   - Comportamiento actual vs esperado
   - Tu perfil (Lean/Fat/Coast/Barista/UCITS) y parámetros

### Ejemplo de Bug Report

```
Title: [BUG] Commission parsing shows 300% instead of 3%

Steps to reproduce:
1. Select "1) Lean FIRE" profile
2. Choose "Edit parameters"
3. Enter "3" for commission fee (expecting 3%, which is 0.03)

Expected: Commission stored as 0.030
Actual: Commission stored as 3.000

Environment:
- Python 3.9.22
- macOS
```

## ✨ Sugerir Mejoras

1. Abre un Issue con título `[FEATURE] Tu idea`
2. Describe:
   - Qué funcionalidad propones
   - Por qué sería útil
   - Impacto esperado en usuarios

### Ejemplos de Mejoras Bienvenidas

- 🗺️ Soporte para nuevos países (impuestos locales)
- 📊 Gráficos interactivos o PDF export
- 🌐 Versión web o API REST
- 🎯 Nuevos perfiles FIRE (Geographic FIRE, etc.)
- 🧩 Mejoras en UX/claridad de mensajes

## 💻 Contribuir Código

### Clonar y Configurar

```bash
# Clone el repo
git clone https://github.com/your-username/FIRE.git
cd FIRE

# Crea una rama para tu feature
git checkout -b feature/my-awesome-feature

# (Opcional) Crea virtual environment
python3 -m venv venv
source venv/bin/activate

# Instala dependencias (si las hay)
pip install -r requirements.txt

# Ejecuta tests para asegurar que todo funciona
pytest tests/ -v
```

### Estilo de Código

Seguimos estas convenciones:

```python
# Use snake_case para funciones y variables
def calculate_fire_number(spending, swr):
    """Calcula el número objetivo de FIRE."""
    return spending / swr

# Use UPPERCASE para constantes
DEFAULT_SWR = 0.04
DEFAULT_INFLATION_RATE = 0.02

# Docstrings en las funciones
def calculate_fire_number(spending: float, swr: float) -> float:
    """
    Calcula el número objetivo de FIRE.
    
    Args:
        spending: Gasto anual esperado en EUR
        swr: Safe Withdrawal Rate (ej: 0.04 para 4%)
    
    Returns:
        Float: Portfolio target acumulado
    
    Example:
        >>> calculate_fire_number(40_000, 0.04)
        1000000
    """
    return spending / swr

# Type hints en funciones críticas
def project_portfolio(
    current_balance: float,
    annual_contribution: float,
    years: int,
    annual_return: float,
) -> list[float]:
    """Proyecta el portfolio en N años."""
    ...

# Comments en lógica compleja
if value > (max_pct / 100):
    # Detecta si el usuario ingresó porcentaje (30) en lugar de decimal (0.30)
    # Ejemplo: Commission > 1% suggests user entered percentage, not decimal
    value /= 100
```

### Tests

**Todos los PRs deben incluir tests** para nuevas funcionalidades.

```python
# tests/test_new_feature.py
import pytest
from src.calculator import my_new_function

def test_my_new_function_basic():
    """Test case básico."""
    result = my_new_function(100, 0.07)
    assert result == 107

def test_my_new_function_edge_case():
    """Test case extremo."""
    with pytest.raises(ValueError):
        my_new_function(-100, 0.07)  # Negative balance no permitido

def test_my_new_function_zero_return():
    """Test case: retorno cero."""
    result = my_new_function(100, 0.00)
    assert result == 100
```

Ejecuta tests antes de hacer commit:

```bash
pytest tests/ -v --cov=src
```

### Hacer un Pull Request

1. **Push tu rama:**
   ```bash
   git add .
   git commit -m "feat: add FIRE scenario comparison table"
   git push origin feature/my-awesome-feature
   ```

2. **Abre un PR en GitHub** con:
   - Titulo claro: `feat: Add FIRE scenario comparison`
   - Descripción detallada de cambios
   - Screenshots si es UI change
   - Confirmar que tests pasan ✅

3. **Responde a reviews:**
   - Sé abierto al feedback
   - Haz cambios solicitados
   - Re-request review después de cambios

### Ejemplo PR Description

```markdown
## Description
Agrega tabla de comparación de escenarios FIRE para que usuarios vean 
fácilmente cuánto tiempo toma cada variante.

## Changes
- New function: `show_fire_scenarios()` in cli.py (lines 1620-1700)
- Added tests in test_cli_workflow.py
- Updated README with example output

## Screenshots
[Adjunta screenshot de la tabla de comparación]

## Checklist
- [x] Tests pass locally (`pytest tests/ -v`)
- [x] Code follows style guide
- [x] Docstrings added
- [x] No breaking changes
```

## 🔄 Ciclo de Desarrollo

```
Issue → Feature Branch → Code → Tests → PR → Review → Merge → Release
  ↑                                           ↓
  └─────────── Iterate if needed ────────────┘
```

## 📚 Estructura de Carpetas (Para Entender)

```
src/
├── cli.py              # Interfaz de usuario + lógica de flujo (2000+ líneas)
├── calculator.py       # Motor de cálculo (450+ líneas)
└── enhanced_input.py   # Validación de inputs mejorada

tests/
├── test_calculator.py        # Tests del motor (30+ cases)
├── test_cli_input.py         # Tests de validación
├── test_cli_workflow.py      # Tests de flujo end-to-end
└── ... (más tests)

examples/
└── scenario_*.py            # Ejemplos de uso
```

## 🎓 Áreas de Enfoque para Contribuidores

### Fácil (Buenas primeras contribuciones)
- Mejorar documentación
- Agregar ejemplos
- Traducir comentarios/docstrings
- Ajustar mensajes de usuario

### Intermedio (Requires calculation understanding)
- Agregar nuevos parámetros a perfiles
- Mejorar validación de inputs
- Agregar más tests

### Avanzado (Modifies core algorithm)
- Cambios en `project_portfolio()`
- Nuevas simulaciones (Monte Carlo improvements)
- Integración con datos en vivo (API integrations)

## 🧪 Testing Requirements

Para que un PR sea aceptado:

1. ✅ Todos los tests deben pasar: `pytest tests/ -v`
2. ✅ Coverage >85% para código crítico
3. ✅ Tests incluyen casos normales Y extremos
4. ✅ Sin warnings de sintaxis o imports

```bash
# Ejecuta pruebas con coverage
pytest tests/ --cov=src --cov-report=html

# Abre el reporte (macOS)
open htmlcov/index.html
```

## 🚀 Mejoras Propuestas Prioritarias

1. **Exportación PDF** — Usuarios quieren un reporte imprimible
2. **Gráficos** — Visualizaciones de proyección (matplotlib/plotly)
3. **Persistencia** — Guardar y cargar escenarios
4. **Localización** — Impuestos por país completamente mapeados
5. **API REST** — Para integración con other tools

## ❓ Preguntas?

- Abre un Issue con tag `[QUESTION]`
- Revisa Issues existentes y Discussions
- Mira el README.md para entender concepts

## 📜 Licencia

Al contribuir, aceptas que tu código será bajo la licencia MIT (o lo que especifique el proyecto).

---

**¡Gracias por ayudar a hacer de FIRE Calculator una herramienta mejor! 🙌**

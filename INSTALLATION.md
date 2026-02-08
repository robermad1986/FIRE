# 🚀 Installation Guide

Guía paso a paso para instalar y ejecutar FIRE Calculator.

## 📋 Requisitos

- **Python** 3.9 o superior
- **pip** (gestor de paquetes de Python)
- **Terminal/CMD** (acceso a línea de comandos)

### Verificar Requisitos

```bash
# Verifica Python 
python3 --version
# Esperado: Python 3.9.x o superior

# Verifica pip
pip3 --version
# Esperado: pip 21.x o superior
```

---

## 🔧 Opción 1: Instalación Rápida (Recomendada)

Para empezar rápidamente sin configuración adicional:

### 1. Clonar el repositorio

```bash
git clone https://github.com/your-username/FIRE.git
cd FIRE
```

### 2. Ejecutar la aplicación

```bash
python3 src/cli.py
```

Eso es todo. La aplicación ejecutará sin dependencias externas (usa solo stdlib).

---

## 🎯 Opción 2: Configuración con Virtual Environment (Recomendado para desarrollo)

Para desarrollo local o si quieres aislar la instalación:

### 1. Clonar el repositorio

```bash
git clone https://github.com/your-username/FIRE.git
cd FIRE
```

### 2. Crear Virtual Environment

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

Al activar, deberías ver `(venv)` al inicio de tu terminal.

### 3. Instalar dependencias

```bash
# Si el proyecto tuviera dependencias (actualmente no)
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
python3 src/cli.py
```

### 5. Para salir del virtual environment

```bash
deactivate
```

---

## 🧪 Instalación para Desarrollo (Con Tests)

Si quieres desarrollar o contribuir:

### 1-2. [Sigue los pasos de arriba]

### 3. Instalar dependencias de desarrollo

```bash
# El proyecto actualmente no tiene dependencias externas
# Pero puedes instalar pytest para ejecutar tests
pip install pytest pytest-cov
```

### 4. Ejecutar tests

```bash
# Ejecuta toda la suite
pytest tests/ -v

# Con coverage
pytest tests/ --cov=src --cov-report=html
```

### 5. Ver el reporte de coverage (opcional)

```bash
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Windows
start htmlcov/index.html
```

---

## 🎮 Verificación de Instalación

Para confirmar que todo funciona:

```bash
python3 src/cli.py
```

Deberías ver el menú principal:

```
Elige tu Perfil FIRE
================================================================================

  1) Lean FIRE            — Gasto €20k-€30k/año: vida modesta pero independiente
  2) Fat FIRE             — Gasto €60k-€100k/año: retiro confortable y sin restricciones
  3) Coast FIRE           — Gasto €40k/año: acumula ahora, deja crecer sin aportes después
  4) Barista FIRE         — Gasto €50k/año: €15k trabajo part-time + €35k portfolio (4% SWR)
  5) UCITS Tax Efficient  — Gasto €45k/año: optimizado para UCITS y cuentas múltiples
  6) Entrada personalizada (Custom)
  7) Ver ejemplo JSON (para usar con API)
  0) Salir

Elige (0-7): 
```

✅ Si ves esto, ¡la instalación fue exitosa!

---

## 🐍 Problemas Comunes de Instalación

### Error: "python3: command not found"

**Problema:** Python no está instalado o no está en PATH.

**Solución:**
- macOS: `brew install python3`
- Linux: `sudo apt-get install python3`
- Windows: Descarga desde [python.org](https://www.python.org/downloads/)

### Error: "ModuleNotFoundError: No module named 'src'"

**Problema:** Estás ejecutando el script desde un directorio incorrecto.

**Solución:** Asegúrate de estar en el directorio raíz del proyecto:
```bash
cd FIRE
python3 src/cli.py
```

### Error: "Permission denied"

**Problema:** No tienes permisos para ejecutar.

**Solución (macOS/Linux):**
```bash
chmod +x src/cli.py
python3 src/cli.py
```

### El programa se cierra inmediatamente

**Problema:** Posible error no capturado.

**Solución:** Ejecuta desde terminal directamente para ver mensajes de error:
```bash
python3 -u src/cli.py
```

---

## 🔄 Actualizar a Nueva Versión

Si ya tienes FIRE Calculator instalado y quieres actualizar:

```bash
# Ve al directorio del proyecto
cd FIRE

# Obtén los cambios
git pull origin main

# (Si usas venv) Actívalo
source venv/bin/activate

# Ejecuta
python3 src/cli.py
```

---

## 📦 Estructura After Installation

Después de instalar, verás:

```
FIRE/
├── README.md              # Documentación principal
├── CONTRIBUTING.md        # Cómo contribuir
├── INSTALLATION.md        # Este archivo
├── requirements.txt       # Dependencias (vacío actualmente)
├── .gitignore            # Archivos a ignorar en git
├── src/
│   ├── cli.py            # Aplicación principal
│   ├── calculator.py     # Motor de cálculo
│   └── enhanced_input.py # Validación de inputs
├── tests/
│   ├── test_calculator.py
│   ├── test_cli_input.py
│   └── ... (más tests)
├── examples/
│   └── ... (ejemplos de uso)
└── DEPRECATED/
    └── ... (archivos históricos de desarrollo)
```

---

## ✅ Siguientes Pasos

1. **Lee el README.md** para entender características
2. **Ejecuta el programa** con tu perfil FIRE favorito
3. **Explora parámetros** para personalizarlo
4. **Lee CONTRIBUTING.md** si quieres contribuir

---

## 💬 ¿Necesitas Ayuda?

- **Lee el README.md** para respuestas sobre features
- **Abre un Issue** en GitHub si hallas bugs
- **Revisa CONTRIBUTING.md** para cómo contribuir

---

**¡Bienvenido a FIRE Calculator! Planifica tu libertad financiera. 🚀**

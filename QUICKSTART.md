# ⚡ Quick Start — FIRE Calculator Web App

## 60 segundos para tener la calculadora FIRE ejecutándose

### 1️⃣ Clonar

```bash
git clone https://github.com/robermad1986/FIRE.git
cd FIRE
```

### 2️⃣ Instalar

```bash
pip install -r requirements.txt
```

### 3️⃣ Ejecutar

```bash
streamlit run app.py
```

✅ **Listo.** Se abrirá en `http://localhost:8501`

---

## 🎯 Primer Uso

1. **Sidebar izquierdo:** Configura tu perfil
2. **Espera 3 segundos:** Se ejecutan 10,000 simulaciones
3. **Visualiza:** KPIs, gráficos, análisis de sensibilidad
4. **Descarga:** CSV con tu proyección

---

## ❓ Problemas Comunes

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError` | `pip install streamlit plotly pandas numpy` |
| Puerto 8501 en uso | `streamlit run app.py --server.port=8502` |
| Python no encontrado | Instala Python 3.9+ desde [python.org](https://www.python.org) |

---

## 📖 Más Información

- **Características completas:** [WEB_APP_README.md](WEB_APP_README.md)
- **Documentación técnica:** [PROMPT_IMPROVEMENTS.md](PROMPT_IMPROVEMENTS.md)
- **Instalación detallada:** [INSTALLATION.md](INSTALLATION.md)

---

**¿Necesitas ayuda?** Abre un [Issue en GitHub](https://github.com/robermad1986/FIRE/issues)

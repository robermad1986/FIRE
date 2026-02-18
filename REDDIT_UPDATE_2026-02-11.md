🚀 **ACTUALIZACIÓN 14 FEBRERO 2026 (Web + motor de simulación)**

Gracias por todo el feedback del hilo. Esta ronda ha sido de **precisión de cálculo + UX + estabilidad**.

## ✅ Qué se ha implementado

### 1) UX y panel de control (web)

* Inputs exactos en campos clave (patrimonio, aportación, cuotas), ocultando la barra cuando activas modo exacto.
* Carga de perfil JSON en sidebar con flujo limpio.
* Comparador **A/B** de escenarios en resultados.
* Ajustes visuales y de legibilidad en bloques principales.

### 2) Persistencia y exportes

* Export de perfil/escenario en JSON.
* CSV mantenido para seguimiento histórico.
* Botón de imprimir/guardar PDF estabilizado.
* Corregida la persistencia de campos de pensión en JSON (carga/guardado consistente en web).

### 3) Fiscalidad

* Selector fiscal: **España (Tax Pack)** y **Internacional básico**.
* Corregido el modelo internacional básico para evitar un drag irreal:
  * ya no resta el tipo como % anual de toda la cartera,
  * ahora aplica un enfoque más razonable sobre base de retorno.

### 4) Simulación y backtesting

* Modelos activos:
  * Monte Carlo normal,
  * Monte Carlo bootstrap histórico,
  * Backtesting histórico por ventanas móviles.
* Añadidos indicadores de fidelidad del backtesting:
  * número de ventanas,
  * rango histórico cubierto,
  * calidad de cobertura mensual.
* En la gráfica:
  * ventana crítica (peor),
  * ventana favorable (mejor),
  * KPI de riesgo de secuencia.

### 5) Gestión del capital en jubilación

* Orden de columnas fijado para evitar desajustes visuales.
* Chequeo contable por fila (`capital inicial + crecimiento - retirada = capital final`).
* Nuevo modelo de retiro por defecto: **2 fases simple** (retirada neta desde cartera en pre/post pensión).
* El modo avanzado con desglose (`pensión pública`, `plan privado`, `otras rentas`) se mantiene como opción.
* Mini-KPI por pestaña con retorno implícito usado.
* Correcciones de coherencia en escenarios P5/P25/P50/P75/P95.
* KPI de jubilación ahora sí responde al slider de años proyectados.
* Añadida columna de ingresos por alquiler en tabla de jubilación (con explicación de cómo impacta en retirada neta).
* Separado “descuadre” de “déficit no cubierto” cuando el capital se agota, para evitar lecturas confusas.

### 6) Robustez técnica

* Correcciones de estado en Streamlit (carga de perfil + recálculo).
* Corrección de bugs detectados con interacción rápida de sliders/inputs.
* Ampliación de tests en fiscalidad, perfiles y modelos.
* Refuerzo de stress tests en motores de simulación (normal/bootstrap/backtest) con invariantes numéricos.

---

## ⚠️ Limitaciones actuales (importantes)

* Sigue siendo una herramienta educativa de planificación (no asesoría fiscal/legal personalizada).
* El modo internacional básico sigue siendo una aproximación agregada.
* Falta más validación externa en casuísticas fiscales complejas.

---

## 🔜 Próximos pasos

1. Mejorar precisión fiscal pre/post pensión con casos reales.
2. Reducir deuda técnica y complejidad de `app.py` y `src/cli.py`.
3. Seguir cerrando paridad web/CLI con tests end-to-end.

Si queréis, en la próxima iteración puedo publicar una **comparativa antes/después** con escenarios reales anonimizados para que se vea mejor el impacto de cada cambio.

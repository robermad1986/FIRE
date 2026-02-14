# Update del proyecto FIRE (14 Feb 2026)

Gracias por todo el feedback del hilo. Esta iteración se ha centrado en precisión del modelo, UX y estabilidad web.

## Cambios ya implementados

1. Inputs y UX (web)
- Inputs exactos en campos clave de importe (patrimonio, aportación, cuotas), ocultando la barra cuando activas modo exacto.
- Carga de perfil JSON en sidebar (flujo de carga limpio y sin duplicar export).
- Reordenación/pulido visual de panel y bloques de resultados.
- Comparador A/B en resultados: guardas un escenario base y comparas contra el actual.

2. Persistencia y exportes
- Perfil y escenario exportables en JSON.
- CSV mantenido para seguimiento.
- Botón de imprimir/guardar PDF vía navegador estabilizado.

3. Fiscalidad
- Modo fiscal `España (Tax Pack)` + `Internacional básico`.
- Ajuste del modelo internacional básico para evitar drag irreal (ya no resta el tipo como porcentaje anual de toda la cartera).

4. Simulación y backtesting
- Monte Carlo normal + bootstrap histórico + backtesting histórico en ventanas.
- Añadidos indicadores de fidelidad en backtesting (ventanas evaluadas, rango histórico y cobertura mensual).
- En gráficos de backtesting: marcado de ventana crítica (peor) y favorable (mejor), con lectura de impacto.
- KPI de riesgo de secuencia (brecha entre ventana crítica y favorable).

5. Jubilación / gasto de capital
- Tabla de gasto de capital con orden de columnas fijo y chequeo de flujo contable por fila.
- Correcciones para alinear mejor escenarios P5–P95 y trazabilidad del retorno implícito usado por escenario.
- Mini-KPI por pestaña con “retorno anual implícito usado”.

6. Robustez técnica
- Correcciones de estados de Streamlit (incluyendo cargas de perfil y recálculo).
- Corrección de bugs detectados moviendo sliders / interacciones rápidas.
- Suite de tests ampliada en módulos fiscales, perfiles y modelos.

## Limitaciones que siguen vigentes

- Sigue siendo un simulador educativo de planificación, no asesoría fiscal/legal personalizada.
- El modo internacional básico es una aproximación agregada (no sustituye un motor fiscal país-a-país).
- Faltan más casos de validación externa para normativa fiscal regional y escenarios complejos de retiro.

## Próximos focos propuestos

1. Mejorar precisión fiscal pre/post pensión con más casuísticas reales.
2. Seguir reduciendo deuda técnica y complejidad de `app.py`/`src/cli.py`.
3. Mayor paridad funcional CLI/web en bloques avanzados y pruebas end-to-end.

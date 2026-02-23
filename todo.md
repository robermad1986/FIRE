# TODO Maestro - FIRE Web (Quick Mode + UX + Robustez)

Este documento es el tablero operativo para ejecutar el plan de mejora.
Se irá actualizando durante la implementación.

## Meta
Entregar un flujo `Rápido` para usuarios nuevos (modular y claro) sin perder la potencia del flujo `Completo`, reforzando estado/UI/tests para eliminar inconsistencias.

## Estado actual (2026-02-23)
- Estado general: `En curso`
- Prioridad: `Alta`
- Riesgo principal: `Inconsistencias de session_state en transiciones de UI`
- Rama sugerida: `feature/quick-mode-v1`

## Avances ya hechos
- [x] Hardening de sincronización sugerido/manual en `Retiro en 2 fases` (modo simple).
- [x] Limpieza de estado sugerido al `Aplicar perfil` y `Limpiar perfil`.
- [x] Corrección de error `profile_name_key cannot be modified after widget instantiation`.
- [x] Extracción de lógica de presets a `src/profile_presets.py`.
- [x] Tests nuevos para presets + máquina de estados (`tests/test_profile_presets.py`).
- [x] Test de dominancia matricial añadido en `tests/test_simulation_models.py`.
- [x] Stress tests repetidos (incluyendo loops) sin fallos.

---

## Alcance de esta iteración
1. Añadir `Modo Rápido` utilizable en menos de 2 minutos.
2. Mantener `Modo Completo` sin regresiones funcionales.
3. Reforzar cobertura de pruebas en estado UI y coherencia de cálculos.
4. Dejar plan de rollout controlado con feature flag.

## Fuera de alcance (por ahora)
- Reescritura completa de `app.py`.
- Rediseño visual profundo completo.
- Motor fiscal país-a-país nuevo.
- Sustituir Streamlit por otro framework.

---

## Roadmap por fases

## Fase 0 - Baseline y control de cambios
Objetivo: fijar referencia para comparar antes/después.

- [ ] Guardar baseline de resultados en 5 escenarios de referencia.
- [ ] Guardar baseline de rendimiento (tiempo de render).
- [ ] Ejecutar baseline de tests:
  - [ ] `pytest -m "not stress"`
  - [ ] `pytest -m stress`
- [ ] Crear tabla de comparación de KPIs (antes/después).

Entregable:
- `docs/baseline_quick_mode.md` con métricas iniciales.

---

## Fase 1 - Arquitectura de UI por modo
Objetivo: separar claramente `Rápido` y `Completo`.

- [ ] Añadir selector global de modo UI (`Rápido` / `Completo`).
- [ ] Crear router principal de render:
  - [ ] `render_quick_mode()`
  - [ ] `render_full_mode()`
- [ ] Asegurar que `render_full_mode()` conserva comportamiento actual.
- [ ] Mantener persistencia de modo seleccionado en `session_state`.
- [ ] Añadir feature flag `feature_quick_mode_v1`.

Archivos previstos:
- `app.py`
- `src/profile_io.py` (si se persiste `ui_mode`)

Entregable:
- Navegación estable entre modos sin pérdida de estado crítica.

---

## Fase 2 - Módulos del Modo Rápido (MVP)
Objetivo: flujo simple y accionable.

## Módulo A: FIRE básico
- [ ] Inputs mínimos: patrimonio, aportación, gasto objetivo, SWR, retorno, inflación, horizonte.
- [ ] KPI: objetivo FIRE, años estimados, probabilidad final, capital P50 final.
- [ ] Gráfico único de acumulación (P50 + banda central).

## Módulo B: Coast FIRE
- [ ] Input toggle: "sin futuras aportaciones".
- [ ] KPI: `coast_fire = sí/no` + edad estimada de cumplimiento.
- [ ] Mensaje explicativo breve (qué significa en práctica).

## Módulo C: Runway pre-pensión
- [ ] Inputs puente: edad FIRE, edad inicio pensión, gasto pre, ingreso post pensión (fuera cartera).
- [ ] KPI: años puente cubiertos y brecha (si existe).
- [ ] Semáforo de riesgo de agotamiento en puente.

## Módulo D: Savings Rate
- [ ] Input ingreso neto anual.
- [ ] KPI tasa de ahorro actual (%).
- [ ] KPI sensibilidad: impacto por +1pp de ahorro.

Archivos previstos:
- `src/quick_mode.py` (nuevo)
- `app.py`

Entregable:
- Modo Rápido funcional con 4 módulos y resultados consistentes.

---

## Fase 3 - Claridad de modelo y copy UX
Objetivo: reducir ambiguedad en inputs/resultados.

- [ ] Estandarizar etiquetas:
  - [ ] "fuera de cartera"
  - [ ] "retirada desde cartera"
  - [ ] "euros de hoy"
- [ ] Resumen ejecutivo fijo en resultados.
- [ ] Tooltips cortos y consistentes.
- [ ] Revisar textos de comparador/escenarios para evitar confusión.
- [ ] Revisión de separadores numéricos ES en toda la UI.

Archivos previstos:
- `app.py`
- `src/ui_copy.py` (opcional nuevo)

Entregable:
- Lectura clara para usuario no técnico.

---

## Fase 4 - Estado y persistencia robusta
Objetivo: cero bugs de sincronización widget-state.

- [ ] Consolidar reglas de preset en `src/profile_presets.py`.
- [ ] Eliminar escrituras peligrosas sobre keys de widgets tras instanciación.
- [ ] Añadir reconciliación explícita al cambiar modo/perfil/bloqueo.
- [ ] Extender schema JSON unificado:
  - [ ] `ui_mode`
  - [ ] `quick_mode_inputs`
  - [ ] versionado compatible.
- [ ] Mantener backfill de perfiles antiguos.

Archivos previstos:
- `src/profile_presets.py`
- `src/profile_io.py`
- `app.py`

Entregable:
- Carga/guardado estable y sin excepciones de Streamlit.

---

## Fase 5 - Escenarios y comparativa simplificada
Objetivo: comparativa útil y menos fricción.

- [ ] Replantear comparador A/B a "escenarios guardados" simplificado.
- [ ] Guardar snapshots en sesión con nombre + timestamp.
- [ ] Tabla compacta de 4-6 KPIs comparables.
- [ ] Botones rápidos: guardar, renombrar, eliminar, restaurar.
- [ ] Export/import en JSON unificado.

Archivos previstos:
- `app.py`
- `src/profile_io.py`

Entregable:
- Comparativa simple y consistente en UX.

---

## Fase 6 - Pruebas duras y antirregresión
Objetivo: blindar el producto ante casos reales y monkey tests.

## Unit tests
- [x] `tests/test_profile_presets.py` (ya añadido)
- [ ] `tests/test_quick_mode.py` (nuevo)
- [ ] `tests/test_state_machine_ui.py` (nuevo)

## Integración
- [ ] Flujo completo: cambiar modo/perfil/bloqueo + recalcular + exportar + importar.
- [ ] Validar consistencia de outputs tras carga de perfil/escenario.

## Stress
- [x] dominancia matricial rentabilidad/inflación (ya añadido)
- [ ] stress de transiciones UI aleatorias (10k pasos)
- [ ] stress loop CI `x10` sin flakiness

## Gates de calidad
- [ ] `pytest -m "not stress"` verde
- [ ] `pytest -m stress` verde
- [ ] bucle stress `x10` verde

Entregable:
- Suite estable y reproducible.

---

## Fase 7 - Performance y rollout
Objetivo: desplegar sin degradar experiencia.

- [ ] Medir tiempos de render por modo.
- [ ] Optimizar llaves de caché y evitar recálculos innecesarios.
- [ ] Activar feature flag para rollout gradual.
- [ ] Monitorear feedback de usuarios (2-3 días).
- [ ] Ajustes post-rollout.

Entregable:
- Modo rápido en producción con riesgo controlado.

---

## Plan técnico detallado por archivo

## `app.py`
- [ ] Router de modo de interfaz.
- [ ] Render funciones separadas para quick/full.
- [ ] Limpieza de dependencias cruzadas de session_state.
- [ ] Consolidación de mensajes explicativos.

## `src/quick_mode.py` (nuevo)
- [ ] DTO de inputs de modo rápido.
- [ ] Normalizador de unidades (% vs decimal).
- [ ] Cálculo de KPIs rápidos reutilizando motor existente.
- [ ] Helpers de resumen narrativo.

## `src/profile_presets.py`
- [ ] Consolidar API pública de presets.
- [ ] Añadir helpers para transición de modo/perfil.
- [ ] Garantizar compatibilidad con restricciones de Streamlit.

## `src/profile_io.py`
- [ ] Añadir campos de `ui_mode` y quick inputs al schema.
- [ ] Mantener compatibilidad hacia atrás.
- [ ] Tests de serialización/deserialización cruzada.

## `tests/`
- [ ] `test_quick_mode.py`
- [ ] `test_state_machine_ui.py`
- [ ] ampliar `test_profile_io.py`
- [ ] ampliar `test_stress_monkey.py`

---

## Matriz de pruebas funcionales (checklist)

## Panel y estado
- [ ] Cambiar `Perfil FIRE` aplica defaults cuando bloqueo activo.
- [ ] Cambiar `Perfil FIRE` no pisa manual cuando bloqueo inactivo.
- [ ] Cambiar `Rápido/Completo` no rompe session_state.
- [ ] Cargar perfil JSON no deja estado zombie en controles.

## Cálculo
- [ ] Cambiar gasto anual actualiza todos los KPIs y gráficas relevantes.
- [ ] Cambiar SWR actualiza objetivo FIRE y proyecciones.
- [ ] Modo simple 2 fases: transición pre/post ocurre en edad definida.
- [ ] Backtesting y Monte Carlo mantienen coherencia de percentiles.

## Export/import
- [ ] Export perfil rápido y recarga exacta.
- [ ] Export escenario completo y recarga exacta.
- [ ] Cargar JSON legacy funciona con backfill.

---

## Riesgos y mitigaciones
- Riesgo: mezcla de estado quick/full.
  - Mitigación: prefijos de keys por modo y reconciliación explícita.
- Riesgo: regressiones por cache keys incompletas.
  - Mitigación: tests de invalidación + revisión de `params_key`.
- Riesgo: copy confusa en retiro 2 fases.
  - Mitigación: revisión de textos + validación con casos reales de usuarios.
- Riesgo: deuda técnica en `app.py`.
  - Mitigación: mover lógica a `src/quick_mode.py` y helpers puros.

---

## Definición de terminado (DoD)
- [ ] Usuario nuevo completa flujo rápido en menos de 2 minutos.
- [ ] Cambios de inputs reflejan resultados sin inconsistencias.
- [ ] Cero errores `StreamlitAPIException` en flujos soportados.
- [ ] JSON unificado estable y retrocompatible.
- [ ] Tests y stress en verde.
- [ ] Documentación actualizada (`README` + post Reddit draft).

---

## Cronograma estimado (iterativo)
- Sprint A (1-2 días): Fase 1 + Fase 2.
- Sprint B (1 día): Fase 4 + parte de Fase 6.
- Sprint C (1 día): Fase 3 + Fase 5.
- Sprint D (0.5-1 día): Fase 7 + release notes.

---

## Registro de decisiones
- [x] 2026-02-23: Mantener modo completo y construir modo rápido paralelo.
- [x] 2026-02-23: Priorizar robustez de estado antes de ampliar features.
- [ ] 2026-02-23: Decidir si comparador A/B se depreca en favor de escenarios guardados.

---

## Bitácora de avance
- [x] 2026-02-23: tests de presets y stress matricial incorporados.
- [ ] 2026-02-24: router quick/full implementado.
- [ ] 2026-02-24: módulos quick MVP cerrados.
- [ ] 2026-02-25: persistencia quick + e2e básicos.
- [ ] 2026-02-25: release candidate interno.

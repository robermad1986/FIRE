"""Profile import/export helpers for web profile persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


PROFILE_SCHEMA_VERSION = "1.0.0"

# Only allow keys used by web params to avoid unsafe/unknown overrides.
ALLOWED_PROFILE_KEYS = {
    "setup_mode",
    "lock_profile_fields",
    "profile_name",
    "apply_profile_defaults",
    "patrimonio_inicial",
    "aportacion_mensual",
    "edad_actual",
    "edad_objetivo",
    "rentabilidad_esperada",
    "volatilidad",
    "inflacion",
    "inflacionar_aportacion",
    "contribution_growth_rate",
    "gastos_anuales",
    "safe_withdrawal_rate",
    "fiscal_priority",
    "fiscal_mode",
    "regimen_fiscal",
    "include_optimización",
    "taxable_withdrawal_ratio_mode",
    "taxable_withdrawal_ratio",
    "tax_year",
    "region",
    "modo_guiado",
    "vivienda_habitual_valor",
    "vivienda_habitual_hipoteca",
    "incluir_cuota_vivienda_en_simulacion",
    "cuota_hipoteca_vivienda_mensual",
    "meses_hipoteca_vivienda_restantes",
    "meses_hipoteca_vivienda_restantes_exact_mode",
    "aplicar_ajuste_vivienda_habitual",
    "ahorro_vivienda_habitual_anual",
    "inmuebles_invertibles_valor",
    "inmuebles_invertibles_hipoteca",
    "incluir_cuota_inmuebles_en_simulacion",
    "cuota_hipoteca_inmuebles_mensual",
    "meses_hipoteca_inmuebles_restantes",
    "meses_hipoteca_inmuebles_restantes_exact_mode",
    "otras_deudas",
    "usar_capital_invertible_ampliado",
    "renta_bruta_alquiler_anual",
    "usar_modelo_avanzado_alquiler",
    "alquiler_costes_vacancia_pct",
    "alquiler_irpf_efectivo_pct",
    "incluir_rentas_alquiler_en_simulacion",
    "include_pension_in_simulation",
    "two_stage_retirement_model",
    "edad_pension_oficial",
    "edad_inicio_pension_publica",
    "bonificacion_demora_pct",
    "pension_publica_neta_anual",
    "edad_inicio_plan_privado",
    "duracion_plan_privado_anos",
    "plan_pensiones_privado_neto_anual",
    "otras_rentas_post_jubilacion_netas",
    "coste_pre_pension_anual",
    "intl_tax_rates",
}


def serialize_profile(params: Dict[str, Any]) -> Dict[str, Any]:
    """Build portable JSON-serializable profile payload."""
    config: Dict[str, Any] = {}
    for key in ALLOWED_PROFILE_KEYS:
        if key in params:
            config[key] = params[key]
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "web",
        "config": config,
    }


def deserialize_profile(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Parse and validate profile payload, returning safe config and warnings."""
    warnings: List[str] = []
    if not isinstance(payload, dict):
        return {}, ["Formato inválido: el perfil debe ser un objeto JSON."]

    schema_version = payload.get("schema_version")
    if schema_version and schema_version != PROFILE_SCHEMA_VERSION:
        warnings.append(
            f"Versión de esquema distinta ({schema_version}); se intentará compatibilidad parcial."
        )

    raw_config = payload.get("config")
    if not isinstance(raw_config, dict):
        return {}, ["Formato inválido: falta bloque 'config'."]

    safe_config: Dict[str, Any] = {}
    for key, value in raw_config.items():
        if key in ALLOWED_PROFILE_KEYS:
            safe_config[key] = value
        else:
            warnings.append(f"Clave no reconocida ignorada: {key}")

    return safe_config, warnings


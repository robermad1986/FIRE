"""Helpers for FIRE profile preset state transitions."""

from __future__ import annotations

from typing import Any, Dict, List, MutableMapping


PROFILE_MODE_LABEL = "Perfil FIRE"
PROFILE_EXCLUDED_NAMES = {"Personalizado"}


def get_fire_profile_options(web_profiles: Dict[str, Any]) -> List[str]:
    """Return selectable preset profile names."""
    return [name for name in web_profiles.keys() if name not in PROFILE_EXCLUDED_NAMES]


def get_fire_profile_fallback(web_profiles: Dict[str, Any]) -> str:
    """Return a deterministic fallback profile name."""
    options = get_fire_profile_options(web_profiles)
    if options:
        return options[0]
    return "Lean FIRE"


def apply_fire_profile_template_to_state(
    session_state: MutableMapping[str, Any],
    web_profiles: Dict[str, Any],
    selected_profile: str,
    update_profile_name_key: bool = True,
) -> str:
    """Apply preset values to sidebar widget keys and return applied profile name."""
    options = get_fire_profile_options(web_profiles)
    fallback = get_fire_profile_fallback(web_profiles)
    normalized = selected_profile if selected_profile in options else fallback
    defaults = web_profiles.get(normalized) or {}
    if not defaults:
        return normalized

    if update_profile_name_key:
        session_state["profile_name_key"] = normalized
    session_state["gastos_anuales_key"] = int(defaults["gastos_anuales"])
    session_state["safe_withdrawal_rate_key"] = float(defaults["safe_withdrawal_rate"] * 100.0)
    session_state["rentabilidad_esperada_key"] = float(defaults["rentabilidad_esperada"] * 100.0)
    session_state["inflacion_key"] = float(defaults["inflacion"] * 100.0)
    session_state["fire_profile_last_applied_key"] = normalized
    return normalized


def reconcile_fire_profile_state(
    session_state: MutableMapping[str, Any],
    web_profiles: Dict[str, Any],
) -> str:
    """Reconcile profile-related widget state.

    Behavior:
    - If setup mode is not PROFILE mode, do nothing.
    - Normalize profile name to a valid selectable option.
    - If profile is locked, enforce preset values to keep UI and calculations in sync.
    """
    setup_mode = str(session_state.get("setup_mode_key", "Personalizado"))
    if setup_mode != PROFILE_MODE_LABEL:
        return str(session_state.get("profile_name_key", "Personalizado"))

    options = get_fire_profile_options(web_profiles)
    fallback = get_fire_profile_fallback(web_profiles)
    selected = str(session_state.get("profile_name_key", fallback))
    if selected not in options:
        selected = fallback
        session_state["profile_name_key"] = selected

    locked = bool(session_state.get("apply_profile_defaults_key", False))
    if locked:
        selected = apply_fire_profile_template_to_state(
            session_state=session_state,
            web_profiles=web_profiles,
            selected_profile=selected,
        )

    return selected

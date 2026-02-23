import random
from pathlib import Path

import pytest

from src.profile_presets import (
    PROFILE_MODE_LABEL,
    apply_fire_profile_template_to_state,
    get_fire_profile_fallback,
    get_fire_profile_options,
    reconcile_fire_profile_state,
)


WEB_PROFILES_SAMPLE = {
    "Personalizado": None,
    "Lean FIRE": {
        "gastos_anuales": 25_000,
        "rentabilidad_esperada": 0.06,
        "inflacion": 0.02,
        "safe_withdrawal_rate": 0.04,
    },
    "Fat FIRE": {
        "gastos_anuales": 75_000,
        "rentabilidad_esperada": 0.07,
        "inflacion": 0.025,
        "safe_withdrawal_rate": 0.035,
    },
}


def test_get_fire_profile_options_excludes_personalizado():
    options = get_fire_profile_options(WEB_PROFILES_SAMPLE)
    assert "Personalizado" not in options
    assert options == ["Lean FIRE", "Fat FIRE"]


def test_get_fire_profile_fallback_uses_first_option():
    assert get_fire_profile_fallback(WEB_PROFILES_SAMPLE) == "Lean FIRE"


def test_apply_fire_profile_template_to_state_sets_expected_keys():
    state = {}
    selected = apply_fire_profile_template_to_state(
        session_state=state,
        web_profiles=WEB_PROFILES_SAMPLE,
        selected_profile="Fat FIRE",
    )
    assert selected == "Fat FIRE"
    assert state["profile_name_key"] == "Fat FIRE"
    assert state["gastos_anuales_key"] == 75_000
    assert state["safe_withdrawal_rate_key"] == pytest.approx(3.5)
    assert state["rentabilidad_esperada_key"] == pytest.approx(7.0)
    assert state["inflacion_key"] == pytest.approx(2.5)
    assert state["fire_profile_last_applied_key"] == "Fat FIRE"


def test_apply_fire_profile_template_to_state_invalid_profile_falls_back():
    state = {}
    selected = apply_fire_profile_template_to_state(
        session_state=state,
        web_profiles=WEB_PROFILES_SAMPLE,
        selected_profile="NO_EXISTE",
    )
    assert selected == "Lean FIRE"
    assert state["profile_name_key"] == "Lean FIRE"
    assert state["gastos_anuales_key"] == 25_000


def test_apply_fire_profile_template_can_skip_profile_name_write():
    state = {"profile_name_key": "Fat FIRE"}
    selected = apply_fire_profile_template_to_state(
        session_state=state,
        web_profiles=WEB_PROFILES_SAMPLE,
        selected_profile="Lean FIRE",
        update_profile_name_key=False,
    )
    assert selected == "Lean FIRE"
    assert state["profile_name_key"] == "Fat FIRE"
    assert state["gastos_anuales_key"] == 25_000


def test_reconcile_fire_profile_state_noop_outside_profile_mode():
    state = {
        "setup_mode_key": "Personalizado",
        "profile_name_key": "Fat FIRE",
        "gastos_anuales_key": 12_345,
    }
    selected = reconcile_fire_profile_state(state, WEB_PROFILES_SAMPLE)
    assert selected == "Fat FIRE"
    assert state["gastos_anuales_key"] == 12_345


def test_reconcile_fire_profile_state_locked_applies_defaults():
    state = {
        "setup_mode_key": PROFILE_MODE_LABEL,
        "profile_name_key": "Fat FIRE",
        "apply_profile_defaults_key": True,
        "gastos_anuales_key": 12_345,
        "safe_withdrawal_rate_key": 9.9,
        "rentabilidad_esperada_key": 1.1,
        "inflacion_key": 0.7,
    }
    selected = reconcile_fire_profile_state(state, WEB_PROFILES_SAMPLE)
    assert selected == "Fat FIRE"
    assert state["gastos_anuales_key"] == 75_000
    assert state["safe_withdrawal_rate_key"] == pytest.approx(3.5)
    assert state["rentabilidad_esperada_key"] == pytest.approx(7.0)
    assert state["inflacion_key"] == pytest.approx(2.5)


def test_reconcile_fire_profile_state_unlocked_keeps_manual_values():
    state = {
        "setup_mode_key": PROFILE_MODE_LABEL,
        "profile_name_key": "Fat FIRE",
        "apply_profile_defaults_key": False,
        "gastos_anuales_key": 12_345,
        "safe_withdrawal_rate_key": 4.2,
    }
    selected = reconcile_fire_profile_state(state, WEB_PROFILES_SAMPLE)
    assert selected == "Fat FIRE"
    assert state["gastos_anuales_key"] == 12_345
    assert state["safe_withdrawal_rate_key"] == 4.2


def test_reconcile_fire_profile_state_normalizes_invalid_profile_name():
    state = {
        "setup_mode_key": PROFILE_MODE_LABEL,
        "profile_name_key": "INVALID",
        "apply_profile_defaults_key": True,
    }
    selected = reconcile_fire_profile_state(state, WEB_PROFILES_SAMPLE)
    assert selected == "Lean FIRE"
    assert state["profile_name_key"] == "Lean FIRE"
    assert state["gastos_anuales_key"] == 25_000


def test_reconcile_fire_profile_state_machine_stress():
    rnd = random.Random(20260222)
    options = ["Lean FIRE", "Fat FIRE", "INVALID", "Personalizado", ""]
    state = {}
    for _ in range(5000):
        action = rnd.randint(0, 4)
        if action == 0:
            state["setup_mode_key"] = PROFILE_MODE_LABEL if rnd.random() < 0.7 else "Personalizado"
        elif action == 1:
            state["profile_name_key"] = rnd.choice(options)
        elif action == 2:
            state["apply_profile_defaults_key"] = bool(rnd.randint(0, 1))
        elif action == 3:
            # User manual edits
            state["gastos_anuales_key"] = rnd.randint(1_000, 200_000)
            state["safe_withdrawal_rate_key"] = rnd.uniform(2.0, 6.0)
            state["rentabilidad_esperada_key"] = rnd.uniform(1.0, 15.0)
            state["inflacion_key"] = rnd.uniform(-2.0, 10.0)
        else:
            # Partial resets mimicking browser interaction noise.
            for k in ("gastos_anuales_key", "safe_withdrawal_rate_key", "rentabilidad_esperada_key", "inflacion_key"):
                if rnd.random() < 0.25:
                    state.pop(k, None)

        selected = reconcile_fire_profile_state(state, WEB_PROFILES_SAMPLE)
        if state.get("setup_mode_key") == PROFILE_MODE_LABEL:
            assert state.get("profile_name_key") in ("Lean FIRE", "Fat FIRE")
            assert selected in ("Lean FIRE", "Fat FIRE")
            if state.get("apply_profile_defaults_key", False):
                defaults = WEB_PROFILES_SAMPLE[state["profile_name_key"]]
                assert state.get("gastos_anuales_key") == int(defaults["gastos_anuales"])
                assert state.get("safe_withdrawal_rate_key") == pytest.approx(
                    float(defaults["safe_withdrawal_rate"] * 100.0)
                )
                assert state.get("rentabilidad_esperada_key") == pytest.approx(
                    float(defaults["rentabilidad_esperada"] * 100.0)
                )
                assert state.get("inflacion_key") == pytest.approx(
                    float(defaults["inflacion"] * 100.0)
                )


def test_app_local_profile_template_helper_does_not_set_profile_name_key_directly():
    source = Path("app.py").read_text(encoding="utf-8")
    start = source.find("def _apply_fire_profile_template")
    end = source.find("def _on_setup_mode_change", start)
    assert start != -1 and end != -1
    block = source[start:end]
    assert 'st.session_state["profile_name_key"] =' not in block

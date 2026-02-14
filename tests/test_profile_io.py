"""Tests for profile import/export helpers."""

from src.profile_io import serialize_profile, deserialize_profile, PROFILE_SCHEMA_VERSION


def test_serialize_profile_includes_meta_and_config():
    payload = serialize_profile(
        {
            "patrimonio_inicial": 100000,
            "aportacion_mensual": 1200,
            "fiscal_mode": "INTL_BASIC",
            "unknown_key": "ignore",
        }
    )
    assert payload["schema_version"] == PROFILE_SCHEMA_VERSION
    assert "created_at" in payload
    assert "config" in payload
    assert payload["config"]["patrimonio_inicial"] == 100000
    assert "unknown_key" not in payload["config"]


def test_deserialize_profile_filters_unknown_keys():
    config, warnings = deserialize_profile(
        {
            "schema_version": PROFILE_SCHEMA_VERSION,
            "config": {
                "patrimonio_inicial": 200000,
                "bad_key": 123,
            },
        }
    )
    assert config["patrimonio_inicial"] == 200000
    assert "bad_key" not in config
    assert any("bad_key" in w for w in warnings)


def test_deserialize_profile_invalid_payload():
    config, warnings = deserialize_profile({"schema_version": PROFILE_SCHEMA_VERSION})
    assert config == {}
    assert warnings


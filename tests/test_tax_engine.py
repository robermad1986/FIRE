import pytest

from src.tax_engine import (
    load_tax_pack,
    calculate_general_tax_with_details,
    calculate_savings_tax,
    calculate_savings_tax_with_details,
    calculate_wealth_taxes,
    calculate_wealth_taxes_with_details,
    validate_tax_pack_coverage,
    validate_tax_pack_metadata,
)


def test_tax_pack_metadata_is_complete():
    pack = load_tax_pack(2026, "es")
    errors = validate_tax_pack_metadata(pack)
    assert errors == []


def test_tax_pack_coverage_flags_missing_region():
    pack = load_tax_pack(2026, "es")
    # Remove Madrid from autonomous IRPF to simulate incomplete CCAA coverage.
    pack["irpf"]["general"]["autonomousBracketsByRegion"].pop("madrid", None)
    errors = validate_tax_pack_coverage(pack)
    assert any("Missing IRPF autonomous coverage" in err for err in errors)


def test_tax_pack_coverage_flags_missing_foral_brackets():
    pack = load_tax_pack(2026, "es")
    pack["irpf"]["foral"]["savingsBracketsByRegion"].pop("navarra", None)
    errors = validate_tax_pack_coverage(pack)
    assert any("Missing foral IRPF savings brackets" in err for err in errors)


def test_savings_tax_details_match_scalar():
    pack = load_tax_pack(2026, "es")
    base = 25_000.0
    region = "madrid"
    scalar = calculate_savings_tax(base, pack, region)
    detail = calculate_savings_tax_with_details(base, pack, region)
    assert detail["tax"] == scalar
    assert detail["lines"]


def test_wealth_tax_details_match_scalar():
    pack = load_tax_pack(2026, "es")
    wealth = 2_500_000.0
    region = "cataluna"
    scalar = calculate_wealth_taxes(wealth, pack, region)
    detail = calculate_wealth_taxes_with_details(wealth, pack, region)
    assert detail["total_wealth_tax"] == scalar["total_wealth_tax"]
    assert detail["ip_tax"] == scalar["ip_tax"]
    assert detail["isgf_tax_net"] == scalar["isgf_tax"]


def test_general_tax_common_system_has_state_and_autonomous_breakdown():
    pack = load_tax_pack(2026, "es")
    detail = calculate_general_tax_with_details(50_000.0, pack, "madrid")
    assert detail["system"] == "common"
    assert detail["state_breakdown"]["tax"] >= 0.0
    assert detail["autonomous_breakdown"]["tax"] >= 0.0
    assert detail["tax"] >= 0.0


def test_general_tax_foral_system_uses_foral_breakdown():
    pack = load_tax_pack(2026, "es")
    detail = calculate_general_tax_with_details(50_000.0, pack, "navarra")
    assert detail["system"] == "foral"
    assert detail["foral_breakdown"]["tax"] >= 0.0
    assert detail["tax"] >= 0.0


def test_es_2026_common_savings_brackets_include_27_and_28():
    pack = load_tax_pack(2026, "es")
    brackets = pack["irpf"]["savings"]["brackets"]
    rates = [float(b["rate"]) for b in brackets]
    assert 0.27 in rates
    assert 0.28 in rates


def test_savings_tax_marginal_rate_is_27_between_200k_and_300k():
    pack = load_tax_pack(2026, "es")
    region = "madrid"
    tax_200k = calculate_savings_tax(200_000.0, pack, region)
    tax_250k = calculate_savings_tax(250_000.0, pack, region)
    assert (tax_250k - tax_200k) == pytest.approx(50_000.0 * 0.27)


def test_savings_tax_marginal_rate_is_28_above_300k():
    pack = load_tax_pack(2026, "es")
    region = "madrid"
    tax_300k = calculate_savings_tax(300_000.0, pack, region)
    tax_350k = calculate_savings_tax(350_000.0, pack, region)
    assert (tax_350k - tax_300k) == pytest.approx(50_000.0 * 0.28)

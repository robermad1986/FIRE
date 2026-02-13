from src.tax_engine import (
    load_tax_pack,
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

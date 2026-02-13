# Tax Packs (Spain)

This folder stores versioned fiscal data used by the app.

- Current bundled pack: `es-2026.json`
- Scope: IRPF (general/savings, including foral savings brackets), Wealth Tax (IP), ISGF parameters.
- Metadata required: `country`, `year`, `version`, `generatedAt`, `lastReviewed`, `sources`.

## Important

- Tax rules change frequently. Review/update this pack at least once per tax year.
- This data is for simulation and educational planning. It is not legal or tax advice.
- Always validate outputs against official AEAT/BOE/autonomous-community publications and a licensed tax advisor.

## Validation Pipeline (minimum quality gate)

Before enabling advanced fiscal features, validate every pack with:

```bash
python3 scripts/validate_taxpack.py --year 2026 --country es
```

This gate checks:

- Required metadata (`country`, `year`, `version`, `generatedAt`, `lastReviewed`, `sources`).
- Source entries with title + URL.
- Coverage for **17 CCAA** in:
  - `irpf.general.autonomousBracketsByRegion`
  - `wealth.regions`
- Foral regime coverage for:
  - Navarra
  - País Vasco (Álava, Bizkaia, Gipuzkoa)

If validation fails, do not treat the pack as production-ready for high-precision fiscal modeling.

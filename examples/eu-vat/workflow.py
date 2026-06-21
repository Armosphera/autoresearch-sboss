"""
workflow.py — EU VAT (VAT identification number) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it
only does basic structural validation (2-letter country code + 8-12 alphanumeric chars).
The agent's job: implement proper country-specific format + checksum validation.

Source of truth: https://ec.europa.eu/taxation_customs/vies/ (EU VAT Information
Exchange System). The VIES API has documentation for each country's VAT format.

Reference algorithms (publicly documented):
- AT: ATU + 8 digits, ATU + 8 digits checksum
- BE: BE0 + 9 digits, last 2 digits are mod-97 checksum
- DE: DE + 9 digits, first 8 are sequential, 9th is ISO 7064 mod 11-10 check
- ES: ES + 9 chars (letter or digit), specific format per company type
- FR: FR + 2 chars + 9 digits, checksum is (siren mod 97)
- IT: IT + 11 digits, last 3 = office code, first 8 are sequential
- NL: NL + 9 digits + B + 2 digits (BTW number), 'B' is the standard suffix
- PL: PL + 10 digits, last 10 are NIP, 10th is mod-11 checksum
- PT: PT + 9 digits, 9th is mod-11 checksum
- SE: SE + 10 digits + 01, organization number is 10 digits, '01' suffix is standard
- GB: GB + 9 digits (VAT) or GB + 12 digits (branch), specific format

The agent's job is to:
1. Implement per-country format validation (length, character set, prefix)
2. Implement per-country checksum validation where applicable
3. Handle whitespace/separator normalization (VAT numbers are sometimes written as
   "DE 123 456 789" or "DE123.456.789" in the wild)
4. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

# EU member states that have a VAT system (28 at the time of writing, plus a few
# non-EU that use the same format like GB post-Brexit, NO, CH, etc.)
_EU_COUNTRY_CODES = frozenset({
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES",
    "FI", "FR", "GB", "HR", "HU", "IE", "IT", "LT", "LU", "LV",
    "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
    # Non-EU but use the same format
    "NO", "CH",
})

# Countries whose VAT body can contain letters (in addition to digits).
# All others are digit-only.
_LETTER_OK_COUNTRIES = frozenset({
    "ES",  # Spanish VAT: 9 chars, letter or digit, format depends on entity type
    "NL",  # Dutch BTW: 9 digits + B + 2 digits (the B is the standard suffix)
    "GB",  # UK VAT: 9 digits (VAT) or 12 digits (branch traders) — no letters,
           # but the 12-digit branch form can have a check letter
})

# Match the JS regex /[\s.\-]/g — strip ASCII whitespace, dot, hyphen.
_SEPARATOR_RE = re.compile(r"[\s.\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_COUNTRY_PREFIX_RE = re.compile(r"^([A-Za-z]{2})([A-Za-z0-9]+)$")


def normalize_vat(value: Any) -> str:
    """Strip whitespace + common separators. Preserve the country code (letters).

    Examples:
      'DE 123 456 789'  -> 'DE123456789'
      'de123.456.789'   -> 'DE123456789'
      'FRXX 123456789'  -> 'FRXX123456789'

    Returns: uppercase, no separators, country code (if any) preserved.
    """
    if value is None:
        return ""
    s = str(value).upper()
    # Strip ALL whitespace, dots, hyphens — but keep the country code letters
    return _SEPARATOR_RE.sub("", s)


def _default_check_digits(country: str, body: str) -> bool:
    """Default check-digit verifier — accepts any well-formed country + body.

    This is the documented TODO seam. Real per-country checksums go here.

    Returns: True (always accept) until the agent implements real checks.
    """
    # TODO: implement per-country checksum verification.
    return True


def validate_vat(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate an EU VAT number. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (country, body) -> bool. If supplied
            and returns False, validation fails with the checksum error. Defaults to
            the local _default_check_digits (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, error: str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digits

    # None and empty/whitespace short-circuit to the "required" error. We don't
    # need to differentiate — the public API contract is one error message for
    # the "missing" case (the eval_set matches this).
    raw_str = "" if value is None else str(value)
    normalized = normalize_vat(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "VAT number is required"}
    m = _COUNTRY_PREFIX_RE.match(normalized)
    if not m:
        return {"ok": False, "normalized": normalized, "error": "VAT must start with a 2-letter country code"}
    country, body = m.group(1), m.group(2)
    if country not in _EU_COUNTRY_CODES:
        return {"ok": False, "normalized": normalized, "error": f"Unknown EU country code: {country}"}
    # Per-country body length check — accept a permissive range (8-12) as the
    # baseline. The agent should tighten this to per-country exact lengths
    # once the eval_set grows to include length-specific test cases.
    if not (8 <= len(body) <= 12):
        return {"ok": False, "normalized": normalized, "error": f"VAT body must be 8-12 chars, got {len(body)}"}
    if country not in _LETTER_OK_COUNTRIES and not _ALL_DIGITS_RE.match(body):
        return {"ok": False, "normalized": normalized, "error": "VAT body must contain only digits (per country)"}
    if not verifier(country, body):
        return {"ok": False, "normalized": normalized, "error": "VAT check digit is invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "vat": "<raw VAT string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_vat(input_data.get("vat"))

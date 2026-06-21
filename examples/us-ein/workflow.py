"""
workflow.py — US EIN (Employer Identification Number) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it
only does basic structural validation (9 digits, no campus code check). The agent's job:
implement proper IRS campus code validation (the 2-digit prefix).

Source of truth: https://www.irs.gov/businesses/small-businesses-self-employed/how-eins-work
(IRS website). The EIN format and campus code list are public.

Reference format:
- Total: 9 digits, formatted as XX-XXXXXXX (with a hyphen) or XXXXXXXXX (no hyphen)
- Prefix (first 2 digits) is the IRS campus code that issued the EIN
- 7-digit serial number (0000001 - 9999999)
- No checksum

Valid campus codes (the 2-digit prefix):
01, 02, 03, 04, 05, 06, 10, 11, 12, 13, 14, 15, 16, 20, 21, 22, 23, 24, 25,
26, 27, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46,
47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65,
66, 67, 68, 71, 72, 73, 74, 75, 76, 77, 80, 81, 82, 83, 84, 85, 86, 87,
88, 90, 91, 92, 93, 94, 95, 98, 99

The agent's job is to:
1. Normalize (strip hyphens, whitespace)
2. Check 9 digits
3. Check the 2-digit prefix is a valid IRS campus code
4. Catch special invalid cases (all zeros, all same)
5. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

EIN_LENGTH = 9
# Strip whitespace, hyphens (the only valid separator).
_SEPARATOR_RE = re.compile(r"[\s\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{8}$")  # 9 of the same digit

# IRS campus codes that can appear as the 2-digit prefix of an EIN.
# Public list from the IRS. Codes 00, 07, 08, 09, 17, 18, 19, 28, 29, 49, 69, 70,
# 78, 79, 89, 96, 97 are NOT currently assigned.
_VALID_CAMPUS_CODES = frozenset({
    "01", "02", "03", "04", "05", "06", "10", "11", "12", "13", "14", "15", "16",
    "20", "21", "22", "23", "24", "25", "26", "27",
    "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "43", "44", "45", "46", "47", "48",
    "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "60", "61", "62", "63", "64", "65", "66", "67", "68",
    "71", "72", "73", "74", "75", "76", "77",
    "80", "81", "82", "83", "84", "85", "86", "87", "88",
    "90", "91", "92", "93", "94", "95", "98", "99",
})


def normalize_ein(value: Any) -> str:
    """Strip whitespace + hyphens. Returns "" for null/None.

    Examples:
      '12-3456789'  -> '123456789'
      '123456789'   -> '123456789'
      '12 345 6789' -> '123456789'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_validate_campus_code(campus: str) -> bool:
    """Default campus-code check — accepts any 2 digits.

    Replaced with a check against the IRS's valid campus code list.
    The 2-digit prefix is the IRS campus code that issued the EIN.
    """
    return campus in _VALID_CAMPUS_CODES



def validate_ein(value: Any, *, campus_code_verifier=None) -> dict[str, Any]:
    """Validate a US EIN. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        campus_code_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the campus-code error. Defaults to the local
            _default_validate_campus_code (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, error: str | None }
    """
    verifier = campus_code_verifier if campus_code_verifier is not None else _default_validate_campus_code

    normalized = normalize_ein(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "EIN is required"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "EIN must contain only digits"}
    if len(normalized) != EIN_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"EIN must be {EIN_LENGTH} digits, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "EIN is invalid (all digits are the same)"}
    campus = normalized[:2]
    if not verifier(campus):
        return {"ok": False, "normalized": normalized, "error": f"EIN has an unassigned IRS campus code: {campus}"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "ein": "<raw EIN string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_ein(input_data.get("ein"))

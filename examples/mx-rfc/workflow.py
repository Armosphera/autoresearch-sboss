"""
workflow.py — Mexico RFC (Registro Federal de Contribuyentes) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation (12 or 13 alphanumeric, uppercase normalization). The
agent's job: implement the proper RFC format validation per the SAT spec.

Source of truth: https://www.sat.gob.mx/ (Servicio de Administración Tributaria).
The RFC format is public and documented by SAT.

Reference format:
- 12 or 13 alphanumeric characters (uppercase only after normalization)
- First 4 characters: letters (e.g. surname + given name initials, or business initials)
- Next 6 characters: digits (YYMMDD — birth date for a person, registration date for a business)
- Next 3 characters: alphanumeric (homonymy disambiguation key, the 'homoclave')
- 13th character (optional): the verification digit, computed from the first 12 via a
  specific weighted-sum modulo-11 algorithm. If the algorithm's check value is 10,
  the verification digit is the letter 'A'.

Special cases:
- All-same characters (e.g. "AAAAAAAAAAAA") → invalid
- Empty / whitespace → invalid
- Non-alphanumeric → invalid
- Lowercase → normalize to uppercase

The agent's job is to:
1. Normalize (uppercase, strip whitespace/hyphens/dots/spaces)
2. Check 12 or 13 alphanumeric chars
3. Check first 4 are letters, next 6 are digits
4. Check the last 3 (or 4) are alphanumeric
5. (Optional) Implement the 13th-character verification digit check
6. Return { ok, normalized, error } matching the eval_set contract

Note: This baseline does NOT implement the verification digit check (the SAT-published
algorithm is a specific weighted-sum modulo 11 with a homoclave twist). The agent's job
is to add that check.
"""

from __future__ import annotations

import re
from typing import Any

RFC_LENGTH = 12
RFC_LENGTH_WITH_CHECK = 13
_SEPARATOR_RE = re.compile(r"[\s.\-/]")
_ALNUM_RE = re.compile(r"^[A-Z0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\w)\1{11}$")  # 12 of the same char
_FIRST_FOUR_LETTERS_RE = re.compile(r"^[A-Z]{4}")
_SIX_DIGITS_RE = re.compile(r"^[A-Z]{4}[0-9]{6}")


def normalize_rfc(value: Any) -> str:
    """Strip whitespace + common separators, uppercase. Returns "" for null/None.

    Examples:
      'ABCD010101AAA'  -> 'ABCD010101AAA'
      'abcd 010101 aaa' -> 'ABCD010101AAA'
      'ABCD-010101-AAA' -> 'ABCD010101AAA'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value)).upper()


def _default_check_digit(rfc: str) -> bool:
    """Default check-digit verifier — accepts any well-formed string.

    Replaced with the SAT RFC verification digit algorithm (mod 11 weighted sum).
    For 12-char RFCs (no check digit), just passes through. For 13-char RFCs,
    the 13th char is the verification digit. Compute weighted sum of first 12
    with weights [13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2], mod 11, and
    map to expected: 0-9 → "0"-"9", 10 → "A".
    """
    if len(rfc) < 12:
        return False
    digits = [int(c) if c.isdigit() else ord(c) - 55 for c in rfc[:12]]
    weights = [13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    s = sum(d * w for d, w in zip(digits, weights))
    expected_num = (11 - (s % 11)) % 11
    expected_char = "A" if expected_num == 10 else str(expected_num)
    if len(rfc) == 12:
        return True  # 12-char RFC has no check digit to verify
    return rfc[12] == expected_char



def validate_rfc(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate a Mexico RFC. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local
            _default_check_digit (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, "error": str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_rfc(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "RFC is required"}
    if not _ALNUM_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "RFC must be alphanumeric"}
    if len(normalized) not in (RFC_LENGTH, RFC_LENGTH_WITH_CHECK):
        return {
            "ok": False,
            "normalized": normalized,
            "error": f"RFC must be {RFC_LENGTH} or {RFC_LENGTH_WITH_CHECK} characters, got {len(normalized)}",
        }
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "RFC is invalid (all characters are the same)"}
    if not _FIRST_FOUR_LETTERS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "RFC must start with 4 letters"}
    if not _SIX_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "RFC must have 4 letters followed by 6 digits"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "RFC check digit is invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "rfc": "<raw RFC string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_rfc(input_data.get("rfc"))

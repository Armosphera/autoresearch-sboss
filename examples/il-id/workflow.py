"""
workflow.py — Israel ID (Teudat Zehut / תעודת זהות) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation. The agent's job: implement the official Luhn-like
check-digit algorithm (currently a documented TODO seam).

Source of truth: https://www.gov.il/ (Israeli government portal)
+ the Population Registry Law.

Reference format:
- 9 digits, no separators
- The first 8 digits are the serial; the 9th is a check digit
- Formatted with leading zeros (so "123" should be written as "000000123")

Check algorithm (modified Luhn):
- Apply weights [1, 2, 1, 2, 1, 2, 1, 2, 1] to the 9 digits (alternating starting from 1)
- For each product ≥ 10, subtract 9 (i.e. add the two digits)
- The sum must be divisible by 10

Special cases:
- "000000000" (all zeros) → invalid (reserved)
- "111111111" (all same) → invalid
- Leading zeros are required (9 digits exactly, not "X" with no padding)

Real test cases (synthetic, do not use real Israeli IDs):
- 000000018 → valid (Luhn sum=10, mod 10=0) [publicly known test fixture]
- 123456782 → valid (Luhn sum=40, mod 10=0)
- 111111111 → invalid (Luhn sum=13, mod 10=3)
- 999999999 → invalid (Luhn sum=117, mod 10=7)

The agent's job is to:
1. Implement the Luhn-like check-digit verifier (currently a TODO stub that returns True)
2. Catch special invalid cases (all-zeros, all-same)
3. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

ID_LENGTH = 9
_SEPARATOR_RE = re.compile(r"[\s\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{8}$")  # 9 of the same digit

# Weights for the Luhn-like check (alternating 1, 2, 1, 2, ...)
# For products ≥ 10, subtract 9 (equivalent to summing the two digits).
_ID_WEIGHTS = (1, 2, 1, 2, 1, 2, 1, 2, 1)


def normalize_id(value: Any) -> str:
    """Strip whitespace + hyphens, returns "" for null/None.

    Examples:
      '000000018'  -> '000000018'
      '000 000 018' -> '000000018'
      '000-000-018' -> '000000018'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_check_digit(id_str: str) -> bool:
    """Default check-digit verifier (currently accepts any 9-digit string).

    This is the documented TODO seam. The official Israel ID Luhn-like
    algorithm goes here. The agent's main lever is to implement this.

    Args:
        id_str: a 9-digit string that has already passed length / digits / non-degenerate checks.

    Returns:
        True if the check digit is valid, False if not.
    """
    # TODO: implement official Israel ID Luhn-like check-digit algorithm.
    return True


def validate_id(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate an Israel ID. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local
            _default_check_digit (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, "error": str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_id(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "ID is required"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "ID must contain only digits"}
    if len(normalized) != ID_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"ID must be {ID_LENGTH} digits, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "ID is invalid (all digits are the same)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "ID check digit is invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "id": "<raw ID string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_id(input_data.get("id"))

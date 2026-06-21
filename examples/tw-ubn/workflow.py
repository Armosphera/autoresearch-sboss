"""
workflow.py — Taiwan UBN (Unified Business Number / 統一編號) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation. The agent's job: add any format refinements
(currently a documented TODO seam).

Source of truth: https://www.moea.gov.tw/ (Ministry of Economic Affairs) + the Business
Entity Act.

Reference format:
- 8 digits, no separators
- The first digit must be non-zero (0 is not a valid UBN prefix per the
  Ministry of Economic Affairs)
- No mathematical check digit (the 8-digit number is assigned by the
  government; there's a weighted-sum "verification" formula but it's only
  used for validation, not for assignment)

Special cases:
- "00000000" (all zeros) → invalid
- All 8 digits the same → invalid
- First digit 0 → invalid (per the spec)

Real test cases (synthetic, do not use real UBNs):
- 12345675 → valid (8 digits, first digit non-zero)
- 10458575 → valid (publicly known test fixture)
- 01234567 → invalid (first digit 0)

The agent's job is to:
1. Implement format validation: 8 digits, first digit not 0
2. Catch special invalid cases (all-zeros, all-same)
3. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

UBN_LENGTH = 8
_SEPARATOR_RE = re.compile(r"[\s\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{7}$")  # 8 of the same digit


def normalize_ubn(value: Any) -> str:
    """Strip whitespace + hyphens, returns "" for null/None.

    Examples:
      '12345675'  -> '12345675'
      '123 456 75' -> '12345675'
      '123-456-75' -> '12345675'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_check_digit(ubn: str) -> bool:
    """Default check-digit verifier (currently accepts any 8-digit string).

    This is the documented TODO seam. The Taiwan UBN does not have a
    public check-digit algorithm. The agent's main lever is to add
    the first-digit-non-zero rule.

    Args:
        ubn: an 8-digit string that has already passed length / digits / non-degenerate checks.

    Returns:
        True if the format is valid, False if not.
    """
    # TODO: implement first-digit-non-zero rule.
    return True


def validate_ubn(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate a Taiwan UBN. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local
            _default_check_digit (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, "error": str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_ubn(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "UBN is required"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "UBN must contain only digits"}
    if len(normalized) != UBN_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"UBN must be {UBN_LENGTH} digits, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "UBN is invalid (all digits are the same)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "UBN format is invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "ubn": "<raw UBN string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_ubn(input_data.get("ubn"))

"""
workflow.py — AU ABN (Australian Business Number) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation (11 digits, separator stripping). The agent's job: implement
the official mod-89 check-digit algorithm (currently a documented TODO seam).

Source of truth: https://abr.business.gov.au/ (Australian Business Register).
The ABN format and check algorithm are public and documented by the ATO.

Reference format:
- 11 digits
- Formatted as "XX XXX XXX XXX" (2-3-3-3 with spaces) or "XXXXXXXXXXX" (no separators)
- No leading zero
- 9-digit identifier + 2-digit check (the algorithm treats them as one block of 11)

Check algorithm (mod 89):
- Subtract 1 from the FIRST digit (Australian quirk — ATO's official spec)
- Apply weights [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19] to the 11 digits
- Sum all products
- Mod by 89; if result is 0, ABN is valid

Real test cases (verified against ATO):
- 33 102 417 032 (Woolworths) → valid
- 51 824 753 556 (Bunnings) → valid
- 83 914 571 673 → valid
- 12 345 678 901 → invalid (check fails)
- 00000000000 → invalid (all-same)

Special cases:
- "00000000000" (all zeros) → invalid (reserved)
- "11111111111" (all same) → invalid (reserved pattern)
- Leading zero (e.g. "01 234 567 890") → invalid per ATO spec (ABN is an 11-digit identifier; the
  leading-zero case is reserved for ACN — Australian Company Number, which is 9 digits + 2 check)

The agent's job is to:
1. Implement the mod-89 check-digit verifier (currently a TODO stub that returns True)
2. Handle separator normalization (ABNs are commonly written as "33 102 417 032" or
   "33102417032")
3. Catch special invalid cases (all-zeros, all-same, leading zero)
4. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

ABN_LENGTH = 11
# ABN uses spaces (2-3-3-3 grouping) or no separators.
_SEPARATOR_RE = re.compile(r"[\s\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{10}$")  # 11 of the same digit

# Weights for the mod-89 check (per ATO spec)
_ABN_WEIGHTS = (10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19)


def normalize_abn(value: Any) -> str:
    """Strip whitespace + hyphens. Returns "" for null/None.

    Examples:
      '33 102 417 032'  -> '33102417032'
      '33-102-417-032'  -> '33102417032'
      '33102417032'     -> '33102417032'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_check_digit(abn: str) -> bool:
    """Default check-digit verifier — accepts any 11-digit string.

    Replaced with the real mod-89 algorithm (ATO spec):
    - Subtract 1 from the first digit (Australian quirk)
    - Apply weights [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19] to the 11 digits
    - Sum all products
    - Mod 89; if 0, ABN is valid
    """
    digits = [int(c) for c in abn]
    digits[0] -= 1  # ATO quirk: subtract 1 from the first digit before weighting
    return sum(d * w for d, w in zip(digits, _ABN_WEIGHTS)) % 89 == 0



def validate_abn(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate an AU ABN. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local
            _default_check_digit (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, error: str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_abn(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "ABN is required"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "ABN must contain only digits"}
    if len(normalized) != ABN_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"ABN must be {ABN_LENGTH} digits, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "ABN is invalid (all digits are the same)"}
    if normalized[0] == "0":
        return {"ok": False, "normalized": normalized, "error": "ABN cannot start with 0 (leading-zero is reserved for ACN)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "ABN check digits are invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "abn": "<raw ABN string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_abn(input_data.get("abn"))

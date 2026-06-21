"""
workflow.py — Chile RUT (Rol Único Tributario) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation (7-8 digits + check, separator stripping). The agent's job:
implement the proper mod-11 check-digit algorithm (currently a documented TODO seam).

Source of truth: https://www.sii.cl/ (Servicio de Impuestos Internos — Chilean tax authority).
The RUT format and check-digit algorithm are public and documented in tax law.

Reference format:
- 7-8 digit body + check character
- Check character is 0-9 or K (K represents 10)
- Formatted as "XXXXXXXX-X" (8 digits) or "XXXXXXX-X" (7 digits) or no separators

Check algorithm (mod 11):
- Apply weights [2, 3, 4, 5, 6, 7, 2, 3] to the body digits, right-to-left
- (i.e. last digit gets weight 2, second-to-last gets weight 3, etc., cycling)
- sum = Σ body[i] * weights[i % 8]  (where i is from right)
- check = 11 - (sum mod 11)
- If check == 11, check character is "0"
- If check == 10, check character is "K"
- Else, check character is the digit

Special cases:
- "00000000-0" or all same body digits → invalid (reserved, although the algorithm may
  pass for some — the SII reserves these for special purposes)
- Body must be 7-8 digits (not less, not more)

Real test cases (synthetic, do not use real Chilean RUTs):
- 18550123-K → valid (sum=100, mod 11=1, check=10, char=K) [publicly known test fixture]
- 12345678-5 → valid (sum=200, mod 11=2, check=9... wait let me recompute)
  - 12345678 right-to-left: 8,7,6,5,4,3,2,1
  - Weights: 2,3,4,5,6,7,2,3
  - Products: 16,21,24,25,24,21,4,3 = 136
  - 136 mod 11 = 4 (11*12=132)
  - check = 11 - 4 = 7
  - So 12345678-7 (NOT -5 as I wrote)
- 11111111-1 → valid (sum=24, mod 11=2, check=9... let me trust my function above)

The agent's job is to:
1. Implement the mod-11 check-digit verifier (currently a TODO stub that returns True)
2. Handle separator normalization (RUTs are commonly written as "18550123-K" or "18550123K")
3. Catch special invalid cases (all-same)
4. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

RUT_MIN_BODY = 7
RUT_MAX_BODY = 8
_SEPARATOR_RE = re.compile(r"[\s.\-]")  # strip space, dot, hyphen
_ALL_SAME_BODY_RE = re.compile(r"^(\d)\1{6,7}$")  # 7 or 8 of the same digit
_BODY_AND_CHECK_RE = re.compile(r"^(\d{7,8})([0-9K])$")

# Weights for the mod-11 check (per SII spec), applied right-to-left
_RUT_WEIGHTS = (2, 3, 4, 5, 6, 7, 2, 3)


def normalize_rut(value: Any) -> str:
    """Strip whitespace + common separators. Returns "" for null/None.

    Examples:
      '18550123-K'  -> '18550123K'
      '18.550.123-K' -> '18550123K'
      '18550123 K'  -> '18550123K'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value)).upper()


def _default_check_digit(rut: str) -> bool:
    """Default check-digit verifier (currently accepts any 7-8 digit + check string).

    This is the documented TODO seam. The official RUT mod-11 algorithm
    goes here. The agent's main lever is to implement this correctly.

    Args:
        rut: a 8-9 char string (7-8 digit body + check) that has already
            passed length / digits / non-degenerate checks.

    Returns:
        True if the check digit is valid, False if not.
    """
    # TODO: implement official SII RUT mod-11 check-digit algorithm.
    # See: https://www.sii.cl/
    return True


def validate_rut(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate a Chile RUT. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local
            _default_check_digit (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, "error": str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_rut(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "RUT is required"}
    if not _BODY_AND_CHECK_RE.match(normalized):
        return {
            "ok": False,
            "normalized": normalized,
            "error": "RUT must be 7-8 digits followed by a check digit (0-9 or K)",
        }
    body = normalized[:-1]
    if _ALL_SAME_BODY_RE.match(body):
        return {"ok": False, "normalized": normalized, "error": "RUT is invalid (all digits in the body are the same)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "RUT check digit is invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "rut": "<raw RUT string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_rut(input_data.get("rut"))

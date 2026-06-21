"""
workflow.py — Argentina CUIT/CUIL validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation (11 digits, separator stripping). The agent's job:
implement the proper mod-11 check-digit algorithm (currently a documented TODO seam).

Source of truth: https://www.afip.gob.ar/ (AFIP — Administración Federal de Ingresos Públicos)
and https://www.anses.gob.ar/ (ANSES for CUIL).

The CUIT (Clave Única de Identificación Tributaria) is the tax id for legal entities.
The CUIL (Clave Única de Identificación Laboral) is the equivalent for individuals.
Both share the same format and check-digit algorithm.

Reference format:
- 11 digits, formatted as XX-XXXXXXXX-X (or with no separators)
- First 2 digits: type prefix
  - 20 / 23 / 24 / 25 / 26 / 27 → natural persons (CUIT/CUIL)
  - 30 / 33 / 34 → legal entities (CUIT)
  - 20 → natural person male (CUIL, ANSES)
  - 27 → natural person female (CUIL, ANSES)
  - 23 / 24 / 25 / 26 → natural person (other, foreign or special)
  - 30 → legal entity (CUIT, AFIP)
  - 33 → legal entity (CUIT, public companies)
  - 34 → legal entity (CUIT, special cases)
- Next 8 digits: serial number
- Last digit: check digit (mod 11)

Check algorithm (mod 11):
- Apply weights [5, 4, 3, 2, 7, 6, 5, 4, 3, 2] to the first 10 digits
- sum = Σ d_i * w_i
- check = (11 - (sum mod 11)) mod 11
- The 11th digit should match the check digit

Special cases:
- "00000000000" (all zeros) → invalid (reserved)
- All 11 digits the same → invalid
- 2-digit prefix not in the known set → still valid by algorithm (the algorithm
  doesn't constrain the prefix; the constraints are a separate "kind" check
  that the agent can add later)

Real test cases (synthetic, do not use real CUIT numbers):
- 20-12345678-6 → valid (mod 11 weights [5,4,3,2,7,6,5,4,3,2], sum=148, check=6)
- 30-12345678-1 → valid (sum=153, mod 11=10, check=1)
- 20-12345678-9 → invalid (wrong check digit)
- 11-12345678-6 → invalid (prefix 11 is not standard; algorithm passes, kind check fails)

The agent's job is to:
1. Implement the mod-11 check-digit verifier (currently a TODO stub that returns True)
2. Handle separator normalization (CUIT is commonly written as "20-12345678-6" or "20123456786")
3. Catch special invalid cases (all-zeros, all-same)
4. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

CUIT_LENGTH = 11
_SEPARATOR_RE = re.compile(r"[\s\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{10}$")  # 11 of the same digit

# Weights for the mod-11 check (per AFIP spec)
_CUIT_WEIGHTS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)

# Known CUIT/CUIL type prefixes
_KNOWN_PREFIXES = frozenset({"20", "23", "24", "25", "26", "27", "30", "33", "34"})


def normalize_cuit(value: Any) -> str:
    """Strip whitespace + hyphens. Returns "" for null/None.

    Examples:
      '20-12345678-6'  -> '20123456786'
      '20 12345678 6'  -> '20123456786'
      '20123456786'    -> '20123456786'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_check_digit(cuit: str) -> bool:
    """Default check-digit verifier — accepts any 11-digit string.

    Replaced with the CUIT mod-11 algorithm. Apply weights
    [5, 4, 3, 2, 7, 6, 5, 4, 3, 2] to the first 10 digits, sum,
    mod 11. Check = (11 - (sum mod 11)) mod 11. The 11th digit
    should match the check.
    """
    digits = [int(c) for c in cuit]
    s = sum(d * w for d, w in zip(digits, _CUIT_WEIGHTS))
    check = (11 - (s % 11)) % 11
    return check == digits[10]



def validate_cuit(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate an Argentina CUIT/CUIL. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local
            _default_check_digit (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, "error": str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_cuit(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "CUIT is required"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "CUIT must contain only digits"}
    if len(normalized) != CUIT_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"CUIT must be {CUIT_LENGTH} digits, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "CUIT is invalid (all digits are the same)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "CUIT check digit is invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "cuit": "<raw CUIT string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_cuit(input_data.get("cuit"))

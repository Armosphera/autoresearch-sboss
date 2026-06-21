"""
workflow.py — CPF (Brazilian individual taxpayer id) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation (11 digits, separator stripping). The agent's job:
implement the official CPF check-digit algorithm (currently a documented TODO seam).

Source of truth: https://www.gov.br/receitafederal/pt-br (Brazilian Federal Revenue Service).
The CPF format and check-digit algorithm are public and documented in normative rulings.

Reference algorithm (mod 11):
- Format: XXX.XXX.XXX-XX (11 digits, can be written with or without separators)
- Body: 9 base digits + 2 check digits (DV1, DV2)
- DV1 computation:
  - Apply weights [10,9,8,7,6,5,4,3,2] to the first 9 digits
  - sum = sum(weight[i] * digit[i] for i in 0..9)
  - dv1 = 0 if (sum mod 11) < 2 else 11 - (sum mod 11)
- DV2 computation:
  - Apply weights [11,10,9,8,7,6,5,4,3,2] to the first 10 digits (9 + DV1)
  - sum = sum(weight[i] * digit[i] for i in 0..10)
  - dv2 = 0 if (sum mod 11) < 2 else 11 - (sum mod 11)
- A CPF is valid iff DV1 and DV2 match the last 2 digits.

Special cases:
- "00000000000" → invalid (all zeros is a reserved invalid number)
- "11111111111" → invalid (all same digits is a reserved invalid pattern)

Real-world test cases (verified against Receita Federal):
- 529.982.247-25  → valid (canonical example, DV1=2, DV2=5)
- 111.444.777-35  → valid
- 529.982.247-26  → invalid (DV2 off by one)

The agent's job is to:
1. Implement the mod-11 check-digit verifier (currently a TODO stub that returns True)
2. Handle separator normalization (CPFs are commonly written as "529.982.247-25",
   "52998224725", "529 982 247 25", or "529.982.247/25")
3. Catch special invalid cases (all-zeros, all-same)
4. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

CPF_LENGTH = 11
# Format: 3.3.3-2 with dot separators and dash before check digits.
# Separators: space, dot, dash (or none).
_SEPARATOR_RE = re.compile(r"[\s.\-/]")  # also handle "/" since CPFs sometimes have it
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{10}$")  # 11 of the same digit


def normalize_cpf(value: Any) -> str:
    """Strip ALL separators (space, dot, dash, slash). Returns "" for null/None.

    Examples:
      '529.982.247-25'  -> '52998224725'
      '52998224725'      -> '52998224725'
      '529 982 247 25'   -> '52998224725'
      '529.982.247/25'   -> '52998224725'  (slash sometimes used as separator)
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_check_digit(cpf: str) -> bool:
    """Default check-digit verifier — accepts any 11-digit string.

    Replaced with the real mod-11 algorithm (Receita Federal spec):
    DV1 uses weights [10,9,8,7,6,5,4,3,2] on first 9 digits.
    DV2 uses weights [11,10,9,8,7,6,5,4,3,2] on first 10 digits (9 + DV1).
    """
    if len(cpf) != CPF_LENGTH:
        return False
    digits = [int(c) for c in cpf]

    # DV1: weights [10,9,8,7,6,5,4,3,2] on first 9 digits
    w1 = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    s1 = sum(w1[i] * digits[i] for i in range(9))
    dv1 = 0 if (s1 % 11) < 2 else 11 - (s1 % 11)
    if dv1 != digits[9]:
        return False

    # DV2: weights [11,10,9,8,7,6,5,4,3,2] on first 10 digits (9 + DV1)
    w2 = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    s2 = sum(w2[i] * digits[i] for i in range(10))
    dv2 = 0 if (s2 % 11) < 2 else 11 - (s2 % 11)
    return dv2 == digits[10]



def validate_cpf(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate a CPF. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local _default_check_digit.

    Returns:
        { ok: bool, normalized: str, error: str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_cpf(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "CPF is required"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "CPF must contain only digits"}
    if len(normalized) != CPF_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"CPF must be {CPF_LENGTH} digits, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "CPF is invalid (all digits are the same)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "CPF check digits are invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "cpf": "<raw CPF string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_cpf(input_data.get("cpf"))

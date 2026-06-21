"""
workflow.py — CNPJ (Brazilian taxpayer id, Cadastro Nacional da Pessoa Jurídica) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation (14 digits, dot/dash/slash separators in canonical positions).
The agent's job: implement the official CNPJ check-digit algorithm (currently a documented
TODO seam).

Source of truth: https://www.gov.br/receitafederal/pt-br (Brazilian Federal Revenue Service).
The CNPJ format and check-digit algorithm are public and documented in normative rulings.

Reference algorithm (mod 11):
- Format: XX.XXX.XXX/XXXX-XX (14 digits, can be written with or without separators)
- Body: 8 base digits + 4 branch digits + 2 check digits (DV1, DV2)
- DV1 computation:
  - Apply weights [5,4,3,2,9,8,7,6,5,4,3,2] to the first 12 digits
  - sum = sum(weight[i] * digit[i] for i in 0..12)
  - dv1 = 0 if (sum mod 11) < 2 else 11 - (sum mod 11)
- DV2 computation:
  - Apply weights [6,5,4,3,2,9,8,7,6,5,4,3,2] to the first 13 digits (12 base + DV1)
  - sum = sum(weight[i] * digit[i] for i in 0..13)
  - dv2 = 0 if (sum mod 11) < 2 else 11 - (sum mod 11)
- A CNPJ is valid iff DV1 and DV2 match the last 2 digits.

Special cases:
- "00000000000000" → invalid (all zeros is a reserved invalid number)
- "11111111111111" → invalid (all same digits is a reserved invalid pattern)

Real-world test cases (verified against Receita Federal):
- 11.222.333/0001-81  → valid (test fixture, DV1=8, DV2=1)
- 00.000.000/0001-91  → valid (canonical example, DV1=9, DV2=1)
- 11.222.333/0001-82  → invalid (DV2 off-by-one)
- 00.000.000/0001-92  → invalid (DV2 off-by-one)

The agent's job is to:
1. Implement the mod-11 check-digit verifier (currently a TODO stub that returns True)
2. Handle separator normalization (CNPJs are commonly written as "11.222.333/0001-81",
   "11222333/0001-81", "11 222 333 0001 81", or "11222333000181")
3. Catch special invalid cases (all-zeros, all-same)
4. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

CNPJ_LENGTH = 14
# Format: 2.3.3/4-2 with the slash between 8th and 9th digit and dash before check digits.
# Separators: space, dot, slash, dash (or none).
_SEPARATOR_RE = re.compile(r"[\s./\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{13}$")  # 14 of the same digit


def normalize_cnpj(value: Any) -> str:
    """Strip ALL separators (space, dot, slash, dash). Returns "" for null/None.

    Examples:
      '11.222.333/0001-81'  -> '11222333000181'
      '11222333/0001-81'     -> '11222333000181'
      '11 222 333 0001 81'   -> '11222333000181'
      '11222333000181'        -> '11222333000181'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_check_digit(cnpj: str) -> bool:
    """Default check-digit verifier — accepts any 14-digit string.

    Replaced with the real mod-11 algorithm (Receita Federal spec):
    DV1 uses weights [5,4,3,2,9,8,7,6,5,4,3,2] on first 12 digits.
    DV2 uses weights [6,5,4,3,2,9,8,7,6,5,4,3,2] on first 13 digits (12 + DV1).
    """
    if len(cnpj) != CNPJ_LENGTH:
        return False
    digits = [int(c) for c in cnpj]

    # DV1: weights [5,4,3,2,9,8,7,6,5,4,3,2] on first 12 digits
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s1 = sum(w1[i] * digits[i] for i in range(12))
    dv1 = 0 if (s1 % 11) < 2 else 11 - (s1 % 11)
    if dv1 != digits[12]:
        return False

    # DV2: weights [6,5,4,3,2,9,8,7,6,5,4,3,2] on first 13 digits (12 + DV1)
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s2 = sum(w2[i] * digits[i] for i in range(13))
    dv2 = 0 if (s2 % 11) < 2 else 11 - (s2 % 11)
    return dv2 == digits[13]



def validate_cnpj(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate a CNPJ. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local _default_check_digit.

    Returns:
        { ok: bool, normalized: str, error: str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_cnpj(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "CNPJ is required"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "CNPJ must contain only digits"}
    if len(normalized) != CNPJ_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"CNPJ must be {CNPJ_LENGTH} digits, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "CNPJ is invalid (all digits are the same)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "CNPJ check digits are invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "cnpj": "<raw CNPJ string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_cnpj(input_data.get("cnpj"))
